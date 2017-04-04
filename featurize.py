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


PRO = {'he', 'she', 'it', 'they', 'you', "y'all", 'we', 'us', 'i', 'me', 'him', 
       'her', 'them', 'this', 'that', 'these', 'those'}
PROX = {'this', 'these', 'here'}
DIST = {'that', 'those', 'there', 'then'}
MASC = {'he', 'him'}
FEM = {'she', 'her'}


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
        tokens_low_i = [token['token'].lower() for token in antecedent]
        tokens_low_j = [token['token'].lower() for token in anaphor]
        tokens_i = '_'.join(tokens_low_i)
        tokens_j = '_'.join(tokens_low_j)
        POSes_i = [token['POS'] for token in antecedent]
        POSes_j = [token['POS'] for token in anaphor]
        tokens_raw_bt = [token['token'] for token in between]
        tokens_bt = '_'.join(tokens_raw_bt).lower()
        overlap = 0
        for t_i in tokens_low_i:
            if t_i in tokens_low_j:
                overlap += 1
        pro_i = len(tokens_low_i)==1 and tokens_low_i[0] in PRO
        pro_j = len(tokens_low_j)==1 and tokens_low_j[0] in PRO
        m_between = len([between[i]['ent_refs'] for i in range(len(between)) 
                        if between[i]['ent_refs'] != '-'])/2
        
        
        # build feature dict
        fts = {}
        fts['dist_t']=token_dist #0
        fts['dist_s']=sentence_dist #0
        fts['overlap']=overlap #0
        fts['mentions_between']=m_between #0
        fts['pro_i']=pro_i #1
        fts['pro_j']=pro_j #1
        
        
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

