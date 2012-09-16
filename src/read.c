#include "read.h"
#include "array.h"
#include "config.h"
#include "io.h"
#include "malloc.h"
#include "matrix.h"
#include <assert.h>

static void
sparsify(input_t * restrict pinput, const plan_t * restrict pplan)
{
    if (pplan->requirements & (WITH_MATRIX_BINARY | WITH_MATRIX_ZOM)) {
        double dense_size = (double)pinput->types.nrow * (double)pinput->types.ncol;
        double sparse_size = (double)pinput->types.nrow + (double)pinput->types.nnonzero;
        double ratio = dense_size / sparse_size;
        if (!pinput->dense && !pinput->sparse) {
            if (ratio > SPARSITY_HEURISTIC) {
                pinput->sparse = true;
            } else {
                pinput->dense = true;
            }
        }
        if (pinput->sparse) {
            init_sparse_matrix(&pinput->types);
        }
    }
}

void
read_raw_input(input_t * restrict pinput, const plan_t * restrict pplan)
{

#define F (&pinput->raw_input_file)

    assert(is_open(F));

    unsigned magic = myfread_uint(F);
    if (magic != INPUT_MAGIC) {
        if (magic == OUTPUT_MAGIC) {
            myerror("%s: wrong file format, this is an output file, not an input file", (F)->filename);
        } else {
            myerror("%s: wrong file format, expected file type %X, got file type %X", (F)->filename, INPUT_MAGIC, magic);
        }
    }

    unsigned nsample     = myfread_uint(F);
    unsigned ncoll       = myfread_uint(F);
    unsigned ntype       = myfread_uint(F);
    unsigned nsamplecoll = myfread_uint(F);
    unsigned nsampletype = myfread_uint(F);

    assert(nsample > 0);
    assert(ncoll > 0);
    assert(ntype > 0);
    assert(nsamplecoll > 0);
    assert(nsampletype > 0);

    pinput->word_count = init_array(nsample);
    for (unsigned i = 0; i < nsample; i++) {
        unsigned v =  myfread_uint(F);
        array_set(&pinput->word_count, i, v);
    }

    pinput->collections = init_matrix(nsample, ncoll, true, false, false);
    for (unsigned i = 0; i < nsamplecoll; i++) {
        unsigned sampleid = myfread_uint(F);
        unsigned collid   = myfread_uint(F);
        assert(0 < sampleid && sampleid <= nsample);
        assert(0 < collid && collid <= ncoll);
        matrix_set(&pinput->collections, sampleid - 1, collid - 1, 1);
    }

    pinput->types = init_matrix(
        nsample, ntype,
        (pplan->requirements & WITH_MATRIX_BINARY) > 0,
        (pplan->requirements & WITH_MATRIX_ZOM) > 0,
        true
    );
    for (unsigned i = 0; i < nsampletype; i++) {
        unsigned sampleid = myfread_uint(F);
        unsigned typeid   = myfread_uint(F);
        unsigned v        = myfread_uint(F);
        assert(0 < sampleid && sampleid <= nsample);
        assert(0 < typeid && typeid <= ntype);
        assert(v > 0);
        matrix_set(&pinput->types, sampleid - 1, typeid - 1, v);
    }
    myfread_zero_exact(F);
    myclose_if_needed(F);

    pinput->xmax.x[XTOKEN] = pinput->types.sum;
    pinput->ymax.y[YTYPE]  = pinput->types.ncol;
    pinput->ymax.y[YHAPAX] = pinput->types.ncol;
    pinput->ymax.y[YTOKEN] = pinput->types.sum;
    pinput->xmax.x[XWORD]  = pinput->word_count.sum;

    sparsify(pinput, pplan);

#undef F

}

void
postprocess_type_word_count(input_t * restrict pinput, const plan_t * restrict pplan)
{
    if (!(pplan->requirements & WITH_WORD_COUNT)) {
        return;
    }
    
    if (pinput->types.nrow != pinput->word_count.n) {
        myerror("the number of rows in the sample-type matrix was %u, "
                "and the number of elements in the word count file was %u",
                pinput->types.nrow, pinput->word_count.n);
    }

    if (pplan->requirements & WITH_INTERLEAVING) {
        MYMALLOCZ(pinput->samples_word_token, word_token_t, pinput->types.nrow, WORD_TOKEN_NULL_C);
        for (unsigned i = 0; i < pinput->types.nrow; i++) {
            pinput->samples_word_token[i].word = pinput->SAMPLES_WORD[i];
            pinput->samples_word_token[i].token = pinput->SAMPLES_TOKEN[i];
        }
    }
}

void
postprocess_collections(input_t * restrict pinput, const plan_t * restrict pplan)
{
    if (!(pplan->requirements & WITH_COLLECTIONS)) {
        return;
    }

    if (pinput->types.nrow != pinput->collections.nrow) {
        myerror("the number of rows in the sample-type matrix was %u, "
                "and the number of rows in the sample-collection matrix was %u",
                pinput->types.nrow, pinput->collections.nrow);
    }
}
