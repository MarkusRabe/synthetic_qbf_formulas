#!/usr/bin/env python3

import os
import sys
import argparse
import glob
import itertools
import numpy as np

import cnf_tools
from cadet_cmdline_utils import eval_formula

def parse_cmdline():
    print('')
    p = argparse.ArgumentParser()
    p.add_argument('-r', '--repetitions', dest='repetitions', action='store',
                   metavar='N', nargs='?', default=1, type=int,
                   help='Number of runs to build the average over')
    p.add_argument('-v', '--vsids', dest='vsids', action='store',
                   metavar='V', nargs='?', default=False, type=int,
                   help='Evaluate VSIDS')
    p.add_argument('-d', '--directory', dest='directory', action='store',
                   default='.',
                   help="Directory to read formulas from. (default '.')")
    p.add_argument('-t', '--file_type', dest='file_type', action='store',
                   default='*.qdimacs',
                   help="File type to read from folder. (default '*.qdimacs')")
    return p.parse_args()

def log_measurement_result(args, conflicts, decisions):
    filename = os.path.join(args.directory, 'STATISTICS')
    textfile = open(filename, "w")
    textfile.write(str(sys.argv))
    textfile.write('\n')
    textfile.write(str(args))
    textfile.write(f'\n\nAvg conflicts: {np.mean(conflicts)}\nVar conflicts: {np.var(conflicts)}\n')
    textfile.write(f'\n\nAvg decisions: {np.mean(decisions)}\nVar decisions: {np.var(decisions)}\n')
    textfile.close()

def main():
    args = parse_cmdline()
    file_names = glob.glob(os.path.join(args.directory, args.file_type))
    print(f'Detected {len(file_names)} files in directory.')
    
    conflicts = []
    decisions = []

    for file_name in file_names:
        print(f'Running {file_name}')
        return_code, avg_conflicts, avg_decisions = eval_formula(file_name, VSIDS=args.vsids, repetitions=args.repetitions)
        # print(f'  {avg_conflicts} {avg_conflicts}')
        conflicts.append(avg_conflicts)
        decisions.append(avg_decisions)

    log_measurement_result(args, conflicts, decisions)
    #  avg_conflicts_sum/len(file_names), avg_decisions_sum/len(file_names)

if __name__ == "__main__":
    main()
