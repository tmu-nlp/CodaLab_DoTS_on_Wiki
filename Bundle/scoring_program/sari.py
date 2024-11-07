import numpy as np
from collections import Counter, namedtuple

D_SARI = namedtuple('SARI', 'SARI, F_keep, P_del, F_add, D_SARI, D_keep, D_del, D_add')

def normalize(x, z):
    return (x / z) if z > 0 else 0

def f1(precision, recall):
    if precision > 0 and recall > 0:
        return 2 * precision * recall / (precision + recall)
    return 0

def keep_f1(s_gram_counter_rep, c_gram_counter_rep, r_gram_counter):
    keep_gram_counter_rep      = s_gram_counter_rep    & c_gram_counter_rep
    keep_gram_counter_good_rep = keep_gram_counter_rep & r_gram_counter
    keep_gram_counter_all_rep  = s_gram_counter_rep    & r_gram_counter

    keep_p = 0
    keep_r = 0
    for keepgram in keep_gram_counter_good_rep:
        keep_p += keep_gram_counter_good_rep[keepgram] / keep_gram_counter_rep[keepgram]
        keep_r += keep_gram_counter_good_rep[keepgram] / keep_gram_counter_all_rep[keepgram]

    keep_pz = len(keep_gram_counter_rep)
    keep_rz = len(keep_gram_counter_all_rep)
    keep_precision = normalize(keep_p, keep_pz)
    keep_recall    = normalize(keep_r, keep_rz)

    return f1(keep_precision, keep_recall), (keep_p, keep_pz, keep_r, keep_rz)

def delete_prec(s_gram_counter_rep, c_gram_counter_rep, r_gram_counter):
    del_gram_counter_rep      = s_gram_counter_rep   - c_gram_counter_rep
    del_gram_counter_good_rep = del_gram_counter_rep - r_gram_counter
    # del_gram_counter_all_rep = s_gram_counter_rep - r_gram_counter

    del_p = 0
    # del_r = 0
    for delgram in del_gram_counter_good_rep:
        del_p += del_gram_counter_good_rep[delgram] / del_gram_counter_rep[delgram]
        # del_r += del_gram_counter_good_rep[delgram] / del_gram_counter_all_rep[delgram]

    del_pz = len(del_gram_counter_rep)
    del_precision = normalize(del_p, del_pz)

    # instead of f1(del_precision, delscore_recall), blaming delscore_recall
    return del_precision, (del_p, del_pz)

def add_f1(s_gram_counter, c_gram_counter, r_gram_counter):

    add_gram_counter      = set(c_gram_counter)   - set(s_gram_counter)
    add_gram_counter_good = set(add_gram_counter) & set(r_gram_counter)
    add_gram_counter_all  = set(r_gram_counter)   - set(s_gram_counter)

    add_ = len(add_gram_counter_good)

    add_pz = len(add_gram_counter)
    add_rz = len(add_gram_counter_all)
    add_precision = normalize(add_, add_pz)
    add_recall    = normalize(add_, add_rz)

    return f1(add_precision, add_recall), (add_, add_pz, add_rz)


def SARI_scores(sgrams, cgrams, rgramslist, numref):

    s_gram_counter = Counter(sgrams)
    s_gram_counter_rep = Counter()
    for sgram, scount in s_gram_counter.items():
        s_gram_counter_rep[sgram] = scount * numref

    c_gram_counter = Counter(cgrams)
    c_gram_counter_rep = Counter()
    for cgram, ccount in c_gram_counter.items():
        c_gram_counter_rep[cgram] = ccount * numref

    r_gram_counter = Counter(rgram for rgrams in rgramslist for rgram in rgrams)

    f_keep, keep_4_scores =     keep_f1(s_gram_counter_rep, c_gram_counter_rep, r_gram_counter)
    p_del, del_2_scores   = delete_prec(s_gram_counter_rep, c_gram_counter_rep, r_gram_counter)
    f_add, add_3_scores   =      add_f1(s_gram_counter,     c_gram_counter,     r_gram_counter)

    return (f_keep, p_del, f_add), keep_4_scores + del_2_scores + add_3_scores

