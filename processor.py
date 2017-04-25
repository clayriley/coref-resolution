
import re, os

class Processor:
    
    start_R = re.compile(r'\((\d+)(?!\d)')
    end_R = re.compile(r'(?<!\d)(\d+)\)')

    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path
        self.lines = []
        self.pairs = {}

    def process(self, classification=None):

        def addToEntities(entities, s1, s2):
            try:
		        for key_1 in entities:
		            for key_2 in entities[key_1]:
		                entities[key_1][key_2].append((s1, s2))
            except AttributeError:
                msg = "addToEntities() is being called incorrectly; verify " \
                      "that supplied dict is valid.\nValid format: {k1:{k2:" \
                      "[], ...}, ...}"
                raise AttributeError(msg)
                           
        def passFields(s1, s2, *other_args):
            return (s1, s2)

        def processFields(s1, s2, id1, id2):
            fields = s1.split()
            return {'sentence_ID':id1,
                    'line_ID':id2, 
                    #'file_name':fields[0],  
                    'section_ID':fields[1],
                    'token_ID':int(fields[2]),
                    'token':fields[3],
                    'POS':fields[4],
                    #'syn_parse':fields[5],
                    'lemma':fields[6],
                    #'frameset':fields[7],
                    #'sense':fields[8],
                    'speaker':fields[9],
                    'named_ents':fields[10],
                    'arg_parse':fields[11:]}

        field_action = processFields if classification is None else passFields
        
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
                        # only add this token's info to opened entities
                        fields = field_action(field_str)
                        addToEntities(opened, fields, refs)

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
  
                        # add it to opened entities
                        fields = field_action(field_str)
                        addToEntities(opened, fields, refs)


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

















 # TODO fix in featurize





                        # record all entities for intervening tokens
                        field_str['ent_refs'] = starting
