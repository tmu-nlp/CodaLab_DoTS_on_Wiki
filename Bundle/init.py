import os

def mkdir(folder):
    if not os.path.isdir(folder):
        os.mkdir(folder)

for folder in ('../tmp', '../tmp/stat', '../tmp/pdf', '../tmp/svg'):
    mkdir(folder)