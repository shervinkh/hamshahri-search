from collections import defaultdict
import json
import time

import phase1
import phase2
import phase3
import phase4


class Parser(object):
    def __init__(self, repl):
        self.repl = repl

    def parse_command(self, command):
        parser = getattr(self, 'parse_%s' % command, self.generic_parse)
        return parser()

    def generic_parse(self):
        print('Command not found!')

    def get_help(self):
        return []


class MainParser(Parser):
    def get_help(self):
        return [
            ('corpus','Go to corpus page (Phase 1 of the project)'),
            ('index', 'Go to index page (Phase 2 of the project)'),
            ('search', 'Go to search page (Phase 3 of the project)'),
            ('eval', 'Go to eval page (Phase 4 of the project)'),
        ]

    def parse_corpus(self):
        return 'corpus'

    def parse_index(self):
        return 'index'

    def parse_search(self):
        return 'search'

    def parse_eval(self):
        return 'eval'


class CorpusParser(Parser):
    def get_help(self):
        return [
            ('normal', 'Normalize a custom text'),
            ('common', 'Show common words of the corpus'),
        ]

    def parse_normal(self):
        inp = input('Enter you text: ').strip()
        print(self.repl.corpus_collector.normalize_query(inp.strip()))

    def parse_common(self):
        inp = int(input('How many? ').strip())
        print('\n'.join([str(t) for t in self.repl.corpus_collector.words_counter.most_common(inp)]))


class IndexParser(Parser):
    def get_help(self):
        return [
            ('add', 'Add document to index'),
            ('del', 'Remove document from index'),
            ('save', 'Save index'),
            ('load', 'Load index'),
            ('post', 'View posting list of a word'),
            ('wild', 'View matching words for a wildcard (also middle wildcard)')
        ]

    def parse_add(self):
        inp = input('What document? ').strip()
        if inp in self.repl.corpus_collector.corpus:
            self.repl.positional_index.add_file(inp)
            self.repl.wildcard_index.add_file(inp)
            self.repl.tf_idf.build_idf_index()

    def parse_del(self):
        inp = input('What document? ').strip()
        if inp in self.repl.corpus_collector.corpus:
            self.repl.positional_index.remove_file(inp)
            self.repl.wildcard_index.remove_file(inp)
            self.repl.tf_idf.build_idf_index()

    def __save_positional(self):
        positional = {}
        for word in self.repl.positional_index._index:
            positional[word] = {}
            for doc in self.repl.positional_index._index[word]:
                positional[word][doc] = list(self.repl.positional_index._index[word][doc])
        return positional

    def __load_positional(self, positional):
        index = defaultdict(lambda: defaultdict(set))
        for word in positional:
            for doc in positional[word]:
                index[word][doc] = set(positional[word][doc])
        return index

    def __save_wildcard(self, index):
        if isinstance(index, bool):
            return index
        wildcard = {}
        for key in index:
            wildcard[key] = self.__save_wildcard(index[key])
        return wildcard

    def __load_wildcard(self, wildcard):
        if isinstance(wildcard, bool):
            return wildcard
        recursive_dict = lambda: defaultdict(recursive_dict)
        index = defaultdict(recursive_dict)
        for key in wildcard:
            index[key] = self.__load_wildcard(wildcard[key])
        return index

    def parse_save(self):
        inp = input('What file? ').strip()
        index = {
            'positional': self.__save_positional(),
            'wildcard': self.__save_wildcard(self.repl.wildcard_index._index),
        }
        open(inp, 'w').write(json.dumps(index))

    def parse_load(self):
        inp = input('What file? ').strip()
        index = json.loads(open(inp, 'r').read())
        self.repl.positional_index._index = self.__load_positional(index['positional'])
        self.repl.wildcard_index._index = self.__load_wildcard(index['wildcard'])

    def parse_post(self):
        inp = self.repl.corpus_collector.normalize_query(input('Word: ').strip())[0]
        print(dict(self.repl.positional_index.query(inp)))

    def parse_wild(self):
        inp = self.repl.corpus_collector.normalize_query(input('Word: ').strip())[0]
        print('\n'.join(self.repl.wildcard_index.query(inp)))


