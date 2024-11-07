from zipfile import ZipFile, ZIP_DEFLATED
import os
# from subprocess import call

valid_set = {'en': 'val', 'de': 'validation', 'ja': 'valid'}
test_set = {'en': ('test_id', 'test_ood'), 'de': ('test',), 'ja': ('test',)}

split_path = '../tmp/split'

def zip_folder(zf, lang, set_name, side, skip_set = None):
    folder = os.path.join(split_path, lang, set_name, side)
    for fname in os.listdir(folder):
        if skip_set:
            arcname = os.path.join(skip_set, lang, side, fname)
        else:
            arcname = None
        zf.write(os.path.join(folder, fname), arcname)

def zip_del(zf, lang, set_name, skip_set = None, with_ids = True):
    lfile = os.path.join(split_path, lang, set_name, 'list.txt')
    if os.path.isfile(lfile):
        if skip_set:
            arcpath = os.path.join(skip_set, lang)
        else:
            arcpath = None
        zf.write(lfile, os.path.join(arcpath, 'list.txt') if skip_set else None)
        if with_ids:
            zf.write(os.path.join(split_path, lang, set_name, 'del_ids.txt'), os.path.join(arcpath, 'del_ids.txt') if skip_set else None)

def merge_files(zf, lang, test_sets, target):
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile('w') as tmp:
        for te_set in test_sets:
            with open(os.path.join(split_path, lang, te_set, target)) as fr:
                for line in fr:
                    tmp.write(line)
            if te_set != test_sets[-1]:
                tmp.write('\n')
        tmp.flush()
        zf.write(tmp.name, os.path.join('test', lang, target))


# data.zip contains all files and data for devepment, testing, and submitting.
with ZipFile('../tmp/data.zip', 'w', compression = ZIP_DEFLATED, compresslevel = 9) as zf:
    zf.write('create.submission.py')
    zf.write('../tmp/dummy.submission.zip')
    for lang, val_set in valid_set.items():
        zip_folder(zf, lang, 'train', 'source')
        zip_folder(zf, lang, val_set, 'source')
        if lang == 'ja':
            zip_folder(zf, lang, 'train', 'target_0')
            zip_folder(zf, lang, val_set, 'target_0')
            zip_folder(zf, lang, 'train', 'target_1')
            zip_folder(zf, lang, val_set, 'target_1')
        else:
            zip_folder(zf, lang, 'train', 'target')
            zip_folder(zf, lang, val_set, 'target')
        zip_del(zf, lang, 'train')
        zip_del(zf, lang, val_set)

    kwargs = dict(skip_set = 'test')
    for lang, test_sets in test_set.items():
        for te_set in test_sets:
            if lang == 'ja':
                zip_folder(zf, lang, te_set, 'source', **kwargs)
            else:
                zip_folder(zf, lang, te_set, 'source', **kwargs)
        if len(test_sets) == 1:
            zip_del(zf, lang, te_set, with_ids = False, **kwargs)
        else:
            merge_files(zf, lang, test_sets, 'list.txt')


# validation data
with ZipFile('../tmp/ref.valid.zip', 'w') as zf:
    kwargs = dict(skip_set = 'valid')
    for lang, val_set in valid_set.items():
        if lang == 'ja':
            zip_folder(zf, lang, val_set, 'source', **kwargs)
            zip_folder(zf, lang, val_set, 'target_0', **kwargs)
            zip_folder(zf, lang, val_set, 'target_1', **kwargs)
        else:
            zip_folder(zf, lang, val_set, 'source', **kwargs)
            zip_folder(zf, lang, val_set, 'target', **kwargs)
        zip_del(zf, lang, val_set, **kwargs)

# test data
with ZipFile('../tmp/ref.test.zip', 'w') as zf:
    kwargs = dict(skip_set = 'test')
    for lang, test_sets in test_set.items():
        for te_set in test_sets:
            if lang == 'ja':
                zip_folder(zf, lang, te_set, 'source', **kwargs)
                zip_folder(zf, lang, te_set, 'target_0', **kwargs)
                zip_folder(zf, lang, te_set, 'target_1', **kwargs)
            else:
                zip_folder(zf, lang, te_set, 'source', **kwargs)
                zip_folder(zf, lang, te_set, 'target', **kwargs)
        if len(test_sets) == 1:
            zip_del(zf, lang, te_set, **kwargs)
        else:
            merge_files(zf, lang, test_sets, 'list.txt')
            merge_files(zf, lang, test_sets, 'del_ids.txt')

# scoring program for either validation or test data (depends on competition schedule)
with ZipFile('../tmp/scoring_program.zip', 'w') as zf:
    zf.write('scoring_program/score.py')
    zf.write('scoring_program/sari.py')
    zf.write('scoring_program/metadata')

# overall bundle for CodaLab
with ZipFile('../bundle.zip', 'w') as zf:
    for fname in os.listdir('html'):
        zf.write(f'html/{fname}')
    zf.write('../tmp/scoring_program.zip', 'scoring_program.zip')
    zf.write('../tmp/data.zip', 'data.zip')
    zf.write('../tmp/ref.valid.zip', 'ref.valid.zip')
    zf.write('../tmp/ref.test.zip', 'ref.test.zip')
    zf.write('competition.yaml', 'competition.yaml')