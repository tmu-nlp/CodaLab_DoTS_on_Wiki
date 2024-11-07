import os
from time import time
# from functools import lru_cache

# @lru_cache()
def get_tokenizer():
    import MeCab
    import subprocess
    result = subprocess.run(["mecab-config", "--dicdir"], stdout = subprocess.PIPE)
    assert result.returncode == 0
    dict_path = os.path.join(result.stdout.rstrip().decode(), 'mecab-ipadic-neologd')
    mecab = MeCab.Tagger(f'-d {dict_path}')

    def tokenizer(sent):
        return [s.split('\t', 1)[0] for s in mecab.parse(sent).split('\n') if '\t' in s]
    return tokenizer

def evaluate_sari(stream, lang, c_folder, s_folder, *r_folders):
    from sari import ScoreSummary
    if lang == 'ja':
        from bunkai import Bunkai
        bunkai = Bunkai()
        summary = ScoreSummary(get_tokenizer())
    else:
        from nltk import sent_tokenize, word_tokenize
        if lang == 'en':
            # summary = ScoreSummary(word_tokenize)
            summary = ScoreSummary(lambda s: [w.lower() for w in word_tokenize(s, language = 'english')])
        elif lang == 'de':
            # summary = ScoreSummary(lambda s: word_tokenize(s, language = 'german'))
            summary = ScoreSummary(lambda s: [w.lower() for w in word_tokenize(s, language = 'german')])

    fnames             = set(x for x in os.listdir(c_folder) if x.endswith('.txt'))
    assert     fnames == set(x for x in os.listdir(s_folder) if x.endswith('.txt')), 'Submission files do not match reference files: submitting dev to test or vise versa?'
    for r_folder in r_folders:
        assert fnames == set(x for x in os.listdir(r_folder) if x.endswith('.txt')), 'Submission files do not match reference files: submitting dev to test or vise versa?'

    duration = time()
    mse = []
    for fname in fnames:
        cr = []
        with open(os.path.join(c_folder, fname)) as fr:
            for s in fr.readlines():
                s = s.strip()
                if lang == 'en':
                    cr.extend(sent_tokenize(s))
                elif lang == 'de':
                    cr.extend(sent_tokenize(s, language = 'german'))
                elif lang == 'ja':
                    cr.extend(bunkai(s))

        with open(os.path.join(s_folder, fname)) as fr:
            sr = [s.strip() for s in fr.readlines()]
        rr = []
        for r_folder in r_folders:
            with open(os.path.join(r_folder, fname)) as fr:
                rr.append([s.strip() for s in fr.readlines()])
        if lang == 'ja':
            mse.append((sum(len(s) for s in cr) - 150) ** 2)
        summary.score(sr, cr, rr)

    duration = time() - duration
    micro, macro = summary()

    write_percentages(
        stream, lang,
        micro_sari = micro.SARI,
        macro_sari = macro.SARI,
        macro_d_sari = macro.D_SARI)

    write_others(
        stream, lang, 
        duration = duration)
    
    if lang == 'ja':
        write_others(
            stream, lang, 
            mse = sum(mse) / len(mse))
    
    return summary


def evaluate_del(stream, lang, s_file, r_file):
    from sari import F1Summary
    succ = 1
    try:
        f1 = F1Summary()
        with open(s_file) as fs, open(r_file) as fr:
            for ss, rs in zip(fs, fr):
                ss = ss.rstrip().split(',')
                rs = rs.rstrip().split(',')
                f1.score(ss, rs)
        pr, rc, f1 = f1()
        print('lang ', lang)
    except FileNotFoundError:
        succ = pr = rc = f1 = 0
    write_percentages(
        stream, lang,
        f1 = f1,
        pr = pr,
        rc = rc)
    return succ


def write_percentages(stream, lang, **scores):
    for k, v in scores.items():
        print(f'{lang}_{k}: {v * 100}', file = stream)

def write_others(stream, lang, **scores):
    for k, v in scores.items():
        print(f'{lang}_{k}: {v}', file = stream)


if __name__ == '__main__':
    try:
        from sys import argv
        _, input_dir, output_dir = argv
        result_dir    = os.path.join(input_dir, 'res')
        reference_dir = os.path.join(input_dir, 'ref')

        if os.path.isdir(reference_dir := os.path.join(reference_dir, 'valid')):
            split = 'en', 'de', 'ja' #{'en': 'val', 'de': 'validation', 'ja': 'valid'}
        elif os.path.isdir(reference_dir := os.path.join(reference_dir, 'test')):
            split = 'en', 'de', 'ja' #{'en': ('test_id', 'test_ood'), 'de': 'test', 'ja': 'test'}
        else:
            raise ValueError(f'System Error: no reference found! {os.listdir(reference_dir)}')
        
        result_langs = [lang for lang in os.listdir(result_dir) if lang in split]
        summaries = []
        del_success = 0

        with open(os.path.join(output_dir, 'scores.txt'), 'w') as fw:
            for lang in result_langs:
                c_lang = os.path.join(result_dir, lang)
                s_lang = os.path.join(reference_dir, lang, 'source')
                if lang == 'ja':
                    r_lang = tuple(os.path.join(reference_dir, lang, f'target_{i}') for i in range(2))
                else:
                    r_lang = os.path.join(reference_dir, lang, 'target'),
                summaries.append(evaluate_sari(fw, lang, c_lang, s_lang, *r_lang))

                del_success += evaluate_del(fw, lang,
                    os.path.join(reference_dir, lang, 'del_ids.txt'),
                    os.path.join(result_dir, lang + '.del'))

            micro, macro = sum(summaries)()
            print(f'ave_micro_sari: {micro.SARI * 100}', file = fw)
            print(f'ave_macro_sari: {macro.SARI * 100}', file = fw)
            print(f'ave_macro_d_sari: {macro.D_SARI * 100}', file = fw)
            print(f"submitted_lang:", len(result_langs) + 0.1 * del_success, file = fw)

        # 说明：上传失败不算做每日计数；不要hack（控制test数据的可见期间）；
    except:
        micro, macro = sum((
            evaluate_sari(None, 'en',
                '../py/split/en/val/dummy', 
                '../py/split/en/val/source',
                '../py/split/en/val/target'),
            evaluate_sari(None, 'de',
                '../py/split/de/validation/dummy', 
                '../py/split/de/validation/source',
                '../py/split/de/validation/target'),
            evaluate_sari(None, 'ja',
                '../py/split/ja/valid/dummy', 
                '../py/split/ja/valid/source',
                '../py/split/ja/valid/target_0',
                '../py/split/ja/valid/target_1')
        ))()
        print('micro', micro)
        print('macro', macro)
        evaluate_del(None, 'en', '../py/split/en/val/del_ids.txt', '../py/split/en/val/dummy.del')
        evaluate_del(None, 'ja', '../py/split/ja/valid/del_ids.txt', '../py/split/ja/valid/dummy.del')