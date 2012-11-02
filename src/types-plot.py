# coding=utf-8

from collections import defaultdict
import optparse
import cPickle
import os
import os.path
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

def msg(msg):
    sys.stderr.write("%s: %s\n" % (TOOL, msg))

def get_args():
    parser = optparse.OptionParser(
        description='Update all plots.',
        version=TypesDatabase.version_string(TOOL),
    )
    parser.add_option('--db', metavar='FILE', dest='db',
                      help='which database to read [default: %default]',
                      default=TypesDatabase.DEFAULT_FILENAME)
    TypesParallel.add_options(parser)
    parser.add_option('--plotdir', metavar='DIRECTORY', dest='plotdir',
                      help='where to store PDF plots [default: %default]',
                      default=PLOT_DIR)
    parser.add_option('--htmldir', metavar='DIRECTORY', dest='htmldir',
                      help='where to store SVG plots and HTML files [default: %default]',
                      default=HTML_DIR)
    (options, args) = parser.parse_args()
    return options

class AllCurves:
    def __init__(self):
        self.curves = []
        self.by_corpus = defaultdict(list)
        self.by_dataset = defaultdict(list)
        self.by_stat = defaultdict(list)
        self.by_corpus_dataset = defaultdict(list)
        self.by_corpus_stat = defaultdict(list)
        self.by_dataset_stat = defaultdict(list)
        self.by_dataset_stat_fallback = dict()
        self.by_corpus_dataset_stat = dict()

    def read_curves(self, args, conn):
        sys.stderr.write('%s: read:' % TOOL)

        dirdict = {
            "pdf": args.plotdir,
            "svg": args.htmldir,
            "html": args.htmldir,
        }

        ### log

        timestamp_by_logid = dict()

        def get_timestamp(logid):
            if logid not in timestamp_by_logid:
                ts = [ r[0] for r in conn.execute("SELECT STRFTIME('%s', timestamp) FROM log WHERE id = ?", (logid,)) ]
                assert len(ts) == 1
                timestamp_by_logid[logid] = int(ts[0])
            return timestamp_by_logid[logid]

        ### stat

        statcode_label = dict()
        sys.stderr.write(' stat')
        r = conn.execute('''
            SELECT statcode, xlabel.labeltext, ylabel.labeltext
            FROM stat
            JOIN label AS ylabel ON stat.y = ylabel.labelcode
            JOIN label AS xlabel ON stat.x = xlabel.labelcode
        ''')
        for statcode, xlabel, ylabel in r:
            statcode_label[statcode] = (xlabel, ylabel)

        ### corpus

        corpus_descr = dict()
        sys.stderr.write(' corpus')
        r = conn.execute('SELECT corpuscode, description FROM corpus')
        for corpuscode, description in r:
            corpus_descr[corpuscode] = description

        ### dataset

        dataset_descr = dict()
        sys.stderr.write(' dataset')
        r = conn.execute('SELECT corpuscode, datasetcode, description FROM dataset')
        for corpuscode, datasetcode, description in r:
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
                c = TypesPlot.Curve(dirdict,
                                    corpuscode, corpus_descr[corpuscode],
                                    statcode, statcode_label[statcode][0], statcode_label[statcode][1],
                                    datasetcode, dataset_descr[(corpuscode, datasetcode)])
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
            if corpuscode in self.by_corpus:
                for c in self.by_corpus[corpuscode]:
                    c.add_collection(groupcode, collectioncode, description)

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

    def generate_index(self, htmldir):
        headblocks = []
        bodyblocks = []
        headblocks.append(E.title("Corpus menu"))
        headblocks.append(E.link(rel="stylesheet", href="types.css", type="text/css"))
        menublocks = []
        for corpuscode in sorted(self.by_corpus.keys()):
            c = self.by_corpus[corpuscode][0]
            link = E.a(corpuscode, href=c.get_pointname_from_root('html', None), **{"class": "menuitem"})
            desc = E.span(c.corpus_descr, **{"class": "menudescinline"})
            menu = E.p(link, u" · ", desc, **{"class": "menurow"})
            menublocks.append(menu)
        bodyblocks = [ E.div(*menublocks, **{"class": "menu mainmenu"}) ]
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
    margin: 1em;
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

P {
    margin: 0px;
    margin-top: 12px;
    margin-bottom: 12px;
    padding: 0px;
}

.mainmenu P {
    margin-top: 2px;
    margin-bottom: 2px;
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
