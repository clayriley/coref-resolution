# Clay Riley 2017

import re
            
# regexes for this task
startR = re.compile(r'\((\d+)(?!\d)')
endR = re.compile(r'(?<!\d)(\d+)\)')
metaR = re.compile(r'#')
blankR = re.compile(r'\s*$')

def readLines(iterable, process, classifying=False):

    processed = {}

    if classifying:
        # TODO extract write_hypotheses.py code to here and abstract
        raise NotImplementedError('readLines() must currently be called with classifying=True.')


    else:  # NOT CLASSIFYING

        instances = []
        abs_IDs = []
        labels = []
        raw = []
            
        # previously encountered and incomplete entities
        antecedents, opened = [], {}
        all_tokens = []
        abs_ID, sen_ID, ref_ID = 0, 0, 0
                 
        for line in iterable:
   
            # new section: reset antecedents and sentence/token IDs
            #if metaR.match(line):
            if line[0]=='#':
                antecedents, opened = [], {}
                sen_ID = 0
                
            # new sentence: update sentence IDs
            #elif blankR.match(line):
            elif len(line.strip())==0:
                sen_ID += 1
                opened = {}  # ignore any entities remaining open
                        
            # new token
            else:
                fields = line.split()
                fields = {'abs_ID':abs_ID, 
                          'sen_ID':sen_ID,
                          'ent_refs':fields[-1],  # coreference resolution via gold standard
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
                          'arg_parse':fields[11:-1]
                          }
                anaphora = []  # list of current anaphora
                starting = startR.findall(fields['ent_refs'])
                ending = endR.findall(fields['ent_refs'])
                   
                # current token has entity start(s), open it
                if len(starting) > 0:  
                    for entity in starting:
                        # inception crash prevention
                        if entity in opened:
                            opened[entity][ref_ID] = []
                        else:
                            opened[entity] = {ref_ID: []}
                        ref_ID += 1     
                    
                # add this token's info to all opened entities and vice versa
                for entity in opened:
                    for r in opened[entity]:
                        fields['ent_refs'] = entity
                        opened[entity][r].append(fields)
                # record all entities for intervening tokens
                fields['ent_refs'] = starting
                    
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
                    for r_ID in closing: # TODO remove this altogether--it isn't necessary, just use a stack
                        anaphora.append(closing[r_ID])  
                   
                # process all possible antecedent-anaphor pairs
                for ana in anaphora:
                    for ant in antecedents:
                        intervening = [all_tokens[i] for i in range(ant[-1]['abs_ID']+1, ana[0]['abs_ID'])]
                        instance, label = process(ant, ana, intervening)
                        ana_range = (ana[0]['abs_ID'], len(ana))
                        ant_range = (ant[0]['abs_ID'], len(ant))
                        instances.append(instance)
                        labels.append(label)
                        abs_IDs.append((ant_range, ana_range))
                    antecedents.append(ana)  # add all completed anaphora to antecedents
                # add this token to list of all tokens in part up to this point
                all_tokens.append(fields)  
                abs_ID += 1

            raw.append(line)

        processed['instances'] = instances
        processed['abs_IDs'] = abs_IDs
        processed['labels'] = labels
        processed['raw'] = raw
    
    return processed

