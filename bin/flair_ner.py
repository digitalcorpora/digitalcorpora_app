from flair.data import Sentence
from flair.models import SequenceTagger
from segtok.segmenter import split_single
tagger = SequenceTagger.load('ner')
def flair_ner(body):
    sentences = [sent for sent in split_single(body)]
    for txt in sentences:
        sentence = Sentence(txt)
        print("txt:",txt)
        print("sentence:",sentence)
        tagger.predict(sentence)
        for entity in sentence.get_spans('ner'):
            print(entity)
