from collections import defaultdict
import optparse
import os
import os.path
import subprocess
import sys
import TypesDatabase

TOOL = 'types-run'
BIN_DIR = os.path.realpath(sys.path[0])
TMP_DIR = 'tmp'

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
    parser.add_option('--bindir', metavar='DIRECTORY', dest='bindir',
                      help='where to find program files [default: %default]',
                      default=BIN_DIR)
    parser.add_option('--tmpdir', metavar='FILE', dest='tmpdir',
                      help='where to store temporary files [default: %default]',
                      default=TMP_DIR)
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


class Runner:
    def __init__(self, tool, bin, cmds, args):
        self.tool = tool
        self.bin = bin
        self.fullpath = os.path.join(args.bindir, bin)
        self.cmds = cmds

    def error(self, msg):
        sys.stderr.write("%s: error: %s\n" % (self.tool, msg))
        sys.exit(1)

    def run(self):
        sys.stderr.write('%s (%d): ' % (self.bin, len(self.cmds)))
        for a in self.cmds:
            cmd = [ self.fullpath ] + [ str(i) for i in a ]
            # self.msg("run: %s" % ' '.join(cmd))
            process = subprocess.Popen(cmd)
            process.wait()
            if process.returncode != 0:
                if process.returncode > 0:
                    self.error("%s returned %d" % (self.bin, process.returncode))
                else:
                    self.error("%s received signal %d" % (self.bin, -process.returncode))
        sys.stderr.write('\n')


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

def get_output_c_file(args, i):
    return os.path.join(args.tmpdir, 'output-c-%d' % (i+1))

def get_output_p_file(args, i):
    return os.path.join(args.tmpdir, 'output-p-%d' % (i+1))

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
    Runner(TOOL, 'types-query', cmds, args).run()

def run_comp(args, task):
    cmds = []
    rngstate = os.path.join(args.bindir, 'rng-state')
    for i, corpuscode, datasetcode in task.inputs:
        k = (corpuscode, datasetcode)
        stat = task.pstat[k]
        if len(stat) > 0:
            cmd = [
                '--progress',
                '--rng-state-file', rngstate,
                '--raw-input', get_input_file(args, i),
                '--processes', 1,
                '--id', 1,
                '--raw-output', get_output_p_file(args, i),
                '--iterations', args.piter,
            ] + [ '--p-%s' % f for f in stat ]
            cmds.append(cmd)
    for i, corpuscode, datasetcode in task.inputs:
        k = (corpuscode, datasetcode)
        stat = task.cstat[k]
        if len(stat) > 0:
            cmd = [
                '--progress',
                '--rng-state-file', rngstate,
                '--raw-input', get_input_file(args, i),
                '--processes', 1,
                '--id', 1,
                '--raw-output', get_output_c_file(args, i),
                '--iterations', args.citer,
                '--x', args.x,
                '--y', args.y
            ] + [ '--%s' % f for f in stat ]
            cmds.append(cmd)
    Runner(TOOL, 'types-comp', cmds, args).run()
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
                files = [ fn(args, i) ]
                cmd = [ 'P', args.db, corpuscode, datasetcode ] + files
                cmds.append(cmd)
                all_files.extend(files)
        add(task.cstat, get_output_c_file)
        add(task.pstat, get_output_p_file)
    Runner(TOOL, 'types-store', cmds, args).run()
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
