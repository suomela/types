#ifndef TYPES_PERMUTATION_H
#define TYPES_PERMUTATION_H

#include "random.h"

inline static void
myswap(unsigned i, unsigned j, unsigned * restrict table)
{
    unsigned tmp = table[j];
    table[j] = table[i];
    table[i] = tmp;
}

inline static void
identity_permutation(unsigned n, unsigned * restrict table)
{
    for (unsigned i = 0; i < n; i++) {
        table[i] = i;
    }
}

inline static void
rand_permutation(rng_state_t * restrict rng_state,
                 unsigned n, unsigned * restrict table)
{
    identity_permutation(n, table);
    for (unsigned i = 0; i < n; i++) {
        unsigned j = myrand_n(rng_state, n - i) + i;
        myswap(i, j, table);
    }
}

#endif
