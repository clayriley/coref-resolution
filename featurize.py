# author: Clay Riley 2017
# script usage: featurize.py <path to file to featurize> <OPTION>
#
# <OPTION> may be "--train" (writes gold standard labels to output)
# Otherwise, only uses gold standard labels for instance generation.
#
# Dumps instances to a pickle file.

import sys, os, re, errno, pickle

class Featurizer:

    def instantiate(self, antecedent, anaphor, between, training):
        """ create a featurized instance given two lists of dicts 
        of mentions' features, a list of dicts of tokens between, 
        and whether or not to train """
        
        # record whether they corefer, if training
        refs_i = set(antecedent[0]['entRefs'])
        refs_j = set(anaphor[0]['entRefs'])
        coreference = int(not refs_i.isdisjoint(refs_j)) if training else None

        # generate values for use in features
        sentence_dist = anaphor[0]['sentenceID'] - antecedent[-1]['sentenceID']
        token_dist = anaphor[0]['tokenID'] - antecedent[-1]['tokenID']
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
            
            # regexes for this task
            startR = re.compile(r'\((\d+)(?!\d)')
            endR = re.compile(r'(?<!\d)(\d+)\)')
            
            # previously encountered and incomplete entities
            antecedents, open_entities = [], {}
            all_tokens = []
            absID, senID, refID = 0, 0, 0
            
            for line in f_in:
    
                # new section: reset antecedents and sentence/token IDs
                if line[0] == '#':
                    antecedents, open_entities = [], {}
                    senID = 0
                
                # new sentence: update sentence IDs
                elif line.strip() == '':
                    senID += 1
                    open_entities = {}  # ignore any entities remaining open
                
                # new token
                else:
                    fields = line.split()
                    fields = {'absID':absID, 
                              'sentenceID':senID,
                              'entRefs':fields[-1],  # coreference resolution via gold standard
                              'fileName':fields[0],  
                              'sectionID':fields[1],
                              'tokenID':int(fields[2]),
                              'token':fields[3],
                              'POS':fields[4],
                              'synParse':fields[5],
                              'lemma':fields[6],
                              'frameset':fields[7],
                              'sense':fields[8],
                              'speaker':fields[9],
                              'namedEnts':fields[10],
                              'argParse':fields[11:-1]}
                    anaphora = []  # list of current anaphora
                    starting = startR.findall(fields['entRefs'])
                    ending = endR.findall(fields['entRefs'])
                
                    # current token has entity start(s), open it
                    if len(starting) > 0:  
                        for entity in starting:
                            open_entities[entity] = [refID]  # cluster ID
                            refID += 1
                    
                    # add this token's info to all opened entities
                    fields['entRefs'] = []  # update the clusters!
                    for entity in open_entities:
                        fields['entRefs'].append(entity)
                        open_entities[entity].append(fields)
                    
                    # current token has entity end(s), close it
                    if len(ending) > 0:  
                        closing = {} 
                        for entity in ending:  # this loop ensures order preservation
                            try:  # pop the completed entity
                                e = open_entities.pop(entity)
                                closing[e[0]] = e[1:]
                            except KeyError:
                                pass  # sweep this annotation problem under the rug
                        for refID in closing: anaphora.append(closing[refID])  
                    
                    # process all possible antecedent-anaphor pairs
                    for ana in anaphora:
                        for ant in antecedents:
                            intervening = [all_tokens[i] for i in range(ant[-1]['absID']+1, ana[0]['absID'])]
                            instance, label = self.instantiate(ant, ana, intervening, self.training)
                            ana_range = [token['absID'] for token in ana]
                            ant_range = [token['absID'] for token in ant]
                            self.instances.append(instance)
                            self.labels.append(label)
                            self.absIDs.append((ana_range, ant_range))
                        antecedents.append(ana)  # add all completed anaphora to antecedents
                    # add this token to list of all tokens up to this point
                    all_tokens.append(fields)  
                    absID += 1


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
                    'absIDs':self.absIDs, 'source':self.input_path}
            pickle.dump(dump, f_out)


    def __init__(self, input_path, output_path, training):
        self.input_path = input_path
        self.output_path = output_path
        self.training = training
        self.instances = []
        self.labels = []
        self.absIDs = []


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
    f.write()
    

if __name__ == '__main__':
    main()

