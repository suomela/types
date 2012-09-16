#ifndef TYPES_PRINT_H
#define TYPES_PRINT_H

#include "collections.h"
#include "curves.h"
#include "input.h"
#include "stat.h"

void
print_head(input_t * restrict pinput);

void
print_permtest_one(input_t * restrict pinput,
                   const stat_t * restrict pstat,
                   unsigned yx);

void
print_curves_one(input_t * restrict pinput,
                 const grid_t * restrict pgrid,
                 const stat_t * restrict pstat,
                 unsigned yx);

#endif
