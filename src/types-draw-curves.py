import sys
if len(sys.argv) > 1:
    sys.stderr.write('(')

import cPickle
import os
import os.path
import multiprocessing
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot
sys.path.append('lib')
import TypesPlot

if len(sys.argv) == 1:
    print "This tool is for internal use only."
    print "See 'types-plot' for the user-friendly interface."
    sys.exit(0)

def get_limit(nredraw, nproc, id):
    assert 0 <= id <= nproc
    if nredraw == nproc:
        return id
    elif id == 0:
        return 0
    elif id == nproc:
        return nredraw
    else:
        frac = float(id) / float(nproc)
        return int(nredraw * frac)

def load():
    with open(datafile) as f:
        redraw = cPickle.load(f)
    return redraw

def do_plot(i):
    c, outdated = redraw[i]
    c.plot_group(matplotlib, outdated)
    sys.stderr.write('.')
    return True

dummy, datafile, nredraw, nproc, id = sys.argv
nredraw, nproc, id = [ int(a) for a in [ nredraw, nproc, id ]]
assert 1 <= id <= nproc
id -= 1

fro = get_limit(nredraw, nproc, id)
to = get_limit(nredraw, nproc, id+1)
if fro == to:
    sys.exit(0)

redraw = load()
sys.stderr.write('!')

pool = multiprocessing.Pool()
results = []
for i in range(fro, to):
    results.append(pool.apply_async(do_plot, [i]))
pool.close()
pool.join()
for r in results:
    assert r.get()
sys.stderr.write(')')
