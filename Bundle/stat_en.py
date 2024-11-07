import json, sys, os
from init import mkdir
from nltk import sent_tokenize
from nltk.tokenize import TreebankWordTokenizer
from collections import Counter
from SWiPE import del_sent_ids
tokenizer = TreebankWordTokenizer()

_, fpath = sys.argv

splits = 'val', 'test_id', 'test_ood', 'train'
base_folder = os.path.join(fpath, 'en')
mkdir(base_folder)
print('SWiPE')

def stats(split, cnt_start = 0, stream = None):
    print('title,s.sent,s.word,r.sent,r.word', file = stream)
    with open(f'../Corpora/SWiPE/data/swipe_{split}.json') as fr:
        data = [s for s in json.load(fr)]
    titles = Counter(s['r_page'] for s in data)
    if titles := {k:v for k,v in titles.items() if v > 1}:
        assert split == 'test_ood'

    del_ids = {}
    for sid, sample in enumerate(data, cnt_start):
        title = sample['r_page']

        if title in titles:
            titles[title] -= 1
            title = title + f'_({sid})'

        article = sample['r_content']
        reference = sample['s_content'] # simple wiki
        src_sents = sent_tokenize(article)
        ref_sents = sent_tokenize(reference)
        src_wlen = sum(len(sent) for sent in tokenizer.tokenize_sents(src_sents))
        ref_wlen = sum(len(sent) for sent in tokenizer.tokenize_sents(ref_sents))
        src_slen = len(src_sents)
        ref_slen = len(ref_sents)
        print(f'"{title}",{src_slen},{src_wlen},{ref_slen},{ref_wlen}', file = stream)
            
        with open(os.path.join(base_folder, split, f'source/{sid}.txt'), 'w') as fw:
            fw.write('\n'.join(src_sents))
        with open(os.path.join(base_folder, split, f'target/{sid}.txt'), 'w') as fw:
            fw.write('\n'.join(ref_sents))

        if 'annotations' in sample:
            del_ids[str(sid)] = src_slen, del_sent_ids(sample, src_sents)
    assert sum(titles.values()) == 0
    return len(data), del_ids

with open('../tmp/stat/en.del.pos.csv', 'w') as fwp, open('../tmp/stat/en.del.ratio.csv', 'w') as fwr, open('../tmp/stat/en.del.cat.csv', 'w') as fwc:
    fwp.write('pos,total,set,cat\n')
    fwr.write('ratio,total,set\n')

    for s in splits:
        mkdir(os.path.join(base_folder, s))
        mkdir(os.path.join(base_folder, s, 'source'))
        mkdir(os.path.join(base_folder, s, 'target'))
        with open(f'../tmp/stat/en.{s}.csv', 'w') as fw:
            ss, del_ids = stats(s, ss if s == 'test_ood' else 0, fw)
            if len(del_ids) == ss:
                print(' ', s, ss)
            else:
                print(' ', s, ss, f'(with {len(del_ids)} having del alignment)')

        fnames = []
        indices = []
        for fname, (total, ids_cats) in del_ids.items():
            fnames.append(fname)
            indices.append(','.join([str(i) for i in sorted(ids_cats)]))
            for eid, cats in ids_cats.items():
                fwp.write(f'{eid},{total},{s},{"+".join(cats)}\n')
            fwr.write(f'{len(ids_cats)},{total},{s}\n')

        with open(os.path.join(base_folder, s, 'list.txt'), 'w') as fws:
            fws.write('\n'.join(fnames))
        with open(os.path.join(base_folder, s, 'del_ids.txt'), 'w') as fwi:
            fwi.write('\n'.join(indices))