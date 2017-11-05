from phase1 import STOP_WORD
from collections import defaultdict, deque


class PositionalIndex(object):
    def __init__(self, corpus):
        self._corpus = corpus
        self._index = defaultdict(lambda: defaultdict(set))

    def build_index(self):
        for file in self._corpus:
            self.add_file(file)

    def remove_file(self, file_name):
        for word in self._index:
            if file_name in self._index[word]:
                del self._index[word][file_name]

    def add_file(self, file_name):
        for idx, word in enumerate(self._corpus[file_name]):
            self._index[word][file_name].add(idx)

    def get_words(self):
        return self._index.keys()

    def query(self, token):
        return self._index[token]


class WildcardIndex(object):
    def __init__(self, corpus):
        self._corpus = corpus
        recursive_dict = lambda: defaultdict(recursive_dict)
        self._index = defaultdict(recursive_dict)

    def __feed(self, word, file_name):
        subtree = self._index
        for char in word:
            subtree = subtree['children'][char]
        subtree['exists'][file_name] = True

    def __find(self, till_now, subtree):
        result = []
        for char in subtree['children']:
            result += self.__find(till_now + char, subtree['children'][char])
        if len(subtree['exists']) > 0:
            result.append(till_now)
        return result

    def __rotations(self, word):
        result = []
        deck = deque(word)
        for i in range(len(word)):
            result.append(''.join(deck))
            deck.rotate()
        return result

    def __remove_file(self, file_name, subtree):
        if file_name in subtree['exists']:
            del subtree['exists'][file_name]
        for char in subtree['children']:
            self.__remove_file(file_name, subtree['children'][char])

    def build_index(self):
        for file in self._corpus:
            self.add_file(file)

    def add_file(self, file_name):
        for word in self._corpus[file_name]:
            for rotation in self.__rotations(word + '$'):
                self.__feed(rotation, file_name)

    def remove_file(self, file_name):
        self.__remove_file(file_name, self._index)

    def query(self, token):
        star_pos = token.index('*') if '*' in token else None
        if star_pos:
            to_shift = len(token) - 1 - star_pos
            token = token[star_pos + 1:] + '$' + token[:star_pos]
        else:
            to_shift = 0
            token = '$' + token
        subtree = self._index
        for char in token:
            if char in subtree['children']:
                subtree = subtree['children'][char]
            else:
                return None
        words = self.__find(token, subtree)
        return [word[to_shift + 1:] + word[:to_shift] for word in words]

