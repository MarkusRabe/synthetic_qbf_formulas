#!/usr/bin/env python3

import os
import sys
import argparse
import re
import glob
import itertools
import numpy as np
from math import inf, log

from cadet_cmdline_utils import eval_formula

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def _parse_cmdline():
    print('')
    p = argparse.ArgumentParser()
    p.add_argument('-r', '--repetitions', dest='repetitions', action='store',
                   metavar='N', nargs='?', default=1, type=int,
                   help='Number of runs to build the average over (default 1)')
    p.add_argument('-d', '--directory', dest='directory', action='store',
                   default='.',
                   help="Directory to read formulas from. (default '.')")
    p.add_argument('-l', '--decision_limit', dest='decision_limit', action='store',
                   default=None,
                   type=int,
                   help="Maximum number of decisions. (default: None)")
    p.add_argument('-t', '--file_type', dest='file_type', action='store',
                   default='*.qdimacs',
                   help="File type to read from folder. (default '*.qdimacs')")
    p.add_argument('-c', '--cactus', type=str2bool, nargs='?',
                        const=True, dest='cactus',
                        help="Create a cactus plot comparing the performance.")
    # p.add_argument('-c', '--cactus', dest='cactus', action='store',
                   # default=False, type=bool,
                   # help="Create a cactus plot comparing the performance.")
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
    log_range = int(log(max(numbers) + 1, 2)) + 2 if len(numbers) > 0 else 2
    for idx in range(log_range):  # + 2 because we need one extra space for values 0
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


def _stats(args, num_formulas, name, numbers):
    res = f'{name}:\nAvg decisions: {np.mean(numbers)}\nVar decisions: {np.var(numbers)}\n'
    res += f'Solved {len(numbers)} of {num_formulas} in the decision limit {args.decision_limit}.\n'
    res += f'Maximum: {max(numbers) if len(numbers) > 0 else None}\n'
    res += f'Exponential histogram: {_histogram(numbers)}\n'
    return res


def _log_result(args, num_formulas, runs, var_numbers):
    file_name = os.path.join(args.directory, 'STATISTICS')
    print('\nGathering statistics\n\n')

    with open(file_name, "w") as textfile:
        textfile.write(str(sys.argv))
        textfile.write('\n')
        textfile.write(str(args) + '\n\n')

        textfile.write(f'Average number of variables: {np.mean(var_numbers)}\n\n')
        print(f'Average number of variables: {np.mean(var_numbers)}\n')

        for name, numbers in runs.items():
            stats = _stats(args, num_formulas, name, numbers)
            print(stats)
            print('\n')
            textfile.write(stats)
            textfile.write('\n\n')


def _num_variables(file_name):
    with open(file_name) as file: 
        s = file.read()
        res = re.findall('p cnf (\d+)', str(s))
        if len(res) == 1:
            return int(res[0])


def _measure_formula(file_name, repetitions, VSIDS=False, decision_limit=None, CEGAR=False):
    timeouts = 0
    decisions_list = []
    for i in range(repetitions):
        return_code, _, decisions = eval_formula(file_name, VSIDS=VSIDS, decision_limit=decision_limit, CEGAR=CEGAR, fresh_seed=False)
        
        assert decisions is not None
        assert return_code != 30 or decisions == decision_limit

        if return_code == 30:
            timeouts += 1
        else:
            decisions_list.append(decisions)

        if timeouts >= repetitions / 2:
            return None

    avg = np.mean(decisions_list)
    # print(f'Average is {avg}')
    return avg


def main():
    args = _parse_cmdline()
    file_names = glob.glob(os.path.join(args.directory, args.file_type))
    num_formulas = len(file_names)
    print(f'Detected {num_formulas} files in directory.')
    
    random_decisions = []
    vsids_decisions = []
    vsids_cegar_decisions = []

    var_numbers = []

    for file_name in file_names:
        print(f'Measuring {file_name}')

        var_numbers.append(_num_variables(file_name))

        avg_decisions = _measure_formula(file_name, args.repetitions, VSIDS=False, CEGAR=False, decision_limit=args.decision_limit)
        if avg_decisions != None:
            random_decisions.append(avg_decisions)

        avg_decisions = _measure_formula(file_name, args.repetitions, VSIDS=True, CEGAR=False, decision_limit=args.decision_limit)
        if avg_decisions != None:
            vsids_decisions.append(avg_decisions)

        avg_decisions = _measure_formula(file_name, args.repetitions, VSIDS=True, CEGAR=True, decision_limit=args.decision_limit)
        if avg_decisions != None:
            vsids_cegar_decisions.append(avg_decisions)

    _log_result(args, num_formulas, {'RANDOM': random_decisions, 'VSIDS': vsids_decisions, 'CEGAR': vsids_cegar_decisions}, var_numbers)
    
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
