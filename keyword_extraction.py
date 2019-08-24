from rake_nltk import  Rake



def extract_keywords(text: str, language='en' ):
    rake = Rake(language=language)
    rake.extract_keywords_from_text(text)
    return rake.get_ranked_phrases()