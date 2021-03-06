#!/usr/bin/env python3

import os
import re
import ipdb
import argparse
import glob
import numpy as np
from subprocess import Popen, PIPE, STDOUT

from cnf_tools import write_to_file, clauses_to_occs, occs_to_clauses, qdimacs_to_clauselist
from aux_utils import sign, is_number
from cadet_cmdline_utils import eval_formula



def normalizeQDIMACS(maxvar, clauses, universals, max_clauses_per_variable):
    occs = clauses_to_occs(clauses)

    # Split variables when they occur in more than 8 clauses
    itervars = set(occs.keys())
    added_vars = 0
    while True:
        if len(itervars) == 0:
            break
        v = itervars.pop()
        if len(occs[v]) > max_clauses_per_variable:
            # print('Found var '+str(v)+ ' with '+ str(len(occs[v]))+ ' occurrences.')
            maxvar += 1
            added_vars += 1
            connector_clauses = [[v,-maxvar],[-v,maxvar]]
            # prepend connector_clauses to shift all clauses back, don't want 
            # to remove the connector_clauses with what follows
            occs[v] = connector_clauses + occs[v] 
            assert(len(occs[v][(max_clauses_per_variable+2):]) > 0)  
                # > MAX_CLAUSES_PER_VARIABLE and we added two connector_clauses
        
            assert(maxvar not in occs)
            occs[maxvar] = connector_clauses
        
            # move surplus clauses over to new variable
            for clause in occs[v][max_clauses_per_variable:]:
                # change clause inplace, so change is consistent for occurrence lists of other variables
                clause[:] = list(map(lambda x: maxvar * sign(x) if abs(x) == v else x, clause))
                occs[maxvar] += [clause]
            assert(len(occs[v]) > len(occs[maxvar]))
        
            occs[v] = occs[v][:(max_clauses_per_variable - 1)]
        
            # if len(occs[maxvar]) > MAX_CLAUSES_PER_VARIABLE: 
                # print('  new var '+str(maxvar)+ ' will be back.')
        
            itervars.add(maxvar)
            
    # print ('  maxvar: ' + str(maxvar))
    # print ('  added vars: ' + str(added_vars))
    # print ('  Max: ' + str( max( [len(occs[v]) for v in occs.keys()] )))
    # print ('  Over MAX_CLAUSES_PER_VARIABLE occs: ' 
        # + str(len( filter(lambda x: x, [len(occs[v]) 
        #   > MAX_CLAUSES_PER_VARIABLE for v in occs.keys()] ))))

    print(f'  added {added_vars} variables')
    return maxvar, occs_to_clauses(occs), universals


def read_and_normalize(filename, max_clauses_per_variable):
    maxvar, clauses, universals = qdimacs_to_clauselist(filename)
    return normalizeQDIMACS(maxvar, clauses, universals, max_clauses_per_variable)


def _parse_cmdline():
    print('')
    p = argparse.ArgumentParser()
    p.add_argument('-d', '--directory', dest='directory', action='store',
                   default='.',
                   help="Directory to read formulas from. (default '.')")
    p.add_argument('-t', '--file_type', dest='file_type', action='store',
                   default='*.qdimacs',
                   help="File type to read from folder. (default '*.qdimacs')")
    p.add_argument('-m', '--max_clauses_per_variable', dest='max_clauses_per_variable', action='store',
                   default=10,
                   help="Maximum number of occurrences of a variable. (default: 10)")
    p.add_argument('-c', '--check', dest='check', action='store',
                   default=True,
                   help="Check converted file for equisatisfiability (default True)")
    return p.parse_args()


def main():
    args = _parse_cmdline()
    args.max_clauses_per_variable = int(args.max_clauses_per_variable)
    file_names = glob.glob(os.path.join(args.directory, args.file_type))
    print(f'Detected {len(file_names)} files')

    normalized_dir = os.path.join(args.directory, 'normalized')
    print(f'Writing to directory: {normalized_dir}\n')
    if not os.path.exists(normalized_dir):
        os.makedirs(normalized_dir)
    
    for path_name in file_names:
        print(f'Normalizing {path_name}')
        
        maxvar, clauses, universals = read_and_normalize(path_name, args.max_clauses_per_variable)

        # assemble name of normalized file
        _, file_name = os.path.split(path_name)
        normalized_path_name = os.path.join(normalized_dir, file_name)
        if normalized_path_name.endswith('.qdimacs'):
            normalized_path_name = normalized_path_name[:-8] + '.n.qdimacs'
        if normalized_path_name.endswith('.qaiger'):
            normalized_path_name = normalized_path_name[:-7] + '.n.qdimacs'
        
        # comment = f'Normalized to {args.max_clauses_per_variable} clauses per variable'
        write_to_file(maxvar, clauses, normalized_path_name, universals=universals)

        
        if args.check == True:
            return_code_orig, _, _ = eval_formula(path_name, VSIDS=True, decision_limit=int(1000), CEGAR=False, fresh_seed=False)
            return_code_normalized, _, _ = eval_formula(normalized_path_name, VSIDS=True, decision_limit=int(1000), CEGAR=False, fresh_seed=False)
            assert return_code_orig == return_code_normalized or return_code_orig == 30 or return_code_normalized == 30


if __name__ == "__main__":
    main()
