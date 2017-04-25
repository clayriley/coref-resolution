
import re, os

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

