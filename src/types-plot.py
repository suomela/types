# coding=utf-8

from collections import defaultdict, Counter, namedtuple
import math
import optparse
import cPickle
import os
import os.path
import re
import sqlite3
import string
import sys
import numpy as np
import TypesDatabase
import TypesParallel
import TypesPlot
from lxml.builder import E

TOOL = 'types-plot'

PLOT_DIR = 'plot'
HTML_DIR = 'html'
BIN_DIR = 'bin'
DATA_FILE = 'types-plot.pickle'

DEFAULT_GROUP = "default"

N_COMMON = 3

FDR = [0.001, 0.01, 0.1]

def msg(msg):
    sys.stderr.write("%s: %s\n" % (TOOL, msg))

def none_to_empty(x):
    return '' if x is None else x

def classes(l):
    if len(l) == 0:
        return {}
    else:
        return { "class": " ".join(l) }

def firstlast(i, rowlist):
    l = []
    if i == 0:
        l.append('first')
    if i == len(rowlist) - 1:
        l.append('last')
    return classes(l)

def get_args():
    parser = optparse.OptionParser(
        description='Update all plots.',
        version=TypesDatabase.version_string(TOOL),
    )
    parser.add_option('--db', metavar='FILE', dest='db',
                      help='which database to read [default: %default]',
                      default=TypesDatabase.DEFAULT_FILENAME)
    TypesParallel.add_options(parser)
    parser.add_option('--type-lists', dest='with_typelists', action='store_true',
                      help='produce type lists',
                      default=False)
    parser.add_option('--sample-lists', dest='with_samplelists', action='store_true',
                      help='produce sample lists',
                      default=False)
    parser.add_option('--slides', dest='slide_version', action='store_true',
                      help='presentation slide version',
                      default=False)
    parser.add_option('--plotdir', metavar='DIRECTORY', dest='plotdir',
                      help='where to store PDF plots [default: %default]',
                      default=PLOT_DIR)
    parser.add_option('--htmldir', metavar='DIRECTORY', dest='htmldir',
                      help='where to store SVG plots and HTML files [default: %default]',
                      default=HTML_DIR)
    (options, args) = parser.parse_args()
    return options

# seq() is a generator that produces
# a, b, ..., z, aa, ab, ..., zz, aaa, aab, ...

C = string.ascii_lowercase

def seqd(depth, prefix):
    if depth <= 0:
        yield prefix
    else:
        for c in C:
            for s in seqd(depth - 1, prefix + c):
                yield s

def seq():
    depth = 1
    while True:
        for s in seqd(depth, ''):
            yield s
        depth += 1


# Convert arbitrary strings to safe, unique filenames

OKCHAR = re.compile(r'[a-zA-Z0-9]+')

class Filenames:
    def __init__(self):
        self.map = dict()
        self.used = set()

    def generate(self, s):
        if s in self.map:
            return

        suffixes = seq()
        prefix = []
        for ok in OKCHAR.finditer(s):
            prefix.append(ok.group().lower())
        if len(prefix) == 0:
            suffix = [ suffixes.next() ]
        else:
            suffix = []
        while True:
            candidate = '-'.join(prefix + suffix)
            assert len(candidate) > 0
            if candidate not in self.used:
                break
            suffix = [ suffixes.next() ]

        self.used.add(candidate)
        self.map[s] = candidate


class SampleData:
    pass


Context = namedtuple('Context', [
    'corpuscode', 'samplecode', 'datasetcode', 'tokencode',
    'before', 'word', 'after', 'link'
])


