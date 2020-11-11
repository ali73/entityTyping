from SPARQLWrapper import SPARQLWrapper, JSON
from pymongo import MongoClient
from config import Path
from pymysql.err import ProgrammingError
import os
import wikitextparser as wtp
import xml.etree.ElementTree as et
import pymysql
import config
from rdflib import RDF, Graph, URIRef
from rdflib.plugins.sparql import  prepareQuery
from rdflib.namespace import OWL, RDF
from json import dumps, loads
import  logging

mongoClient = MongoClient(connect=False)
namespace = 'http://www.mediawiki.org/xml/export-0.10/'
sqlConnection = pymysql.connect(host=config.DB_HOST, user=config.DB_USER,
                                password=config.DB_PASS,
                                charset='utf8mb4',
                                cursorclass=pymysql.cursors.DictCursor)


def init_database():
    # sqlConnection.cursor().execute('create database {}'.format(config.DB_NAME))
    sqlConnection.select_db(config.DB_NAME)
    init_views()
    init_fasttext_datbase()


def init_views():
    query = 'create table if not exists views (article_id int, view_name char(4), view text, language char(3), primary key (article_id, view_name, language));'
    try:
        sqlConnection.cursor().execute(query)
    except ProgrammingError as e:
        print("Error %d: %s" % (e.args[0], e.args[1]))
        raise e


def init_fasttext_datbase():
    # query = 'create table if not exists fasttext '
    query = 'create table if not exists fasttext ('\
            'word char(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin, ' \
            'vector text, ' \
            'primary key(word));'
    try:
        sqlConnection.cursor().execute(query)
    except ProgrammingError as e:
        print("Error %d: %s" % (e.args[0], e.args[1]))
        raise e

def get_item_id(connection, title):
    title = title.replace("'","''")
    query = "select * from wb_items_per_site where ips_site_page = '{}'".format(title)
    cursor = connection.cursor()
    cursor.execute(query)
    return cursor.fetchone()

def get_title_id_dict(title, id):
    d = dict()
    d['title'] = title
    d['id'] = id
    return d


class Revision:
    def replace_id(self):
        parsed = wtp.parse(self.text)
        # remove templates from text
        for template in parsed.templates:
            template.string = ''
        for section in parsed.sections:
            if section.title is not None:
                section = section.title + '\n' + section.contents
        for table in parsed.tables:
            table = ''
        for list in parsed.lists():
            list.string = ' '.join(list.items)
        for tag in parsed.tags():
            try:
                tag.string = tag.contents
            except AttributeError as e:
                pass
        for link in parsed.wikilinks:
            id = get_item_id(sqlConnection, link.title)
            try:
                link.string = str(id['ips_item_id'])
            except TypeError as e:
                # logging.warn(e)
                logging.info("No id found for link {0}".format(link.title))
                logging.warn(e)
                link.string = link.title
        self.final_text = parsed.string

    def __init__(self, element: et.Element, title: str):
        self.parent_title = title
        try:
            self.id = element.find('{{{}}}{}'.format(namespace, 'id')).text
        except AttributeError:
            self.id = None
            print(title)
        try:
            self.parentid = element.find('{{{}}}{}'.format(namespace, 'parentid')).text
        except AttributeError:
            self.parentid = None
        try:
            self.text = element.find('{{{}}}{}'.format(namespace, 'text')).text
        except AttributeError as e:
            logging.warn("Article {0} has no text".format(self.parent_title))
            # logging.exception(e)
            self.text = None
        self.final_text = None
        if self.text == '' or self.text is None:
            return
        self.replace_id()

    # def __init__(self, json: dict):
    #     try:
    #         self.parent_title = json['parent_title']
    #     except KeyError:
    #         pass
    #     try:
    #         self.parentid = json['parent_id']
    #     except KeyError:
    #         pass
    #     try:
    #         self.id = json['id']
    #     except KeyError:
    #         pass
    #     try:
    #         self.text = json['text']
    #     except KeyError:
    #         pass
    #     try:
    #         self.final_text = json['altered_text']
    #     except KeyError:
    #         pass

    def json(self):
        json = dict()
        json["parent_title"] = self.parent_title
        if self.parentid is not None:
            json["parent_id"] = self.parentid
        json["id"] = self.id
        json["text"] = self.text
        json["altered_text"] = self.final_text
        return json


class Page:
    def __init__(self, element: et.Element):
        try:
            self.title = element.find('{{{}}}{}'.format(namespace, 'title')).text
        except AttributeError as e:
            print(e)
            print(element)
            raise AttributeError
        self.ns = element.find('{{{}}}{}'.format(namespace, 'ns')).text
        self.id = element.find('{{{}}}{}'.format(namespace, 'id')).text
        self.revision = Revision(element.find('{{{}}}{}'.format(namespace, 'revision')), self.title)


    def json(self):
        json = dict()
        json['title'] = self.title
        json['ns'] = self.ns
        json['id'] = self.id
        json['revision'] = self.revision.json()
        return json


