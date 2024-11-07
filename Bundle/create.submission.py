import os
import zipfile
import argparse

parser = argparse.ArgumentParser(
    prog = 'create.submission.py', usage='%(prog)s ZIP_FILE [options]',
    description = 'DoTS/Wiki Submission Tool - Create submission package (.zip file)',
    epilog = 'Composed by zchen0420')

parser.add_argument('fzip', metavar = 'ZIP_FILE', help = 'e.g. submission.zip', type = str)
parser.add_argument('-e', '--en', type = str, help = "English Prediction Directory", default = None)
parser.add_argument('-d', '--de', type = str, help = "German Prediction Directory", default = None)
parser.add_argument('-j', '--ja', type = str, help = "Japanese Prediction Directory", default = None)
parser.add_argument('--deletion', type = str, help = "Sentence Deletion Prediction File Name", default = 'del_ids.txt')
args = parser.parse_args()

todo = {}
if args.en:
    todo['en'] = args.en
if args.de:
    todo['de'] = args.de
if args.ja:
    todo['ja'] = args.ja
if not todo:
    print('Nothing is created.')
    exit()

done = {}
for lang, folder in todo.items():
    folder = os.path.abspath(os.path.expanduser(folder))
    if not os.path.isdir(folder):
        print(f'ERROR: Folder {folder} does not exist!')
        exit()

    files = []
    for fname in os.listdir(folder):
        if fname[-4:] == '.txt':
            files.append(os.path.join(folder, fname))
    print(f'  Include {len(files)} .txt files')
    
    if os.path.isfile(fname := os.path.join(folder, args.deletion)):
        print(f'    plus {fname}')
        files.pop(files.index(fname))
        files.append(fname)
    elif os.path.isfile(fname := os.path.join(os.path.dirname(folder), args.deletion)):
        print(f'    with {fname}')
        files.append(fname)
    else:
        print(f'    without d{args.deletion}')

    done[lang] = files

fzip = args.fzip.strip()
if fzip[-4:]!= '.zip':
    fzip += '.zip'

with zipfile.ZipFile(fzip, 'w') as zf:
    for lang, files in done.items():
        if files[-1].endswith(args.deletion):
            zf.write(files.pop(), lang + '.del')
        for fpath in files:
            zf.write(fpath, os.path.join(lang, os.path.basename(fpath)))