#
#
#

import sys, os, re
from read_CoNLL import *

class Hypothesizer:

    def __init__(self, dictionary):
        y = dictionary.pop('y')
        abs_IDs = dictionary.pop('abs_IDs')            
        try:
            data = {i:{'y':y[i], 'abs_IDs':abs_IDs[i]} for i in range(len(y))}
            y,abs_IDs = None,None
        except IndexError:
            msg = 'Hypothesizer must be provided with predictions and '
            msg += 'absolute IDs that are the same length.  '
            msg += '(y={}, IDs={})'.format(len(y),len(abs_IDs))
            raise IOError(msg)
        self.data = self.organizeIDs(data)
        self.in_path = os.path.abspath(dictionary.pop('fts_path'))
        self.source = dictionary.pop('src_path')
        self.out_path = self.in_path[:-4]+'.hyp'
        self.clusters = {}

    def writeHypotheses(self):

        with open(self.source, 'rb') as f_in:

            lines = []
            abs_ID = 0
            cluster_ID = 0
            ref_ID = 0
            opened = {}
            escrow = {}
            clusters = {}
            closed = {}
                    
            for line in f_in:

                if metaR.match(line):  # new section
                    lines.append(line+'\n')

                elif blankR.match(line):  # new sentence
                    lines.append(line+'\n')

                else:  # new token
                
                    ent_refs = line[line.rfind(' ')+1:]
                    starts = startR.findall(ent_refs)
                    ends = endR.findall(ent_refs)
                    
                    # mention starts have been found here
                    if len(starts)>0: 
                        for m in starts: 
                            # avoid crashes for inceptive mentions
                            if m in opened:
                                opened[m][ref_ID] = {'abs_ID':abs_ID, 'len':0}
                            else:
                                opened[m] = {ref_ID:{'abs_ID':abs_ID, 'len':0}}
                            ref_ID += 1
                            
                    escrow[abs_ID] = [line[:line.rfind(' ')+1], []]
                    for m in opened:
                        for r in opened[m]:
                            opened[m][r]['len'] += 1
                        
                    # mention ends have been found here
                    if len(ends)>0:
                        for m in ends:
                            try:
                                d = opened.pop(m)
                                # only pop the YOUNGEST inceptive mention,
                                # as there will never be an overlap
                                if len(d)>1:
                                    youngest = d.pop(sorted(d.keys())[-1])
                                    opened[m] = d
                                    d = youngest
                                else:
                                    d = d.values()[0]
                            except KeyError:
                                print 'KEYERROR'
                                print 'ending m=',repr(m)
                                print 'opened=',opened
                                print 'till now:', lines[-20:]
                                print 
                                raise

                                
                            if d['abs_ID'] in closed:
                                closed[d['abs_ID']][d['len']] = m
                            else:
                                closed[d['abs_ID']] = {d['len']: m}
                            
                    
                    # once all mentions have been closed, dump them
                    if len(opened)==0:
                        for ana in sorted(closed.keys()):
                            for span in sorted(closed[ana].keys()):
                                clustered = False
                                hyp = cluster_ID
                                for ant in sorted(self.data[ana][span].keys(), reverse=True):
                                    for ant_span in sorted(self.data[ana][span][ant].keys(),reverse=True):
                                        
                                        if self.data[ana][span][ant][ant_span]==1:
                                            clustered = True
                                            try:
                                                hyp = clusters[ant][ant_span]
                                            except KeyError as e:
                                                # this can happen with long, overlapping mentions.
                                                # just keep searching.
                                                continue
                                            if ana in clusters:
                                                clusters[ana][span] = hyp
                                            else:
                                                clusters[ana] = {span: hyp}
                                            break
                                    if clustered:
                                        break
                                    
                                if not clustered:
                                    clusters[ana] = {span:cluster_ID}
                                    hyp = cluster_ID
                                    cluster_ID += 1
                                
                                gold = closed[ana][span]
                                if span==1:
                                    escrow[ana][1].append('('+str(hyp)+')')
                                else:
                                    escrow[ana][1].append('('+str(hyp))
                                    escrow[ana+span-1][1].append(str(hyp)+')')
                                    
                        for l in sorted(escrow.keys()):
                            if len(escrow[l][1])==0:
                                lines.append(escrow[l][0] + '-\n')
                            else:
                                lines.append(escrow[l][0] + '|'.join(escrow[l][1]) + '\n')
                        escrow.clear()
                        closed.clear()
                                
                    abs_ID += 1

        # write out
        with open(self.out_path, 'wb') as f_out:
            f_out.writelines(lines)


    def organizeIDs(self, data):

        lookup = {}
        
        for i in range(len(data.keys())):
            instance = data.pop(i)
            ant, ana = instance.pop('abs_IDs')
            prediction = instance.pop('y')
            ana_0, ana_len = ana
            ant_0, ant_len = ant
            
            # add the first referent, which has no possible antecedent!
            if ant_0 not in lookup:
                lookup[ant_0] = {ant_len: {}}  
            
            if ana_0 in lookup:
                if ana_len in lookup[ana_0]:
                    if ant_0 in lookup[ana_0][ana_len]:
                        lookup[ana_0][ana_len][ant_0][ant_len] = prediction
                    else:
                        lookup[ana_0][ana_len][ant_0] = {ant_len: prediction}
                else: 
                    lookup[ana_0][ana_len] = {ant_0: {ant_len: prediction}}
            else:
                lookup[ana_0] = {ana_len: {ant_0: {ant_len: prediction}}}

        return lookup
















