#!/bin/bash

split_path="../tmp/split"
if [ -d "$split_path" ]; then
    rm -rf "$split_path"
fi
mkdir "$split_path"

# CodaLab uses python 2.7 workers, so we need to avoid using unicode characters in the filenames.
python stat_en.py "$split_path"
python stat_de.py "$split_path" first_section # de_core_news_dm # <- use spacy intead of nltk.german
python split_stat_jp.py ../Corpora/JADOS-Wiki/data/wikipedia_corpus/wikipedia_v0.1.2.json "$split_path" #3141592653589793 6 2 2
Rscript stat.R
python dummy.submission.py "$split_path"
python packup.py
# for file in plot/*.pdf; do
#     pdfcrop "$file" "$file"
# done