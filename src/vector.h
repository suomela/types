#ifndef TYPES_VECTOR_H
#define TYPES_VECTOR_H

#include <limits.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>

// The size of the words that are used to store the bit vectors.
#define VECTOR_BITS 64
typedef uint_fast64_t vector_t;
#define VECTOR_ONE UINT64_C(1)
#define MSB_SHIFT 6

inline static unsigned
number_of_vectors(unsigned number_of_bits)
{
    return (number_of_bits + (VECTOR_BITS - 1)) / VECTOR_BITS;
}

// A bitmask for extracting the least significant bits of an index.
#define LSB_MASK ((VECTOR_ONE << MSB_SHIFT) - VECTOR_ONE)

inline static size_t
get_msb_index(size_t i)
{
    return i >> MSB_SHIFT;
}

inline static unsigned
get_lsb_index(size_t i)
{
    return i & LSB_MASK;
}

inline static vector_t
get_lsb_bit(size_t i)
{
    return VECTOR_ONE << get_lsb_index(i);
}

inline static bool
get_lsb_bool(vector_t v, size_t i)
{
    return (v >> get_lsb_index(i)) & 1;
}

//// Bit counting

inline static unsigned
bitcount(vector_t v)
{
#ifdef USE_BUILTIN_POPCOUNT
    return __builtin_popcountll(v);
#else
    typedef vector_t T;
    unsigned c;

    // From http://graphics.stanford.edu/~seander/bithacks.html#CountBitsSetParallel
    v = v - ((v >> 1) & (T)~(T)0/3);                           // temp
    v = (v & (T)~(T)0/15*3) + ((v >> 2) & (T)~(T)0/15*3);      // temp
    v = (v + (v >> 4)) & (T)~(T)0/255*15;                      // temp
    c = (T)(v * ((T)~(T)0/255)) >> (sizeof(T) - 1) * CHAR_BIT; // count

    return c;
#endif
}

//// Bit-parallel arithmetic on numbers 0, 1, more

typedef struct {
    vector_t at_least_1;
    vector_t at_least_2;
} zom_t;

extern const zom_t ZOM_NULL_C;


// Calculate x + y in zom_t.
inline static zom_t zom_add(zom_t x, zom_t y)
{
    zom_t z;
    z.at_least_1 = x.at_least_1 | y.at_least_1;
    z.at_least_2 = x.at_least_2 | y.at_least_2 | (x.at_least_1 & y.at_least_1);
    return z;
}

// Return a bit vector where a bit is set if the value is exactly 1.
inline static vector_t zom_exactly_1(zom_t x)
{
    return x.at_least_1 & ~x.at_least_2;
}

inline static void
vector_clear(vector_t * restrict array, size_t n)
{
    for (unsigned i = 0; i < n; i++) {
        array[i] = 0;
    }
}

inline static void
zom_clear(zom_t * restrict array, size_t n)
{
    for (unsigned i = 0; i < n; i++) {
        array[i].at_least_1 = 0;
        array[i].at_least_2 = 0;
    }
}

#endif
