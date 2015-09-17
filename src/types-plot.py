# coding=utf-8

from collections import defaultdict
import optparse
import cPickle
import os
import os.path
import re
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

FDR = [0.001, 0.01, 0.1]

def msg(msg):
    sys.stderr.write("%s: %s\n" % (TOOL, msg))

def none_to_empty(x):
    return '' if x is None else x

def classes(l):
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


class AllCurves:
    def __init__(self):
        self.curves = []
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
        self.tokens = defaultdict(list)
        self.sample_collection = defaultdict(list)

    def read_curves(self, args, conn):
        sys.stderr.write('%s: read:' % TOOL)

        self.with_typelists = args.with_typelists

        dirdict = {
            "pdf": args.plotdir,
            "svg": args.htmldir,
            "html": args.htmldir,
        }

        file_corpus = Filenames()
        file_stat = Filenames()
        file_dataset = Filenames()
        file_group = Filenames()
        file_collection = Filenames()

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
            SELECT statcode, xlabel.labeltext, ylabel.labeltext
            FROM stat
            JOIN label AS ylabel ON stat.y = ylabel.labelcode
            JOIN label AS xlabel ON stat.x = xlabel.labelcode
            ORDER BY statcode
        ''')
        for statcode, xlabel, ylabel in r:
            file_stat.generate(statcode)
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
            file_corpus.generate(corpuscode)
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
            file_dataset.generate(datasetcode)
            dataset_descr[(corpuscode, datasetcode)] = description

        ### result_curve

        sys.stderr.write(' result_curve')
        r = conn.execute('''
            SELECT corpuscode, statcode, datasetcode, id, level, side, logid
            FROM result_curve
            ORDER BY corpuscode, statcode, datasetcode
        ''')
        for corpuscode, statcode, datasetcode, curveid, level, side, logid in r:
            k = (corpuscode, datasetcode, statcode)
            if k not in self.by_corpus_dataset_stat:
                c = TypesPlot.Curve(
                        dirdict,
                        corpuscode, file_corpus.map[corpuscode],
                        corpus_descr[corpuscode],
                        statcode, file_stat.map[statcode],
                        self.statcode_label[statcode][0],
                        self.statcode_label[statcode][1],
                        datasetcode, file_dataset.map[datasetcode],
                        dataset_descr[(corpuscode, datasetcode)]
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
            file_group.generate(groupcode)
            file_collection.generate(collectioncode)
            if corpuscode in self.by_corpus:
                for c in self.by_corpus[corpuscode]:
                    c.add_collection(
                        groupcode, file_group.map[groupcode],
                        collectioncode, file_collection.map[collectioncode],
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
            p = TypesPlot.Point(collectioncode, y, x, above, below, total)
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

        if self.with_typelists:

            ### token

            sys.stderr.write(' token')
            r = conn.execute('''
                SELECT corpuscode, samplecode, datasetcode, tokencode, tokencount
                FROM token
            ''')
            for corpuscode, samplecode, datasetcode, tokencode, tokencount in r:
                self.tokens[(corpuscode, datasetcode, samplecode)].append(tokencode)

            ### sample_collection

            sys.stderr.write(' sample_collection')
            r = conn.execute('''
                SELECT corpuscode, samplecode, collectioncode
                FROM sample_collection
            ''')
            for corpuscode, samplecode, collectioncode in r:
                self.sample_collection[(corpuscode, collectioncode)].append(samplecode)

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
        headblocks = []
        bodyblocks = []
        headblocks.append(E.title("Corpus menu"))
        headblocks.append(E.link(rel="stylesheet", href="types.css", type="text/css"))
        tablerows = self.generate_corpus_menu()
        bodyblocks.append(E.table(*tablerows))
        tablerows = self.generate_fdr_table()
        if len(tablerows) > 0:
            bodyblocks.append(E.table(*tablerows))
        doc = E.html(E.head(*headblocks), E.body(*bodyblocks))
        with open(os.path.join(htmldir, "index.html"), 'w') as f:
            TypesPlot.write_html(f, doc)
        with open(os.path.join(htmldir, "types.css"), 'w') as f:
            f.write(CSS)

    def find_outdated(self):
        redraw = []
        for c in self.curves:
            for outdated in c.get_outdated():
                redraw.append((c, outdated))
        return redraw

    def get_typelist(self, corpuscode, datasetcode, collectioncode):
        return []


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
    ac.generate_html()
    ac.generate_index(args.htmldir)
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
    font-family: Verdana, sans-serif;
    padding: 0px;
    margin: 15px;
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
    margin-bottom: 30px;
}

TD {
    padding: 0px;
    padding-top: 1px;
    padding-bottom: 1px;
    text-align: left;
    vertical-align: baseline;
    white-space: nowrap;
    font-size: 95%;
}

TD+TD {
    padding-left: 15px;
}

TD.wrap {
    white-space: normal;
}

TD.small {
    font-size: 80%;
}

TR.head TD {
    padding-top: 7px;
    padding-bottom: 7px;
    border-bottom: 1px solid #000;
    font-size: 100%;
}

TR.head.sep TD {
    padding-top: 30px;
}

TR.first TD {
    padding-top: 7px;
}

TR.last TD {
    padding-bottom: 7px;
    border-bottom: 1px solid #000;
}

P {
    margin: 0px;
    margin-top: 12px;
    margin-bottom: 12px;
    padding: 0px;
}

.plot {
    margin-top: 35px;
    margin-bottom: 15px;
}

.menudesc {
    margin-left: 30px;
}

.menudesc, .menudescinline {
    font-size: 80%;
}

.menuitem {
    font-size: 95%;
}

.menutitle {
    font-weight: bold;
}

.menuitem, .menutitle, .menudescinline {
    display: inline-block;
    padding: 3px;
    border: 1px solid #fff;
    margin-top: 1px;
    margin-bottom: 1px;
    margin-left: 4px;
    margin-right: 4px;
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

.menusel {
    color: #a00;
}

A.menusame, A.menutitle {
    color: #008;
}

A.menuother {
    color: #888;
}
"""

main()
