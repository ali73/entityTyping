from database import Subject, insert_farsbase_row, insert_namespace, insert_link, insert_dbpedia_item
import re
import pymysql
import config
import codecs
import os
from config import Path


connection = pymysql.connect(host=config.DB_HOST, user=config.DB_USER,
                             password=config.DB_PASS, db=config.DB_NAME,
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)


class BadGrammarException(Exception):
    pass


type_predicates = ['a', 'fkgo:type','rdf:instanceOf']


def parse(fileAddress):
    """
    Parse given farsbase dump files and save entities which are part of fkgr: into farsbase table.

    Each row in farsbase table consists of  entity name and corresponding type with some complementary data.
    :param fileAddress:
    :return:
    """
    # print('Starting file {} parse.'.format(fileAddress))
    file = codecs.open(fileAddress, 'r', encoding='utf8')
    subject = None
    state = 0
    temp = ''
    last_state = 0
    category_regex = re.compile('http://fkg.iust.ac.ir/category/.*|fkgc:.*')
    for line in file.readlines():
        if line.startswith('@prefix'):
            parts = line.split(' ')
            insert_namespace(connection, parts[1], parts[2])
        else:
            line = line.replace('\n', '')
            if line is None or line == '':
                continue
            parts = line.split(' ')
            while '' in parts:
                parts.remove('')
            for part in parts:
                part = part.replace('\t', '')
                if state == 0:
                    # Read subject
                    if part[0] != '"':
                        subject = Subject(part)
                        state = 1
                    else:
                        temp = ''
                        temp += part
                        state = 4
                elif state == 1:
                    # Read predicate
                    if part[0] != '"':
                        subject.type_predicate = part
                        state = 2
                    else:
                        temp = ''
                        temp += part
                        state = 5
                elif state == 2:
                    quotation = re.compile('(?<!\\\\)\"+')
                    # endquot = re.compile()
                        # Read object
                    # if part[0] != '"' or (part.count('"') == 2 and '\\"' not in part):
                    # if quotation.search(part) is not None and dquot.search(part) is None:
                    if part[0] == '"' and len(quotation.findall(part)) == 1:
                        temp = ''
                        temp += part
                        state = 6
                    else:
                        subject.name = subject.name.replace('<', '').replace('>', '')
                        # if subject.type_predicate == 'owl:sameAs' and not category_regex.match(subject.name):
                        if subject.type_predicate == 'owl:sameAs':
                            insert_link(connection, subject.name, part, ignore=True)
                        # elif subject.type_predicate in type_predicates and not category_regex.match(subject.name):
                        elif subject.type_predicate in type_predicates:
                            subject.type = part
                            subject.file_name = fileAddress.split('/')[-1]
                            insert_farsbase_row(connection, subject, ignore=True)
                        state = 3
                elif state == 3:
                    if part == ',':
                        state = 2
                    elif part == ';':
                        state = 1
                    elif part == '.':
                        state = 0
                    else:
                        print(part)
                        print(line)
                        print(subject.name)
                        print(fileAddress.split('/')[-1])
                        raise BadGrammarException
                elif part == 4:
                    temp += ' ' + part
                    if '"' in part:
                        subject = Subject(temp)
                        state = 1
                elif state == 5:
                    temp += ' ' + part
                    if '"' in part:
                        subject.type_predicate = temp
                        state = 2

                elif state == 6:
                    temp += ' ' + part
                    sentenceEnd = re.compile('["]+@[a-z]{2}$')
                    if '"' in part and part.count('"') % 2 == 0 and '\\"' not in part or sentenceEnd.search(
                            part) is not None:
                        if subject.type_predicate == 'owl:sameAs':
                            insert_link(connection, subject.name, temp, ignore=True)
                        elif subject.type_predicate in type_predicates:
                            subject.type = temp
                            subject.file_name = fileAddress.split('/')[-1]
                            insert_farsbase_row(connection, subject, ignore=True)
                        state = 3


def pars_db_pedia():
    type_predicates = set()
    file = open(os.path.join(Path.files_path,'instance_types_en.ttl'),'r')
    for line in file.readlines()[1:]:
        parts = line.split(' ')
        type_predicates.add(parts[1])
        name = parts[0].replace('<','').replace('>','')[28:]
        insert_dbpedia_item(connection, name, parts[2].replace('\n','').replace('<','').replace('>',''))
