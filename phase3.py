from collections import Counter, defaultdict
from itertools import chain
from math import log10, sqrt, floor

class TF_IDF(object):
    def __init__(self, corpus_collector, positional_index, wildcard_index):
        self._corpus_collector = corpus_collector
        self._positional_index = positional_index
        self._wildcard_index = wildcard_index

    def __term_candidates(self, term):
        return self._wildcard_index.query(term) if '*' in term else [term]

    def __normalize_query(self, q):
        normalized_q = self._corpus_collector.normalize_query(q)
        processed_query = [self.__term_candidates(term) for term in normalized_q]
        return [term for term in processed_query if term]

    def __get_all_combinations(self, q):
        if len(q) == 0:
            return [[]]
        else:
            head = q[0]
            tail = q[1:]
            rest = self.__get_all_combinations(tail)
            return list(chain.from_iterable([list([head_c] + rest_c for rest_c in rest) for head_c in head]))

    def __tf_log(self, term_dict):
        new_dict = {}
        for term in term_dict:
            new_dict[term] = 1 + log10(term_dict[term]) if term_dict[term] > 0 else 0
        return new_dict

    def __multiply_idf(self, tf):
        new_dict = {}
        for term in tf:
            new_dict[term] = tf[term] * self._log_idf.get(term, 1)
        return new_dict

    def __normalize_vector(self, vector):
        vector_length = sqrt(sum([vector[x] * vector[x] for x in vector]))
        if vector_length == 0:
            return vector
        normal_vector = {}
        for term in vector:
            normal_vector[term] = vector[term] / vector_length
        return normal_vector

    def __compute_score(self, document, query_vector, normalize):
        document_vector = {}
        for term in query_vector:
            index = self._positional_index.query(term)
            document_vector[term] = len(index[document]) if document in index else 0
        document_vector = self.__tf_log(document_vector)
        if normalize:
            document_vector = self.__normalize_vector(document_vector)
        return sum([document_vector[term] * query_vector[term] for term in query_vector])

    def __process_single_query(self, query, normalize):
        query_vector = self.__multiply_idf(self.__tf_log(Counter(query)))
        if normalize:
            query_vector = self.__normalize_vector(query_vector)
        document_scores = [(self.__compute_score(document, query_vector, normalize), document)
                for document in self._corpus_collector.corpus
                if self._document_set is None or document in self._document_set]
        return document_scores

    def build_idf_index(self):
        self._log_idf = {}
        N = len(self._corpus_collector.corpus)
        for word in self._positional_index.get_words():
            self._log_idf[word] = log10(N / len(self._positional_index.query(word)))

    def query(self, q, normalize, document_set=None):
        self._document_set = document_set
        all_queries = self.__get_all_combinations(self.__normalize_query(q))
        results = defaultdict(int)
        i = 0
        last_percent = -1
        for query in all_queries:
            for rank, doc in self.__process_single_query(query, normalize):
                results[doc] = max(results[doc], rank)
            i += 1
            percent = floor(100 * i / len(all_queries))
            if percent != last_percent:
                print('%d%% complete!' % percent)
                last_percent = percent
        results = [(results[doc], doc) for doc in results]
        return reversed(sorted(results))


class PhraseSearch(object):
    def __init__(self, corpus_collector, positional_index, tf_idf):
        self._corpus_collector = corpus_collector
        self._positional_index = positional_index
        self._tf_idf = tf_idf
        self._phrase_queries = []
        self._whole_query = []

    def __normalize_query(self, q):
        return self._corpus_collector.normalize_query(q, remove_stop_words=False)

    def __parse_query(self, q):
        self._phrase_queries = []
        idx = 0
        while idx < len(q):
            start = q.find('"', idx)
            if start != -1:
                end = q.find('"', start + 1)
                if end != -1:
                    self._phrase_queries.append(self.__normalize_query(q[start + 1:end]))
                    idx = end + 1
                else:
                    break
            else:
                break
        self._whole_query = q.replace('"', '')

    def __apply_phrase_queries(self, phrase_query):
        result = set()
        first_docs = self._positional_index.query(phrase_query[0])
        for doc in first_docs:
            for doc_pos in first_docs[doc]:
                is_ok = True
                for i in range(1, len(phrase_query)):
                    word = phrase_query[i]
                    word_index = self._positional_index.query(word)
                    if doc not in word_index:
                        is_ok = False
                        break
                    if doc_pos + i not in word_index[doc]:
                        is_ok = False
                        break
                if is_ok:
                    result.add(doc)
                    break
        self._document_set &= result

    def query(self, q, normalize):
        self.__parse_query(q)
        self._document_set = set(self._corpus_collector.corpus.keys())
        for phrase_query in self._phrase_queries:
            self.__apply_phrase_queries(phrase_query)
        return self._tf_idf.query(self._whole_query, normalize,
                document_set=self._document_set)

