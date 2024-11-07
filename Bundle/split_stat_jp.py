import json
from collections import Counter, defaultdict
import sys, os
from init import mkdir

try:
    _, fname, fpath, n_seed, n_train, n_valid, n_test = sys.argv
    from random import sample, seed
    follow_nagai = False
except:
    _, fname, fpath = sys.argv
    follow_nagai = True

with open(fname) as fr:
    wiki = json.load(fr)
splits = 'train', 'valid', 'test'
indices = defaultdict(set)
nagai_titles = set()

if follow_nagai:
    t2i = {s['title']: eid for eid, s in enumerate(wiki)}

    with open('../Corpora/Nagai/stratified_split.csv') as fr:
        assert next(fr) == 'key,class,split\n'
        for line in fr:
            term, cat, split = line.rstrip().split(',')
            if (idx := t2i.get(term)) is None:
                print(term, 'not found')
            else:
                indices[split].add(idx)
                wiki[idx]['category'] = cat
                nagai_titles.add(term)
else:
    n_train = int(n_train)
    n_valid = int(n_valid)
    n_test  = int(n_test)
    n = n_train + n_valid + n_test

    n_wiki = len(wiki)
    n_train = int(n_train / n * n_wiki)
    n_valid = int(n_valid / n * n_wiki)
    n_test  = n_wiki - n_train - n_valid

    ids_gen = (i for i in range(n_wiki))

    seed(int(n_seed))
    for split in splits:
        ids = sample(ids_gen, eval('n_' + split))
        indices[split].update(ids)
        nagai_titles.update({wiki[i]['title'] for i in ids})
    # from sklearn.model_selection import train_test_split
    # a, b = train_test_split(wiki, test_size = 0.5, random_state = 12, stratify = [w['category'] for w in wiki])
    # train_set_a, valid_set  = train_test_split(a, test_size = 0.2, random_state = 12, stratify = [w['category'] for w in a])
    # train_set_b, test_set = train_test_split(b, test_size = 0.2, random_state = 12, stratify = [w['category'] for w in b])
    # train_set = train_set_a + train_set_b

assert not (indices['train'] & indices['valid'])
assert not (indices['train'] & indices['test'])
assert not (indices['valid'] & indices['test'])
jados_titles = set(w['title'] for w in wiki)
assert jados_titles == nagai_titles
# from pprint import pprint
# pprint(Counter(w['category'] for w in wiki if 'category' in w),)
# print({w['title'] for w in wiki if 'category' not in w})
# print(f'  {len(wiki)} & {len(train_titles) + len(valid_titles) + len(test_ids)} = {len(train_ids) + len(valid_ids) + len(test_ids)}')
# print(f'  {jados_titles - nagai_titles = }')
# print(f'  {nagai_titles - jados_titles = }')

splits = {s: [wiki[idx] for idx in indices[s]] for s in splits}

def dump(split, dataset):
    for sid, sample in enumerate(dataset):
        # unicode is not supported on CodaLab workers with Py27
        # fname = title.replace('/',  '_') + '.txt'
        fname = f'{sid}.txt'
        with open(os.path.join(base_folder, split, 'source', fname), 'w') as fs:
            # if '/' in title:
            #     from pprint import pprint
            #     pprint(sample)
            #     print(prefix)
            #     breakpoint()
            #     continue
            fs.write('\n'.join(sample['source_text']))
        for eid, t in enumerate(sample['annotations']):
            with open(os.path.join(base_folder, split, f'target_{eid}', fname), 'w') as ft:
                ft.write('\n'.join(t['target_text']))
                # target_text
                # simplification_labels
                # alignment_ids
                # summarization_ids
        assert eid == 1

base_folder = os.path.join(fpath, 'ja')
mkdir(base_folder)
for s in splits:
    mkdir(os.path.join(base_folder, s))
    mkdir(os.path.join(base_folder, s, 'source'))
    mkdir(os.path.join(base_folder, s, 'target_0'))
    mkdir(os.path.join(base_folder, s, 'target_1'))

for s, ds in splits.items():
    dump(s, ds)

mean = lambda x: sum(x) / len(x)

def get_tokenizer():
    import os
    import MeCab
    import subprocess
    result = subprocess.run(["mecab-config", "--dicdir"], stdout = subprocess.PIPE)
    assert result.returncode == 0
    dict_path = os.path.join(result.stdout.rstrip().decode(), 'mecab-ipadic-neologd')
    mecab = MeCab.Tagger(f'-d {dict_path}')

    def tokenizer(sent):
        return [s.split('\t', 1)[0] for s in mecab.parse(sent).split('\n') if '\t' in s]
    return tokenizer
tokenizer = get_tokenizer()

def stats(dataset, stream = None):
    print('wiki,category,title,s.sent,s.word,r.sent,r.word,I,D,M,E,S', file = stream)
    for sample in dataset:
        print(sample['class'], end = ',', file = stream)
        print(sample['category'], end = ',', file = stream)
        print(sample['title'], end = ',', file = stream)

        article = sample['source_text']
        print(len(article), end = ',', file = stream)
        print(sum(len(tokenizer(x)) for x in article), end = ',', file  = stream)

        references = [a['target_text'] for a in sample['annotations']]
        print(mean([len(r) for r in references]), end = ',', file = stream)
        print(mean([sum(len(tokenizer(x)) for x in r) for r in references]), end = ',', file = stream)
        edits = Counter()
        for a in sample['annotations']:
            edits += Counter(a['simplification_labels'])
        print(','.join(str(edits[k]) for k in 'IDMES'), file = stream)

print('JADOS')
for ds_, ds in splits.items():
    print(' ', ds_, len(ds))
    with open(f'../tmp/stat/ja.{ds_}.csv', 'w') as fw:
        stats(ds, fw)

with open('../tmp/stat/ja.del.pos.csv', 'w') as fwp, open('../tmp/stat/ja.del.ratio.csv', 'w') as fwr:
    fwp.write('pos,total,set\n')
    fwr.write('ratio,total,set\n')
    for ds_, ds in splits.items():
        fnames = []
        indices = []
        for sid, sample in enumerate(ds):
            fnames.append(str(sid))
            idx = []
            for annotation in sample['annotations']:
                alignment = annotation['alignment_ids']
                total = len(alignment)
                count = 0
                for eid, tgt in enumerate(alignment):
                    if not tgt:
                        idx.append(eid)
                        count += 1
                        fwp.write(f'{eid},{total},{ds_}\n')
                fwr.write(f'{count},{total},{ds_}\n')
            indices.append(','.join(str(i) for i in idx))

        with open(os.path.join(base_folder, ds_, 'list.txt'), 'w') as fws:
            fws.write('\n'.join(fnames))
        with open(os.path.join(base_folder, ds_, 'del_ids.txt'), 'w') as fwi:
            fwi.write('\n'.join(indices))