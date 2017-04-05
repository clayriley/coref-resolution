# Clay Riley 2017
#
# USAGE: classify.py <ALGORITHM> [<OPTIONS> ...]
#
# OPTIONS:
# --save <PATH> : path to save classifier to
# --load <PATH> : path to classifier
# --train <PATH> : path to feature file or directory
# --test <PATH> <PATH> : path to feature file, path to output
# --consolidate : if present, training from multiple files should be faster
#

import sys, os, pickle
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction import DictVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC
#from sklearn.neural_network import MLPClassifier
from consolidate import consolidate
from write_hypotheses import Hypothesizer


class Classifier:
    
    # TODO: add more classifiers here if desired
    ALLOWED = {'--svm': LinearSVC(),
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
        """ make changes to model default params here. """
        if self.algorithm not in Classifier.ALLOWED:
            msg = "classify.py must be provided with a supported"
            msg += " classifier flag.  Supported classifiers:"
            for c in sorted(Classifier.ALLOWED.keys()): msg += '\n'+c
            raise IOError(msg)
        return Classifier.ALLOWED[self.algorithm]

    def save(self, out_file=None):
        # dump model to pickle file
        out_file = self.save_path if out_file is None else out_file
        with open(out_file, 'wb') as f_out:
            dump = {'save_path':out_file, 
                    'algorithm':self.algorithm,  
                    'model':self.model}
            pickle.dump(dump, f_out)

    @classmethod
    def load(cls, file_path):
        with open(file_path, 'rb') as f:
            loaded = pickle.load(f)
        clf = Classifier(loaded['algorithm'],loaded['save_path'])
        clf.model = loaded['model']
        return clf


def main():

    SAVE = '--save'
    TRAIN = '--train'
    TEST = '--test'
    LOAD = '--load'
    CONS_TR = '--consolidate'

    save = SAVE in sys.argv
    train = TRAIN in sys.argv
    test = TEST in sys.argv
    load = LOAD in sys.argv
    consolidate_training = CONS_TR in sys.argv

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
        if consolidate_training:
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

        # JUST ONE FILE
        else:
            with open(train_path, 'rb') as f_in:
                data = pickle.load(f_in)
                X, y = data['instances'], data['labels']

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
                    d = {'y': y, 'abs_IDs': data['abs_IDs'], 
                         'src_path':data['source'], 'fts_path':path}
                    # OUTPUT PREDICTIONS
                    #print predictions[path]['abs_IDs']
                    hypothesizer = Hypothesizer(d)
                    hypothesizer.writeHypotheses()
        print '...{} files hypothesized.'.format(count)
        print '...({} featurized)'.format(len(test_paths))

    # SAVE CLASSIFIER AT THE END
    print '...saving classifier to {}...'.format(classifier.save_path)
    classifier.save()


if __name__ == '__main__':
    main()

