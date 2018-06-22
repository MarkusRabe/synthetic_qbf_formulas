#!/usr/bin/env python3

import os
import sys
import argparse
import glob
import itertools

from aiger import parser, aig
import cnf_tools
from cadet_cmdline_utils import eval_formula


def parse_cmdline():
    print('')
    p = argparse.ArgumentParser()
    p.add_argument('-p', '--prefix', dest='file_prefix', action='store',
                   nargs='?', default='', type=str, metavar='P',
                   help='Prefix given to all files.')
    p.add_argument('-d', '--directory', dest='directory', action='store',
                   default='*.qaiger',
                   help="Directory to read qaiger formulas from. Writing to the same directory (default '*.qaiger')")
    return p.parse_args()

def log_parameters(args):
    filename = os.path.join(args.directory, 'README')
    textfile = open(filename, "w")
    textfile.write(str(sys.argv))
    textfile.write('\n')
    textfile.write(str(args))
    textfile.close()


def aiger_sign(x):
    return - 2*(x % 2) + 1

assert aiger_sign(3) == -1
assert aiger_sign(2) ==  1
assert aiger_sign(15) == -1
assert aiger_sign(14) ==  1

def aiger2dimacs_lit(x):
    assert x > 1  # otherwise represents true or false
    return (x//2) * aiger_sign(x)


def aiger2dimacs_var(x):
    assert x > 1
    assert x % 2 == 0  # is not negated
    assert aiger_sign(x) == 1  # logically equivalent to previous line
    return x//2


def _max_qdimacs_var(aag):
    return aag.header.max_var_index


def _quantifiers(aag):
    universals = set()
    for name, aigervar in aag.inputs.items():
        assert aigervar % 2 == 0
        if name.startswith('1 '):
            universals.add(aiger2dimacs_var(aigervar))

    existentials = []
    for i in range(1, aag.header.max_var_index + 1):
        if i not in universals:
            existentials.append(i)

    return list(universals), existentials


def _gate_to_clauses(gate):
    # assert isinstance(gate, list)
    assert len(gate) == 3
    return [[ - aiger2dimacs_lit(gate[1]), - aiger2dimacs_lit(gate[2]), aiger2dimacs_lit(gate[0])], 
            [   aiger2dimacs_lit(gate[1]), - aiger2dimacs_lit(gate[0])], 
            [   aiger2dimacs_lit(gate[2]), - aiger2dimacs_lit(gate[0])]]


def aag2qdimacs(aag, filename):
    clause_list = list(itertools.chain.from_iterable(map(_gate_to_clauses, aag.gates)))
    assert len(aag.outputs) == 1
    clause_list.append([aiger2dimacs_lit(list(aag.outputs.items())[0][1])])  # output must be true

    universals, existentials = _quantifiers(aag)


    textfile = open(filename, "w")
    textfile.write(f'p cnf {_max_qdimacs_var(aag)} {len(clause_list)}\n')

    textfile.write('a')
    for u in universals:
        assert u > 0
        textfile.write(f' {u}')
    textfile.write(' 0\n')

    textfile.write('e')
    for e in existentials:
        assert e > 0
        textfile.write(f' {e}')
    textfile.write(' 0\n')

    for c in clause_list:
        textfile.write(cnf_tools.clause_to_string(c))
    textfile.close()


def main():
    args = parse_cmdline()
    file_names = glob.glob(args.directory)
    print(f'Detected {len(file_names)} files to transform.')
    
    for file_name in file_names:
        print(f'Transforming {file_name}')
        circuit = parser.load(file_name, to_aig=False)
        aag2qdimacs(circuit, file_name + '.qdimacs')

        # res1 = eval_formula(file_name, VSIDS=True, fresh_seed=False)[0]
        # res2 = eval_formula(file_name + ".qdimacs", VSIDS=True, fresh_seed=False)[0]
        # print(file_name + f': {res1}, {res2}')
        # assert res1 == res2
        



if __name__ == "__main__":
    main()
