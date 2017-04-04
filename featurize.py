# author: Clay Riley 2017
# script usage: featurize.py <path to file to featurize> (<OPTION> ...)
#
# <OPTION> may be: 
# "--train" (writes gold standard labels to output)
# Otherwise, only uses gold standard labels for instance generation.
# "--append" <string> is added to output filepaths, if provided.
#
# Dumps instances to a pickle file.

import sys, os, re, errno, pickle
from read_CoNLL import readLines


PROX = {'this', 'these', 'here'}
DIST = {'that', 'those', 'there', 'then'}
PERS = {'i','me', 'you', 'he','she','it','him','her', 'they','them', 'we','us'}
POSS = {'my', 'mine', 'your', 'yours', 'his', 'her', 'hers', 'its', 'their', 'theirs', 'our', 'ours'}
PRO = POSS.union(PERS.union(DIST.union(PROX)))
DEF = {'the'}.union(PRO)
MASC = {'he', 'him', 'his'}
FEM = {'she', 'her', 'her'} # not 'hers'!


class Featurizer:

    def instantiate(self, antecedent, anaphor, between):
        """ create a featurized instance given: two lists of dicts 
        of mentions' values, a list of dicts of tokens between """
        
        # record whether they corefer
        coreference = int(antecedent[0]['ent_refs']==anaphor[0]['ent_refs'])

        # generate values for use in features
        sentence_dist = anaphor[0]['sen_ID'] - antecedent[-1]['sen_ID']
        token_dist = anaphor[0]['token_ID'] - antecedent[-1]['token_ID']
        tokens_i = [t['token'].lower() for t in antecedent]
        tokens_j = [t['token'].lower() for t in anaphor]
        pos_i = [t['POS'] for t in antecedent]
        pos_j = [t['POS'] for t in anaphor]
        overlap = 0
        for t in tokens_i:
            if t in tokens_j:
                overlap += 1
        pro_i = len(tokens_i)==1 and tokens_i[0] in PRO
        pro_j = len(tokens_j)==1 and tokens_j[0] in PRO
        m_between = len([between[i]['ent_refs'] for i in range(len(between)) 
                        if between[i]['ent_refs'] != '-'])/2
        prox_i = tokens_i[0] in PROX
        prox_j = tokens_j[0] in PROX
        dist_i = tokens_i[0] in DIST
        dist_j = tokens_j[0] in DIST
        def_i = tokens_i[0] in DEF or pos_i[0] in {'NNP', 'NNPS'}
        def_j = tokens_j[0] in DEF or pos_j[0] in {'NNP', 'NNPS'}
        
        
        # build feature dict
        fts = {
            'dist_t':token_dist, #0
            'dist_s':sentence_dist, #0
            'overlap':overlap, #0
            #
            # TODO: this is wrong
            #'mentions_between':m_between, #0
            #
            'pro_i':pro_i, #2
            'pro_j':pro_j, #2
            'prox_i':prox_i, #2
            'prox_j':prox_j, #2
            'dist_i':dist_i, #2
            'dist_j':dist_j, #2
            'def_i':def_i, #3
            'def_j':def_j, #3
            }
        
        
        
        return fts, coreference


    def getInstances(self, in_path=None):
        """ reads raw data, separates it into more easily parsed 
        formats, and creates classification instances """

        # reset input path if needed
        self.input_path = self.input_path if in_path is None else in_path

        with open(self.input_path, 'r') as f_in:

            processed = readLines(f_in, self.instantiate, classifying=False)

            self.instances = processed['instances'] 
            self.abs_IDs = processed['abs_IDs'] 
            self.labels = processed['labels']            


    def write(self, out_path=None):
        """ write instances and labels to pickle file. """

        out_path = self.output_path if out_path is None else out_path

        # ensure data is okay
        if len(self.instances) != len(self.labels): 
            raise IOError('Numbers of labels ({}) and instances ({}) differ'
                          '!'.format(len(self.labels), len(self.instances))) 

        # build directory for output
        try: os.makedirs(os.path.dirname(out_path))
        except OSError as e: 
            if e.errno != errno.EEXIST: raise e

        # dump to pickle file
        with open(out_path, 'wb') as f_out:
            dump = {'instances':self.instances, 'labels':self.labels, 
                    'abs_IDs':self.abs_IDs, 'source':self.input_path}
            pickle.dump(dump, f_out)


    def __init__(self, input_path, output_path, training):
        self.input_path = input_path
        self.output_path = output_path
        self.training = training
        self.instances = []
        self.labels = []
        self.abs_IDs = []


def main():

    if len(sys.argv) < 2: 
        raise IOError('featurize.py requires a filepath arg.\nusage: >'
                      'featurize.py <path to file to featurize> (--train)')

    inp = os.path.abspath(sys.argv[1])
    app = '--append' in sys.argv
    if app:
        try:
            append = sys.argv[sys.argv.index('--append')+1]
        except IndexError:
            raise IOError('featurize.py must be given an appendix if using '
                          'the --append flag.')
    else:
        append=''
    out = re.sub('/data/', '/output'+append+'/', re.sub(r'\..+\b', '.fts', inp))
    train = '--train' in sys.argv

    #print 'Input:', inp
    #print 'Output:', out
    #print 'Training:', train

    f = Featurizer(inp, out, train)

    f.getInstances()
    #print f.instances[:5]
    #print f.labels[:5]
    #print f.abs_IDs[:5]
    f.write()
    

if __name__ == '__main__':
    main()

