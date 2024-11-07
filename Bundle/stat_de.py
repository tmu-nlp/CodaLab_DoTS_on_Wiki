import sys, os
from init import mkdir
from tqdm import tqdm

try:
    _, fpath, trim, use_spacy = sys.argv
    import spacy
    nlp = spacy.load(use_spacy, disable = ("ner",))
except:
    _, fpath, trim = sys.argv
    use_spacy = False
    from nltk import sent_tokenize, word_tokenize

match trim:
    case 'all':
        trim = False
    case 'first_section':
        trim = True
    case _:
        ValueError(f"Invalid argument: {trim} not in (all, first_section)")

splits = 'validation', 'test', 'train'

def stats(split, stream = None):
    w_folder = f'../Corpora/Klexikon/data/splits/{split}/wiki/'
    k_folder = f'../Corpora/Klexikon/data/splits/{split}/klexikon/'
    data = []
    for sid, fname in enumerate(os.listdir(w_folder)):
        title = fname[:-4]
        w_fname = os.path.join(w_folder, fname)
        k_fname = os.path.join(k_folder, fname)
        nw_fname = os.path.join(base_folder, f'{split}/source/{sid}.txt')
        nk_fname = os.path.join(base_folder, f'{split}/target/{sid}.txt')
        if not os.path.isfile(nw_fname): os.link(w_fname, nw_fname)
        with open(k_fname) as fr:
            lines = [line for line in fr]
        if trim:
            abstract = []
            for line in lines:
                if abstract and line.startswith('=='):
                    break
                abstract.append(line)
            while abstract and not abstract[0].strip():
                abstract.pop(0)
            while abstract and not abstract[-1].strip():
                abstract.pop()
            if not abstract:
                breakpoint()
            with open(nk_fname, 'w') as fw:
                for line in abstract:
                    fw.write(line)
            klexikon = ''.join(abstract)
        elif not os.path.isfile(nk_fname): # not trimming
            os.link(k_fname, nk_fname)
            klexikon = ''.join(line for line in lines if not line.startswith('=='))
        with open(w_fname) as fr:
            wiki = ' '.join(fr.readlines())
        data.append((title, wiki, klexikon))

    print('title,s.sent,s.word,r.sent,r.word', file = stream)
    with tqdm(total = len(data), desc = f'  {split}') as qbar:
        for (title, article, reference) in data:
            article = article.replace('\n', '').replace('==== ', '').replace('=== ', '').replace('== ', '').replace('= ', '')
            if use_spacy:
                s_doc = nlp(article)
                r_doc = nlp(reference)
                src_wlen = sum(1 for s in s_doc if s.text.strip())
                ref_wlen = sum(1 for s in r_doc if s.text.strip())
                src_slen = sum(1 for s in s_doc.sents if s.text.strip())
                ref_slen = sum(1 for s in r_doc.sents if s.text.strip())
            else:
                s_sents = sent_tokenize(article, language = 'german')
                r_sents = sent_tokenize(reference, language = 'german')
                src_slen = len(s_sents)
                ref_slen = len(r_sents)
                src_wlen = sum(len(word_tokenize(s, language = 'german')) for s in s_sents if len(s.strip()))
                ref_wlen = sum(len(word_tokenize(r, language = 'german')) for r in r_sents if len(r.strip()))
                # if ref_slen < 4:
                #     breakpoint()
            print(f'"{title}",{src_slen},{src_wlen},{ref_slen},{ref_wlen}', file = stream)
            qbar.update(1)
        qbar.total = 0
        qbar.update(0)

base_folder = os.path.join(fpath, 'de')
mkdir(base_folder)
print('Klexikon (slow down by nltk tokenization in german, spacy is even slower..)')
for s in splits:
    mkdir(os.path.join(base_folder, s))
    mkdir(os.path.join(base_folder, s, 'source'))
    mkdir(os.path.join(base_folder, s, 'target'))
    with open(f'../tmp/stat/de.{s}.csv', 'w') as fw:
        stats(s, fw)