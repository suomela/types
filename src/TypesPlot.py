# coding=utf-8

import os.path
import numpy as np
from lxml.builder import E
from lxml import etree

WIDTH = 9
HEIGHT = 6
DPI = 96

LABEL_SEP = 0.06
LABEL_AREA = (0.03, 0.97)
AXIS_PAD = 0.02
XSEP = 0.04
THRESHOLD = 0.005

def colour(c):
    return tuple([ int(c[2*i:2*i+2], 16)/float(255) for i in range(3) ])

def colours(l):
    return [ colour(c) for c in l ]

BLUE   = colours(('95a8c9','acbbd5','c2cddf','d7deeb','e7ebf2'))
ORANGE = colours(('e5af5a','ebc07f','f0d1a1','f5e0c3','f9eddc'))
RED    = colours(('c99eb1','d4b3c1','dfc7d2','eadae1','f2e9ed'))
WHITE  = colour('ffffff')
GREY   = colour('999999')
DARK   = colour('333333')
BLACK  = colour('000000')
BLUE2  = colour('3f4f6c')

def lim(maxval):
    return (-AXIS_PAD * maxval, (1.0 + AXIS_PAD) * maxval)

def ucfirst(s):
    if s == '':
        return s
    else:
        return s[0].upper() + s[1:]

def add_sep(l, sep):
    # [1,2,3] -> [1,sep,2,sep,3]
    return [x for y in l for x in (y, sep)][:-1]

def write_html(f, doc):
    f.write('<!DOCTYPE html>\n')
    f.write(etree.tostring(doc, method='html', pretty_print=True))

def longest_common_prefix(a, b):
    i = 0
    while i < len(a) and i < len(b) and a[i] == b[i]:
        i += 1
    return i

def wrap_svg_link(el, url, title=None):
    link = etree.Element("a")
    link.set('{http://www.w3.org/1999/xlink}href', url)
    if title is not None:
        link.set('{http://www.w3.org/1999/xlink}title', title)
    link.set('target', '_top')
    parent = el.getparent()
    assert parent is not None
    parent.replace(el, link)
    link.append(el)

class LabelPlacement:
    def __init__(self):
        self.freelist = set()
        self.freelist.add(LABEL_AREA)

    def place(self, y):
        closest = None
        bestdist = None
        bestplace = None
        for free in self.freelist:
            a, b = free
            if y < a:
                dist = a - y
                place = a
            elif a <= y <= b:
                dist = 0.0
                place = y
            elif b < y:
                dist = y - b
                place = b
            else:
                assert False
            if bestdist is None or bestdist > dist or (bestdist == dist and free < closest):
                closest = free
                bestdist = dist
                bestplace = place
        if closest is None:
            return None
        self.freelist.remove(closest)
        y1, y4 = closest
        y2 = bestplace - LABEL_SEP
        y3 = bestplace + LABEL_SEP
        if y1 < y2:
            self.freelist.add((y1, y2))
        if y3 < y4:
            self.freelist.add((y3, y4))
        return bestplace

class CPoint:
    def __init__(self, ec, fc, lw):
        self.ec = ec
        self.fc = fc
        self.lw = lw

SEL   = CPoint( BLACK, WHITE, 1.5 )
UNSEL = CPoint( GREY,  WHITE, 0.5 )

class Point:
    def __init__(self, collectioncode, y, x, above, below, total):
        self.collectioncode = collectioncode
        self.y = y
        self.x = x
        if above < below:
            is_above = True
            self.side = 'above'
            self.pvalue = float(above)/float(total)
        else:
            is_above = False
            self.side = 'below'
            self.pvalue = float(below)/float(total)

        self.ms = 7
        self.marker = 'o'

        if self.side is None:
            pass
        elif self.pvalue > 0.1:
            pass
        elif is_above:
            self.ms = 10
            self.marker = '^'
        else:
            self.ms = 10
            self.marker = 'v'

        self.ec = BLACK
        self.fc = WHITE
        self.lw = 1.0

        palette = ORANGE if is_above else RED

        if self.pvalue is None:
            pass
        elif self.pvalue < 0.000001:
            self.fc = palette[0]
        elif self.pvalue < 0.00001:
            self.fc = palette[1]
        elif self.pvalue < 0.0001:
            self.fc = palette[2]
        elif self.pvalue < 0.001:
            self.fc = palette[3]
        elif self.pvalue < 0.01:
            self.fc = palette[4]
        else:
            self.ec = DARK


