#include <stdio.h>
#include <stdlib.h>
#include "config.h"
#include "db2.h"
#include "version.h"

const char * const TOOL = "types-query";

_Noreturn static void
usage(void)
{
    short_version();
    printf(
        "\n"
        "Read datasets from the database.\n"
        "Store results in a machine-readable format.\n"
        "\n"
        "This is a low-level tool. See 'types-run' for a user-friendly interface.\n"
        "\n"
        "Usage: %s <VERBOSITY> <DATABASE> <CORPUSCODE> <DATASETCODE> <TARGET-FILE>\n"
        "\n"
        "VERBOSITY: 'V' for verbose, 'P' for progress information, '-' for no output\n"
        "\n",
        TOOL);
    exit(EXIT_SUCCESS);
}

int
main(int argc, char **argv)
{
    if (argc == 1) {
        usage();
    }
    if (argc != 6) {
        myerror("wrong number of parameters");
    }
    bool verbose = argv[1][0] == 'V';
    bool progress = argv[1][0] == 'P';
    const char *database = argv[2];
    const char *corpuscode = argv[3];
    const char *datasetcode = argv[4];
    const char *target_file = argv[5];

    db_open(database, false);
    db_exec("BEGIN", NOBIND);

    unsigned nsample = create_temp_sample(corpuscode);
    unsigned ncoll = create_temp_collection(corpuscode);
    unsigned ntype = create_temp_token(corpuscode, datasetcode);
    unsigned nsamplecoll = create_temp_sample_collection(corpuscode);
    unsigned nsampletype = create_temp_sample_token(corpuscode, datasetcode);

    if (verbose) {
        myinfo("%s: corpus %s, data set %s: "
               "%d samples, %d collections, %d types, %d sample-collection pairs, %d sample-type pairs",
               database, corpuscode, datasetcode, nsample, ntype, ncoll, nsamplecoll, nsampletype);
    }
    if (nsample == 0 || ntype == 0 || ncoll == 0 || nsamplecoll == 0 || nsampletype == 0) {
        myerror("%s: corpus %s, data set %s: no data", database, corpuscode, datasetcode);
    }

    myfile_t f = myopen(target_file, true);

    // Header

    myfwrite_uint(&f, INPUT_MAGIC);
    myfwrite_uint(&f, nsample);
    myfwrite_uint(&f, ncoll);
    myfwrite_uint(&f, ntype);
    myfwrite_uint(&f, nsamplecoll);
    myfwrite_uint(&f, nsampletype);

    // Data

    db_storearray(&f, nsample,     1, "SELECT wordcount FROM tmp_sample ORDER BY rowid",           NOBIND);
    db_storearray(&f, nsamplecoll, 2, "SELECT sampleid, collectionid FROM tmp_sample_collection",  NOBIND);
    db_storearray(&f, nsampletype, 3, "SELECT sampleid, typeid, tokencount FROM tmp_sample_token", NOBIND);

    myclose(&f);

    db_exec("COMMIT", NOBIND);

    if (progress) {
        fprintf(stderr, ".");
    }

    return EXIT_SUCCESS;
}
