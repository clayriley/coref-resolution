# author: Clay Riley 2017
# script usage: featurize.py <path to file to featurize> <OPTION>
#
# <OPTION> may be "--train" (writes gold standard labels to output)
# Otherwise, only uses gold standard labels for instance generation.
#
# Dumps instances to a pickle file.

import sys, os, re, errno, pickle
from read_CoNLL import readLines

class Featurizer:

    def instantiate(self, antecedent, anaphor, between):
        """ create a featurized instance given two lists of dicts 
        of mentions' features, a list of dicts of tokens between """
        
        # record whether they corefer, if training
        refs_i = set(antecedent[0]['ent_refs'])
        refs_j = set(anaphor[0]['ent_refs'])
        coreference = int(not refs_i.isdisjoint(refs_j)) if self.training else None

        # generate values for use in features
        sentence_dist = anaphor[0]['sen_ID'] - antecedent[-1]['sen_ID']
        token_dist = anaphor[0]['token_ID'] - antecedent[-1]['token_ID']
        tokens_raw_i = [token['token'] for token in antecedent]
        tokens_raw_j = [token['token'] for token in anaphor]
        tokens_i = '_'.join(tokens_raw_i).lower()
        tokens_j = '_'.join(tokens_raw_j).lower()
        POSes_i = [token['POS'] for token in antecedent]
        POSes_j = [token['POS'] for token in anaphor]
        tokens_raw_bt = [token['token'] for token in between]
        tokens_bt = '_'.join(tokens_raw_bt).lower()
        
        # build feature dict
        fts = {}
        fts['i']=tokens_i
        fts['j']=tokens_j
        fts['dist_t']=token_dist
        fts['dist_s']=sentence_dist
        
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
    out = re.sub('/data/', '/output/', re.sub(r'\..+\b', '.fts', inp))
    train = '--train' in sys.argv

    print 'Input:', inp
    print 'Output:', out
    print 'Training:', train

    f = Featurizer(inp, out, train)

    f.getInstances()
    print f.instances[:5]
    print f.labels[:5]
    f.write()
    

if __name__ == '__main__':
    main()

