import codecs
import sys

def parse_tsv(l):
    return [ s if s != '' else None for s in l.rstrip('\r\n').split('\t') ]

def process_file(store, filename, encoding, fields, header, hook=None):
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
                store(r)
    print "%-60s %7d/%d" % (filename, relevant, total)


def import_file(conn, filename, encoding, fields, header, insert, hook=None):
    def store(r):
        try:
            conn.execute(insert, r)
        except:
            sys.stderr.write("%s\n%s\n" % (insert, str(r)))
            raise
    process_file(store, filename, encoding, fields, header, hook)

def convert_file(fin, fout, encoding, fields, header, hook=None):
    with open(fout, 'w') as f:
        def store(r):
            f.write('\t'.join(r))
            f.write('\n')
        process_file(store, fin, encoding, fields, header, hook)