def micro_sari(keep_p, keep_pz, keep_r, keep_rz, del_p, del_pz, add_, add_pz, add_rz):
    keep_f = f1(normalize(keep_p, keep_pz), normalize(keep_r, keep_rz))
    add_f  = f1(normalize(add_, add_pz),    normalize(add_, add_rz))
    del_p  = normalize(del_p, del_pz)
    return D_SARI((keep_f + del_p + add_f) / 3, keep_f, del_p, add_f, None, None, None, None)

def d_score(keep_f, del_p, add_f, LP_1, LP_2, SLP):
    d_keep = keep_f * LP_2 * SLP
    d_del  = del_p * LP_2
    d_add  = add_f * LP_1
    d_sari = (d_keep + d_del + d_add) / 3
    return d_keep, d_del, d_add, d_sari

def score(ssent, csent, rsents, tokenizer = str.split, aggregator = None):

    s1grams = tokenize(ssent, tokenizer)
    s2grams = []
    s3grams = []
    s4grams = []
    c1grams = tokenize(csent, tokenizer)
    c2grams = []
    c3grams = []
    c4grams = []
    make_ngram(c1grams, c2grams, c3grams, c4grams)
    make_ngram(s1grams, s2grams, s3grams, s4grams)

    r1gramslist = []
    r2gramslist = []
    r3gramslist = []
    r4gramslist = []

    for rsent in rsents:

        r1grams = tokenize(rsent, tokenizer)
        r2grams = []
        r3grams = []
        r4grams = []
        make_ngram(r1grams, r2grams, r3grams, r4grams)
        r1gramslist.append(r1grams)
        r2gramslist.append(r2grams)
        r3gramslist.append(r3grams)
        r4gramslist.append(r4grams)

    numref = len(rsents)
    fpf1, s71 = SARI_scores(s1grams, c1grams, r1gramslist, numref)
    fpf2, s72 = SARI_scores(s2grams, c2grams, r2gramslist, numref)
    fpf3, s73 = SARI_scores(s3grams, c3grams, r3gramslist, numref)
    fpf4, s74 = SARI_scores(s4grams, c4grams, r4gramslist, numref)

    # SARI
    macro_scores = np.asarray([fpf1, fpf2, fpf3, fpf4]).mean(axis = 0)
    keep_f, del_p, add_f = macro_scores
    sari = macro_scores.mean()

    if aggregator is not None:
        aggregator += np.asarray([s71, s72, s73, s74]).sum(axis = 0)

    # D-SARI
    token_input_length  = len(s1grams)
    token_output_length = len(c1grams)
    token_reference_length = sum(len(r1grams) for r1grams in r1gramslist) // len(r1gramslist)
    
    if token_output_length >= token_reference_length:
        LP_1 = 1
    else:
        LP_1 = np.exp((token_output_length - token_reference_length) / token_output_length)

    if token_output_length > token_reference_length:
        LP_2 = np.exp((token_reference_length - token_output_length) / max(token_input_length - token_reference_length, 1))
    else:
        LP_2 = 1

    sentence_output_length    = len(csent)
    sentence_reference_length = sum(len(rsent) for rsent in rsents) // len(rsents)
    SLP = np.exp(-abs(sentence_reference_length - sentence_output_length) / max(sentence_reference_length, sentence_output_length))

    d_keep, d_del, d_add, d_sari = d_score(keep_f, del_p, add_f, LP_1, LP_2, SLP)
    return D_SARI(sari, keep_f, del_p, add_f, d_sari, d_keep, d_del, d_add)

