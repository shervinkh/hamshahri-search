
class Evaluator(object):
    def __init__(self, phrase_search):
        self._phrase_search = phrase_search
        self._queries = []
        self._answers = []

    def __get_query_file(self, i):
        return 'HamshahriData/Queris/%d.q' % i

    def __get_judgement_file(self):
        return 'HamshahriData/RelativeAssesemnt/judgements.txt'

    def read_files(self):
        for i in range(1, 51):
            self._queries.append(open(self.__get_query_file(i)).read())
            self._answers.append(set())
        for line in open(self.__get_judgement_file()):
            i, res = line.strip().split(' ')
            self._answers[int(i) - 1].add(res)

    def evaluate_map(self, idx, normalize):
        idx -= 1
        results = list(self._phrase_search.query(self._queries[idx], normalize))[:20]
        correct_results = self._answers[idx]
        correct = 0
        wrong = 0
        precisions = []
        for _, result in results:
            if result in correct_results:
                correct += 1
                precisions.append(correct / (correct + wrong))
            else:
                wrong += 1
        return sum(precisions) / len(precisions) if len(precisions) else 0

    def evaluate_map_all(self, normalize):
        maps = []
        for i in range(1, len(self._queries) + 1):
            maps.append(self.evaluate_map(i, normalize))
        return sum(maps) / len(maps)

    def evaluate_f(self, idx, normalize):
        idx -= 1
        results = set(list(self._phrase_search.query(self._queries[idx], normalize))[:20])
        correct_results = self._answers[idx]
        correct = 0
        wrong = 0
        for _, result in results:
            if result in correct_results:
                correct += 1
            else:
                wrong += 1
        return correct / (correct + wrong)

    def evaluate_f_all(self, normalize):
        fs = []
        for i in range(1, len(self._queries) + 1):
            fs.append(self.evaluate_f(i, normalize))
        return sum(fs) / len(fs)

