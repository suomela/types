#ifndef TYPES_INPUT_H
#define TYPES_INPUT_H

#include "array.h"
#include "io.h"
#include "matrix.h"
#include "yx.h"

#define SAMPLES_WORD  word_count.data
#define SAMPLES_TOKEN types.rowsum

typedef struct {
    unsigned word;
    unsigned token;
} word_token_t;

#define WORD_TOKEN_NULL { 0, 0 }
extern const word_token_t WORD_TOKEN_NULL_C;

typedef struct {

    //// From the command line options

    myfile_t rng_state_file;
    myfile_t raw_input_file;
    myfile_t raw_output_file;

    yxbool_t curves;
    yxbool_t permtest;

    unsigned iterations;
    unsigned xres;            // WITH_CURVES
    unsigned yres;            // WITH_CURVES
    unsigned processes;
    unsigned id;

    bool progress;
    bool dense;
    bool sparse;

    //// From the input files

    matrix_t types;
    matrix_t collections;     // WITH_COLLECTIONS
    array_t word_count;       // WITH_WORD_COUNT

    //// Derived values

    word_token_t * restrict samples_word_token;     // WITH_INTERLEAVING

    x_t xmax;
    y_t ymax;

} input_t;

extern const input_t INPUT_NULL_C;

void
parse_command_line(input_t * restrict pinput, int argc, char **argv);

void
free_input(const input_t * restrict pinput);

#endif