def make_ngram(unigrams, *ngrams):
    n_token = len(unigrams)
    n_gram  = len(ngrams)
    for i in range(n_token - 1):
        for j in range(n_gram):
            k = i + j + 2
            if k <= n_token:
                ngrams[j].append(tuple(unigrams[i:k]))

def tokenize(sentences, tokenizer):
    unigram = []
    for sent in sentences:
        unigram.extend(tokenizer(sent))
    return unigram

class ScoreSummary:
    def __init__(self, tokenizer = str.split):
        self.tokenizer = tokenizer
        self.micro_scores = np.zeros(9)
        self.macro_scores = []

    def score(self, source, target, refereces):
        macro = score(source, target, refereces, self.tokenizer, self.micro_scores)
        self.macro_scores.append(macro)
        return macro
    
    def __len__(self):
        return len(self.macro_scores)
    
    def __call__(self):
        return micro_sari(*self.micro_scores), D_SARI(*np.asarray(self.macro_scores).mean(axis = 0))
    
    def __add__(self, other):
        summary = ScoreSummary()
        summary.micro_scores = self.micro_scores + other.micro_scores
        summary.macro_scores = self.macro_scores + other.macro_scores
        return summary
    
    def __radd__(self, other):
        if other == 0:
            return self
        else:
            return self.__add__(other)

def micro_f1(gold, predict):
    gold = Counter(gold)
    predict = set(predict)
    match = sum(gold[k] for k in (gold.keys() & predict))
    return match, sum(gold.get(k, 1) for k in predict), sum(gold.values())

class F1Summary:
    def __init__(self):
        self.micro_scores = np.zeros(3)
        self.macro_scores = []

    def score(self, source, target):
        mt, pd, gd = micro_f1(source, target)
        self.micro_scores += np.asarray([mt, pd, gd])
        pr = normalize(mt, pd)
        rc = normalize(mt, gd)
        self.macro_scores.append(np.asarray([pr, rc, f1(pr, rc)]))
    
    def __len__(self):
        return len(self.macro_scores)
    
    def __call__(self):
        mt, pd, gd = self.micro_scores
        pr = normalize(mt, pd)
        rc = normalize(mt, gd)
        return pr, rc, f1(pr, rc)


def test0():
    import nltk

    ssent = nltk.sent_tokenize("marengo is a town in and the county seat of iowa county , iowa , united states . it has served as the county seat since august 1845 , even though it was not incorporated until july 1859 . the population was 2,528 in the 2010 census , a decline from 2,535 in 2000 .")
    csent1 = nltk.sent_tokenize("in the US . 2,528 in 2010 .")
    csent2 = nltk.sent_tokenize("marengo is a city in iowa , the US . it has served as the county seat since august 1845 , even though it was not incorporated . the population was 2,528 in the 2010 census , a decline from 2,535 in 2010 .")
    csent3 = nltk.sent_tokenize("marengo is a town in iowa . marengo is a town in the US . in the US . the population was 2,528 . the population in the 2010 census .")
    csent4 = nltk.sent_tokenize("marengo is a town in iowa , united states . in 2010 , the population was 2,528 .")
    rsents = [nltk.sent_tokenize("marengo is a city in iowa in the US . the population was 2,528 in 2010 .")]
    
    s9 = np.zeros(9)
    print(score(ssent, csent1, rsents, aggregator = s9))
    print(score(ssent, csent2, rsents, aggregator = s9))
    print(score(ssent, csent3, rsents, aggregator = s9))
    print(score(ssent, csent4, rsents, aggregator = s9))
    s = micro_sari(*s9)

    print(f'Micro SARI Keep: {s.F_keep:.2f} Delete: {s.P_del:.2f} Add: {s.F_add:.2f}   Avg: {s.SARI:.2f}')

def test1():
    summ = F1Summary()
    summ.score([0, 1, 2, 2], [2])
    summ.score([0, 1, 2, 2], [0, 1])
    print(summ.macro_scores)
    print(summ())
    
if __name__ == '__main__':
    test0()
    test1()