class AllCurves:
    def __init__(self):
        self.curves = []
        self.statcode_stat = dict()
        self.statcode_label = dict()
        self.by_corpus = defaultdict(list)
        self.by_dataset = defaultdict(list)
        self.by_stat = defaultdict(list)
        self.by_corpus_dataset = defaultdict(list)
        self.by_corpus_stat = defaultdict(list)
        self.by_dataset_stat = defaultdict(list)
        self.by_dataset_stat_fallback = dict()
        self.by_corpus_dataset_stat = dict()
        self.result_q = []

    def read_curves(self, args, conn):
        sys.stderr.write('%s: read:' % TOOL)

        if args.slide_version:
            layout = TypesPlot.layout_slides
        else:
            layout = TypesPlot.layout_normal

        listings = [None]
        if args.with_typelists:
            listings += ['t']
        if args.with_samplelists:
            listings += ['s']
        self.with_lists = len(listings) > 1

        dirdict = {
            "pdf": args.plotdir,
            "svg": args.htmldir,
            "html": args.htmldir,
            "tmp.svg": args.htmldir,
        }

        self.file_corpus = Filenames()
        self.file_stat = Filenames()
        self.file_dataset = Filenames()
        self.file_group = Filenames()
        self.file_collection = Filenames()

        ### log

        timestamp_by_logid = dict()

        def get_timestamp(logid):
            if logid not in timestamp_by_logid:
                ts = [ r[0] for r in conn.execute("SELECT STRFTIME('%s', timestamp) FROM log WHERE id = ?", (logid,)) ]
                assert len(ts) == 1
                timestamp_by_logid[logid] = int(ts[0])
            return timestamp_by_logid[logid]

        ### stat

        sys.stderr.write(' stat')
        r = conn.execute('''
            SELECT statcode, x, y, xlabel.labeltext, ylabel.labeltext
            FROM stat
            JOIN label AS ylabel ON stat.y = ylabel.labelcode
            JOIN label AS xlabel ON stat.x = xlabel.labelcode
            ORDER BY statcode
        ''')
        for statcode, x, y, xlabel, ylabel in r:
            self.file_stat.generate(statcode)
            self.statcode_stat[statcode] = (x, y)
            self.statcode_label[statcode] = (xlabel, ylabel)

        ### corpus

        corpus_descr = dict()
        sys.stderr.write(' corpus')
        r = conn.execute('''
            SELECT corpuscode, description
            FROM corpus
            ORDER BY corpuscode
        ''')
        for corpuscode, description in r:
            self.file_corpus.generate(corpuscode)
            corpus_descr[corpuscode] = description

        ### dataset

        dataset_descr = dict()
        sys.stderr.write(' dataset')
        r = conn.execute('''
            SELECT corpuscode, datasetcode, description
            FROM dataset
            ORDER BY corpuscode, datasetcode
        ''')
        for corpuscode, datasetcode, description in r:
            self.file_dataset.generate(datasetcode)
            dataset_descr[(corpuscode, datasetcode)] = description

        ### sample

        corpus_size = dict()
        sys.stderr.write(' sample')
        r = conn.execute('''
            SELECT corpuscode, COUNT(*), SUM(wordcount)
            FROM sample
            GROUP BY corpuscode
        ''')
        for corpuscode, samplecount, wordcount in r:
            corpus_size[corpuscode] = (samplecount, wordcount)

        ### token

        dataset_size = dict()
        sys.stderr.write(' token')
        r = conn.execute('''
            SELECT corpuscode, datasetcode, COUNT(DISTINCT tokencode), SUM(tokencount)
            FROM token
            GROUP BY corpuscode, datasetcode
        ''')
        for corpuscode, datasetcode, typecount, tokencount in r:
            dataset_size[(corpuscode, datasetcode)] = (typecount, tokencount)

        ### result_curve

        sys.stderr.write(' result_curve')
        r = conn.execute('''
            SELECT corpuscode, statcode, datasetcode, id, level, side, logid
            FROM result_curve
            ORDER BY corpuscode, statcode, datasetcode
        ''')
        for corpuscode, statcode, datasetcode, curveid, level, side, logid in r:
            k = (corpuscode, datasetcode, statcode)

            totals = {
                'type':  dataset_size[(corpuscode,datasetcode)][0],
                'hapax': None,
                'token': dataset_size[(corpuscode,datasetcode)][1],
                'word':  corpus_size[corpuscode][1],
            }

            if k not in self.by_corpus_dataset_stat:
                xkey, ykey = self.statcode_stat[statcode]
                xlabel, ylabel = self.statcode_label[statcode]
                xtotal, ytotal = totals[xkey], totals[ykey]
                c = TypesPlot.Curve(
                        layout,
                        dirdict,
                        corpuscode, self.file_corpus.map[corpuscode],
                        corpus_descr[corpuscode],
                        statcode, self.file_stat.map[statcode],
                        xlabel, ylabel,
                        xtotal, ytotal,
                        datasetcode, self.file_dataset.map[datasetcode],
                        dataset_descr[(corpuscode, datasetcode)],
                        listings
                )
                c.levels = defaultdict(dict)
                self.curves.append(c)
                self.by_corpus[corpuscode].append(c)
                self.by_dataset[datasetcode].append(c)
                self.by_stat[statcode].append(c)
                self.by_corpus_stat[(corpuscode, statcode)].append(c)
                self.by_corpus_dataset[(corpuscode, datasetcode)].append(c)
                self.by_dataset_stat[(datasetcode, statcode)].append(c)
                self.by_corpus_dataset_stat[k] = c
            else:
                c = self.by_corpus_dataset_stat[k]
            c.add_timestamp(get_timestamp(logid))
            c.levels[level][side] = curveid

        ### result_curve_point

        sys.stderr.write(' result_curve_point')

        def get_one_path(curveid):
            return np.array(list(conn.execute('''
                SELECT x, y
                FROM result_curve_point
                WHERE curveid = ?
                ORDER BY x
            ''', (curveid,))), dtype=np.int32)

        for c in self.curves:
            for level in sorted(c.levels.keys()):
                d = c.levels[level]
                if 'upper' in d and 'lower' in d:
                    upper = get_one_path(d['upper'])
                    lower = get_one_path(d['lower'])
                    c.add_poly(level, upper, lower)

        ### collection

        sys.stderr.write(' collection')
        r = conn.execute('''
            SELECT corpuscode, groupcode, collectioncode, description
            FROM collection
            ORDER BY corpuscode, groupcode, collectioncode
        ''')
        for corpuscode, groupcode, collectioncode, description in r:
            if groupcode is None:
                groupcode = DEFAULT_GROUP
            self.file_group.generate(groupcode)
            self.file_collection.generate(collectioncode)
            if corpuscode in self.by_corpus:
                for c in self.by_corpus[corpuscode]:
                    c.add_collection(
                        groupcode, self.file_group.map[groupcode],
                        collectioncode, self.file_collection.map[collectioncode],
                        description
                    )

        ### result_p

        sys.stderr.write(' result_p')
        r = conn.execute('''
            SELECT corpuscode, collectioncode, datasetcode, statcode, y, x, above, below, total, logid
            FROM result_p
        ''')
        for corpuscode, collectioncode, datasetcode, statcode, y, x, above, below, total, logid in r:
            k1 = (corpuscode, datasetcode, statcode)
            p = TypesPlot.Point(collectioncode, y, x, above, below, total, -FDR[-1])
            self.by_corpus_dataset_stat[k1].add_point(p, get_timestamp(logid))

        ### result_q

        sys.stderr.write(' result_q')
        r = conn.execute('''
            SELECT corpuscode, collectioncode, datasetcode, statcode, side, p, q
            FROM result_q
            ORDER BY i
        ''')
        for row in r:
            self.result_q.append(row)

        if self.with_lists:

            self.typelist_cache = {}
            self.samplelist_cache = {}
            self.sample_cache = {}
            self.sampleset_by_collection = defaultdict(set)
            self.sampleset_by_corpus = defaultdict(set)
            self.collectionset_by_sample = defaultdict(set)
            self.collectionset_by_token = defaultdict(set)
            self.sampleset_by_token = defaultdict(set)
            self.tokenset_by_sample = defaultdict(set)
            self.sample_info = {}
            self.tokenset_by_dataset = defaultdict(set)
            self.token_short = {}
            self.tokencount_by_token = Counter()
            self.tokencount_by_sample = Counter()
            self.tokencount_by_sample_token = defaultdict(Counter)
            self.context_by_sample = defaultdict(list)
            self.context_by_token = defaultdict(list)

            self.file_sample = Filenames()
            self.file_token = Filenames()

            ### sample

            sys.stderr.write(' sample')
            try:
                r = conn.execute('''
                    SELECT corpuscode, samplecode, wordcount, description, link
                    FROM sample
                ''')
            except sqlite3.OperationalError:
                r = conn.execute('''
                        SELECT corpuscode, samplecode, wordcount, description, NULL
                        FROM sample
                    ''')
            for corpuscode, samplecode, wordcount, description, link in r:
                self.file_sample.generate(samplecode)
                self.sampleset_by_corpus[corpuscode].add(samplecode)
                self.sample_info[(corpuscode, samplecode)] = (wordcount, description, link)

            ### sample_collection

            sys.stderr.write(' sample_collection')
            r = conn.execute('''
                SELECT corpuscode, samplecode, collectioncode
                FROM sample_collection
            ''')
            for corpuscode, samplecode, collectioncode in r:
                self.sampleset_by_collection[(corpuscode, collectioncode)].add(samplecode)
                self.collectionset_by_sample[(corpuscode, samplecode)].add(collectioncode)

            ### token

            sys.stderr.write(' token')
            r = conn.execute('''
                SELECT corpuscode, samplecode, datasetcode, tokencode, tokencount
                FROM token
            ''')
            for corpuscode, samplecode, datasetcode, tokencode, tokencount in r:
                self.file_token.generate(tokencode)
                self.sampleset_by_token[(corpuscode, datasetcode, tokencode)].add(samplecode)
                self.tokenset_by_sample[(corpuscode, datasetcode, samplecode)].add(tokencode)
                self.tokenset_by_dataset[(corpuscode, datasetcode)].add(tokencode)
                self.token_short[(corpuscode, datasetcode, tokencode)] = tokencode
                self.tokencount_by_token[(corpuscode, datasetcode, tokencode)] += tokencount
                self.tokencount_by_sample[(corpuscode, datasetcode, samplecode)] += tokencount
                self.tokencount_by_sample_token[(corpuscode, datasetcode, samplecode)][tokencode] += tokencount
                collectioncodes = self.collectionset_by_sample[(corpuscode, samplecode)]
                for c in collectioncodes:
                    self.collectionset_by_token[(corpuscode, datasetcode, tokencode)].add(c)

            ### tokeninfo

            sys.stderr.write(' tokeninfo')
            r = list(conn.execute('''
                SELECT COUNT(*)
                FROM sqlite_master
                WHERE type='table' AND name='tokeninfo'
            '''))
            if r[0][0] > 0:
                r = conn.execute('''
                    SELECT corpuscode, datasetcode, tokencode, shortlabel, longlabel
                    FROM tokeninfo
                ''')
                for corpuscode, datasetcode, tokencode, shortlabel, longlabel in r:
                    self.token_short[(corpuscode, datasetcode, tokencode)] = shortlabel

            ### context

            sys.stderr.write(' context')
            r = list(conn.execute('''
                SELECT COUNT(*)
                FROM sqlite_master
                WHERE type='table' AND name='context'
            '''))
            if r[0][0] > 0:
                r = conn.execute('''
                    SELECT corpuscode, samplecode, datasetcode, tokencode,
                           before, word, after, link
                    FROM context
                ''')
                for row in r:
                    c = Context(*row)
                    self.context_by_token[(c.corpuscode, c.datasetcode, c.tokencode)].append(c)
                    self.context_by_sample[(c.corpuscode, c.datasetcode, c.samplecode)].append(c)

        sys.stderr.write('\n')

        ### fallbacks

        for datasetcode, statcode in self.by_dataset_stat.keys():
            l = []
            for corpuscode in sorted(self.by_corpus.keys()):
                if (corpuscode, datasetcode, statcode) in self.by_corpus_dataset_stat:
                    c = self.by_corpus_dataset_stat[(corpuscode, datasetcode, statcode)]
                elif (corpuscode, statcode) in self.by_corpus_stat:
                    c = self.by_corpus_stat[(corpuscode, statcode)][0]
                elif (corpuscode, datasetcode) in self.by_corpus_dataset:
                    c = self.by_corpus_dataset[(corpuscode, datasetcode)][0]
                else:
                    c = self.by_corpus[corpuscode][0]
                l.append(c)
            self.by_dataset_stat_fallback[(datasetcode, statcode)] = l

    def create_directories(self):
        directories = set()
        for c in self.curves:
            directories.update(c.get_directories())
        for d in directories:
            if not os.path.exists(d):
                os.makedirs(d)

    def generate_html(self):
        for c in self.curves:
            sys.stderr.write('.')
            c.generate_html(self)

    def generate_corpus_menu(self):
        tablerows = []
        cell = E.td("Corpora", colspan="2")
        tablerows.append(E.tr(cell, **classes(['head'])))
        corpuslist = sorted(self.by_corpus.keys())
        for i, corpuscode in enumerate(corpuslist):
            c = self.by_corpus[corpuscode][0]
            cells = [
                E.td(E.a(corpuscode, href=c.get_pointname_from_root('html', None))),
                E.td(none_to_empty(c.corpus_descr), **classes(['wrap', 'small'])),
            ]
            tablerows.append(E.tr(*cells, **firstlast(i, corpuslist)))
        return tablerows

    def generate_fdr_table(self):
        blocks = []
        current = None
        fdri = 0
        for row in self.result_q:
            corpuscode, collectioncode, datasetcode, statcode, side, p, q = row
            while fdri < len(FDR) and q > FDR[fdri]:
                fdri += 1
                current = None
            if fdri == len(FDR):
                break
            if current is None:
                current = []
                blocks.append((fdri, current))
            current.append(row)

        small = classes(['small'])
        tablerows = []
        for fdri, block in blocks:
            text = u"Findings — false discovery rate %s" % FDR[fdri]
            cell = E.td(text, colspan="6")
            l = ['head']
            if len(tablerows) > 0:
                l.append('sep')
            tablerows.append(E.tr(cell, **classes(l)))
            for i, row in enumerate(block):
                corpuscode, collectioncode, datasetcode, statcode, side, p, q = row
                c = self.by_corpus_dataset_stat[(corpuscode, datasetcode, statcode)]
                groupcode = c.group_by_collection[collectioncode]
                point = c.point_by_collection[collectioncode]
                point.fdr = FDR[fdri]
                desc = c.collection_descr[collectioncode]
                lh = u"−" if side == "below" else "+"
                x, y = self.statcode_label[statcode]
                attr = dict()
                if desc is not None:
                    attr["title"] = desc
                attr["href"] = c.get_pointname_from_root('html', groupcode, point)
                cells = [
                    E.td(E.a(collectioncode, **attr)),
                    E.td(lh),
                    E.td("%s/%s" % (y,x), **small),
                    E.td(datasetcode, **small),
                    E.td(corpuscode, **small),
                    E.td("%.5f" % p, **small),
                ]
                tablerows.append(E.tr(*cells, **firstlast(i, block)))
        return tablerows

    def generate_index(self, htmldir):
        sys.stderr.write('.')
        headblocks = []
        bodyblocks = []
        headblocks.append(E.title("Corpus menu"))
        headblocks.append(E.link(rel="stylesheet", href="types.css", type="text/css"))
        tablerows = self.generate_corpus_menu()
        bodyblocks.append(E.div(E.table(*tablerows), **classes(["mainmenu"])))
        tablerows = self.generate_fdr_table()
        if len(tablerows) > 0:
            bodyblocks.append(E.div(E.table(*tablerows), **classes(["findings"])))
        doc = E.html(E.head(*headblocks), E.body(*bodyblocks))
        with open(os.path.join(htmldir, "index.html"), 'w') as f:
            TypesPlot.write_html(f, doc)
        with open(os.path.join(htmldir, "types.css"), 'w') as f:
            f.write(CSS)

    def get_context_filename_sample(self, datasetcode, samplecode):
        b = TypesPlot.cleanlist([
            '',
            's',
            self.file_dataset.map[datasetcode],
            self.file_sample.map[samplecode],
        ])
        return '_'.join(b) + '.html'

    def get_context_filename_token(self, datasetcode, tokencode, collectioncode=None):
        b = TypesPlot.cleanlist([
            '',
            't',
            self.file_dataset.map[datasetcode],
            self.file_token.map[tokencode],
            None if collectioncode is None else self.file_collection.map[collectioncode],
        ])
        return '_'.join(b) + '.html'

    def sample_link(self, corpuscode, datasetcode, samplecode, tokencode=None):
        if (corpuscode, datasetcode, samplecode) not in self.context_by_sample:
            return samplecode
        else:
            link = self.get_context_filename_sample(datasetcode, samplecode)
            if tokencode is not None:
                link += "#t{}".format(self.file_token.map[tokencode])
            return E.a(samplecode, href=link)

    def token_link(self, corpuscode, datasetcode, tokencode, samplecode=None, collectioncode=None, shorten=True):
        token = self.token_short[(corpuscode, datasetcode, tokencode)] if shorten else tokencode
        flags = {}
        if token != tokencode:
            flags["title"] = tokencode
        if (corpuscode, datasetcode, tokencode) not in self.context_by_token:
            return E.span(token, **flags)
        else:
            link=self.get_context_filename_token(datasetcode, tokencode, collectioncode)
            if samplecode is not None:
                link += "#s{}".format(self.file_sample.map[samplecode])
            return E.a(token, href=link, **flags)

    def generate_context(self, htmldir):
        for key in sorted(self.context_by_sample.keys()):
            sys.stderr.write('.')
            corpuscode, datasetcode, samplecode = key
            title = samplecode
            wordcount, descr, link = self.sample_info[(corpuscode, samplecode)]
            if descr is None:
                if link is None:
                    headtext = [E.p(samplecode)]
                else:
                    headtext = [E.p(E.a(samplecode, href=link))]
            else:
                if link is None:
                    headtext = [E.p(samplecode, ": ", descr)]
                else:
                    headtext = [E.p(samplecode, ": ", E.a(descr, href=link))]
            filename = self.get_context_filename_sample(datasetcode, samplecode)
            filename = os.path.join(htmldir, self.file_corpus.map[corpuscode], filename)
            l = self.context_by_sample[(corpuscode, datasetcode, samplecode)]
            self.generate_context_one(l, filename, title, headtext, "sample")
        for key in sorted(self.context_by_token.keys()):
            sys.stderr.write('.')
            corpuscode, datasetcode, tokencode = key
            collectioncodes = sorted(self.collectionset_by_token[key])
            l_all = self.context_by_token[(corpuscode, datasetcode, tokencode)]
            for collectioncode in [None] + collectioncodes:
                if collectioncode is not None:
                    title = u'{} · {}'.format(tokencode, samplecode)
                    headtext = [E.p(
                        self.token_link(corpuscode, datasetcode, tokencode, shorten=False),
                        u' — ',
                        collectioncode
                    )]
                    sampleset = self.sampleset_by_collection[(corpuscode, collectioncode)]
                    l = [c for c in l_all if c.samplecode in sampleset]
                else:
                    title = tokencode
                    if len(collectioncodes) > 0:
                        links = [
                            E.a(c, href=self.get_context_filename_token(datasetcode, tokencode, c))
                            for c in collectioncodes
                        ]
                        headtext = [E.p(
                            tokencode,
                            u' — ',
                            *TypesPlot.add_sep(links, u' · ')
                        )]
                    else:
                        headtext = [E.p(tokencode)]
                    l = l_all
                filename = self.get_context_filename_token(datasetcode, tokencode, collectioncode)
                filename = os.path.join(htmldir, self.file_corpus.map[corpuscode], filename)
                self.generate_context_one(l, filename, title, headtext, "token")

    def generate_context_one(self, l, filename, title, headtext, what):
        headblocks = []
        bodyblocks = []
        headblocks.append(E.title(title))
        headblocks.append(E.link(rel="stylesheet", href="../types.css", type="text/css"))
        headrow = [
            E.td('Sample', colspan="2"),
            E.td('Token', **classes(["pad"])),
            E.td(E.span('Before'), **classes(["before"])),
            E.td(E.span('Word'), **classes(["word"])),
            E.td(E.span('After'), **classes(["after"])),
        ]
        bodyblocks.extend(headtext)
        tablerows = [E.tr(*headrow, **classes(["head"]))]
        grouped = defaultdict(list)
        for c in l:
            if what == "sample":
                key = "t{}".format(self.file_token.map[c.tokencode])
            elif what == "token":
                key = "s{}".format(self.file_sample.map[c.samplecode])
            else:
                assert False
            grouped[key].append(c)

        for key in sorted(grouped.keys()):
            ll = grouped[key]
            ll = sorted(ll, key=lambda c: (c.after, c.before, c.word))
            block = []
            for c in ll:
                row = []
                wordcount, descr, link = self.sample_info[(c.corpuscode, c.samplecode)]
                if descr is None:
                    if link is None:
                        dl = None
                    else:
                        dl = E.a('link', href=link)
                else:
                    if link is None:
                        dl = descr
                    else:
                        dl = E.a(descr, href=link)
                if what == "sample":
                    sample = c.samplecode
                    token = self.token_link(c.corpuscode, c.datasetcode, c.tokencode, c.samplecode)
                elif what == "token":
                    sample = self.sample_link(c.corpuscode, c.datasetcode, c.samplecode, c.tokencode)
                    token = self.token_short[(c.corpuscode, c.datasetcode, c.tokencode)]
                else:
                    assert False
                before = none_to_empty(c.before)
                word = none_to_empty(c.word)
                after = none_to_empty(c.after)
                if c.link is not None:
                    word = E.a(word, href=c.link)
                if dl is None:
                    row = [
                        E.td(sample, colspan="2")
                    ]
                else:
                    row = [
                        E.td(sample),
                        E.td(dl),
                    ]
                row += [
                    E.td(token, **classes(["pad"])),
                    E.td(E.span(before), **classes(["before"])),
                    E.td(E.span(word), **classes(["word"])),
                    E.td(E.span(after), **classes(["after"])),
                ]
                block.append(E.tr(*row))
            tablerows.append(E.tbody(*block, id=key))

        bodyblocks.append(E.div(E.table(*tablerows), **classes(["context"])))
        doc = E.html(E.head(*headblocks), E.body(*bodyblocks))
        with open(filename, 'w') as f:
            TypesPlot.write_html(f, doc)

    def find_outdated(self):
        redraw = []
        for c in self.curves:
            for outdated in c.get_outdated():
                redraw.append((c, outdated))
        return redraw

    def get_typelist(self, corpuscode, datasetcode, collectioncode):
        k = (corpuscode, datasetcode, collectioncode)
        if k not in self.typelist_cache:
            self.typelist_cache[k] = self.calc_typelist(*k)
        return self.typelist_cache[k]

    def get_samplelist(self, corpuscode, datasetcode, collectioncode):
        k = (corpuscode, datasetcode, collectioncode)
        if k not in self.samplelist_cache:
            self.samplelist_cache[k] = self.calc_samplelist(*k)
        return self.samplelist_cache[k]

    def get_sample(self, corpuscode, datasetcode, samplecode):
        k = (corpuscode, datasetcode, samplecode)
        if k not in self.sample_cache:
            self.sample_cache[k] = self.calc_sample(*k)
        return self.sample_cache[k]

    def calc_typelist(self, corpuscode, datasetcode, collectioncode):
        if collectioncode is None:
            typelist = sorted(self.tokenset_by_dataset[(corpuscode, datasetcode)])
            r = defaultdict(list)
            for t in typelist:
                tsamples = self.sampleset_by_token[(corpuscode, datasetcode, t)]
                total = len(tsamples)
                if total == 0:
                    continue
                bracket = int(math.log(total, 2))
                r[bracket].append((t, total))
            tables = []
            brackets = sorted(r.keys())
            for bracket in brackets:
                table = []
                l = sorted(r[bracket], key=lambda x: (-x[1], x[0]))
                for t, total in l:
                    table.append(E.tr(
                        bar(total, 'bara', bracket=bracket),
                        E.td(E.span(self.token_link(corpuscode, datasetcode, t))),
                        title=u"{}: {} samples".format(t, total)
                    ))
                tables.append(E.table(*table))
        else:
            csamples = self.sampleset_by_collection[(corpuscode, collectioncode)]
            typelist = sorted(self.tokenset_by_dataset[(corpuscode, datasetcode)])
            r = defaultdict(list)
            for t in typelist:
                tsamples = self.sampleset_by_token[(corpuscode, datasetcode, t)]
                here = len(tsamples & csamples)
                other = len(tsamples - csamples)
                total = here + other
                if total == 0:
                    continue
                bracket = int(math.log(total, 2))
                ratio = here / float(total)
                r[bracket].append((t, here, other, ratio))
            tables = []
            brackets = sorted(r.keys())
            for bracket in brackets:
                table = []
                l = sorted(r[bracket], key=lambda x: (-x[3], -x[1], x[2], x[0]))
                for t, here, other, ratio in l:
                    table.append(E.tr(
                        bar(here, 'bara', bracket=bracket),
                        bar(other, 'barb', bracket=bracket),
                        E.td(E.span(self.token_link(corpuscode, datasetcode, t, collectioncode=collectioncode),
                                    style="color: {};".format(grayness(here, other)))),
                        title=u"{} — {}: {} samples, other: {} samples".format(t, collectioncode, here, other)
                    ))
                tables.append(E.table(*table))
        return [E.table(
            E.tr(E.td(u"Types that occur in…", colspan="{}".format(len(brackets)))),
            E.tr(*[E.td(descr_bracket(bracket)) for bracket in brackets], **{"class": "head"}),
            E.tr(*[E.td(x) for x in tables], **{"class": "first last"}),
        )]

    def calc_sample(self, corpuscode, datasetcode, samplecode):
        s = SampleData()
        s.samplecode = samplecode
        skey = (corpuscode, datasetcode, samplecode)
        s.wordcount, s.descr, s.link = self.sample_info[(corpuscode, samplecode)]
        typelist = sorted(self.tokenset_by_sample[skey])
        s.collections = sorted(self.collectionset_by_sample[(corpuscode, samplecode)])
        s.hapaxlist = []
        s.otherlist = []
        s.uniquelist = []
        for t in typelist:
            if self.tokencount_by_token[(corpuscode, datasetcode, t)] == 1:
                s.hapaxlist.append(t)
            elif len(self.sampleset_by_token[(corpuscode, datasetcode, t)]) == 1:
                s.uniquelist.append(t)
            else:
                s.otherlist.append(t)
        s.commonlist = self.tokencount_by_sample_token[skey].most_common(N_COMMON + 1)
        if len(s.commonlist) > 0:
            if len(s.commonlist) == N_COMMON + 1:
                threshold = max(s.commonlist[-1][1], 1)
            else:
                threshold = 1
            s.commonlist = [(x,c) for x,c in s.commonlist if c > threshold]
            s.commonlist = sorted(s.commonlist, key=lambda x: (-x[1], x[0]))
        s.tokencount = self.tokencount_by_sample[skey]
        s.typecount = len(typelist)
        s.uniquecount = len(s.uniquelist) + len(s.hapaxlist)
        s.hapaxcount = len(s.hapaxlist)
        return s

    def calc_samplelist(self, corpuscode, datasetcode, collectioncode):
        if collectioncode is not None:
            csamples = self.sampleset_by_collection[(corpuscode, collectioncode)]
        else:
            csamples = self.sampleset_by_corpus[corpuscode]
        l = []
        maxwords = 1
        maxtokens = 1
        maxtypes = 1
        for samplecode in csamples:
            s = self.get_sample(corpuscode, datasetcode, samplecode)
            l.append(s)
            maxwords = max(maxwords, s.wordcount)
            maxtokens = max(maxtokens, s.tokencount)
            maxtypes = max(maxtypes, s.typecount)

        l = sorted(l, key=lambda s: (-s.wordcount, s.samplecode))
        tablerows = []
        for s in l:
            clist = []
            for t,c in s.commonlist:
                if len(clist) > 0:
                    clist.append(', ')
                clist.append(self.token_link(corpuscode, datasetcode, t, s.samplecode))
                clist.append(u"\u202F×\u202F{}".format(c))
            ulist = [self.token_link(corpuscode, datasetcode, t, s.samplecode) for t in s.uniquelist + s.hapaxlist]
            tablerows.append([
                E.td(self.sample_link(corpuscode, datasetcode, s.samplecode)),
                E.td(none_to_empty(s.descr)),
                E.td(str(s.wordcount), **{"class": "right"}),
                bar(s.wordcount, 'bar', maxval=maxwords),
                E.td(str(s.tokencount), **{"class": "right"}),
                bar(s.tokencount, 'bar', maxval=maxtokens),
                E.td(str(s.typecount), **{"class": "right"}),
                bar(s.typecount, 'bar', maxval=maxtypes),
                E.td(str(s.uniquecount), **{"class": "right"}),
                bar(s.uniquecount, 'bar', maxval=maxtypes),
                E.td(str(s.hapaxcount), **{"class": "right"}),
                bar(s.hapaxcount, 'bar', maxval=maxtypes),
                E.td(*clist),
                E.td(*TypesPlot.add_sep(ulist, ', '), **{"class": "wrap"}),
            ])
        table = [
            E.tr(
                E.td('Sample', colspan="2"),
                E.td('Words', colspan="2"),
                E.td('Tokens', colspan="2"),
                E.td('Types', colspan="2"),
                E.td('Unique', colspan="2"),
                E.td('Hapaxes', colspan="2"),
                E.td('Common types'),
                E.td('Unique types', **{"class": "wide"}),
                **{"class": "head"}
            )
        ]
        for i, row in enumerate(tablerows):
            table.append(E.tr(*row, **firstlast(i, tablerows)))
        return [E.table(*table)]


