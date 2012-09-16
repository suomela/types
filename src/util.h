#ifndef TYPES_UTIL_H
#define TYPES_UTIL_H

#include <stdlib.h>

#define STRINGIFY2(x) #x
#define STRINGIFY(x) STRINGIFY2(x)

#define MIN(x, y) ((x) < (y) ? (x) : (y))
#define MAX(x, y) ((x) > (y) ? (x) : (y))

size_t
size_multiply(size_t a, size_t b);

unsigned
uint_multiply(unsigned a, unsigned b, unsigned max);

/*
    Split range 0..total-1 evenly in n parts:
    
    [ split(total, n, 0), split(total, n, 1) ),
    [ split(total, n, 1), split(total, n, 2) ),
    ...
    [ split(total, n, n-1), split(total, n, n) )
*/

unsigned
split(unsigned total, unsigned n, unsigned i);

#endif