class Curve:
    def __init__(self, dirdict,
                 corpuscode, corpus_filename, corpus_descr,
                 statcode, stat_filename, xlabel, ylabel,
                 datasetcode, dataset_filename, dataset_descr):
        self.dirdict = dirdict
        self.corpuscode = corpuscode
        self.corpus_filename = corpus_filename
        self.corpus_descr = corpus_descr
        self.statcode = statcode
        self.stat_filename = stat_filename
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.datasetcode = datasetcode
        self.dataset_filename = dataset_filename
        self.dataset_descr = dataset_descr
        self.timestamp = None
        self.collection_descr = dict()
        self.collection_filenames = dict()
        self.group_by_collection = dict()
        self.group_filenames = dict()
        self.point_by_collection = dict()
        self.points_by_group = dict()
        self.groups = []
        self.group_set = set()
        self.timestamp_by_group = dict()
        self.polys = []
        self.maxx = 0
        self.maxy = 0
        self.group_seen(None)

    def group_seen(self, groupcode):
        if groupcode not in self.group_set:
            self.points_by_group[groupcode] = []
            self.groups.append(groupcode)
            self.group_set.add(groupcode)
            self.points_by_group[groupcode] = []

    def add_timestamp(self, timestamp):
        if self.timestamp is None:
            self.timestamp = timestamp
        else:
            self.timestamp = max(self.timestamp, timestamp)

    def add_timestamp_group(self, timestamp, groupcode):
        if groupcode not in self.timestamp_by_group:
            self.timestamp_by_group[groupcode] = timestamp
        else:
            self.timestamp_by_group[groupcode] = max(self.timestamp_by_group[groupcode], timestamp)

    def add_poly(self, level, upper, lower):
        poly = np.concatenate((upper, np.flipud(lower)))
        maxs = np.amax(poly, axis=0)
        self.polys.append(poly)
        self.maxx = max(self.maxx, maxs[0])
        self.maxy = max(self.maxy, maxs[1])

    def add_collection(self, groupcode, group_filename,
                       collectioncode, collection_filename, description):
        self.group_filenames[groupcode] = group_filename
        self.group_by_collection[collectioncode] = groupcode
        self.collection_filenames[collectioncode] = collection_filename
        self.collection_descr[collectioncode] = description

    def add_point(self, p, timestamp):
        assert p.collectioncode not in self.point_by_collection
        self.point_by_collection[p.collectioncode] = p
        groupcode = self.group_by_collection[p.collectioncode]
        self.group_seen(groupcode)
        self.points_by_group[groupcode].append(p)
        self.add_timestamp_group(timestamp, groupcode)

    def get_suffixes(self, p=None):
        if p is None:
            return ['pdf', 'svg']
        else:
            return ['svg']

    def get_pointname(self, suffix, groupcode, p=None):
        b = [self.stat_filename, self.dataset_filename]
        if groupcode is not None:
            b.append(self.group_filenames[groupcode])
        if p is not None:
            b.append('')
            b.append(self.collection_filenames[p.collectioncode])
        return '_'.join(b) + '.' + suffix

    def get_pointname_from_root(self, suffix, groupcode, p=None):
        return self.corpus_filename + "/" + self.get_pointname(suffix, groupcode, p)

    def get_pointname_relative(self, other, suffix, groupcode, collectioncode=None):
        changed = False
        if groupcode is not None and groupcode not in self.group_set:
            groupcode = None
            changed = True
        if groupcode is None and collectioncode is not None:
            collectioncode = None
            changed = True
        if collectioncode is not None and collectioncode not in self.point_by_collection:
            collectioncode = None
            changed = True
        if collectioncode is not None:
            exp = self.group_by_collection[collectioncode]
            if exp != groupcode:
                changed = True
                collectioncode = None
        if collectioncode is not None:
            p = self.point_by_collection[collectioncode]
        else:
            p = None
        name = self.get_pointname(suffix, groupcode, p)
        if self.corpuscode == other.corpuscode:
            full = name
        else:
            full = "../" + self.corpus_filename + "/" + name
        return full, changed

    def get_directory(self, suffix):
        return os.path.join(self.dirdict[suffix], self.corpus_filename)

    def get_filename(self, suffix, groupcode, p=None):
        return os.path.join(self.get_directory(suffix), self.get_pointname(suffix, groupcode, p))

    def get_directories(self):
        return [ self.get_directory(suffix) for suffix in self.get_suffixes() ]

    def get_filenames(self, groupcode, p=None):
        return [ self.get_filename(suffix, groupcode, p) for suffix in self.get_suffixes(p) ]

    def is_outdated(self, groupcode):
        for filename in self.get_filenames(groupcode):
            if not os.path.exists(filename):
                return True
            mtime = os.path.getmtime(filename)
            if mtime < self.timestamp:
                return True
            if groupcode in self.timestamp_by_group and mtime < self.timestamp_by_group[groupcode]:
                return True
        return False

    def get_outdated(self):
        outdated = []
        for groupcode in sorted(self.points_by_group.keys()):
            if self.is_outdated(groupcode):
                outdated.append(groupcode)
        return outdated

    def plot_group(self, matplotlib, groupcode):
        self.plot_group_points(matplotlib, groupcode, None)
        for point in self.points_by_group[groupcode]:
            self.plot_group_points(matplotlib, groupcode, point)

    def plot_group_points(self, matplotlib, groupcode, point):
        points = sorted(self.points_by_group[groupcode], key=lambda p: p.x, reverse=True)
        SPP = matplotlib.figure.SubplotParams(left=0.1, right=0.85, bottom=0.1, top=0.98)
        fig = matplotlib.pyplot.figure(figsize=(WIDTH, HEIGHT), subplotpars=SPP)
        ax = fig.add_subplot(111)
        ax.set_autoscalex_on(False)
        ax.set_autoscaley_on(False)
        ax.set_xlim(lim(self.maxx))
        ax.set_ylim(lim(self.maxy))
        self.plot_polys(ax)
        self.plot_points(ax, points, groupcode, point)
        self.plot_labels(ax)
        for suffix in self.get_suffixes(point):
            filename = self.get_filename(suffix, groupcode, point)
            fig.savefig(filename)
            if suffix == 'svg':
                self.add_svg_links(filename, points, groupcode, point)
        matplotlib.pyplot.close(fig)

    def plot_polys(self, ax):
        for i, poly in enumerate(self.polys):
            f = i/(len(self.polys)-1.0)
            j = min(i, len(BLUE)-1)
            edge = BLUE2
            fill = BLUE[-(j+1)]
            ax.fill(poly[:,0], poly[:,1], fc=fill, ec=edge, linewidth=0.4, zorder=100 + f)

    def plot_points(self, ax, points, groupcode, point):
        placement = LabelPlacement()
        for i, p in enumerate(points):
            scx, scy = float(p.x)/self.maxx, float(p.y)/self.maxy
            stx = scx + XSEP
            sty = placement.place(scy)
            zbase = 201.0 - p.pvalue
            if point is None:
                cp = p
            elif point == p:
                cp = SEL
                zbase += 100
            else:
                cp = UNSEL
            if sty is not None:
                tx = stx * self.maxx
                ty = sty * self.maxy
                ax.plot(
                    [p.x, p.x, tx],
                    [p.y, ty,  ty],
                    color=cp.ec,
                    linewidth=cp.lw,
                    clip_on=False,
                    zorder=zbase,
                    gid='types_pl_%d' % i,
                )
            ax.plot(
                p.x, p.y,
                marker=p.marker,
                mec=cp.ec,
                mfc=cp.fc,
                mew=cp.lw,
                ms=p.ms,
                zorder=zbase + 2,
                gid='types_pm_%d' % i,
            )
            if sty is not None:
                ax.text(
                    tx, ty,
                    p.collectioncode,
                    color=cp.ec,
                    va='center',
                    bbox=dict(
                        boxstyle="round,pad=0.3",
                        fc=cp.fc,
                        ec=cp.ec,
                        linewidth=cp.lw,
                    ),
                    zorder=zbase + 1,
                    gid='types_pt_%d' % i,
                )

    def plot_labels(self, ax):
        ax.set_xlabel(ucfirst(self.xlabel), labelpad=10)
        ax.set_ylabel(ucfirst(self.ylabel), labelpad=15)

    def add_svg_links(self, filename, points, groupcode, point):
        with open(filename) as f:
            svg = etree.parse(f)
        for i, p in enumerate(points):
            if point is not None and point == p:
                url = self.get_pointname('html', groupcode)
            else:
                url = self.get_pointname('html', groupcode, p)
            title = self.collection_descr[p.collectioncode]
            if title is None:
                title = p.collectioncode
            for what in ['pl', 'pm', 'pt']:
                gid = 'types_%s_%d' % (what, i)
                path = ".//{http://www.w3.org/2000/svg}g[@id='%s']" % gid
                el = svg.find(path)
                if el is not None:
                    wrap_svg_link(el, url, title)
        with open(filename, 'w') as f:
            svg.write(f)

    def generate_html(self, ac):
        for groupcode in sorted(self.points_by_group.keys()):
            for p in [None] + self.points_by_group[groupcode]:
                filename = self.get_filename('html', groupcode, p)
                with open(filename, 'w') as f:
                    self.generate_html_one(f, groupcode, p, ac)

    def generate_html_one(self, f, groupcode, point, ac):
        collectioncode = point.collectioncode if point is not None else None

        headblocks = []
        bodyblocks = []

        t = [ self.corpuscode, self.datasetcode, groupcode, collectioncode, self.statcode ]
        t = u" — ".join([a for a in t if a is not None])
        headblocks.append(E.title(t))
        headblocks.append(E.link(rel="stylesheet", href="../types.css", type="text/css"))

        def add_menu(title, cl, gl, xl, labelhook, titlelink=None, groupby=None):
            prev = []
            prevj = 0
            result = []
            for c in cl:
                for g in gl:
                    for x in xl:
                        addbreak = False
                        label, desc = labelhook(c, g, x)
                        selected = c == self and g is groupcode and x is collectioncode
                        if groupby is not None:
                            cur = label.split(groupby)
                            # A heuristic rule that tries to produce reasonable abbreviations
                            j = longest_common_prefix(prev, cur)
                            if j == len(prev):
                                j -= 1
                            if j < prevj:
                                j = 0
                            if 0 < prevj < j:
                                j = prevj
                            if j > 0:
                                label = u"…" + groupby.join(cur[j:])
                            if j == 0 and prevj > 0:
                                addbreak = True
                            prev = cur
                            prevj = j
                        attr = dict()
                        if selected:
                            attr["class"] = "menuitem menusel"
                            e = E.span(label, **attr)
                        else:
                            href, changed = c.get_pointname_relative(self, 'html', g, x)
                            if desc is not None:
                                attr["title"] = desc
                            attr["class"] = "menuitem menuother" if changed else "menuitem menusame"
                            e = E.a(label, href=href, **attr)
                        if addbreak:
                            result.append(E.br())
                        result.append(e)
            t = title + ":"
            if titlelink is None:
                t = E.span(t, **{"class": "menutitle"})
            else:
                t = E.a(t, href=titlelink, **{"class": "menutitle"})
            menu = E.p(*add_sep([t] + result, " "), **{"class": "menurow"})
            menublocks.append(menu)

        menublocks = []
        add_menu(
            "Corpus",
            ac.by_dataset_stat_fallback[(self.datasetcode, self.statcode)],
            [ groupcode ],
            [ collectioncode ],
            lambda c, g, x: (c.corpuscode, c.corpus_descr),
            titlelink="../index.html",
            groupby='-'
        )
        if self.corpus_descr is None:
            menublocks.append(E.p(self.corpuscode, **{"class": "menudesc"}))
        else:
            menublocks.append(E.p(self.corpuscode, u" · ", self.corpus_descr, **{"class": "menudesc"}))
        add_menu(
            "Dataset",
            ac.by_corpus_stat[(self.corpuscode, self.statcode)],
            [ groupcode ],
            [ collectioncode ],
            lambda c, g, x: (c.datasetcode, c.dataset_descr)
        )
        if self.dataset_descr is not None:
            menublocks.append(E.p(self.dataset_descr, **{"class": "menudesc"}))
        add_menu(
            "Points",
            [ self ],
            sorted(self.groups),
            [ collectioncode ],
            lambda c, g, x: ("none", None) if g is None else (g, None)
        )
        add_menu(
            "Axes",
            ac.by_corpus_dataset[(self.corpuscode, self.datasetcode)],
            [ groupcode ],
            [ collectioncode ],
            lambda c, g, x: (
                "%s/%s" % (c.ylabel, c.xlabel),
                "y = %s, x = %s" % (c.ylabel, c.xlabel)
            )
        )
        bodyblocks.append(E.div(*menublocks, **{"class": "menu"}))

        fig = E.p(E.object(
            data=self.get_pointname('svg', groupcode, point),
            type="image/svg+xml",
            width=str(WIDTH*DPI),
            height=str(HEIGHT*DPI),
        ), **{"class": "plot"})
        bodyblocks.append(fig)

        menublocks = []
        add_menu(
            "Collection",
            [ self ],
            [ groupcode ],
            [ None ] + [ p.collectioncode for p in self.points_by_group[groupcode] ],
            lambda c, g, x: ("none", None) if x is None else (x, self.collection_descr[x])
        )
        if collectioncode is not None:
            if self.collection_descr[collectioncode] is not None:
                menublocks.append(E.p(self.collection_descr[collectioncode], **{"class": "menudesc"}))
            stat = [
                u"%s %s" % (point.x, self.xlabel),
                u"%d %s" % (point.y, self.ylabel),
                u"%f %s" % (point.pvalue, point.side),
            ]
            t = E.span("Statistics:", **{"class": "menutitle"})
            stat = [ E.span(v, **{"class": "menuitem"}) for v in stat ]
            menu = E.p(*add_sep([t] + stat, " "), **{"class": "menurow"})
            menublocks.append(menu)

        bodyblocks.append(E.div(*menublocks, **{"class": "menu"}))
        if ac.with_typelists:
            typelist = ac.get_typelist(self.corpuscode, self.datasetcode, collectioncode)
            bodyblocks.append(E.div(*typelist, **{"class": "typelist"}))

        doc = E.html(E.head(*headblocks), E.body(*bodyblocks))
        write_html(f, doc)
