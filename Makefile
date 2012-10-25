###
### Compilation:
###
###     ./config
###     make
###     make check
###

config = etc/config.inc
include $(config)

sfmt = external/SFMT-src-1.4

### Modules

#--- Programs

prog_py = types-db-init types-db-refresh types-draw-curves types-plot types-run
prog_db = types-convert types-query types-store
prog_other = types-comp types-rng 
mod_py = TypesDatabase TypesParallel TypesPlot TypesVersion
mod_comp = types-comp array calculate collections curves driver input io malloc matrix plan print random read stat util vector version yx SFMT
mod_rng = types-rng io jump malloc random seed util version SFMT SFMT-jump
mod_convert = types-convert db db2 io util version
mod_query = types-query db db2 io util version
mod_store = types-store db db2 io malloc util version yx
mod_unittest = unittest io malloc random util SFMT version

#--- All modules

#--- Generated source files

jump = jump.c jump.h
seed = seed.c seed.h
gen = alg.h calculate.c calculate.h yx.c yx.h $(jump) $(seed)

### Derived values

bin_py = $(prog_py:%=bin/%)
bin_py_debug = $(prog_py:%=debug/%)
lib_py = $(mod_py:%=bin/%.py)
lib_py_debug = $(mod_py:%=debug/%.py)
bin_other = build/unittest $(prog_other:%=bin/%)
bin_other_debug = debug/unittest $(prog_other:%=debug/%)
bin_db = $(prog_db:%=bin/%)
bin_db_debug = $(prog_db:%=debug/%)
bin = $(bin_py) $(lib_py) $(bin_other) $(bin_db)
bin_debug = $(bin_py_debug) $(lib_py_debug) $(bin_other_debug) $(bin_db_debug)

mod = $(sort $(mod_comp) $(mod_rng) $(mod_convert) $(mod_query) $(mod_store) $(mod_unittest))
dep = $(mod:%=dep/%.d)
obj = $(mod:%=build/%.o)
obj_debug = $(mod:%=debug/%.o)
gensrc = $(gen:%=src/%)
jumpsrc = $(jump:%=src/%)
seedsrc = $(seed:%=src/%)

jumptable = code-gen/JumpTable.py
calcjump = code-gen/calc-jump
characteristic = code-gen/characteristic.$(MEXP).txt

state = bin/rng-state
state_debug = debug/rng-state

### Targets

.PHONY: build debug bin check debug-check valgrind-check unittest debug-unittest valgrind-unittest jumptable clean veryclean

all: build

build: $(bin) $(state)

bin: $(bin)

debug: $(bin_debug)

### Rng state

$(state): bin/types-rng
	$< $@

$(state_debug): debug/types-rng
	$< $@

### Binaries

build/unittest: $(mod_unittest:%=build/%.o)
bin/types-comp: $(mod_comp:%=build/%.o)
bin/types-rng: $(mod_rng:%=build/%.o)
bin/types-convert: $(mod_convert:%=build/%.o)
bin/types-query: $(mod_query:%=build/%.o)
bin/types-store: $(mod_store:%=build/%.o)

debug/unittest: $(mod_unittest:%=debug/%.o)
debug/types-comp: $(mod_comp:%=debug/%.o)
debug/types-rng: $(mod_rng:%=debug/%.o)
debug/types-convert: $(mod_convert:%=debug/%.o)
debug/types-query: $(mod_query:%=debug/%.o)
debug/types-store: $(mod_store:%=debug/%.o)

build/unittest:

$(bin_py): bin/%: src/%.py
	mkdir -p $(@D)
	echo "#!$(PYTHON)" > $@
	cat $< >> $@
	chmod +x $@

$(bin_py_debug): debug/%: src/%.py
	mkdir -p $(@D)
	echo "#!$(PYTHON)" > $@
	cat $< >> $@
	chmod +x $@

$(lib_py): bin/%.py: src/%.py
	mkdir -p $(@D)
	cp $< $@

$(lib_py_debug): debug/%.py: src/%.py
	mkdir -p $(@D)
	cp $< $@

$(bin_other):
	mkdir -p $(@D)
	$(CC) $(LDFLAGS) $+ $(LOADLIBES) $(LDLIBS) -o $@

$(bin_other_debug):
	mkdir -p $(@D)
	$(CC) $(LDFLAGSD) $+ $(LOADLIBESD) $(LDLIBSD) -o $@

$(bin_db):
	mkdir -p $(@D)
	$(CC) $(LDFLAGS) $+ $(LOADLIBES) $(LDLIBS) $(LDLIBSDB) -o $@

$(bin_db_debug):
	mkdir -p $(@D)
	$(CC) $(LDFLAGSD) $+ $(LOADLIBESD) $(LDLIBSD) $(LDLIBSDB) -o $@

### Object files

$(obj) $(obj_debug): $(config)

$(obj): build/.dir

$(obj_debug): debug/.dir

$(obj): build/%.o: src/%.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@

$(obj_debug): debug/%.o: src/%.c
	$(CC) $(CPPFLAGSD) $(CFLAGSD) -c $< -o $@

### Automatic dependency tracking

$(dep): $(gensrc)

$(dep): $(config)

$(dep): dep/%.d: src/%.c dep/.dir
	$(CC) -MT "$(@:dep/%.d=build/%.o) $(@:dep/%.d=debug/%.o) $@" -MM $(CFLAGSM) $(CPPFLAGSM) $< > $@

### Code generation

$(gensrc): code-gen/src-gen $(config)
	$(PYTHON) code-gen/src-gen $@

$(seedsrc): etc/seed

#----
# Formally, we should have the following dependency:
#
#     $(jumpsrc): $(jumptable)
#
# However, we will only re-generate $(jumptable) manually,
# using the following target, and keep it in git.
#----

jumptable: $(jumptable)

$(jumptable): code-gen/jump-gen $(calcjump) $(characteristic) $(config)
	 $(PYTHON) code-gen/jump-gen $(MEXP) $(calcjump) $(characteristic) $@

$(calcjump):
	make -C $(sfmt)/jump calc-jump
	cp -p $(sfmt)/jump/calc-jump $@

$(characteristic):
	cp -p $(sfmt)/jump/characteristic.$(MEXP).txt $@

### Directory generation

%/.dir:
	mkdir -p $(@D)
	touch $@

### Testing

unittest: build/unittest $(state)
	build/unittest $(state)

debug-unittest: debug/unittest $(state_debug)
	debug/unittest $(state_debug)

valgrind-unittest: debug/unittest $(state_debug)
	valgrind debug/unittest $(state_debug)

check: $(bin) $(state) unittest
	check/run bin

debug-check: $(bin_debug) $(state_debug) debug-unittest
	check/run debug

valgrind-check: $(bin_debug) $(state_debug) valgrind-unittest
	check/run debug valgrind

### Cleanup

veryclean: clean $(config)
	rm -f $(jumptable) $(calcjump) $(characteristic) $(sfmt)/jump/calc-jump

clean:
	rm -f code-gen/*.pyc lib/*.pyc
	rm -f $(gensrc) $(sfmt)/jump/calc-jump
	rm -rf bin build debug dep tmp

ifneq ($(MAKECMDGOALS),clean)
  ifneq ($(MAKECMDGOALS),veryclean)
    ifneq ($(MAKECMDGOALS),jumptable)
      include $(dep)
    endif
  endif
endif
