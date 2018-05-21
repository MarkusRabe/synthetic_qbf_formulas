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

