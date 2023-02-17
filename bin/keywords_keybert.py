#!/usr/bin/env python3
"""
KeyBert demo, from
https://www.analyticsvidhya.com/blog/2022/01/four-of-the-easiest-and-most-effective-methods-of-keyword-extraction-from-a-single-text-using-python/

requirements:
pip install keybert

"""

from bs4 import BeautifulSoup
from keybert import KeyBERT
import json
import sys
import time
import yake
from multi_rake import Rake
import summa


kw_model = KeyBERT(model='all-mpnet-base-v2')

## 12 seconds
def bert_keywords(full_text):
    keywords = kw_model.extract_keywords(full_text,
                                         keyphrase_ngram_range=(1, 3),
                                         stop_words='english',
                                         highlight=False,
                                         top_n=10)

    print(json.dumps(keywords))
    keywords_list= list(dict(keywords).keys())
    return keywords_list

## 0.1 seconds, but dirty results
def yake_keywords(full_text):
    kw_extractor = yake.KeywordExtractor(top=10, stopwords=None)
    keywords = kw_extractor.extract_keywords(full_text)
    for kw, v in keywords:
        print("Keyphrase: ",kw, ": score", v)
    return keywords

## rake crashes
def rake_keywords(full_text):
    rake = Rake()
    keywords = rake.apply(full_text)
    return keywords[:10]

# Just single words
def summa_keywords(full_text):
    TR_keywords = summa.keywords.keywords(full_text, scores=True)
    return (TR_keywords[0:10])


if __name__=="__main__":
    text = ' '.join(BeautifulSoup(open(sys.argv[1]).read(),features="lxml").body.stripped_strings)
    print(json.dumps(summa_keywords(text)))
    t1 = time.time()
    print(json.dumps(summa_keywords(text)))
    t2 = time.time()
    print("t:",t2-t1)
