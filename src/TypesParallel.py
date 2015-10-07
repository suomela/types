import os
import os.path
import subprocess
import sys

BIN_DIR = 'bin'
TMP_DIR = 'tmp'
LOGIN_FILE = 'loginfile'
PARTS=1

PARALLEL = 'parallel'
MINVERSION = '20120222'


def add_options(parser):
    parser.add_option('--bindir', metavar='DIRECTORY', dest='bindir',
                      help='where to find program files [default: %default]',
                      default=BIN_DIR)
    parser.add_option('--tmpdir', metavar='FILE', dest='tmpdir',
                      help='where to store temporary files [default: %default]',
                      default=TMP_DIR)
    parser.add_option('--local', dest='locally', action='store_true',
                      help='run locally',
                      default=False)
    parser.add_option('--loginfile', metavar='FILE', dest='loginfile',
                      help='SSH login file if you want to distribute computation on multiple machines, see "parallel --sshloginfile" for more information on the file format [default: %default]',
                      default=LOGIN_FILE)
    parser.add_option('--parts', metavar='N', dest='parts', type=int,
                      help='split each execution in how many independent parts [default: %default]',
                      default=PARTS)


class Parallel:
    def __init__(self, tool, bin, cmds, args):
        self.tool = tool
        self.bin = bin
        self.fullpath = os.path.join(args.bindir, bin)
        self.cmds = cmds
        self.locally = args.locally
        self.loginfile = args.loginfile

    def msg(self, msg):
        sys.stderr.write("%s: %s\n" % (self.tool, msg))

    def error(self, msg):
        sys.stderr.write("%s: error: %s\n" % (self.tool, msg))
        sys.exit(1)

    def run_serial(self):
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

    def run_parallel(self):
        sys.stderr.write('%s [%d]: ' % (self.bin, len(self.cmds)))
        cwd = os.getcwd()
        cmd0 = [
            PARALLEL,
            '--ungroup',
            '--workdir', cwd,
            '--sshloginfile', self.loginfile,
            '--delim', '\\n',
            '--colsep', '\\t',
            '--trim', 'n',
            self.fullpath
        ]
        # self.msg("run: %s" % ' '.join(cmd0))
        process = subprocess.Popen(cmd0, stdin=subprocess.PIPE)
        for a in self.cmds:
            b = [ str(i) for i in a ]
            # self.msg("queue: %s" % ' '.join(b))
            process.stdin.write('\t'.join(b))
            process.stdin.write('\n')
        process.stdin.close()
        process.wait()
        sys.stderr.write('\n')
        if process.returncode != 0:
            if process.returncode > 0:
                self.error("%d child processes failed" % process.returncode)
            else:
                self.error("%s received signal %d" % (PARALLEL, -process.returncode))

    def parallel_ok(self):
        cmd = [ PARALLEL, '--minversion', MINVERSION ]
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        except:
            return False
        process.communicate()
        return process.returncode == 0

    def run(self):
        if self.locally:
            self.run_serial()
        elif not os.path.exists(self.loginfile):
            if self.loginfile != LOGIN_FILE:
                self.msg("login file %s missing, running locally" % self.loginfile)
            self.run_serial()
        elif not self.parallel_ok():
            self.msg("could not find GNU parallel version %s or later, running locally" % MINVERSION)
            self.run_serial()
        else:
            self.run_parallel()
