import nltk
import spacy
import unidecode

SUFFIXES_TO_REMOVE=["’S","'s"]
MAXLEN = 63

nlp = spacy.load("en_core_web_sm")

def clean_results(names):
    # Now, if the two-word version is present, remove the one word versions
    multiword_names = set(" ".join([name for name in names if ' ' in name]).split())
    for name in multiword_names:
        if name in names:
            names.remove(name)

    return names

def spacy_ner(body, maxlen=MAXLEN):
    assert body is not None
    assert isinstance(maxlen, int)
    names = set()
    sentences = nltk.sent_tokenize(body)
    for sentence in sentences:
        doc = nlp(sentence)
        for entity in doc.ents:
            if entity.label_=="PERSON":
                name = unidecode.unidecode(entity.text.title()[0:maxlen]).title().strip()

                # ignore names that have newlines in them because that's just wrong
                if '\n' in name:
                    continue

                # remove non-alpha leading values
                while len(name)>0 and not name[0:1].isalpha():
                    name = name[1:]

                for suffix in SUFFIXES_TO_REMOVE:
                    if name.upper().endswith(suffix.upper()):
                        name = name[0:-len(suffix)]

                if len(name)>0:
                    names.add(name)

    return clean_results(names)
