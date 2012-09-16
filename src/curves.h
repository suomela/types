#ifndef TYPES_CURVES_H
#define TYPES_CURVES_H

#include "input.h"
#include "plan.h"
#include "slot.h"
#include "yx.h"
#include <assert.h>

/*
    Buckets for single-pass permutation testing.

    Let
    
        f(i) = "a lower bound for the value in the closed range
                from threshold[i] items to threshold[i + 1] items",

        g(i) = "an upper bound for the value in the closed range
                from threshold[i] items to threshold[i + 1] items",

    Then
    
        slots[slot(get_yslot(j), i)].lower = number of permutations such that f(i) = j,
        slots[slot(get_yslot_up(j), i)].upper = number of permutations such that g(i) = j.
*/

typedef struct {
    x_t xslots;
    y_t yslots;
    xd_t xscale;
    yd_t yscale;
    yx_t elements;  // <= INT_MAX
} grid_t;

#define GRID_NULL { X_NULL, Y_NULL, XD_NULL, YD_NULL, YX_NULL }

extern const grid_t GRID_NULL_C;

void
setup_grid(const input_t * restrict pinput, const plan_t * restrict pplan, grid_t * restrict pgrid);

void
set_slot_scale(unsigned max,
               unsigned res,
               double * restrict scale,
               unsigned * restrict slots);

inline static size_t
slot(const grid_t * restrict pgrid,
     unsigned y,
     unsigned x,
     size_t yslot,
     size_t xslot)
{
    return slot_raw(pgrid->yslots.y[y], pgrid->xslots.x[x], yslot, xslot);
}

inline static unsigned
get_slot(unsigned v, double scale)
{
    return (unsigned)((v + 0.5) / scale);
}

inline static unsigned
get_slot_up(unsigned v, double scale)
{
    return (unsigned)((v - 0.5) / scale + 1.0);
}

inline static unsigned
get_threshold(unsigned i, double scale)
{
    return (unsigned)(i * scale + 0.5);
}

inline static unsigned
get_xslot(const grid_t * restrict pgrid, unsigned x, unsigned i)
{
    return get_slot(i, pgrid->xscale.x[x]);
}

inline static unsigned
get_yslot(const grid_t * restrict pgrid, unsigned y, unsigned i)
{
    return get_slot(i, pgrid->yscale.y[y]);
}

inline static unsigned
get_yslot_up(const grid_t * restrict pgrid, unsigned y, unsigned i)
{
    return get_slot_up(i, pgrid->yscale.y[y]);
}

inline static unsigned
get_xthreshold(const grid_t * restrict pgrid, unsigned x, unsigned i)
{
    return get_threshold(i, pgrid->xscale.x[x]);
}

inline static unsigned
get_ythreshold(const grid_t * restrict pgrid, unsigned y, unsigned i)
{
    return get_threshold(i, pgrid->yscale.y[y]);
}

#endif