class SearchParser(Parser):
    def get_help(self):
        return [
            ('order', 'Do a ordered search'),
            ('phrase', 'Do a phrasal search'),
            ('show', 'Show a document'),
        ]

    def __get_normalization(self):
        return bool(input('Enter 0 for lnn-ltn and 1 for lnc-ltc: ').strip())

    def __get_query(self):
        return input('Enter your search phrase: ').strip()

    def parse_order(self):
        normalize = self.__get_normalization()
        print('\n'.join([str(r) for r in list(self.repl.tf_idf.query(self.__get_query(), normalize))[:20]]))

    def parse_phrase(self):
        normalize = self.__get_normalization()
        print('\n'.join([str(r) for r in list(self.repl.phrase_search.query(self.__get_query(), normalize))[:20]]))

    def parse_show(self):
        document = input('What document? ').strip()
        if document in self.repl.corpus_collector.corpus:
            print(' '.join([term for term in self.repl.corpus_collector.corpus[document] if term != phase1.STOP_WORD]))


class EvalParser(Parser):
    def get_help(self):
        return [
            ('map', 'Evaluate MAP'),
            ('f', 'Evaluate F-Measure'),
        ]

    def __get_normalization(self):
        return bool(input('Enter 0 for lnn-ltn and 1 for lnc-ltc: ').strip())

    def parse_map(self):
        normalize = self.__get_normalization()
        doc = input('What document (or all)? ').strip().lower()
        if doc == 'all':
            print('%.3f%%' % (self.repl.evaluator.evaluate_map_all(normalize) * 100))
        elif int(doc) >= 1 and int(doc) <= 50:
            print('%.3f%%' % (self.repl.evaluator.evaluate_map(int(doc), normalize) * 100))

    def parse_f(self):
        normalize = self.__get_normalization()
        doc = input('What document (or all)? ').strip().lower()
        if doc == 'all':
            print('%.3f%%' % (self.repl.evaluator.evaluate_f_all(normalize) * 100))
        elif int(doc) >= 1 and int(doc) <= 50:
            print('%.3f%%' % (self.repl.evaluator.evaluate_f(int(doc), normalize) * 100))

class REPL(object):
    def __init__(self):
        self._page = 'main'

    def __show_progress(self, message, func):
        print('%s...' % message, end=' ', flush=True)
        start_time = time.time()
        func()
        end_time = time.time()
        print('[%.2fs]' % (end_time - start_time))

    def __initialize(self):
        print('Welcome to My Hamshahri Search Engine!')
        print('Please wait while initializing corpus and indexes...')
        self.corpus_collector = phase1.CorpusCollector()
        self.__show_progress('Reading corpus', lambda: self.corpus_collector.read_corpus())
        self.positional_index = phase2.PositionalIndex(corpus=self.corpus_collector.corpus)
        self.__show_progress('Building positional inverted index', lambda: self.positional_index.build_index())
        self.wildcard_index = phase2.WildcardIndex(corpus=self.corpus_collector.corpus)
        self.__show_progress('Building wildcard index', lambda: self.wildcard_index.build_index())
        self.tf_idf = phase3.TF_IDF(self.corpus_collector, self.positional_index, self.wildcard_index)
        self.__show_progress('Building IDF index', lambda: self.tf_idf.build_idf_index())
        self.phrase_search = phase3.PhraseSearch(self.corpus_collector, self.positional_index, self.tf_idf)
        self.evaluator = phase4.Evaluator(self.phrase_search)
        self.__show_progress('Reading judgement files', lambda: self.evaluator.read_files())
        print('Done initializing.')

    def __initialize_parsers(self):
        self._parsers = {
            'main': MainParser(self),
            'corpus': CorpusParser(self),
            'index': IndexParser(self),
            'search': SearchParser(self),
            'eval': EvalParser(self),
        }

    def __print_help(self, commands):
        print('Here\'s the list of commands you can use:')
        if self._page != 'main':
            commands = commands + [('back', 'Back to main menu')]
        commands = commands + [('help', 'Show commands'), ('exit', 'Exit')]
        for command, description in commands:
            print('%s\t%s' % (command, description))

    def __print_current_help(self):
        self.__print_help(self._parsers[self._page].get_help())

    def __loop(self):
        self.__print_current_help()
        while True:
            parser = self._parsers[self._page]
            inp = input('%s> ' % self._page).strip().lower()
            if inp == 'exit':
                break
            elif inp == 'help':
                self.__print_help(parser.get_help())
            elif inp == 'back':
                self._page = 'main'
                self.__print_current_help()
            else:
                try:
                    start_time = time.time()
                    next_page = parser.parse_command(inp)
                    end_time = time.time()
                    if next_page:
                        self._page = next_page
                        self.__print_current_help()
                    else:
                        print('[Command took %.2fs]' % (end_time - start_time))
                except Exception as e:
                    print('[Exception: %s]' % e)

    def run(self):
        self.__initialize()
        self.__initialize_parsers()
        self.__loop()

if __name__ == '__main__':
    repl = REPL()
    repl.run()

