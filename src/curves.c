#include "curves.h"
#include "util.h"
#include <stdlib.h>

const grid_t GRID_NULL_C = GRID_NULL;

void
set_slot_scale(unsigned max,
               unsigned res,
               double * restrict scale,
               unsigned * restrict slots)
{
    if (max + 1 <= res) {
        *slots = max + 1;
        *scale = 1.0;
    } else {
        *slots = res;
        *scale = max;
        *scale /= (*slots - 1);
    }

    // Sanity-checking...

    unsigned t0 = get_threshold(0, *scale);
    unsigned t1 = get_threshold(1, *scale);
    unsigned tm2 = get_threshold(*slots - 2, *scale);
    unsigned tm1 = get_threshold(*slots - 1, *scale);

    assert(0 == t0);
    assert(0 < t1);
    assert(tm2 < max);
    assert(tm1 == max);

    assert(get_slot(t0,      *scale) == 0);
    assert(get_slot(t1 - 1,  *scale) == 0);
    assert(get_slot(t1,      *scale) == 1);
    assert(get_slot(tm2,     *scale) == *slots - 2);
    assert(get_slot(tm1 - 1, *scale) == *slots - 2);
    assert(get_slot(tm1,     *scale) == *slots - 1);

    assert(get_slot_up(t0,      *scale) == 0);
    assert(get_slot_up(t0 + 1,  *scale) == 1);
    assert(get_slot_up(t1,      *scale) == 1);
    assert(get_slot_up(tm2,     *scale) == *slots - 2);
    assert(get_slot_up(tm2 + 1, *scale) == *slots - 1);
    assert(get_slot_up(tm1,     *scale) == *slots - 1);
}

void
setup_grid(const input_t * restrict pinput, const plan_t * restrict pplan, grid_t * restrict pgrid)
{
    set_slot_scale(pinput->xmax.x[XTOKEN], pinput->xres, &pgrid->xscale.x[XTOKEN], &pgrid->xslots.x[XTOKEN]);
    if (pplan->requirements & WITH_WORD_COUNT) {
        set_slot_scale(pinput->xmax.x[XWORD], pinput->xres, &pgrid->xscale.x[XWORD], &pgrid->xslots.x[XWORD]);
    }
    for (unsigned y = 0; y < NY; y++) {
        set_slot_scale(pinput->ymax.y[y], pinput->yres, &pgrid->yscale.y[y], &pgrid->yslots.y[y]);
    }
    for (unsigned i = 0; i < NYX; i++) {
        pgrid->elements.yx[i] = uint_multiply(pgrid->yslots.y[YX[i].y], pgrid->xslots.x[YX[i].x], INT_MAX);
    }
}
