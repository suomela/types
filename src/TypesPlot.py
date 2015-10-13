# coding=utf-8

from collections import namedtuple
import itertools
import os
import numpy as np
from lxml.builder import E
from lxml import etree

def colour(c):
    return tuple([ int(c[2*i:2*i+2], 16)/float(255) for i in range(3) ])

def colours(l):
    return [ colour(c) for c in l ]

# Colour scheme from:
# http://colorbrewer2.org/?type=sequential&scheme=PuBu&n=4
REGIONS_RGB = ('0570b0', '74a9cf', 'bdc9e1', 'f1eef6')

WHITE  = colour('ffffff')
GREY   = colour('999999')
DARK   = colour('333333')
BLACK  = colour('000000')
REGIONS = colours(REGIONS_RGB)

class CPoint:
    def __init__(self, ec, fc, lw):
        self.ec = ec
        self.fc = fc
        self.lw = lw

Layout = namedtuple('Layout', [
    'width', 'height', 'dpi',
    'label_sep', 'label_area', 'xsep',
    'sel', 'unsel',
    'xbins'
])

layout_slides = Layout(
    width = 5,
    height = 3,
    dpi = 96,
    label_sep = 0.12,
    label_area = (0.03, 0.97),
    xsep = 0.05,
    sel = CPoint( BLACK, WHITE, 1.5 ),
    unsel = CPoint( GREY,  WHITE, 1.0 ),
    xbins = 5,
)

layout_normal = Layout(
    width = 9,
    height = 6,
    dpi = 96,
    label_sep = 0.06,
    label_area = (0.03, 0.97),
    xsep = 0.03,
    sel = CPoint( BLACK, WHITE, 1.5 ),
    unsel = CPoint( GREY,  WHITE, 0.5 ),
    xbins = None,
)

LISTING_LABEL = { None: 'summary', 't': 'type list', 's': 'sample list' }

AXIS_PAD = 0.02

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

def cleanlist(l):
    l = ['' if x is None else x for x in l]
    while len(l) > 0 and l[-1] == '':
        l = l[:-1]
    return l


class LabelPlacement:
    def __init__(self, layout):
        self.layout = layout
        self.freelist = set()
        self.freelist.add(self.layout.label_area)

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
        y2 = bestplace - self.layout.label_sep
        y3 = bestplace + self.layout.label_sep
        if y1 < y2:
            self.freelist.add((y1, y2))
        if y3 < y4:
            self.freelist.add((y3, y4))
        return bestplace

class Point:
    def __init__(self, collectioncode, y, x, above, below, total, fdr):
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
        # negative if larger
        self.fdr = fdr

        self.ms = 7
        self.marker = 'o'

        if self.side is None:
            pass
        elif self.pvalue > 0.01:
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


