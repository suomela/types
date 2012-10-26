from collections import defaultdict
import optparse
import os
import os.path
import subprocess
import sys
import TypesDatabase
import TypesParallel

TOOL = 'types-run'

CITER=1000000
PITER=100000000
X_DEF=1000
Y_DEF=1000

def msg(msg):
    sys.stderr.write("%s: %s\n" % (TOOL, msg))

def get_args():
    parser = optparse.OptionParser(
        description='Initialise the database and calculate all statistics.',
        version=TypesDatabase.version_string(TOOL),
    )
    parser.add_option('--db', metavar='FILE', dest='db',
                      help='which database to read [default: %default]',
                      default=TypesDatabase.DEFAULT_FILENAME)
    TypesParallel.add_options(parser)
    parser.add_option('--dry-run', dest='dryrun', action='store_true',
                      help='initialise the database if needed, but do not run calculation; just tell what would happen',
                      default=False)
    parser.add_option('--recalc', dest='recalc', action='store_true',
                      help='recalculate even if results already exist',
                      default=False)
    parser.add_option('--conly', dest='p', action='store_false',
                      help='only curves [default: curves and permutation testing]',
                      default=True)
    parser.add_option('--ponly', dest='c', action='store_false',
                      help='only permutation testing',
                      default=True)
    parser.add_option('--citer', metavar='N', dest='citer', type=int,
                      help='number of iterations for curves [default: %default]',
                      default=CITER)
    parser.add_option('--piter', metavar='N', dest='piter', type=int,
                      help='number of iterations for permutation testing [default: %default]',
                      default=PITER)
    parser.add_option('--x', metavar='N', dest='x',
                      help='maximum x resolution (number of slots) [default: %default]',
                      default=X_DEF)
    parser.add_option('--y', metavar='N', dest='y',
                      help='maximum y resolution (number of slots) [default: %default]',
                      default=Y_DEF)
    (options, args) = parser.parse_args()
    return options


class Task:
    def __init__(self):
        self.sizes = dict()
        self.pstat = defaultdict(list)
        self.cstat = defaultdict(list)

    def add(self, corpuscode, datasetcode, samplecount):
        k = (corpuscode, datasetcode)
        if k in self.sizes:
            assert self.sizes[k] == samplecount
        else:
            self.sizes[k] = samplecount

    def add_p(self, corpuscode, datasetcode, statcode, samplecount):
        self.add(corpuscode, datasetcode, samplecount)
        self.pstat[(corpuscode, datasetcode)].append(statcode)

    def add_c(self, corpuscode, datasetcode, statcode, samplecount):
        self.add(corpuscode, datasetcode, samplecount)
        self.cstat[(corpuscode, datasetcode)].append(statcode)

    def prepare(self):
        self.inputs = []
        l = sorted(self.sizes.iteritems(), key=lambda x:(-x[1],x[0]))
        for i, p in enumerate(l):
            k, size = p
            corpuscode, datasetcode = k
            self.inputs.append((i, corpuscode, datasetcode))


def find_all(conn, args, task):
    r = conn.execute('''
        SELECT dataset.corpuscode, datasetcode, statcode, samplecount
        FROM dataset
        JOIN defaultstat
        JOIN view_corpus USING (corpuscode)
    ''')
    for corpuscode, datasetcode, statcode, samplecount in r:
        if args.p:
            task.add_p(corpuscode, datasetcode, statcode, samplecount)
        if args.c:
            task.add_c(corpuscode, datasetcode, statcode, samplecount)

def find_missing(conn, args, task):
    if args.c:
        r = conn.execute('''
            SELECT corpuscode, datasetcode, statcode, samplecount
            FROM view_missing_curve
            JOIN view_corpus USING (corpuscode)
            GROUP BY corpuscode, datasetcode, statcode, samplecount
        ''')
        for corpuscode, datasetcode, statcode, samplecount in r:
            task.add_c(corpuscode, datasetcode, statcode, samplecount)

    if args.p:
        r = conn.execute('''
            SELECT corpuscode, datasetcode, statcode, samplecount
            FROM view_missing_p
            JOIN view_corpus USING (corpuscode)
            GROUP BY corpuscode, datasetcode, statcode, samplecount
        ''')
        for corpuscode, datasetcode, statcode, samplecount in r:
            task.add_p(corpuscode, datasetcode, statcode, samplecount)

