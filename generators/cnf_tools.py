#!/usr/bin/env python3

import os
import re
import ipdb
import numpy as np
from subprocess import Popen, PIPE, STDOUT

from aux_utils import sign, is_number


MAX_CLAUSES_PER_VARIABLE = 30000


def clause_to_string(c):
    return ' '.join(map(str,c)) + ' 0\n'


def write_to_file(maxvar, clause_list, filename, universals=set(), comment=None):
    textfile = open(filename, "w")

    if comment is not None:
        comment.replace('\n', '\nc ')
        textfile.write(f'c {comment}\n')

    textfile.write(f'p cnf {maxvar} {len(clause_list)}\n')
    
    if len(universals) > 0:
        textfile.write('a')
        for u in universals:
            textfile.write(f' {u}')
        textfile.write(' 0\n')
        textfile.write('e')
        for v in range(1, maxvar+1):
            if v not in universals:
                textfile.write(f' {v}')
        textfile.write(' 0\n')
    for c in clause_list:
        textfile.write(clause_to_string(c))
    textfile.close()


def read_qdimacs(filename):
    with open(filename, 'r') as f:
        qdimacs = f.readlines()

        clauses = []
        universals = []
        maxvar = 0
        for line in qdimacs:
            lits = line.split()
            if len(lits) == 0:
                continue
            if is_number(lits[0]):
                lits = [int(l) for l in lits[0:-1]]
                clauses.append(lits)
            elif lits[0] == 'p': # header
                assert(lits[1] == 'cnf')
                assert(is_number(lits[2]))
                maxvar = int(lits[2])
                assert(maxvar != 0)
            elif lits[0] == 'a':
                assert len(universals) == 0  # there can only be one set of universals
                universals = [int(x) for x in lits[1:-1]]
            elif lits[0] == 'e':  # nothing to be done
                continue
            else: # must be comment in dimacs format
                 if lits[0] != 'c':
                     print ('Could not read line ' + str(lits))
                     quit() 
        assert (maxvar != 0)
        return maxvar, clauses, universals


def dimacs_to_clauselist(dimacs):
    clauses = []
    assert(MAX_CLAUSES_PER_VARIABLE >= 8) # otherwise code below might not work
    maxvar = 0
    for line in dimacs:
        lits = line.split()[0:-1]
        if is_number(lits[0]):
            lits = list(map(int,lits))
            clauses.append(lits)
        elif lits[0] == b'p': # header
            assert(lits[1] == b'cnf')
            assert(is_number(lits[2]))
            maxvar = int(lits[2])
            assert(maxvar != 0)
        else: # must be comment in dimacs format
             if lits[0] != b'c':
                 print ('Could not read line ' + str(lits))
                 quit() 
    assert (maxvar != 0)
    return maxvar, clauses


def clauses_to_occs(clauses): 
    occs = {}
    for lits in clauses:
        for l in lits:
            if abs(l) not in occs:
                occs[abs(l)] = []
            occs[abs(l)] += [lits] # storing reference to lits so we can manipulate them consistently
    return occs


def occs_to_clauses(occs):
    clause_str_set = set()
    clauses = []
    for v in occs.keys():
        for c in occs[v]:
            c_string = ' '.join(map(str,c))
            if c_string not in clause_str_set: # because string is hashable
                clause_str_set.add(c_string)
                clauses.append(c)
    return clauses

