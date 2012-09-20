#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "config.h"
#include "db2.h"
#include "io.h"
#include "slot.h"
#include "stat.h"
#include "malloc.h"
#include "util.h"
#include "yx.h"
#include "version.h"

const char * const TOOL = "types-store";

typedef struct {
    myfile_t *files;
    const char *database;
    const char *corpuscode;
    const char *datasetcode;
    char **filenames;
    unsigned nfile;
    int64_t logid;
    unsigned nsample;
    unsigned ncoll;
    unsigned ntype;
    bool verbose;
    bool progress;
} store_t;

_Noreturn static void
usage(void)
{
    version();
    printf(
        "\n"
        "Store results in the database.\n"
        "\n"
        "This is a low-level tool. See 'types-run' for a user-friendly interface.\n"
        "\n"
        "Usage: %s <VERBOSITY> <DATABASE> <CORPUSCODE> <DATASETCODE> <SOURCE-FILE> ...\n"
        "\n"
        "VERBOSITY: 'V' for verbose, 'P' for progress information, '-' for no output\n"
        "\n",
        TOOL);
    exit(EXIT_SUCCESS);
}

static void
init(store_t * restrict s)
{
    s->nsample = create_temp_sample(s->corpuscode);
    s->ncoll   = create_temp_collection(s->corpuscode);
    s->ntype   = create_temp_token(s->corpuscode, s->datasetcode);

    if (s->verbose) {
        myinfo("corpus %s, data set %s: %d samples, %d collections, %d types",
               s->corpuscode, s->datasetcode, s->nsample, s->ntype, s->ncoll);
    }
    if (s->nsample == 0 || s->ntype == 0 || s->ncoll == 0) {
        myerror("corpus %s, data set %s: no data", s->corpuscode, s->datasetcode);
    }
}

static void
write_log(store_t * restrict s)
{
    db_exec(
        "INSERT INTO log (corpuscode, datasetcode, timestamp, description) VALUES (?, ?, datetime('now'), ?)",
        BIND(STRING(s->corpuscode), STRING(s->datasetcode), STRING(TOOL))
    );
    s->logid = db_last_insert_rowid();
}

static unsigned
read_common_uint(store_t * restrict s)
{
    unsigned v = myfread_uint(&s->files[0]);
    for (unsigned i = 1; i < s->nfile; i++) {
        unsigned v2 = myfread_uint(&s->files[i]);
        if (v != v2) {
            myerror("mismatch: %u in file %s but %u in file %s",
                    v, s->files[0].filename,
                    v2, s->files[i].filename);
        }
    }
    return v;
}

#define PRINT_STEP 10000
#define PRINT_LIMIT (5*PRINT_STEP)

static void
read_stat_sum(store_t * restrict s, stat_t * restrict stat, size_t n)
{
    bool print = n > PRINT_LIMIT && s->verbose;
    if (print) {
        fprintf(stderr, "%s: read ", TOOL);
    }
    unsigned zerocount[s->nfile];
    for (unsigned i = 0; i < s->nfile; i++) {
        zerocount[i] = 0;
    }
    for (size_t j = 0; j < n; j++) {
        if (print && j % PRINT_STEP == 0) {
            fprintf(stderr, ".");
        }
        stat[j].lower = 0;
        stat[j].upper = 0;
        for (unsigned i = 0; i < s->nfile; i++) {
            if (zerocount[i]) {
                zerocount[i]--;
            } else {
                unsigned c = myfread_uchar(&s->files[i]);
                if (c == STAT_END) {
                    myerror("%s: unexpected end-of-record indicator", s->filenames[i]);
                } else if (c <= STAT_ZEROCOUNT_MAX) {
                    zerocount[i] = c - 1;
                } else if (c >= STAT_2_MASK) {
                    stat_t ss;
                    ss.upper = c & 0x03;
                    ss.lower = (c >> 2) & 0x03;
                    stat[j].lower += ss.lower;
                    stat[j].upper += ss.upper;
                } else if (c == STAT_4) {
                    unsigned c2 = myfread_uchar(&s->files[i]);
                    stat_t ss;
                    ss.upper = c2 & 0x0F;
                    ss.lower = (c2 >> 4) & 0x0F;
                    stat[j].lower += ss.lower;
                    stat[j].upper += ss.upper;
                } else if (c == STAT_8) {
                    stat_8_t ss;
                    myfread(&s->files[i], &ss, sizeof(ss), 1);
                    stat[j].lower += ss.lower;
                    stat[j].upper += ss.upper;
                } else if (c == STAT_16) {
                    stat_16_t ss;
                    myfread(&s->files[i], &ss, sizeof(ss), 1);
                    stat[j].lower += ss.lower;
                    stat[j].upper += ss.upper;
                } else if (c == STAT_32) {
                    stat_32_t ss;
                    myfread(&s->files[i], &ss, sizeof(ss), 1);
                    stat[j].lower += ss.lower;
                    stat[j].upper += ss.upper;
                } else {
                    myerror("%s: invalid data", s->filenames[i]);
                }
            }
        }
    }
    if (print) {
        fprintf(stderr, "\n");
    }
    for (unsigned i = 0; i < s->nfile; i++) {
        if (zerocount[i] != 0) {
            myerror("%s: too much data in the record", s->filenames[i]);
        }
        unsigned c = myfread_uchar(&s->files[i]);
        if (c != STAT_END) {
            myerror("%s: too much data in the record", s->filenames[i]);
        }
    }
}

