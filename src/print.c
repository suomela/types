#include "print.h"
#include "config.h"
#include "util.h"

static void
write_stat_compressed(myfile_t * restrict f, const stat_t * restrict pstat, size_t n)
{
    unsigned zerocount = 0;
    for (size_t i = 0; i < n; i++) {
        const stat_t s = pstat[i];
        unsigned max = MAX(s.lower, s.upper);
        if (max == 0) {
            zerocount++;
            if (zerocount == STAT_ZEROCOUNT_MAX) {
                myfwrite_uchar(f, zerocount);
                zerocount = 0;
            }
        } else {
            if (zerocount) {
                myfwrite_uchar(f, zerocount);
                zerocount = 0;
            }
            if (max < (1<<2)) {
                unsigned v = 0;
                v |= s.lower;
                v <<= 2;
                v |= s.upper;
                v |= STAT_2_MASK;
                myfwrite_uchar(f, v);
            } else if (max < (1<<4)) {
                unsigned v = 0;
                v |= s.lower;
                v <<= 4;
                v |= s.upper;
                myfwrite_uchar(f, STAT_4);
                myfwrite_uchar(f, v);
            } else if (max < (1<<8)) {
                stat_8_t ss = { s.lower, s.upper };
                myfwrite_uchar(f, STAT_8);
                myfwrite(f, &ss, sizeof(ss), 1);
            } else if (max < (1<<16)) {
                stat_16_t ss = { s.lower, s.upper };
                myfwrite_uchar(f, STAT_16);
                myfwrite(f, &ss, sizeof(ss), 1);
            } else {
                stat_32_t ss = { s.lower, s.upper };
                myfwrite_uchar(f, STAT_32);
                myfwrite(f, &ss, sizeof(ss), 1);
            }
        }
    }
    if (zerocount) {
        myfwrite_uchar(f, zerocount);
        zerocount = 0;
    }
    myfwrite_uchar(f, STAT_END);
}

#define F (&pinput->raw_output_file)

void
print_head(input_t * restrict pinput)
{
    assert(is_open(F));

    myfwrite_uint(F, OUTPUT_MAGIC);
    myfwrite_uint(F, pinput->processes);
    myfwrite_uint(F, pinput->id);
}

void
print_permtest_one(input_t * restrict pinput,
                   const collection_t * restrict pcoll,
                   const stat_t * restrict pstat,
                   unsigned yx)
{
    if (pstat == NULL) {
        return;
    }
    if (!pinput->permtest.yx[yx]) {
        return;
    }

    const unsigned y = YX[yx].y;
    const unsigned x = YX[yx].x;

    assert(is_open(F));

    // Header

    myfwrite_uint(F, CLASS_PERMTEST);
    myfwrite_uint(F, yx);
    myfwrite_uint(F, pinput->iterations);
    myfwrite_uint(F, pinput->collections.ncol);

    // Summary
    
    for (size_t i = 0; i < pinput->collections.ncol; i++) {
        myfwrite_uint(F, pcoll[i].x.x[x]);
        myfwrite_uint(F, pcoll[i].y.y[y]);
    }

    // Data

    write_stat_compressed(F, pstat, pinput->collections.ncol);
}

void
print_curves_one(input_t * restrict pinput,
                 const grid_t * restrict pgrid,
                 const stat_t * restrict pstat,
                 unsigned yx)
{
    if (pstat == NULL) {
        return;
    }
    if (!pinput->curves.yx[yx]) {
        return;
    }

    const unsigned y = YX[yx].y;
    const unsigned x = YX[yx].x;
    const unsigned nx = pgrid->xslots.x[x];
    const unsigned ny = pgrid->yslots.y[y];

    assert(is_open(F));

    // Header

    myfwrite_uint(F, CLASS_CURVES);
    myfwrite_uint(F, yx);
    myfwrite_uint(F, pinput->iterations);
    myfwrite_uint(F, nx);
    myfwrite_uint(F, ny);

    // Thresholds

    for (unsigned i = 0; i < nx; i++) {
        myfwrite_uint(F, get_xthreshold(pgrid, x, i));
    }

    for (unsigned j = 0; j < ny; j++) {
        myfwrite_uint(F, get_ythreshold(pgrid, y, j));
    }

    // Data

    write_stat_compressed(F, pstat, size_multiply(nx, ny));
}
