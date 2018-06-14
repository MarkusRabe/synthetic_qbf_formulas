#!/usr/bin/env python3

import os
import sys
import argparse
import glob
import itertools
import numpy as np
from math import inf, log

from cadet_cmdline_utils import eval_formula

def _parse_cmdline():
    print('')
    p = argparse.ArgumentParser()
    p.add_argument('-r', '--repetitions', dest='repetitions', action='store',
                   metavar='N', nargs='?', default=1, type=int,
                   help='Number of runs to build the average over (default 1)')
    # p.add_argument('-v', '--vsids', dest='vsids', action='store',
    #                metavar='V', nargs='?', default=False, type=int,
    #                help='Evaluate VSIDS')
    p.add_argument('-d', '--directory', dest='directory', action='store',
                   default='.',
                   help="Directory to read formulas from. (default '.')")
    p.add_argument('-l', '--decision_limit', dest='decision_limit', action='store',
                   default=0,
                   help="Maximum number of decisions. (default: None)")
    p.add_argument('-t', '--file_type', dest='file_type', action='store',
                   default='*.qdimacs',
                   help="File type to read from folder. (default '*.qdimacs')")
    p.add_argument('-c', '--cactus', dest='cactus', action='store',
                   default=False, type=bool,
                   help="Create a cactus plot comparing the performance.")
    return p.parse_args()



def _write_cactus_data(file_name, data_name_x, data_name_y, data):
    with open(file_name, "w") as textfile:
        textfile.write(f'{data_name_x}\t{data_name_y}\n')
        data = data.copy()
        data.sort()
        for idx, x in enumerate(data):
            textfile.write(f'{idx + 1}\t{x}\n')


# creates an exponential histogram from a list of natural numbers
def _histogram(numbers):
    histogram = dict()
    for idx in range(int(log(max(numbers) + 1, 2)) + 2):  # + 2 because we need one extra space for values 0
        if idx == 0:
            histogram['0'] = 0
        else:
            histogram[f'<= 2**{idx}'] = 0
    for n in numbers:
        assert n >= 0
        if n == 0:
            histogram['0'] += 1
        else:
            idx = int(log(n, 2)) + 1
            histogram[f'<= 2**{idx}'] += 1
    return histogram


def _stats(args, name, numbers):
    decision_limit = int(args.decision_limit)
    if decision_limit == 0:
        decision_limit = inf
    filtered = list(filter(lambda x: x <= decision_limit, numbers))

    res = f'{name}:\nAvg decisions: {np.mean(filtered)}\nVar decisions: {np.var(filtered)}\n'
    res += f'Solved {len(filtered)} of {len(numbers)} in the decision limit {decision_limit}.\n'
    res += f'Maximum: {max(numbers)}\n'
    res += f'Exponential histogram: {_histogram(numbers)}\n'
    return res


def _log_result(args, runs):
    file_name = os.path.join(args.directory, 'STATISTICS')
    with open(file_name, "w") as textfile:
        textfile.write(str(sys.argv))
        textfile.write('\n')
        textfile.write(str(args) + '\n\n')

        for name, numbers in runs.items():
            stats = _stats(args, name, numbers)
            print(stats)
            print('\n')
            textfile.write(stats)
            textfile.write('\n\n')
    

def main():
    args = _parse_cmdline()
    file_names = glob.glob(os.path.join(args.directory, args.file_type))
    print(f'Detected {len(file_names)} files in directory.')
    
    random_decisions = []
    vsids_decisions = []
    vsids_cegar_decisions = []

    for file_name in file_names:
        print(f'Running {file_name}')
        return_code, _, avg_decisions = eval_formula(file_name, VSIDS=False, repetitions=args.repetitions, decision_limit=int(args.decision_limit))
        if avg_decisions is not None:
            random_decisions.append(avg_decisions)

        return_code, _, avg_decisions = eval_formula(file_name, VSIDS=True, repetitions=args.repetitions, decision_limit=int(args.decision_limit))
        if avg_decisions is not None:
            vsids_decisions.append(avg_decisions)

        return_code, _, avg_decisions = eval_formula(file_name, VSIDS=True, repetitions=args.repetitions, decision_limit=int(args.decision_limit), CEGAR=True)
        if avg_decisions is not None:
            vsids_cegar_decisions.append(avg_decisions)

    _log_result(args, {'RANDOM': random_decisions, 'VSIDS': vsids_decisions, 'CEGAR': vsids_cegar_decisions})
    
    if (args.cactus):
        print(f'\nWriting cactus plot data to {args.directory}')
        file_name = os.path.join(args.directory, 'Random.dat')
        _write_cactus_data(file_name, 'number_of_formulas', 'decisions', random_decisions)
        file_name = os.path.join(args.directory, 'VSIDS.dat')
        _write_cactus_data(file_name, 'number_of_formulas', 'decisions', vsids_decisions)
        file_name = os.path.join(args.directory, 'CEGAR.dat')
        _write_cactus_data(file_name, 'number_of_formulas', 'decisions', vsids_cegar_decisions)

if __name__ == "__main__":
    main()