static void
read_permtest(store_t * restrict s)
{
    // Read header

    unsigned yx         = read_common_uint(s);
    unsigned iterations = read_common_uint(s);
    unsigned ncoll      = read_common_uint(s);
    
    if (s->verbose) {
        myinfo("%9s,%12s,%10u iterations,%4u collections",
               "permtest", YX[yx].label, iterations, ncoll);
    }
    if (s->database && s->ncoll != ncoll) {
        myerror("expected %u collections, got %u collections", s->ncoll, ncoll);
    }

    // Read summary

    unsigned x[ncoll];
    unsigned y[ncoll];
    for (unsigned c = 0; c < ncoll; c++) {
        x[c] = read_common_uint(s);
        y[c] = read_common_uint(s);
    }

    // Read data

    stat_t stat[ncoll];
    read_stat_sum(s, stat, ncoll);

    if (s->database) {

        // Delete old results

        db_exec(
            "DELETE FROM result_p "
            "WHERE corpuscode = ? AND datasetcode = ? AND statcode = ?",
            BIND(STRING(s->corpuscode), STRING(s->datasetcode), STRING(YX[yx].label))
        );

        // Store results in database

        db_create_cache(
            "INSERT INTO result_p "
            "(corpuscode, datasetcode, collectioncode, statcode, x, y, below, above, total, logid) "
            "SELECT ?, ?, collectioncode, ?, ?, ?, ?, ?, ?, ? "
            "FROM tmp_collection "
            "WHERE rowid = ?"
        );
        for (unsigned c = 0; c < ncoll; c++) {
            unsigned below = stat[c].lower;
            unsigned above = stat[c].upper;
            if (below > iterations || above > iterations) {
                myerror("invalid input: overflow in permtest data");
            }
            if (below + above < iterations) {
                myerror("invalid input: underflow in permtest data");
            }
            db_exec_cache(BIND(
                STRING(s->corpuscode), STRING(s->datasetcode), STRING(YX[yx].label),
                INT(x[c]), INT(y[c]), INT(below), INT(above), INT(iterations),
                INT(s->logid), INT(c+1)
            ));
        }
        db_close_cache();

    }
}

static const double levels[] = { 0.0001, 0.001, 0.01, 0.10 };
static const unsigned nlevel = sizeof(levels)/sizeof(double);

typedef struct {
    unsigned yx;
    unsigned iterations;
    unsigned nx;
    unsigned ny;
    unsigned * restrict xthreshold;
    unsigned * restrict ythreshold;
} curve_t;

typedef struct {
    unsigned * restrict lower;
    unsigned * restrict upper;
} curve_bounds_t;

