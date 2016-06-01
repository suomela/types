# coding=utf-8

import json
import optparse
import os
import shutil
import sqlite3
import sys
import TypesDatabase

TOOL = 'types-web'
BIN_DIR = 'bin'
DEFAULT_SRC = os.path.realpath(os.path.join(sys.path[0], '..', 'ui'))
DEFAULT_DEST = 'web'

what = [
    ('label', ['labelcode'], [], [], 'normal'),
    ('stat', ['statcode'], [], [], 'normal'),
    ('defaultstat', ['statcode'], [], [], 'set'),
    ('corpus', ['corpuscode'], [], [], 'normal'),
    ('dataset', ['corpuscode', 'datasetcode'], [], [], 'normal'),
    ('sample', ['corpuscode', 'samplecode'], [], [], 'normal'),
    ('collection', ['corpuscode', 'collectioncode'], [], [], 'normal'),
    ('sample_collection', ['corpuscode', 'collectioncode', 'samplecode'], [], [], 'set'),
    ('token', ['corpuscode', 'datasetcode', 'samplecode', 'tokencode'], [], [], 'normal'),
    ('tokeninfo', ['corpuscode', 'datasetcode', 'tokencode'], [], [], 'normal'),
    ('context', ['corpuscode', 'datasetcode', 'samplecode', 'tokencode'], [], [], 'multi'),
    ('result_p', ['corpuscode', 'datasetcode', 'collectioncode', 'statcode'], ['id', 'logid'], [], 'normal'),
    ('result_q', ['i'], [], [], 'normal'),
    ('result_curve', ['corpuscode', 'datasetcode', 'statcode', 'level', 'side'], ['logid'], [], 'normal'),
    ('result_curve_point', ['curveid'], [], ['x'], 'multi'),
]

def msg(msg):
    sys.stderr.write("%s: %s\n" % (TOOL, msg))

def get_args():
    parser = optparse.OptionParser(
        description='Generate web user interface.',
        version=TypesDatabase.version_string(TOOL),
    )
    parser.add_option('--db', metavar='FILE', dest='db',
                      help='which database to read [default: %default]',
                      default=TypesDatabase.DEFAULT_FILENAME)
    parser.add_option('--srcdir', metavar='FILE', dest='srcdir',
                      help='HTML source directory [default: %default]',
                      default=DEFAULT_SRC)
    parser.add_option('--destdir', metavar='FILE', dest='destdir',
                      help='HTML targer directory [default: %default]',
                      default=DEFAULT_DEST)
    (options, args) = parser.parse_args()
    return options

def dump(data, conn, table, keys, skip, sort, kind):
    assert table not in data
    d = {}
    data[table] = d

    r = list(conn.execute('''
        SELECT COUNT(*)
        FROM sqlite_master
        WHERE type='table' AND name=?
    ''', [table]))
    if r[0][0] == 0:
        return

    r = conn.execute(
        'SELECT * FROM ' + table + ' ORDER BY ' + ','.join(keys + sort)
    )
    key_columns = []
    plain_columns = []
    key_map = {}
    for j,key in enumerate(keys):
        key_columns.append(None)
        key_map[key] = j
    for i,x in enumerate(r.description):
        column = x[0]
        if column in key_map:
            j = key_map[column]
            assert key_columns[j] is None
            key_columns[j] = i
        elif column in skip:
            pass
        else:
            plain_columns.append((i, column))

    for j,key in enumerate(keys):
        assert key_columns[j] is not None, (table, key)

    if kind == 'set':
        assert len(plain_columns) == 0
    else:
        assert len(plain_columns) > 0

    for row in r:
        p = d
        if kind == 'normal':
            for j,key in enumerate(keys):
                v = row[key_columns[j]]
                if v not in p:
                    p[v] = {}
                p = p[v]
            assert len(p) == 0
            for i,column in plain_columns:
                v = row[i]
                if v is not None:
                    p[column] = v
        elif kind == 'multi':
            for j,key in enumerate(keys[:-1]):
                v = row[key_columns[j]]
                if v not in p:
                    p[v] = {}
                p = p[v]
            v = row[key_columns[-1]]
            if v not in p:
                p[v] = []
            p = p[v]
            p2 = {}
            p.append(p2)
            p = p2
        elif kind == 'set':
            for j,key in enumerate(keys[:-2]):
                v = row[key_columns[j]]
                if v not in p:
                    p[v] = {}
                p = p[v]
            if len(key_columns) > 1:
                v = row[key_columns[-2]]
            else:
                v = 'v'
            if v not in p:
                p[v] = []
            p = p[v]
            v = row[key_columns[-1]]
            assert v not in p
            p.append(v)
        else:
            assert False, kind

        if kind != 'set':
            for i,column in plain_columns:
                v = row[i]
                if v is not None:
                    p[column] = v

def main():
    args = get_args()
    conn = TypesDatabase.open_db(args.db)
    data = {}

    s = args.srcdir
    d = args.destdir
    if not os.path.exists(d):
        print d
        os.makedirs(d)

    for fn in os.listdir(s):
        if fn.startswith('.'):
            continue
        print fn
        shutil.copy2(os.path.join(s, fn), os.path.join(d, fn))

    for w in what:
        dump(data, conn, *w)
    fn = "types-data.js"
    print(fn)
    jsfile = os.path.join(d, fn)
    with open(jsfile, "w") as f:
        f.write('types.data(')
        f.write(json.dumps(data, sort_keys=True, separators=(',', ':')))
        f.write(')')

main()
