#ifndef TYPES_RANDOM_H
#define TYPES_RANDOM_H

/*
    Note:
    
    Malloc and rng_state_read do not necessarily return properly aligned memory.
    However, myrand_n will expect properly aligned memory.
    Use a temporary variable as follows to solve the problem:
    
        rng_state_t *rng_state = rng_state_read(...);
        rng_state_t s = rng_state[i];
        myrand_n(&s, n);
*/

#include "io.h"
#include "SFMT.h"
#include <limits.h>
#include <stdint.h>

#if UINT32_MAX == UINT_MAX
#define my_genrand sfmt_genrand_uint32
#elif UINT64_MAX == UINT_MAX
#define my_genrand sfmt_genrand_uint64
#else
#error "'unsigned' should be either 32-bit or 64-bit"
#endif

#ifdef __GNUC__
#define my_clz __builtin_clz
#else
// A naive fallback implementation
inline static unsigned
my_clz(unsigned n)
{
    const unsigned HIGHBIT = UINT_MAX - (UINT_MAX >> 1);
    unsigned shift = 0;
    while ((n & HIGHBIT) == 0) {
        n <<= 1;
        shift++;
    }
    return shift;
}
#endif

typedef sfmt_t rng_state_t;

rng_state_t *
rng_state_read(myfile_t * restrict f);

void
rng_state_write(myfile_t * restrict f, const rng_state_t * restrict rng_state);


// Return a random unsigned integer between 0 and n-1.
inline static unsigned
myrand_n(rng_state_t * restrict rng_state, unsigned n)
{
    assert(n > 0);

    unsigned limit = n - 1;
    if (limit == 0) {
        return 0;
    }

    unsigned shift = my_clz(limit);
    assert((UINT_MAX >> shift) >= limit);
    assert(((UINT_MAX >> shift) >> 1) < limit);

    unsigned val;
    do {
        val = my_genrand(rng_state) >> shift;
    } while (val > limit);
    return val;
}

// If
//   i = get_iteration(processes, id)
//   j = get_iteration(processes, id+1),
// then process id uses RNGs i..j

unsigned
get_generator(unsigned processes, unsigned id);

// If
//   a = get_iteration(iterations, i)
//   b = get_iteration(iterations, i+1),
// then we will use RNG i for iterations in the range [a,b).

unsigned
get_iteration(unsigned iterations, unsigned part);

#endif
