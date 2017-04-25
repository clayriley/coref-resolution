# Clay Riley 2017
#
# USAGE: classify.py <ALGORITHM> [<OPTIONS> ...]
#
# OPTIONS:
# --save <PATH> : path to save classifier to
# --load <PATH> : path to classifier
# --train <PATH> : path to raw file or directory
# --test <PATH> <PATH> : path to feature file, path to output
# --consolidate : if present, training from multiple files should be faster
#

import sys, os, re, pickle
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction import DictVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC
#from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from consolidate import consolidate
from write_hypotheses import Hypothesizer
from sklearn.linear_model import LogisticRegression

class Classifier:
    
    # TODO: add more classifiers here if desired
    ALLOWED = {'--svmlin': LinearSVC(),
               '--rf': RandomForestClassifier(n_estimators=20),
               '--svm': SVC(),
               '--logit': LogisticRegression(solver='sag'),
               #'--mlp': MLPClassifier((8,4))
               }  
  
    def __init__(self, algorithm, save_path=None):
        if save_path is None: 
            self.save_path = os.path.join(os.getcwd(), 'default_clf.pkl')
        else: 
            self.save_path = save_path
        self.algorithm = algorithm
        self.model = self.makeModel()

    def train(self, X, y):
        self.model.fit(X, y)

    def test(self, X):
        return self.model.predict(X)

    def makeModel(self):
        """ make changes to preprocessing steps here. """
        steps = []
        steps.append(('dictVectorizer',DictVectorizer()))
        steps.append(('standardScaler',StandardScaler(with_mean=False)))
        steps.append((self.algorithm, self.makeEstimator()))
        return Pipeline(steps)

    def makeEstimator(self):
        """ validate input and get model """
        if self.algorithm not in Classifier.ALLOWED:
            msg = "classify.py must be provided with a supported"
            msg += " classifier flag.  Supported classifiers:"
            for c in sorted(Classifier.ALLOWED.keys()): msg += '\n'+c
            raise IOError(msg)
        return Classifier.ALLOWED[self.algorithm]

    def save(self, out_file=None):
        """ dump model to pickle file """
        # reset save path, if given
        self.save_path = out_file if out_file is not None else self.save_path
        with open(self.save_path, 'wb') as f_out:
            dump = {'save_path':self.save_path, 
                    'algorithm':self.algorithm,  
                    'model':self.model}
            pickle.dump(dump, f_out)

    @classmethod
    def load(cls, file_path):
        """ load classifier from file """
        with open(file_path, 'rb') as f:
            loaded = pickle.load(f)
        clf = Classifier(loaded['algorithm'],loaded['save_path'])
        clf.model = loaded['model']
        return clf


class Processor:
    
    start_R = re.compile(r'\((\d+)(?!\d)')
    end_R = re.compile(r'(?<!\d)(\d+)\)')

    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path
        self.lines = []
        self.pairs = {}

    def read(self, classification=None):
                            
        with open(self.input_path, 'rb') as f:
            
            instances = []
            line_IDs = []
            labels = []
            raw = []
            
            # previously encountered and incomplete entities
            antecedents, opened = [], {}
            all_tokens = []
            line_ID, sentence_ID, unique_ID = 0, 0, 0
            
            for line in f:
                            
                # end of sentence: update sentence IDs
                if line.strip() == '':
                    sentence_ID += 1
                    line_ID += 1
                    opened = {}
                
                # new section: reset all entities and sentence IDs
                elif line[0] == '#':
                    antecedents, opened, sentence_ID = [], {}, 0
                    line_ID += 1
                
                # new token
                else:
                    field_str, refs = line.rsplit(' ', 1)
                    if '-' in refs:
                        pass # TODO
                    else:
                        starts = Processor.start_R.findall(refs)
                        ends = Processor.end_R.findall(refs)
                                       
                        # current token has entity start(s); open it
                        if len(starts) > 0:  
                            for original_ID in starts:
                                # inception crash prevention
                                if original_ID in opened:
                                    opened[original_ID][unique_ID] = []
                                else:
                                    opened[original_ID] = {unique_ID: []}
                                unique_ID += 1  
                        
                        # add this token's info to all opened entities
                        for identifier in opened:
                            for u_ID in opened[original_ID]:
                                field_str['ent_refs'] = identifier
                                opened[entity][u_ID].append(field_str)
                        # record all entities for intervening tokens
                        field_str['ent_refs'] = starting
                        


            processed = readLines(f_in, self.instantiate, classifying=False)
            
            self.instances = processed['instances'] 
            self.line_IDs = processed['line_IDs'] 
            self.labels = processed['labels']    

            if len(pairs) > 0:
                yield pairs.pop()
            else:
            for 
            
            
    def readLines(iterable, process):
        for line in iterable:
   

                        
            # new token
            else:
                
                anaphora = []  # list of current anaphora
                #starting = startR.findall(field_str['ent_refs'])
                #ending = endR.findall(field_str['ent_refs'])
                   
   
                    

                    
                # current token has entity end(s), close it
                if len(ending) > 0:  
                    closing = {} 
                    for entity in ending:  # this loop ensures order preservation
                        try:  # pop the completed entity
                            e = opened.pop(entity)
                            # crash catch
                            if len(e)>1:
                                r = sorted(e.keys())[-1]
                                youngest = e.pop(r)
                                opened[entity] = e
                                e = youngest
                            else:
                                r, e = e.items()[0]
                            closing[r] = e
                        except KeyError:
                            print 'entity:', entity
                            raise
                    for unique_ID in closing: 
                        anaphora.append(closing[unique_ID])  
                   
                # process all possible antecedent-anaphor pairs
                for ana in anaphora:
                    for ant in antecedents:
                        intervening = [all_tokens[i] for i in range(ant[-1]['line_ID']+1, ana[0]['line_ID'])]
                        instance, label = process(ant, ana, intervening)
                        ana_range = (ana[0]['line_ID'], len(ana))
                        ant_range = (ant[0]['line_ID'], len(ant))
                        instances.append(instance)
                        labels.append(label)
                        line_IDs.append((ant_range, ana_range))
                    antecedents.append(ana)  # add all completed anaphora to antecedents
                # add this token to list of all tokens in part up to this point
                all_tokens.append(field_str)  
                line_ID += 1

            raw.append(line)

        processed['instances'] = instances
        processed['line_IDs'] = line_IDs
        processed['labels'] = labels
        processed['raw'] = raw
        
        return processed