static curve_bounds_t
find_curves(const curve_t * restrict curve, const stat_t * restrict stat)
{
    curve_bounds_t bounds;
    MYMALLOC(bounds.lower, unsigned, size_multiply(curve->nx, nlevel));
    MYMALLOC(bounds.upper, unsigned, size_multiply(curve->nx, nlevel));

    for (unsigned i = 0; i < curve->nx; i++) {
        unsigned cum = 0;
        unsigned next_level = 0;
        for (unsigned j = 0; j < curve->ny; j++) {
            cum += stat[slot_raw(curve->ny, curve->nx, j, i)].lower;
            if (cum > curve->iterations) {
                myerror("invalid input: overflow in curves");
            }
            double fract = (double)cum / (double)curve->iterations;
            while (next_level < nlevel && levels[next_level] < fract) {
                bounds.lower[i * nlevel + next_level] = curve->ythreshold[j];
                next_level++;
            }
        }
        if (cum < curve->iterations) {
            myerror("invalid input: underflow in curves");
        }
        assert(next_level == nlevel);

        cum = 0;
        next_level = 0;
        for (unsigned j2 = 0; j2 < curve->ny; j2++) {
            unsigned j = curve->ny - 1 - j2;
            cum += stat[slot_raw(curve->ny, curve->nx, j, i)].upper;
            if (cum > curve->iterations) {
                myerror("invalid input: overflow in curves");
            }
            double fract = (double)cum / (double)curve->iterations;
            while (next_level < nlevel && levels[next_level] < fract) {
                bounds.upper[i * nlevel + next_level] = curve->ythreshold[j];
                next_level++;
            }
        }
        if (cum < curve->iterations) {
            myerror("invalid input: underflow in curves");
        }
        assert(next_level == nlevel);
    }
    
    return bounds;
}

static void
store_curves(store_t * restrict s, const curve_t * restrict curve, unsigned * restrict bounds, const char * restrict side)
{
    db_create_cache(
        "INSERT INTO result_curve_point (curveid, x, y) "
        "VALUES (?, ?, ?)"
    );

    for (unsigned level = 0; level < nlevel; level++) {
        db_exec(
            "INSERT INTO result_curve "
            "(corpuscode, datasetcode, statcode, level, side, xslots, yslots, iterations, logid) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            BIND(
                STRING(s->corpuscode), STRING(s->datasetcode), STRING(YX[curve->yx].label),
                DOUBLE(levels[level]), STRING(side), INT(curve->nx), INT(curve->ny),
                INT(curve->iterations), INT(s->logid)
            )
        );
        int64_t curveid = db_last_insert_rowid();

        for (unsigned i = 0; i < curve->nx; i++) {
            unsigned v = bounds[i * nlevel + level];
            if (i > 0 && i + 1 < curve->nx) {
                unsigned prev = i - 1;
                unsigned next = i + 1;
                unsigned vprev = bounds[prev * nlevel + level];
                unsigned vnext = bounds[next * nlevel + level];
                if (v == vprev && v == vnext) {
                    continue;
                }
            }
            db_exec_cache(BIND(INT(curveid), INT(curve->xthreshold[i]), INT(v)));
        }
    }

    db_close_cache();
}

static void
read_curves(store_t * restrict s)
{
    // Read header

    curve_t curve;

    curve.yx         = read_common_uint(s);
    curve.iterations = read_common_uint(s);
    curve.nx         = read_common_uint(s);
    curve.ny         = read_common_uint(s);

    if (s->verbose) {
        myinfo("%9s,%12s,%10u iterations,%5u x%5u slots",
               "curves", YX[curve.yx].label, curve.iterations, curve.nx, curve.ny);
    }

    // Read thresholds

    MYMALLOC(curve.xthreshold, unsigned, curve.nx);
    MYMALLOC(curve.ythreshold, unsigned, curve.ny);
    for (unsigned j = 0; j < curve.nx; j++) {
        curve.xthreshold[j] = read_common_uint(s);
    }
    for (unsigned j = 0; j < curve.ny; j++) {
        curve.ythreshold[j] = read_common_uint(s);
    }

    // Read data

    size_t ntotal = size_multiply(curve.nx, curve.ny);
    stat_t *stat;
    MYMALLOC(stat, stat_t, ntotal);
    read_stat_sum(s, stat, ntotal);

    // Convert raw data to curves

    curve_bounds_t bounds = find_curves(&curve, stat);

    if (s->database) {

        // Delete old results

        db_exec(
            "DELETE FROM result_curve_point "
            "WHERE curveid IN "
            "(SELECT id FROM result_curve WHERE corpuscode = ? AND datasetcode = ? AND statcode = ?)",
            BIND(STRING(s->corpuscode), STRING(s->datasetcode), STRING(YX[curve.yx].label))
        );
        db_exec(
            "DELETE FROM result_curve "
            "WHERE corpuscode = ? AND datasetcode = ? AND statcode = ?",
            BIND(STRING(s->corpuscode), STRING(s->datasetcode), STRING(YX[curve.yx].label))
        );

        // Store curves in database

        store_curves(s, &curve, bounds.lower, "lower");
        store_curves(s, &curve, bounds.upper, "upper");

    }

    free(curve.xthreshold);
    free(curve.ythreshold);
    free(stat);
    free(bounds.lower);
    free(bounds.upper);
}

