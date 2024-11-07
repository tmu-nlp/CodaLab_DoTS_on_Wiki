import os, sys
from random import random
from init import mkdir
from subprocess import call
from nltk.tokenize import TreebankWordTokenizer
tokenizer = TreebankWordTokenizer()

_, fpath = sys.argv

def pseudo_prediction(split):
    source = os.path.join(split, 'source')
    target = os.path.join(split, 'target')
    is_ja = not os.path.isdir(target)
    dummy = os.path.join(split, 'dummy')
    mkdir(dummy)

    fnames = os.listdir(source)
    for fname in fnames:
        with open(os.path.join(dummy, fname), 'w') as fd, \
            open(os.path.join(source, fname), 'r') as fs:
            if is_ja:
                lines = [line.rstrip() for line in fs]
                tar_len = 150
            else:
                lines = tokenizer.tokenize_sents(fs.readlines())
                with open(os.path.join(target, fname), 'r') as ft:
                    tar_len = sum(len(l) for l in tokenizer.tokenize_sents(ft.readlines()))

            src_len = sum(len(l) for l in lines)
            if tar_len > src_len:
                ratio = .9
            else:
                ratio = tar_len / src_len

            for line in lines:
                if is_ja:
                    pseudo = ''.join(char for char in line if random() < ratio)
                else:
                    pseudo = ' '.join(word for word in line if random() < ratio)
                fd.write(pseudo)
                fd.write('\n')
    with open(os.path.join(split, 'dummy.del'), 'w') as fd:
        fd.write('\n'.join('0' for _ in fnames))

pseudo_prediction(os.path.join(fpath, 'ja', 'valid'))
pseudo_prediction(os.path.join(fpath, 'en', 'val'))
pseudo_prediction(os.path.join(fpath, 'de', 'validation'))

call(['python', 'create.submission.py', '../tmp/dummy.submission.zip',
      '-j', os.path.join(fpath, 'ja', 'valid', 'dummy'),
      '-e', os.path.join(fpath, 'en', 'val', 'dummy'),
      '-d', os.path.join(fpath, 'de', 'validation', 'dummy'),
      '--deletion', 'dummy.del'])