def main():

    SAVE = '--save'
    TRAIN = '--train'
    TEST = '--test'
    LOAD = '--load'

    save = SAVE in sys.argv
    train = TRAIN in sys.argv
    test = TEST in sys.argv
    load = LOAD in sys.argv

    # SAVE PATH FOR CLASSIFIER
    if save:
        try:
            # TODO include valid file checks
            save_path = sys.argv[sys.argv.index(SAVE)+1]
        except IndexError as e: 
            msg = 'Must provide classify.py with a filepath to save'
            msg += ' to when using the {} option.'.format(SAVE)
            raise IOError(msg)
    else:
        save_path = None

    # LOADING CLASSIFIER FROM FILE
    if load:
        try: 
            # TODO include valid file checks
            load_path = sys.argv[sys.argv.index(LOAD)+1]
            classifier = Classifier.load(load_path)
        except IndexError as e: 
            msg = 'Must provide classify.py with a filepath to load'
            msg += ' from when using the {} option.'.format(LOAD)
            raise IOError(msg)

    # BUILDING CLASSIFIER FROM SCRATCH
    else:
        algorithm = sys.argv[1]
        classifier = Classifier(algorithm, save_path)

    # TRAINING CLASSIFIER
    if train:
        try: 
            # TODO include valid file checks
            train_path = os.path.abspath(sys.argv[sys.argv.index(TRAIN)+1])
        except IndexError as e: 
            msg = 'Must provide classify.py with a filepath containing'
            msg += ' instances when using the {} option.'.format(TRAIN)
            raise IOError(msg)

        
        # PUTTING ALL TRAINING INSTANCES INTO ONE OBJECT
        else:  # TODO: repair
            print '...consolidating training instances...'
            try: 
                data = consolidate(train_path)
                X, y = [], []
                for fName in data:
                    X.extend(data[fName]['instances'])
                    y.extend(data[fName]['labels'])
            except IndexError as e: 
                msg = 'Must provide classify.py with a filepath to write'
                msg += ' to when using the {} option.'.format(CONS_TR)
                raise IOError(msg) 


        classifier.train(X, y)
        
    # PREDICTING WITH CLASSIFIER
    if test:
        print '...gathering testset...'
        test_paths = []
        try: 
            # TODO include valid file checks
            test_path = os.path.abspath(sys.argv[sys.argv.index(TEST)+1])
        except IndexError as e: 
            msg = 'Must provide classify.py with one filepath containing '
            msg += 'instances and one filepath to write hypotheses to '
            msg += 'when using the {} option.'.format(TEST)
            raise IOError(msg)

        # PROVIDED: DIRECTORY
        if os.path.isdir(test_path):
            for parent, children, files in os.walk(test_path):
                for f in files:
                    if f[-4:] == '.fts':  # only test feature files
                        path = os.path.abspath(os.path.join(parent,f))
                        test_paths.append(path)
        # PROVIDED: FILE
        else:
            test_paths.append(test_path)

        # TEST ALL IDENTIFIED DATA
        print '...testing...'
        count = 0
        for path in test_paths:
            with open(path, 'rb') as f_in:
                data = pickle.load(f_in)
                instances = data['instances']
                if len(instances)==0:
                    msg = 'No instances produced from file:\n'
                    msg += '{}\n(at file:\n{})'.format(data['source'], path)
                    msg += 'Skipping...'
                    print msg
                    continue
                else:
                    count += 1
                    try:
                        y = classifier.test(instances)
                    except ValueError:
                        print path
                        print type(data['instances'])
                        print data['instances']
                        raise
                    d = {'y': y, 'line_IDs': data['line_IDs'], 
                         'src_path':data['source'], 'fts_path':path}
                    # OUTPUT PREDICTIONS
                    #print predictions[path]['line_IDs']
                    hypothesizer = Hypothesizer(d)
                    hypothesizer.writeHypotheses()
        print '...{} files hypothesized.'.format(count)
        print '...({} featurized)'.format(len(test_paths))

    # SAVE CLASSIFIER AT THE END
    print '...saving classifier to {}...'.format(classifier.save_path)
    classifier.save()


if __name__ == '__main__':
    main()

