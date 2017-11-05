from collections import Counter
from glob import glob
from hazm import *
import os

STOP_WORD_COUNT = 49
STOP_WORD = '@#^%'
normalizer = Normalizer()
stemmer = Stemmer()

class CorpusCollector(object):
    def __init__(self):
        self.words_counter = Counter()
        self.corpus = {}

    def __get_corpus_files(self):
        return glob('HamshahriData/HamshahriCorpus/*/*')

    def __normalize_content_phase1(self, content):
        return word_tokenize(normalizer.normalize(content))

    def __calculate_stop_words(self):
        self.stop_words = set([word for (word, _) in self.words_counter.most_common(STOP_WORD_COUNT)])

    def __normalize_content_phase2(self, content):
        func = lambda word: STOP_WORD if word in self.stop_words else stemmer.stem(word)
        return [func(word) for word in content]

    def read_corpus(self):
        files = self.__get_corpus_files()
        for file in files:
            file_name = file.split(os.path.sep)[-1].split('.')[0]
            file_content = open(file).read()
            self.corpus[file_name] = self.__normalize_content_phase1(file_content)
            self.words_counter.update(self.corpus[file_name])
        self.__calculate_stop_words()
        for file in self.corpus:
            self.corpus[file] = self.__normalize_content_phase2(self.corpus[file])

    def normalize_query(self, query, remove_stop_words=True):
        normalized = self.__normalize_content_phase2(self.__normalize_content_phase1(query))
        if remove_stop_words:
            return [term for term in normalized if term != STOP_WORD]
        else:
            return normalized

