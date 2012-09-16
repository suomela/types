#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include "config.h"
#include "db2.h"
#include "version.h"

const char * const TOOL = "types-convert";

_Noreturn static void
usage(void)
{
    short_version();
    printf(
        "\n"
        "Store plain text dataset files into the database.\n"
        "Remove any prior data related to the same <CORPUSCODE>.\n"
        "\n"
        "Usage: %s <DATABASE> <CORPUS> <DATASET> ...\n"
        "\n"
        "CORPUS:   <CORPUSCODE> <WORDCOUNT-FILE> <SAMPLE-COLLECTION-FILE>\n"
        "DATASET:  <DATASETCODE> <SAMPLE-TYPE-FILE>\n"
        "\n",
        TOOL);
    exit(EXIT_SUCCESS);
}

#define BUFLEN 200

static void
gen_code(char * restrict buf, const char * restrict kind, unsigned i, unsigned n)
{
    assert(i < n);
    int maxlen = snprintf(NULL, 0, "%u", n);
    assert(maxlen > 0);
    int result = snprintf(buf, BUFLEN, "%s-%0*u", kind, maxlen, i+1);
    if (result < 0 || result >= BUFLEN) {
        myerror("internal error while trying to generate the label for %s number %u/%u", kind, i+1, n);
    }
}

static unsigned
read_list(
    const char * restrict filename,
    const char * restrict row_sql,
    const db_param_t * restrict row_param,
    const char * restrict row_label
)
{
    myfile_t f = myopen(filename, false);
    unsigned n = (unsigned)read_int_minmax(&f, "number of elements", 1, INT_MAX);
    db_create_cache(row_sql);
    for (unsigned i = 0; i < n; i++) {
        unsigned value = (unsigned)read_int_minmax(&f, "element", 1, INT_MAX);
        char code[BUFLEN];
        gen_code(code, row_label, i, n);
        db_exec_cache(BIND(RECURSE(row_param), STRING(code), INT(value)));
    }
    read_eof(&f);
    db_close_cache();
    myclose_if_needed(&f);

    return n;
}

static unsigned
read_matrix(
    const char * restrict filename,
    unsigned nrow_expected,
    bool binary,
    const char * restrict col_sql,
    const db_param_t * restrict col_param,
    const char * restrict element_sql,
    const db_param_t * restrict element_param,
    const char * restrict row_label,
    const char * restrict col_label
)
{
    myfile_t f = myopen(filename, false);

    unsigned nrow = (unsigned)read_int_minmax(&f, "number of rows", 1, INT_MAX);
    unsigned ncol = (unsigned)read_int_minmax(&f, "number of columns", 1, INT_MAX);

    if (nrow != nrow_expected) {
        myerror("%s: expected %u rows, got %u rows", filename, nrow_expected, nrow);
    }

    if (col_sql) {
        db_create_cache(col_sql);
        for (unsigned j = 0; j < ncol; j++) {
            char col_code[BUFLEN];
            gen_code(col_code, col_label, j, ncol);
            db_exec_cache(BIND(RECURSE(col_param), STRING(col_code)));
        }
        db_close_cache();
    }

    db_create_cache(element_sql);
    int max = binary ? 1 : INT_MAX;
    unsigned zerocounter = 0;
    for (unsigned i = 0; i < nrow; i++) {
        for (unsigned j = 0; j < ncol; j++) {
            unsigned v;
            if (zerocounter > 0) {
                zerocounter--;
                v = 0;
            } else {
                int raw = read_int_minmax(&f, "element", INT_MIN, max);
                if (raw < 0) {
                    zerocounter = -(raw+1);
                    v = 0;
                } else {
                    v = (unsigned)raw;
                }
            }
            if (v > 0) {
                char row_code[BUFLEN];
                char col_code[BUFLEN];
                gen_code(row_code, row_label, i, nrow);
                gen_code(col_code, col_label, j, ncol);
                if (binary) {
                    db_exec_cache(BIND(RECURSE(element_param), STRING(row_code), STRING(col_code)));
                } else {
                    db_exec_cache(BIND(RECURSE(element_param), STRING(row_code), STRING(col_code), INT(v)));
                }
            }
        }
    }
    db_close_cache();
    read_eof(&f);
    myclose_if_needed(&f);
    
    return ncol;
}

static unsigned
read_wordcount_file(
    const char * restrict corpuscode,
    const char * restrict wordcount_file
)
{
    return read_list(
        wordcount_file,
        "INSERT INTO sample (corpuscode, samplecode, wordcount) VALUES (?, ?, ?)",
        BIND(STRING(corpuscode)),
        "sample"
    );
}

static unsigned
read_sample_collection_file(
    const char * restrict corpuscode,
    const char * restrict sample_collection_file,
    unsigned nsample
)
{
    return read_matrix(
        sample_collection_file, nsample, true,
        "INSERT INTO collection (corpuscode, collectioncode) VALUES (?, ?)",
        BIND(STRING(corpuscode)),
        "INSERT INTO sample_collection (corpuscode, samplecode, collectioncode) VALUES (?, ?, ?)",
        BIND(STRING(corpuscode)),
        "sample", "collection"
    );
}

static unsigned
read_sample_type_file(
    const char * restrict corpuscode,
    const char * restrict datasetcode,
    const char * restrict sample_type_file,
    unsigned nsample
)
{
    db_exec(
        "INSERT INTO dataset (corpuscode, datasetcode) VALUES (?, ?)",
        BIND(STRING(corpuscode), STRING(datasetcode))
    );
    return read_matrix(
        sample_type_file, nsample, false,
        NULL, NULL,
        "INSERT INTO token (corpuscode, datasetcode, samplecode, tokencode, tokencount) VALUES (?, ?, ?, ?, ?)",
        BIND(STRING(corpuscode), STRING(datasetcode)),
        "sample", "token"
    );
}

int
main(int argc, char **argv)
{
    if (argc == 1) {
        usage();
    }
    if (argc < 5 || (argc % 2) != 1) {
        myerror("wrong number of parameters");
    }
    const char *database = argv[1];
    const char *corpuscode = argv[2];
    const char *wordcount_file = argv[3];
    const char *sample_collection_file = argv[4];

    db_open(database, true);
    db_exec("BEGIN", NOBIND);
    recreate_corpus(corpuscode);
    unsigned nsample = read_wordcount_file(corpuscode, wordcount_file);
    read_sample_collection_file(corpuscode, sample_collection_file, nsample);

    for (unsigned i = 5; i+1 < argc; i += 2) {
        const char *datasetcode = argv[i];
        const char *sample_type_file = argv[i+1];
        read_sample_type_file(corpuscode, datasetcode, sample_type_file, nsample);
    }

    db_exec("COMMIT", NOBIND);
    return EXIT_SUCCESS;
}
