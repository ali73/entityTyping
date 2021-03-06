import os
from conf_local import *


class Path:
    files_path = os.path.abspath('/media/ali/4E18CE7660884013/dataset')
    freebase_path = os.path.join('/media/ali/4E18CE7660884013/dataset')
    root_path = os.path.abspath('.')

INSERT_TITLES = False
UPDATE_ID = False
PARSE = False
PARSE_DBPEDIA = False
PARSE_WIKI_ARTICLES = False
PARSE_FASTTEXT = False
FARS_BASE = 'http://localhost:8890/farsbase'
DB_PEDIA = 'http://localhost:8890/dbpedia'
WORD_VEC_SIZE = 300
d = 30
HIDDEN_LAYER_SIZE = 300
languages = ['en']