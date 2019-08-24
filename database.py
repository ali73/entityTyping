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
client = MongoClient(connect=False)
namespace = 'http://www.mediawiki.org/xml/export-0.10/'
connection = pymysql.connect(host=config.DB_HOST, user=config.DB_USER,
                                 password=config.DB_PASS, db=config.DB_NAME,
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)


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
            id = get_item_id(connection, link.title)
            try:
                link.string = str(id['ips_item_id'])
            except TypeError as E:
                print(E)
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
        except AttributeError:
            print(AttributeError)
            self.text = None
        self.final_text = None
        if self.text == '' or self.text is None:
            return
        self.replace_id()

    def __init__(self, json: dict):
        try:
            self.parent_title = json['parent_title']
        except KeyError:
            pass
        try:
            self.parentid = json['parent_id']
        except KeyError:
            pass
        try:
            self.id = json['id']
        except KeyError:
            pass
        try:
            self.text = json['text']
        except KeyError:
            pass
        try:
            self.final_text = json['altered_text']
        except KeyError:
            pass

    def json(self):
        json = dict()
        json['parent_title'] = self.parent_title
        if self.parentid is not None:
            json['parent_id'] = self.parentid
        json['id'] = self.id
        json['text'] = self.text
        json['altered_text'] = self.final_text
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

    def __init__(self, json: dict):
        try:
            self.title = json['title']
        except KeyError:
            pass
        try:
            self.id = json['id']
        except KeyError:
            pass
        try:
            self.ns = json['ns']
        except KeyError:
            pass
        try:
            self.revision = Revision(json['revision'])
        except KeyError:
            pass

    def json(self):
        json = dict()
        json['title'] = self.title
        json['ns'] = self.ns
        json['id'] = self.id
        json['revision'] = str(self.revision.json())
        return json


def get_article(title):
    from pymongo import MongoClient
    client = MongoClient()
    collection = client['wiki']
    pages = collection.articles.find('{title:\''+title+'\'}')
    result = []
    for page in pages:
        result.append(Page(page))
    return result

def get_things():
    graph = Graph()
    graph.load(config.FARS_BASE)
    query = prepareQuery('select ?p ?d where '
                         '{?p rdf:instanceOf <http://fkg.iust.ac.ir/ontology/Thing>. '
                         '?p owl:sameAs ?d.'
                         'filter(strstarts(str(?d), "http://dbpedia.org/")).'
                         '}',initNs={'OWL':OWL,'rdf':RDF})
    return graph.query(query)