def get_article(title):
    collection = mongoClient['wiki']
    pages = collection.articles.find('{title:\''+title+'\'}')
    result = []
    for page in pages:
        result.append(Page(page))
    return result

def get_things():
    wrapper = SPARQLWrapper('http://localhost:8890/sparql')
    wrapper.setCredentials('dba', 'dba')
    wrapper.setReturnFormat(JSON)
    wrapper.setQuery('select ?p ?d '
                     'from <{0}>'
                     'where '
                         '{{?p rdf:instanceOf <http://fkg.iust.ac.ir/ontology/Thing>. '
                         '?p owl:sameAs ?d.'
                         'filter(strstarts(str(?d),"http://wikidata")||strstarts(str(?d),"http://www.wikidata"))'
                         '}}'.format(config.FARS_BASE))
    results = wrapper.query().convert()["results"]["bindings"]
    ret = []
    for result in results:
        ret.append((result['p']['value'],result['d']['value']))
    return ret

def get_types ():
    wrapper = SPARQLWrapper('http://localhost:8890/sparql')
    wrapper.setCredentials('dba', 'dba')
    wrapper.setQuery('select distinct ?t from <{0}>'
                     'wehre {{'
                     '?p rdf:instanceOf ?t'
                     'filter not exists{{'
                     '?p rdf:instanceOf <http://fkg.iust.ac.ir./ontology/Thing>'
                     '}}'
                     '}}'.format(config.FARS_BASE))
    wrapper.returnFormat(JSON)
    results = wrapper.query().convert()["results"]["bindings"]
    ret = []
    for result in results:
        ret.append(result['t']['value'])
    return ret
def get_types_size():
    wrapper = SPARQLWrapper('http://localhost:8890/sparql')
    wrapper.setCredentials('dba', 'dba')
    wrapper.setReturnFormat(JSON)
    wrapper.setQuery('select count(distinct ?t) from'
                     '<{0}>'
                     'wehre {{'
                     '?p rdf:instanceOf ?t'
                     '}}'.format(config.FARS_BASE))
    results = wrapper.query().convert()["results"]["bindings"]
    return results['results']['bindings'][0]['callret-0']['value']



def get_view(id, language, name):
    nameQ = " and view_name = '{}' ".format(name)
    languageQ = " and language= '{}' ".format(language)
    query = "select * from views where article_id = {} ".format(id)
    if name is not None:
        query += nameQ
    if language is not None:
        query += languageQ
    cursor = sqlConnection.cursor()
    return cursor.fetchall()

def insert_view(id, name, language, view):
    query = "insert into views (article_id, view_name, language, view) values(%d, %s, %s, %s)"
    sqlConnection.cursor().execute(query, (id, name, language, view))
    sqlConnection.commit()


def get_entities_with_type():
    wrapper = SPARQLWrapper('http://localhost:8890/farsbase')
    wrapper.setCredentials('dba', 'dba')
    wrapper.setReturnFormat(JSON)
    wrapper.setQuery('select ?p '
                     'from <{}>'
                     'wehre {{'
                     '?p rdf:instanceOf ?t'
                     'filter not exists {{?p rdf:instanceOf <http://fkg.iust.ac.ir/ontology/Thing>}}'
                     '}}'.format(config.FARS_BASE))
    results = wrapper.query().convert()["results"]["bindings"]
    ret = []
    for result in results:
        ret.append(result['p']['value'])
    return  ret

def getArticleID(pageID:int):
    query = 'select pp_value from page_props where pp_page = {}'.format(pageID)
    result = sqlConnection.cursor().execute(query)
    return result
def insert_fasttext_vector(word, vector):
    query = 'insert into fasttext (word, vector) values (\'{0}\', \'{1}\');'
    try:
        word = word.replace("'", "''")
        word = word.replace("\\", "\\\\")
        sqlConnection.commit()
        query = query.format(word, vector)
        sqlConnection.cursor().execute(query)
    except Exception as e:
        print('word', word)
        print(vector)
        raise e

def get_articleText(articleID:int):

    collection = mongoClient['wiki']
    article = collection.articles.find_one({'id':str(articleID)})
    if article is None:
        return None
    text = loads(article['revision'])
    return text['text']

def get_article_title(articleID:int):

    collection = mongoClient['wiki']
    article = collection.articles.find_one({'id':str(articleID)})
    if article is None:
        return None
    title = article['title']
    return title