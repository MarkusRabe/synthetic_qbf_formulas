#!/usr/bin/env python3

import argparse
import time
import numpy as np
from subprocess import PIPE, call

from cadet_cmdline_utils import eval_formula

def _parse_cmdline():
    p = argparse.ArgumentParser()
    p.add_argument('-r', '--repetitions', dest='repetitions', action='store',
                   metavar='N', nargs='?', default=1, type=int,
                   help='Number of runs to build the average over (default 1)')
    p.add_argument('-f', '--file', dest='file', action='store',
                   default=None,
                   help="File to evaluate on; REQUIRED")
    p.add_argument('-l', '--decision_limit', dest='decision_limit', action='store',
                   default=None,
                   type=int,
                   help="Maximum number of decisions. (default: None)")
    return p.parse_args()


def main():
    args = _parse_cmdline()
    assert(args.file)
    
    print(f'Running {args.file}')

    times = []
    for i in range(args.repetitions):
        start = time.time()
        _, _, decisions = eval_formula(args.file, decision_limit=args.decision_limit, 
                                       soft_decision_limit=False, VSIDS=True, 
                                       fresh_seed=False, RL=True)
        assert decisions != None
        assert decisions != 0
        end = time.time()

        print(f'  Time {end - start}')
        print(f'  Decisions {decisions}')

        times.append((end - start) / decisions)

    print(f'Time avg: {np.mean(times)}')

if __name__ == "__main__":
    main()
