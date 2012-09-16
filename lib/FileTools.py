import codecs
import sys

def parse_tsv(l):
    return [ s if s != '' else None for s in l.rstrip('\r\n').split('\t') ]

def import_file(conn, filename, encoding, fields, header, insert, hook=None):
    relevant, total = 0, 0
    with codecs.open(filename, 'rU', encoding) as f:
        check_header = header is not None
        for l in f:
            r = parse_tsv(l)
            r = [ r[i] for i in fields ]
            if check_header:
                assert r == header, r
                check_header = False
            else:
                total += 1
                if hook is not None:
                    r = hook(r)
                if r is None:
                    continue
                relevant += 1
                try:
                    conn.execute(insert, r)
                except:
                    sys.stderr.write("%s\n%s\n" % (insert, str(r)))
                    raise
    print "%-55s %8d/%-8d" % (filename, relevant, total)
