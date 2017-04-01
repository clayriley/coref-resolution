# USAGE: consolidate.py <search directory>

import sys, os, pickle

def consolidate(search_dir):
    repository = {}
    for parent, children, files in os.walk(os.path.abspath(search_dir)):
        for fName in files:
            path = os.path.join(parent, fName)
            if fName[-4:] == '.fts':  # only consolidate pickled features
                with open(path,'rb') as f:
                    repository[fName] = pickle.load(f)  # unpickle
    return repository