def init_and_get_task(args):
    conn = TypesDatabase.open_db(args.db)
    TypesDatabase.create_if_needed(conn)
    task = Task()
    if args.recalc:
        find_all(conn, args, task)
    else:
        find_missing(conn, args, task)
    conn.commit()
    task.prepare()
    return task

def get_input_file(args, i):
    return os.path.join(args.tmpdir, 'input-%d' % (i+1))

def get_output_c_file(args, i, j):
    return os.path.join(args.tmpdir, 'output-c-%d-%d' % (i+1, j+1))

def get_output_p_file(args, i, j):
    return os.path.join(args.tmpdir, 'output-p-%d-%d' % (i+1, j+1))

def print_tasks(args, task):
    for i, corpuscode, datasetcode in task.inputs:
        k = (corpuscode, datasetcode)
        pstat = task.pstat[k]
        cstat = task.cstat[k]
        stats = [ 'c-%s' % s for s in cstat ] + [ 'p-%s' % s for s in pstat ]
        print "%s %s: %s" % (corpuscode, datasetcode, ' '.join(stats))

def run_query(args, task):
    cmds = []
    for i, corpuscode, datasetcode in task.inputs:
        cmd = [ 'P', args.db, corpuscode, datasetcode, get_input_file(args, i) ]
        cmds.append(cmd)
    TypesParallel.Parallel(TOOL, 'types-query', cmds, args).run_serial()

def run_comp(args, task):
    cmds = []
    rngstate = os.path.join(args.bindir, 'rng-state')
    for i, corpuscode, datasetcode in task.inputs:
        k = (corpuscode, datasetcode)
        stat = task.pstat[k]
        if len(stat) > 0:
            for j in range(args.parts):
                cmd = [
                    '--progress',
                    '--rng-state-file', rngstate,
                    '--raw-input', get_input_file(args, i),
                    '--processes', args.parts,
                    '--id', j+1,
                    '--raw-output', get_output_p_file(args, i, j),
                    '--iterations', args.piter,
                ] + [ '--p-%s' % f for f in stat ]
                cmds.append(cmd)
    for i, corpuscode, datasetcode in task.inputs:
        k = (corpuscode, datasetcode)
        stat = task.cstat[k]
        if len(stat) > 0:
            for j in range(args.parts):
                cmd = [
                    '--progress',
                    '--rng-state-file', rngstate,
                    '--raw-input', get_input_file(args, i),
                    '--processes', args.parts,
                    '--id', j+1,
                    '--raw-output', get_output_c_file(args, i, j),
                    '--iterations', args.citer,
                    '--x', args.x,
                    '--y', args.y
                ] + [ '--%s' % f for f in stat ]
                cmds.append(cmd)
    TypesParallel.Parallel(TOOL, 'types-comp', cmds, args).run()
    for i, corpuscode, datasetcode in task.inputs:
        os.remove(get_input_file(args, i))

def store(args, corpuscode, datasetcode, files):
    bin = os.path.join(args.bindir, 'types-store')
    cmd = [ bin, args.db, corpuscode, datasetcode ] + files
    subprocess.check_call(cmd)
    for f in files:
        os.remove(f)

def run_store(args, task):
    all_files = []
    cmds = []
    for i, corpuscode, datasetcode in task.inputs:
        def add(check, fn):
            k = (corpuscode, datasetcode)
            if len(check[k]) > 0:
                files = [ fn(args, i, j) for j in range(args.parts) ]
                cmd = [ 'P', args.db, corpuscode, datasetcode ] + files
                cmds.append(cmd)
                all_files.extend(files)
        add(task.cstat, get_output_c_file)
        add(task.pstat, get_output_p_file)
    TypesParallel.Parallel(TOOL, 'types-store', cmds, args).run_serial()
    for f in all_files:
        os.remove(f)

def postprocess(args):
    conn = TypesDatabase.open_db(args.db)
    TypesDatabase.refresh_result(conn)
    conn.commit()

def main():
    args = get_args()
    task = init_and_get_task(args)
    if len(task.inputs) == 0:
        msg('database up to date')
    elif args.dryrun:
        print_tasks(args, task)
    else:
        if not os.path.exists(args.tmpdir):
            os.makedirs(args.tmpdir)
        run_query(args, task)
        run_comp(args, task)
        run_store(args, task)
        postprocess(args)
        msg('all done')

main()
