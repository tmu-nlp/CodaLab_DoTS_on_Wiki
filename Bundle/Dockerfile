# this file setup the CodaLab workers' environment
FROM --platform=linux/amd64 amd64/python:3.12.4-bookworm

RUN apt update

# for mecab
RUN apt install -y mecab
RUN apt install -y libmecab-dev
RUN apt install -y mecab-ipadic-utf8
RUN apt install -y git
RUN apt install -y curl
RUN apt install -y file
RUN apt install -y make
RUN apt install -y xz-utils
RUN git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git
RUN mecab-ipadic-neologd/bin/install-mecab-ipadic-neologd --newest --asuser --forceyes
# base requirement for mecab and python3
# https://qiita.com/relu/items/af042f73785aec979ed2

# RUN apt install -y python3-pip
RUN pip install mecab-python3
RUN pip install unidic-lite

# for d-sari
RUN pip install numpy

RUN pip install emoji~=1.6.3
RUN pip install bunkai
RUN pip install nltk
RUN python -m nltk.downloader -d /usr/local/share/nltk_data punkt