static void
read_file(store_t * restrict s)
{
    MYMALLOC(s->files, myfile_t, s->nfile);
    for (unsigned i = 0; i < s->nfile; i++) {
        s->files[i] = myopen(s->filenames[i], false);
        unsigned magic = myfread_uint(&s->files[i]);
        if (magic != OUTPUT_MAGIC) {
            if (magic == INPUT_MAGIC) {
                myerror("%s: wrong file format, this is an input file, not an output file",
                        s->filenames[i]);
            } else {
                myerror("%s: wrong file format, expected file type %X, got file type %X",
                        s->filenames[i], OUTPUT_MAGIC, magic);
            }
        }
    }

    unsigned processes = read_common_uint(s);
    if (processes != s->nfile) {
        myerror("%u files, but each file indicates that there were %u processes",
                s->nfile, processes);
    }
    unsigned seen[processes];
    for (unsigned i = 0; i < s->nfile; i++) {
        seen[i] = 0;
    }
    for (unsigned i = 0; i < s->nfile; i++) {
        unsigned id = myfread_uint(&s->files[i]);
        if (id < 1 || id > processes) {
            myerror("invalid input: id out of bounds");
        }
        seen[id-1]++;
    }
    for (unsigned i = 0; i < s->nfile; i++) {
        if (seen[i] != 1) {
            myerror("invalid input: there were %u files with ID %u", seen[i], i+1);
        }
    }

    bool more = true;
    while (more) {
        unsigned what = read_common_uint(s);
        switch (what) {
        case CLASS_PERMTEST:
            read_permtest(s);
            break;
        case CLASS_CURVES:
            read_curves(s);
            break;
        case CLASS_NONE:
            more = false;
            break;
        default:
            myerror("unknown class code: %u", what);
        }
    }
    for (unsigned i = 0; i < s->nfile; i++) {
        myfread_zero_exact(&s->files[i]);
        myclose(&s->files[i]);
    }
    free(s->files);
}

int
main(int argc, char **argv)
{
    if (argc == 1) {
        usage();
    }
    if (argc < 6) {
        myerror("wrong number of parameters");
    }

    store_t s;
    s.verbose = argv[1][0] == 'V';
    s.progress = argv[1][0] == 'P';
    if (strcmp(argv[2], "-") == 0) {
        s.database = NULL;
    } else {
        s.database = argv[2];
    }
    s.corpuscode = argv[3];
    s.datasetcode = argv[4];
    s.filenames = argv + 5;
    s.nfile = argc - 5;

    if (s.verbose) {
        myinfo("corpus %s, dataset %s: processing %u input files", s.corpuscode, s.datasetcode, s.nfile);
    }
    if (s.database) {
        db_open(s.database, true);
        db_exec("BEGIN", NOBIND);
        init(&s);
        write_log(&s);
    } else {
        if (s.verbose) {
            myinfo("not storing in database");
        }
    }
    read_file(&s);
    if (s.database) {
        db_exec("COMMIT", NOBIND);
    }
    if (s.verbose) {
        myinfo("all done");
    } else if (s.progress) {
        fprintf(stderr, "+");
    }

    return EXIT_SUCCESS;
}
