import os
import re
import ipdb
import numpy as np
import tempfile
from subprocess import Popen, PIPE, STDOUT

from aux_utils import is_number


def extract_num_conflicts(s):
    res = re.findall(' Conflicts: (\d+)', str(s))
    if len(res) == 1:
        return int(res[0])
    else:
        print('  ERROR: {}'.format(s))
        return 0


def extract_num_decisions(s):
    res = re.findall(' Decisions: (\d+)', str(s))
    if len(res) == 1:
        return int(res[0])
    else:
        print('  ERROR: {}'.format(s))
        return 0


def _ignore_output(p):
    # p.wait()
    # print(p.poll())
    # print('Poll end')
    for line in p.stdout:
        # print(line[:-1])
        newfile = line == 'Enter new filename:\n'
        if line.startswith('s ') or newfile:
            return newfile

    # while True:
    #     out = p.stdout.readline()
    #     print(out)
    #     if not out:
    #         break

def _rl_interaction(tool, filename):
    p = Popen(tool, stdout=PIPE, stdin=PIPE, universal_newlines=True, bufsize=1)

    _ignore_output(p)
    # print('writing ' + f'{filename}')
    p.stdin.write(f'{filename}\n')
    # print('Written!')
    i = 0
    while not _ignore_output(p):
        i += 1
        p.stdin.write('?\n')
    p.terminate()
    print(f'Terminated after {i} steps')
    return 30, None, i


def eval_formula(filename, repetitions=1, decision_limit=None, 
                 soft_decision_limit=False, VSIDS=False, fresh_seed=True, 
                 CEGAR=False, RL=False):
    assert isinstance(filename, str)

    returncodes = []
    conflicts = []
    decisions = []

    for _ in range(repetitions):
        tool = ['./../../cadet/dev/cadet','-v','1',
                '--debugging',
                '--sat_by_qbf']
        if decision_limit != None:
            tool += ['-l', f'{decision_limit}']
        if soft_decision_limit:
            tool += ['--cegar_soft_conflict_limit']
        if CEGAR:
            tool += ['--cegar']
        if not VSIDS:
            tool += ['--random_decisions']
        if fresh_seed:
            tool += ['--fresh_seed']
        if RL:
            tool += ['--rl']
        else:
            tool += [filename]

        if RL:
            return _rl_interaction(tool, filename)

        p = Popen(tool, stdout=PIPE, stdin=PIPE)
        stdout, stderr = p.communicate()
        if p.returncode is 30:
            return 30, None, decision_limit

        if p.returncode not in [10, 20, 30]:
            print(stdout)
            print(stderr)
            return None, None, None
            
        returncodes.append(p.returncode)
        conflicts.append(extract_num_conflicts(stdout))
        num_decisions = extract_num_decisions(stdout)
        decisions.append(num_decisions)

        if decision_limit != None and num_decisions > decision_limit:
            print('Error: decision limit was violated')
            print(formula)
            print(' '.join(tool))
            print(stdout)
            quit()

    assert 30 not in returncodes
    assert all(x == returncodes[0] for x in returncodes)

    return returncodes[0], np.mean(conflicts), np.mean(decisions)

