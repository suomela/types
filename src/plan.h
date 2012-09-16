#ifndef TYPES_PLAN_H
#define TYPES_PLAN_H

#include "input.h"
#include "alg.h"

#define WITH_CURVES         0x01
#define WITH_PERMTEST       0x02
#define WITH_WORD_COUNT     0x04
#define WITH_COLLECTIONS    0x08
#define WITH_INTERLEAVING   0x10
#define WITH_MATRIX_ZOM     0x20
#define WITH_MATRIX_BINARY  0x40

typedef struct {
    bool calg[NALG];
    bool palg[NALG];
    unsigned requirements;
} plan_t;

void
execution_plan(const input_t * restrict pinput, plan_t * restrict pplan);

#endif
