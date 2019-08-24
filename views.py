import xml.etree.ElementTree as ET
import os
import csv
import  numpy as np
from wikipedia_page_reader import read_pages, main

files_path = os.path.abspath('Data/')

# dev_file = open(os.path.join(files_path,'dev.tsv'))
# dev_set = np.array(list(csv.reader(dev_file, delimiter = '\t')))
# # the array structure will be like:
# # (freebase_mid, frequency, english_wiki_title, titles in other languages, figer types, freebase types)
# for c in dev_set[0]:
#     print(c)


# read_pages()
main()
