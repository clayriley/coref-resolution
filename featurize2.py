# author: Clay Riley 2017

import sys, os, re, errno, pickle

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

def instantiate(antecedent, between, anaphor):
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

