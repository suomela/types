#include "malloc.h"
#include "io.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>

size_t
size_multiply(size_t a, size_t b)
{
    size_t x = a;
    x *= b;
    if (b > 0 && x / b != a) {
        size_t limit = SIZE_MAX;
        myerror("overflow: %zu * %zu > %zu", a, b, limit);
    }
    return x;
}

unsigned
uint_multiply(unsigned a, unsigned b, unsigned max)
{
    unsigned x = a;
    x *= b;
    if (b > 0 && x / b != a) {
        myerror("overflow: %u * %u > %u", a, b, max);
    }
    if (x > max) {
        myerror("overflow: %u * %u > %u", a, b, max);
    }
    return x;
}

unsigned
split(unsigned total, unsigned n, unsigned i)
{
    assert(i <= n);
    if (i == 0) {
        return 0;
    } else if (i == n) {
        return total;
    } else {
        double a = i;
        a /= n;
        a *= total;
        unsigned x = (unsigned)(a + 0.5);
        return x;
    }
}