def descr_bracket(bracket):
    a = 2 ** bracket
    b = 2 * a
    if a == 1:
        assert b == 2
        return '{} sample'.format(a)
    else:
        return '< {} samples'.format(b)

def bar(x, label, bracket=None, maxval=None):
    x = bar_scale(x, bracket, maxval)
    return E.td(
        E.span(
            '',
            style="border-left-width: {}px;".format(x)
        ),
        **classes([label])
    )

def bar_scale(x, bracket=None, maxval=None):
    if bracket is not None:
        scale = math.sqrt(2 ** bracket)
        return int(round(5.0 * x / scale))
    elif maxval is not None:
        return int(round(25.0 * x / maxval))
    else:
        return x

def grayness(here, other):
    total = here + other
    ratio = int(round(10 * float(here) / total))
    return ['#000', '#111', '#222', '#333', '#444', '#555', '#666', '#777', '#888', '#999', '#aaa'][10-ratio]


def get_datafile(args):
    return os.path.join(args.tmpdir, DATA_FILE)

def write_data(args, redraw):
    with open(get_datafile(args), 'w') as f:
        cPickle.dump(redraw, f, -1)

def run(args, nredraw):
    cmds = []
    for j in range(args.parts):
        cmd = [ get_datafile(args), nredraw, args.parts, j+1 ]
        cmds.append(cmd)
    TypesParallel.Parallel(TOOL, 'types-draw-curves', cmds, args).run()

