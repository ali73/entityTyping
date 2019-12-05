import xml.etree.ElementTree as et
import re
import config
import pymysql, pymysql.cursors
import pymongo
from database import *
import json
import numpy as np
import io
import bz2
from fasttext import FastText
import fasttext
from database import Page, Revision, get_things, get_entities_with_type, get_types_size, get_types
import subprocess
from keyword_extraction import extract_keywords
from config import WORD_VEC_SIZE, HIDDEN_LAYER_SIZE

redirects = {}
# pages = []
client = MongoClient()
database = client['MVET']
articles = database['title_id.articles']
title_ids = {}
titles = []
fastText = {}
embedding_size = 30
connection = pymysql.connect(host=config.DB_HOST, user=config.DB_USER,
                                 password=config.DB_PASS, db=config.DB_NAME,
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
#
# NAME = []
# CTXT = []
# DESC = []




class NameSpace:
    key = None
    case = None
    value = None


class SiteInfo:
    siteName = None
    dbName = None
    base = None
    generator = None


def extract_namespace(tag):
    nsReg = re.compile('\{.*\}')
    return nsReg.search(tag).group(0)

'''
def context_view():
    file = open(os.path.join(Path.files_path, 'output.txt'), 'w')
    for page in pages:
        page.revision.replace_id()
        file.write(page.revision.text)
        file.write('\n')
    file.close()
'''

def init_fastText(lan='en'):
    """
    Load pre-trained fastText word vectors into {fastText} with word as key and vector as value.
    :param lan:Will specify the language to load word embedding for.
    :return: number and dimension of word embedding vectors.
    """
    print('initializing fastText for {}'.format(lan))
    if lan == 'en':
        fname = os.path.join(Path.files_path,'wiki-news-300d-1M.vec')
    fin = io.open(fname, 'r', encoding='utf-8', newline='\n', errors='ignore')
    # n is
    n, embedding_size = map(int, fin.readline().split())
    fastText = {}
    for line in fin:
        tokens = line.rstrip().split(' ')
        # fastText[tokens[0]] = map(float, tokens[1:])
        insert_fasttext_vector(tokens[0] , ' '.join(tokens[1:]))
    return n


def get_NAME(title, dimension, lan='en'):
    """
    get NAME view of the article.

    Just get the title of article and return average of vectors of name

    :param title: Title of article to return embedding for.
    :param dimension: Dimension of embedding to return. In the case of fast text it'll be 30.
    P.S. we will use only fast text
    :param lan:
    :return:
    """

    if fastText == {}:
        _, dimension = init_fastText(lan)
    words = title.split(' ')
    size = len(words)
    vector = np.zeros(dimension)
    try:
        for title in words:
            if title[0] == '(' and title[-1] == ')':
                size -= 1
                continue
            vector += fastText[title]
    except KeyError:
        pass
        #TODO: Compute word embedding for word and add the vector to {vector}
    return vector / size




#

def parse_page_element(element: et.Element):
    '''
    Get a xml element of wikipedia dump and store it in mongo db
    :param element:
    :return:
    '''
    try:
        page = Page(element)
    except AttributeError as e:
        print(e)
    store_page_in_mongo(page)

def read_pages(language = 'en'):
    '''
    Read wikipedia pages from dumps, parse them and store data in database
    :param language:
    :return:
    '''
    print('Start parsing wikipedia articles')
    with bz2.BZ2File(os.path.join(Path.files_path,'enwiki-20190801-pages-articles-multistream.xml.bz2')) as wikifile:
        articles = et.iterparse(wikifile,events=['start'])
        for _, element in articles:
            if element.tag == '{{{}}}{}'.format(namespace,'page'):
                parse_page_element(element)
        # context_view()
    print('End parsing wikipedia articles')




def links_matches(link):
    """
    Get link and check if it is a valid link.

    Valid links are from 'DBpedia' or 'Freebase'.
    :param link: Link to check
    :return: True if link is valid. False otherwise.
    """
    link = link.replace('<','').replace('>','')
    dbpedia_reg = re.compile('http://([a-z]{2}.)?dbpedia.org/resource/.*')
    if dbpedia_reg.match(link):
        return True

    return False





def store_page_in_mongo(page: Page):
    from pymongo import MongoClient
    client = MongoClient()
    collection = client['wiki']
    collection.articles.insert_one(page.json())


def compute_NAME_view(language='en'):
    '''
    Compute NAME view for all articles and store them in  database
    :param language:
    :return:
    '''
    print('creating Name views')
    names = list()
    # TODO: get names list
    reg = re.compile('(\[\w\])|(\(\w\))')
    file = open(os.path.join(Path.files_path,'temp.txt'),'w')
    things = get_things()

    for thing in things:
        entityId = thing[1].split('/')[-1][1:]
        name = get_article_title(entityId)
        embedding = np.zeros(embedding_size)
        file.write(name)
        name = re.sub(reg,'',name)
        for word in name.split(' '):
            try:
                embedding += fastText[word]
            except KeyError:
                print('No embedding in fastText for word {}'.format(word))
                model = fasttext.train_unsupervised(os.path.join(Path.files_path,'temp.txt'), model='cbow')
                embedding += model[word]
        # NAME.append(embedding)
        insert_view(get_item_id(sqlConnection, name), 'NAME', language, embedding)
        file.truncate()


def get_CTXT(text):
    file = open(os.path.join(Path.files_path,'temp.txt'),'w')
    file.write(text)
    file.close()
    presult = subprocess.call([os.path.join(Path.root_path,'wang2vec','word2vec'),'-train',os.path.join(Path.files_path,'temp.txt'),
                    '-output',os.path.join(Path.files_path,'temp_output.txt'), '-type 0', '-size', str(config.WORD_VEC_SIZE),
                     '-window 5 -negative 10 -nce 0 -hs 0 -sample 1e-4 -threads 1 -binary 1 -iter 5 -cap 0'])
    if presult == 0:
        file = open(os.path.join(Path.files_path,'temp_output.txt'),'r')
        result = file.read()
        file.close()
        return result
    else:
        return None


def compute_CTXT_view(language='en'):
    """
    Compute CTXT view of each article and store in database
    :param language:
    :return:
    """
    print('creating Context views')
    things = get_things()
    for thing in things:
        # print(thing)
        entityId = thing[1].split('/')[-1][1:]
        text = get_articleText(entityId)
        if text is None:
            print('text is null')
            continue
        context = get_CTXT(text)
        if context is not None:
            # CTXT.append(context)
            # TODO: get article title from thing
            insert_view(int(get_item_id(sqlConnection, 'name')), 'CTXT', language, context)


def compute_DESC_view(language='en'):

    """
    Compute DESC view for all articles and store in database
    :param language:
    :return:
    """

    print('creating Description views')
    things = get_things()
    # file = open(os.path.join(Path.files_path,'temp.txt'),'w')
    for thing in things:
        description = np.zeros(config.WORD_VEC_SIZE)
        # print(thing)
        # file.write(thing)
        # TODO: extract keywords from first paragraph of text
        keywords = extract_keywords('text',language)
        for word in keywords:
            try:
                description += fasttext[word]
            except  KeyError:
                model = fasttext.train_unsupervised(os.path.join(Path.files_path, 'temp.txt'), model='cbow')
                description += model[word]
        # file.truncate()
        # DESC.append(description / description.size)
        insert_view(get_item_id(sqlConnection, thing), 'DESC', language, description / description.size)


def create_temp_dir(language = 'en'):
    """
    Create a temporary directory to keep temporary files.
    :param language:
    :return:
    """
    if not os.path.exists(os.path.join(Path.files_path,'temp',language)):
        print("Temporary direcotries created")
        os.makedirs(os.path.join(Path.files_path,'temp',language))


def train():
    entities = get_entities_with_type()
    for thing in entities:
        # TODO: give article title to get id
        p = np.zeros(config.WORD_VEC_SIZE)
        views = get_view(get_item_id(thing))
        for view in views:
            p += view
        p /= len(views)


def get_views(name):
    """
    Get an article name and return all views of it in all languages
    :param name:
    :return:list of article
    """

def main():
    for lan in config.languages:
        create_temp_dir(lan)
        if config.PARSE_WIKI_ARTICLES:
            read_pages(lan)
        init_database()
        if config.PARSE_FASTTEXT:
            init_fastText(lan)
        compute_CTXT_view(lan)
        compute_NAME_view(lan)
        compute_DESC_view(lan)


# main()
# from keras.models import Sequential
# from keras.layers import Dense, LeakyReLU
# output_size = get_types_size()
# model = Sequential()
# model.add(LeakyReLU(HIDDEN_LAYER_SIZE, input_shape=(WORD_VEC_SIZE, ),alpha=0.2  ))
# model.add(Dense(output_size, input_shape=(HIDDEN_LAYER_SIZE,)))
# train()

# from SPARQLWrapper import SPARQLWrapper, JSON
# wrapper = SPARQLWrapper('http://localhost:8890/sparql')
# wrapper.setQuery('select count(*) from <http://localhost:8890/dbpedia> where {?p ?d ?s} limit 20')
# wrapper.setReturnFormat(JSON)
# results = wrapper.query().convert()
# for result in results["results"]["bindings"]:
#     print (result["p"]['value'], result["d"]['value'])
# from rdflib import G/raph
# graph = Graph()
# graph.parse(os.path.join(config.Path.root_path, 'Data', 'dbpedia_2016-10.nt'),format='nt')
# qres = graph.query("select * from <http://localhost:8890/dbpedia> where {?p ?d ?s} limit 20")
# for p,d,s in qres:
#     print('{} {} {}'.format(p, d, s))