class Curve:
    def __init__(self, layout, dirdict,
                 corpuscode, corpus_filename, corpus_descr,
                 statcode, stat_filename,
                 xlabel, ylabel, xtotal, ytotal,
                 datasetcode, dataset_filename, dataset_descr,
                 listings):
        self.layout = layout
        self.dirdict = dirdict
        self.corpuscode = corpuscode
        self.corpus_filename = corpus_filename
        self.corpus_descr = corpus_descr
        self.statcode = statcode
        self.stat_filename = stat_filename
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.xtotal = xtotal
        self.ytotal = ytotal
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
        self.listings = listings

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

    def get_pointname(self, suffix, groupcode, p=None, l=None):
        b = cleanlist([
            self.stat_filename,
            self.dataset_filename,
            None if groupcode is None else self.group_filenames[groupcode],
            None if p is None else self.collection_filenames[p.collectioncode],
            None if l is None else l,
        ])
        return '_'.join(b) + '.' + suffix

    def get_pointname_from_root(self, suffix, groupcode, p=None, l=None):
        return self.corpus_filename + "/" + self.get_pointname(suffix, groupcode, p, l)

    def get_pointname_relative(self, other, suffix, groupcode, collectioncode=None, l=None):
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
        name = self.get_pointname(suffix, groupcode, p, l)
        if self.corpuscode == other.corpuscode:
            full = name
        else:
            full = "../" + self.corpus_filename + "/" + name
        return full, changed

    def get_directory(self, suffix):
        return os.path.join(self.dirdict[suffix], self.corpus_filename)

    def get_filename(self, suffix, groupcode, p=None, l=None):
        return os.path.join(self.get_directory(suffix), self.get_pointname(suffix, groupcode, p, l))

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
        fig = matplotlib.pyplot.figure(
            figsize=(self.layout.width, self.layout.height),
            subplotpars=SPP
        )
        ax = fig.add_subplot(111)
        ax.set_autoscalex_on(False)
        ax.set_autoscaley_on(False)
        ax.set_xlim(lim(self.maxx))
        ax.set_ylim(lim(self.maxy))
        if self.layout.xbins != None:
            ax.locator_params(axis='x', nbins=self.layout.xbins)
        self.plot_polys(ax)
        self.plot_points(ax, points, groupcode, point)
        self.plot_labels(ax)
        for suffix in self.get_suffixes(point):
            if suffix == 'svg':
                suffix2 = 'tmp.svg'
            else:
                suffix2 = suffix
            filename = self.get_filename(suffix2, groupcode, point)
            fig.savefig(filename)
            if suffix == 'svg':
                for listing in self.listings:
                    target = self.get_filename(suffix, groupcode, point, listing)
                    self.add_svg_links(filename, target, points, groupcode, point, listing)
                os.remove(filename)
        matplotlib.pyplot.close(fig)

    def plot_polys(self, ax):
        for i, poly in enumerate(self.polys):
            f = i/(len(self.polys)-1.0)
            j = min(i, len(REGIONS)-1)
            fill = REGIONS[-(j+1)]
            ax.fill(poly[:,0], poly[:,1], fc=fill, ec=BLACK, linewidth=0.2, zorder=100 + f)

    def plot_points(self, ax, points, groupcode, point):
        placement = LabelPlacement(self.layout)
        for i, p in enumerate(points):
            scx, scy = float(p.x)/self.maxx, float(p.y)/self.maxy
            stx = scx + self.layout.xsep
            sty = placement.place(scy)
            zbase = 201.0 - p.pvalue
            if point is None:
                cp = p
            elif point == p:
                cp = self.layout.sel
                zbase += 100
            else:
                cp = self.layout.unsel
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

    def add_svg_links(self, filename, target, points, groupcode, point, listing):
        with open(filename) as f:
            svg = etree.parse(f)
        for i, p in enumerate(points):
            if point is not None and point == p:
                url = self.get_pointname('html', groupcode)
            else:
                url = self.get_pointname('html', groupcode, p, listing)
            title = self.collection_descr[p.collectioncode]
            if title is None:
                title = p.collectioncode
            for what in ['pl', 'pm', 'pt']:
                gid = 'types_%s_%d' % (what, i)
                path = ".//{http://www.w3.org/2000/svg}g[@id='%s']" % gid
                el = svg.find(path)
                if el is not None:
                    wrap_svg_link(el, url, title)
        with open(target, 'w') as f:
            svg.write(f)

    def generate_html(self, ac):
        for groupcode in sorted(self.points_by_group.keys()):
            ps = [None] + self.points_by_group[groupcode]
            for p in ps:
                for l in self.listings:
                    filename = self.get_filename('html', groupcode, p, l)
                    with open(filename, 'w') as f:
                        self.generate_html_one(f, groupcode, p, l, ac)

    def generate_html_one(self, f, groupcode, point, listing, ac):
        collectioncode = point.collectioncode if point is not None else None

        headblocks = []
        bodyblocks = []

        t = [ self.corpuscode, self.datasetcode, groupcode, collectioncode, self.statcode ]
        t = u" — ".join([a for a in t if a is not None])
        headblocks.append(E.title(t))
        headblocks.append(E.link(rel="stylesheet", href="../types.css", type="text/css"))

        def add_menu(title, cl, gl, xl, ll, labelhook, titlelink=None, groupby=None, stat=None):
            prev = []
            prevj = 0
            result = []
            count = len(cl) * len(gl) * len(xl) * len(ll)
            for c, g, x, l in itertools.product(cl, gl, xl, ll):
                addbreak = False
                label, desc = labelhook(c, g, x, l)
                selected = c == self and g is groupcode and x is collectioncode and l is listing
                if groupby is not None and count >= 5:
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
                if desc is not None:
                    attr["title"] = desc
                if selected:
                    attr["class"] = "menuitem menusel"
                    e = E.span(label, **attr)
                else:
                    href, changed = c.get_pointname_relative(self, 'html', g, x, l)
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
            [ listing ],
            lambda c, g, x, l: (c.corpuscode, c.corpus_descr),
            titlelink="../index.html",
            groupby='-'
        )
        add_menu(
            "Dataset",
            ac.by_corpus_stat[(self.corpuscode, self.statcode)],
            [ groupcode ],
            [ collectioncode ],
            [ listing ],
            lambda c, g, x, l: (c.datasetcode, c.dataset_descr)
        )
        add_menu(
            "Points",
            [ self ],
            sorted(self.groups),
            [ collectioncode ],
            [ listing ],
            lambda c, g, x, l: ("none", None) if g is None else (g, None)
        )
        add_menu(
            "Axes",
            ac.by_corpus_dataset[(self.corpuscode, self.datasetcode)],
            [ groupcode ],
            [ collectioncode ],
            [ listing ],
            lambda c, g, x, l: (
                "%s/%s" % (c.ylabel, c.xlabel),
                "y = %s, x = %s" % (c.ylabel, c.xlabel)
            )
        )
        bodyblocks.append(E.div(*menublocks, **{"class": "menu"}))

        fig = E.p(E.object(
            data=self.get_pointname('svg', groupcode, point, listing),
            type="image/svg+xml",
            width=str(self.layout.width * self.layout.dpi),
            height=str(self.layout.height * self.layout.dpi),
        ), **{"class": "plot"})
        bodyblocks.append(fig)

        menublocks = []
        add_menu(
            "Collection",
            [ self ],
            [ groupcode ],
            [ None ] + [ p.collectioncode for p in self.points_by_group[groupcode] ],
            [ listing ],
            lambda c, g, x, l: ("none", None) if x is None else (x, self.collection_descr[x])
        )
        if collectioncode is not None and self.collection_descr[collectioncode] is not None:
            menublocks.append(E.p(self.collection_descr[collectioncode], **{"class": "menudesc"}))

        if len(self.listings) > 1:
            add_menu(
                "Show",
                [ self ],
                [ groupcode ],
                [ collectioncode ],
                self.listings,
                lambda c, g, x, l: (LISTING_LABEL[l], None)
            )

        bodyblocks.append(E.div(*menublocks, **{"class": "menu"}))

        if listing is None:
            stat = []
            if collectioncode is None:
                what = []
                for total, label in [
                    (self.xtotal, self.xlabel),
                    (self.ytotal, self.ylabel),
                ]:
                    if total is not None:
                        what.append('{} {}'.format(total, label))
                if len(what) > 0:
                    stat.append(E.p("This corpus contains {}.".format(
                        ' and '.join(what)
                    )))
                bodyblocks.append(E.div(*stat, **{"class": "stats"}))
            else:
                stat.append(E.p("This collection contains {} {} and {} {}.".format(
                    point.x, self.xlabel,
                    point.y, self.ylabel
                )))
                w = "at most" if point.side == "below" else "at least"
                if point.pvalue > 0.1:
                    ppvalue = "{:.1f}%".format(100 * point.pvalue)
                elif point.pvalue > 0.01:
                    ppvalue = "{:.2f}%".format(100 * point.pvalue)
                else:
                    ppvalue = "{:.3f}%".format(100 * point.pvalue)
                stat.append(E.p(
                    ("Only approx. " if point.pvalue < 0.1 else "Approx. "),
                    E.strong(ppvalue),
                    " of random collections with {} {} contain {} {} {}.".format(
                        point.x, self.xlabel, w, point.y, self.ylabel
                    )
                ))
                if point.pvalue > 0.1:
                    stat.append(E.p(
                        "This seems to be a fairly typical collection."
                    ))
                elif point.fdr < 0:
                    stat.append(E.p(
                        "This finding is probably not interesting: ",
                        "the false discovery rate is larger than {}".format(-point.fdr)
                    ))
                else:
                    stat.append(E.p(
                        "This finding is probably interesting: ",
                        "the false discovery rate is ",
                        E.strong("smaller than {}".format(point.fdr)),
                        "."
                    ))
            bodyblocks.append(E.div(*stat, **{"class": "stats"}))
        elif listing == 't':
            typelist = ac.get_typelist(self.corpuscode, self.datasetcode, collectioncode)
            bodyblocks.append(E.div(*typelist, **{"class": "listing"}))
        elif listing == 's':
            samplelist = ac.get_samplelist(self.corpuscode, self.datasetcode, collectioncode)
            bodyblocks.append(E.div(*samplelist, **{"class": "listing"}))
        else:
            assert False

        doc = E.html(E.head(*headblocks), E.body(*bodyblocks))
        write_html(f, doc)