def main():
    args = get_args()
    if not os.path.exists(args.tmpdir):
        os.makedirs(args.tmpdir)
    conn = TypesDatabase.open_db(args.db)
    ac = AllCurves()
    ac.read_curves(args, conn)
    conn.commit()
    if len(ac.curves) == 0:
        msg('there are no results in the database')
        return
    ac.create_directories()
    sys.stderr.write('%s: write: (' % TOOL)
    ac.generate_index(args.htmldir)
    if ac.with_lists:
        ac.generate_context(args.htmldir)
    ac.generate_html()
    sys.stderr.write(')\n')
    redraw = ac.find_outdated()
    nredraw = len(redraw)
    if nredraw == 0:
        msg('all files up to date')
    else:
        msg('outdated: %d files' % nredraw)
        write_data(args, redraw)
        run(args, nredraw)
        os.remove(get_datafile(args))
        msg('all done')

CSS = """
BODY {
    color: #000;
    background-color: #fff;
    font-family: Helvetica, Arial, sans-serif;
    padding: 0px;
    margin: 15px;
}

.listing, .stats, .context {
    font-size: 85%;
}

.menuitem {
    font-size: 90%;
}

.small, .menudesc, .menudescinline {
    font-size: 80%;
}

A:link {
    color: #00f;
    text-decoration: none;
}

A:visited {
    color: #008;
    text-decoration: none;
}

A:hover, A:active {
    text-decoration: underline;
}

TABLE {
    border-collapse: collapse;
}

.mainmenu, .findings, .listing, .stats {
    margin-left: 4px;
    margin-bottom: 20px;
}

.findings, .listing, .stats, .context {
    margin-top: 20px;
}

TD {
    padding: 0px;
    padding-top: 1px;
    padding-bottom: 1px;
    text-align: left;
    vertical-align: top;
    white-space: nowrap;
}

TD.right {
    text-align: right;
}

TD+TD {
    padding-left: 15px;
}

TD.pad {
    padding-right: 15px;
}

TD.wrap {
    white-space: normal;
}

TR.head>TD {
    padding-top: 5px;
    padding-bottom: 5px;
    border-bottom: 1px solid #888;
}

TR.head.sep>TD {
    padding-top: 30px;
}

TR.first>TD, .context TBODY>TR:first-child>TD {
    padding-top: 5px;
}

TR.last>TD, .context TBODY>TR:last-child>TD {
    padding-bottom: 5px;
    border-bottom: 1px solid #888;
}

P {
    margin: 0px;
    margin-top: 3px;
    margin-bottom: 3px;
    padding: 0px;
}

.plot {
    margin-top: 20px;
    margin-bottom: 10px;
}

.menudesc {
    margin-left: 30px;
}

.menuitem, .menutitle, .menudescinline {
    display: inline-block;
    padding-top: 1px;
    padding-bottom: 1px;
    padding-left: 2px;
    padding-right: 2px;
    border: 1px solid #fff;
    margin-top: 1px;
    margin-bottom: 1px;
    margin-left: 1px;
    margin-right: 1px;
}

.menuitem, .menutitle {
    white-space: nowrap;
}

.menu A:hover, .menu A:link, .menu A:visited {
    text-decoration: none;
}

.menusel {
    border: 1px solid #aaa;
    background-color: #fff;
}

A.menuitem:hover, A.menutitle:hover {
    border: 1px dotted #000;
    background-color: #eee;
}

TD.bar {
    padding-left: 5px;
}

TD.bara {
    text-align: right;
}

TD.barb {
    padding-left: 1px;
}

TD.barb+TD {
    padding-left: 5px;
}

TD.bar>SPAN, TD.bara>SPAN {
    border-left: 0px solid #a00;
}

TD.barb>SPAN {
    border-left: 0px solid #888;
}

TD.wide {
    min-width: 40ex;
}

TD.before {
    text-align: right;
}

TD.word {
    text-align: center;
}

TD.after {
    text-align: left;
}

TD.before, TD.after {
    overflow: hidden;
    position: relative;
    width: 50%;
}

TD.before SPAN {
    position: absolute;
    right: 0px;
}

TD.after SPAN {
    position: absolute;
    left: 15px;
}

.menusel {
    color: #a00;
}

A.menusame, A.menutitle {
    color: #008;
}

A.menuother {
    color: #888;
}

TBODY:target {
    background-color: #eee;
}
"""

main()
