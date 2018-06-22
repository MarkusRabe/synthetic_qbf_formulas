#!/usr/bin/env python3

import os
import sys
import argparse
import re
import glob
import itertools
import numpy as np
from math import inf, log
import git

from cadet_cmdline_utils import eval_formula


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
    p.add_argument('-c', '--cactus', dest='cactus', action='store_true',
                        help="Create a cactus plot comparing the performance (default False).")
    p.add_argument('--random', dest='random', action='store_true',
                        help="Test random heuristic (default False).")
    p.add_argument('--vsids', dest='vsids', action='store_true',
                        help="Test VSIDS heuristic (default False).")
    p.add_argument('--cegar', dest='cegar', action='store_true',
                        help="Test VSIDS+CEGAR heuristic (default False).")
    p.add_argument('--projection', dest='projection', action='store_true',
                        help="Test projection with CADET (default False).")
    return p.parse_args()



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



def _num_variables(file_name):
    with open(file_name) as file: 
        s = file.read()
        res = re.findall('p cnf (\d+)', str(s))
        if len(res) == 1:
            return int(res[0])


class StatisticsAccumulator(object):
    def __init__(self, 
                 name,
                 repetitions, 
                 decision_limit=None,
                 soft_decision_limit=False,
                 VSIDS=False,
                 fresh_seed=False,
                 CEGAR=False,
                 RL=False,
                 debugging=False,
                 projection=False):

        self.name = name
        self.repetitions = repetitions

        # Parameters for CADET
        self.decision_limit = decision_limit
        self.soft_decision_limit = soft_decision_limit
        self.VSIDS = VSIDS
        self.fresh_seed = fresh_seed
        self.CEGAR = CEGAR
        self.RL = RL
        self.debugging = debugging
        self.projection = projection
        
        # Accumulate the number of decisions
        self.num_decision_list = []
        self.num_files = 0


    def measure_formula(self, file_name):
        self.num_files += 1
        timeouts = 0
        decisions_list = []
        for i in range(self.repetitions):
            rc, _, decisions = eval_formula(file_name,
                                            VSIDS=self.VSIDS,
                                            decision_limit=self.decision_limit,
                                            CEGAR=self.CEGAR,
                                            fresh_seed=self.fresh_seed,
                                            debugging=self.debugging,
                                            RL=self.RL,
                                            soft_decision_limit=self.soft_decision_limit,
                                            projection=self.projection)

            assert decisions is not None
            assert rc != 30 or decisions == decision_limit

            if rc == 30:
                timeouts += 1
            else:
                decisions_list.append(decisions)

            if timeouts >= self.repetitions / 2:
                return  # don't add a new value to self.num_decision_list

        avg = np.mean(decisions_list)
        self.num_decision_list.append(avg)

    def write_cactus_data(self, directory):
        file_name = os.path.join(args.directory, f'{self.name}.dat')
        data_name_x = 'number_of_formulas'
        data_name_y = 'decisions'
        with open(file_name, "w") as textfile:
            textfile.write(f'{data_name_x}\t{data_name_y}\n')
            data = self.num_decision_list.copy()
            data.sort()
            for idx, x in enumerate(data):
                textfile.write(f'{idx + 1}\t{x}\n')

    def stats(self):
        res = f'{self.name}:\n'
        res += f'Avg decisions: {np.mean(self.num_decision_list)}\n'
        res += f'Var decisions: {np.var(self.num_decision_list)}\n'
        res += f'Solved {len(self.num_decision_list)} of {self.num_files} in the decision limit {self.decision_limit}.\n'
        res += f'Maximum: {max(self.num_decision_list) if len(self.num_decision_list) > 0 else None}\n'
        res += f'Exponential histogram: {_histogram(self.num_decision_list)}\n'
        return res


def _log_result(args, accumulators, var_numbers):
    file_name = os.path.join(args.directory, 'STATISTICS')
    print('\nGathering statistics\n\n')

    with open(file_name, "w") as textfile:
        textfile.write(str(sys.argv))
        textfile.write('\n')
        textfile.write(str(args) + '\n\n')

        repo = git.Repo(search_parent_directories=True)
        textfile.write(f'Git hash: {repo.head.object.hexsha}\n\n')

        textfile.write(f'Average number of variables: {np.mean(var_numbers)}\n\n')
        print(f'Average number of variables: {np.mean(var_numbers)}\n')

        for a in accumulators:
            stats = a.stats()
            print(stats)
            print('\n')
            textfile.write(stats)
            textfile.write('\n\n')


def main():
    args = _parse_cmdline()
    file_names = glob.glob(os.path.join(args.directory, args.file_type))
    print(f'Detected {len(file_names)} files in directory.')
    
    accumulators = []

    if args.random:
        accumulators.append(StatisticsAccumulator("Random", args.repetitions,
                                                  VSIDS=False, CEGAR=False,
                                                  decision_limit=args.decision_limit))
    if args.vsids:
        accumulators.append(StatisticsAccumulator("VSIDS", args.repetitions,
                                                  VSIDS=True, CEGAR=False,
                                                  decision_limit=args.decision_limit))
    if args.cegar:
        accumulators.append(StatisticsAccumulator("CEGAR", args.repetitions,
                                                  VSIDS=True, CEGAR=True,
                                                  decision_limit=args.decision_limit))
    if args.projection:
        accumulators.append(StatisticsAccumulator("Projection", args.repetitions,
                                                  VSIDS=True, CEGAR=False,
                                                  decision_limit=args.decision_limit,
                                                  projection=True))

    if len(accumulators) == 0:
        print('No configuration to measure specified. Type "./measure_cadet.py -h" for help.')

    var_numbers = []

    for file_name in file_names:
        print(f'Measuring {file_name}')
        var_numbers.append(_num_variables(file_name))
        for a in accumulators:
            a.measure_formula(file_name)

    _log_result(args, accumulators, var_numbers)
    
    if (args.cactus):
        print(f'\nWriting cactus plot data to {args.directory}')
        for a in accumulators:
            a.write_cactus_data(args.directory)

if __name__ == "__main__":
    main()
