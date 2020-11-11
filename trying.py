import argparse

if __name__ == "__main__":
    print('main')
    parser = argparse.ArgumentParser()
    parser.add_argument('--parse_wiki', help='If true it will parse wikipedia pages.For permanent change, you could change '
                                            'you could set PARSE_WIKI_ARTICLES in config.py file.')
    parser.add_argument('--parse_fasttext', help='If true it will parse fast text.For permanent change, you could change '
                                            'you could set PARSE_FASTTEXT in config.py file.')

    parser.parse_args()