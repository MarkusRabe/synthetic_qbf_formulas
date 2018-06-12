#!/usr/bin/env python3

import os
import sys
import argparse
import glob
import itertools

from aux_utils import sign
from cnf_tools import read_qdimacs, write_to_file
from cadet_cmdline_utils import eval_formula


def _parse_cmdline():
    print('')
    p = argparse.ArgumentParser()
    p.add_argument('-s', '--source_directory', dest='source', action='store',
                   default=None,
                   help="Directory to read formulas from. (default '.')")
    p.add_argument('-d', '--destination_directory', dest='destination', action='store',
                   default=None,
                   help="Directory to write formulas to. (default '.')")
    p.add_argument('-t', '--file_type', dest='file_type', action='store',
                   default='*.qdimacs',
                   help="File type to read from folder. (default '*.qdimacs')")
    p.add_argument('-v', '--validate', dest='validate', action='store',
                   default=False, type=bool,
                   help="File type to read from folder. (default '*.qdimacs')")
    p.add_argument('-n', dest='duplicates', action='store', default=2, type=int,
                   help="Number of copies of the original formula to conjoin. (default 2)")
    return p.parse_args()


def duplicate(maxvar, clauses, universals, duplicates):
    assert all(map(lambda u: u > 0 and u <= maxvar, universals))
    assert all(map(lambda c: all(map(lambda l: l != 0 and abs(l) <= maxvar, c)), clauses))

    clause_lists = []
    for d in range(duplicates):
        offset_clauses = [[l + maxvar * d * sign(l) for l in c] for c in clauses]
        clause_lists.append(offset_clauses)

    universals_lists = [[u + maxvar * d for d in range(duplicates)] for u in universals]

    return maxvar * duplicates, list(itertools.chain.from_iterable(clause_lists)), list(itertools.chain.from_iterable(universals_lists))


def main():
    args = _parse_cmdline()
    assert args.duplicates > 0
    if args.source is None or args.destination is None:
        print('Source and Destination directories must be given. See --help.')
        quit()

    file_names = glob.glob(os.path.join(args.source, args.file_type))
    print(f'Detected {len(file_names)} files in directory.')

    if not os.path.exists(args.destination):
        print('Destination directory does not exist; creating {args.destination}')
        os.makedirs(args.destination)

    for file_name in file_names:
        print(f'Processing {file_name}')
        maxvar, clauses, universals = read_qdimacs(file_name)
        maxvar, clauses, universals = duplicate(maxvar, clauses, universals, args.duplicates)

        output_file_name = os.path.basename(file_name).split('.')
        output_file_name.insert(len(output_file_name) - 1, f'{args.duplicates}')
        output_file_name = '.'.join(output_file_name)
        output_file_name = os.path.join(args.destination, output_file_name)

        write_to_file(maxvar, clauses, output_file_name, universals=universals)

        if args.validate:
            print('   Validating')
            returncode_orig, _, _ = eval_formula(file_name, repetitions=1, decision_limit=None, VSIDS=True, fresh_seed=False, CEGAR=True)
            returncode_tandem, _, _ = eval_formula(output_file_name, repetitions=1, decision_limit=None, VSIDS=True, fresh_seed=False, CEGAR=True)
            assert returncode_orig == returncode_tandem


if __name__ == "__main__":
    main()
