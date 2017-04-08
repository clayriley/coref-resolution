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
PLU1 = {'these','those','they','them','we','us'}
PLU2 = {'NNS', 'NNPS'}


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
        overlap = 0
        for t in tokens_i:
            if t in tokens_j:
                overlap += 1
        pro_i = len(tokens_i)==1 and tokens_i[0] in PRO
        pro_j = len(tokens_j)==1 and tokens_j[0] in PRO
        pos_i = [t['POS'] for t in antecedent]
        pos_j = [t['POS'] for t in anaphor]
        def_i = tokens_i[0] in DEF or pos_i[0] in {'NNP', 'NNPS'}
        def_j = tokens_j[0] in DEF or pos_j[0] in {'NNP', 'NNPS'}
        prox_i = tokens_i[0] in PROX
        prox_j = tokens_j[0] in PROX
        dist_i = tokens_i[0] in DIST
        dist_j = tokens_j[0] in DIST
        plu_i = tokens_i[-1] in PLU1 or pos_i[-1] in PLU2
        plu_j = tokens_j[-1] in PLU1 or pos_j[-1] in PLU2
        speakers_same = anaphor[0]['speaker']==antecedent[0]['speaker']
        ents_i, ents_j = set([]), set([])
        for a in anaphor: 
            e = a['named_ents'].strip('()*')
            if e != '': ents_j.add(e)
        for a in antecedent: 
            e = a['named_ents'].strip('()*') 
            if e != '': ents_i.add(e)
        ents_same = ents_i.isdisjoint(ents_j)
        m_between = 0
        for i in range(len(between)): m_between += len(between[i]['ent_refs'])
        masc_i = float(sum([tokens_i[i] in MASC for i in range(len(tokens_i))]))/len(tokens_i)
        masc_j = float(sum([tokens_i[i] in MASC for i in range(len(tokens_i))]))/len(tokens_i)
        fem_i = float(sum([tokens_i[i] in FEM for i in range(len(tokens_i))]))/len(tokens_i)
        fem_j = float(sum([tokens_i[i] in FEM for i in range(len(tokens_i))]))/len(tokens_i)
        overlap_i = float(overlap)/len(tokens_i)
        overlap_j = float(overlap)/len(tokens_j)
        lems_i = set([a['lemma'] for a in antecedent])
        lems_j = set([a['lemma'] for a in anaphor])
        overlap_lem = len(lems_i.intersection(lems_j))
        overlap_lem_i = float(overlap)/len(lems_i)
        overlap_lem_j = float(overlap)/len(lems_j)
        sen_pos_i = antecedent[0]['token_ID']
        sen_pos_j = anaphor[0]['token_ID']
        arg_i = 'None'
        for p in antecedent[0]['arg_parse']:
            arg = p.strip('()*') 
            if arg != '':
                arg_i = arg
                break
        arg_j = 'None'
        for p in anaphor[0]['arg_parse']:
            arg = p.strip('()*') 
            if arg != '':
                arg_j= arg
                break
 
        
        # build feature dict
        fts = {
            'dist_t':token_dist, #0
            'dist_s':sentence_dist, #0
            'overlap':overlap, #0
            'pro_i':pro_i, #1
            'pro_j':pro_j, #1
            'def_i':def_i, #1
            'def_j':def_j, #1
            'prox_i':prox_i, #1
            'prox_j':prox_j, #1
            'dist_i':dist_i, #1
            'dist_j':dist_j, #1
            'plu_i':plu_i, #2
            'plu_j':plu_j, #2
            'same_speakers':speakers_same, #2
            'same_ent_types':ents_same, #2
            'mentions_between':m_between, #3
            'masc_i':masc_i, #4
            'masc_j':masc_j, #4
            'fem_i':fem_i, #4
            'fem_j':fem_j, #4
            'overlap_i_normed':overlap_i, #5
            'overlap_j_normed':overlap_j, #5
            'overlap_lem_i_normed':overlap_lem_i, #6
            'overlap_lem_j_normed':overlap_lem_j, #6
            'sen_pos_i':sen_pos_i, #6
            'sen_pos_j':sen_pos_j, #6
            'arg_i':arg_i, #7
            'arg_j':arg_j, #7
            }
        
        
        
        return (fts, coreference)


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

