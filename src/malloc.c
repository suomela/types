#include "malloc.h"
#include "io.h"
#include <stdint.h>
#include <stdio.h>

void *
mymalloc(size_t a, size_t b)
{
    const size_t s = size_multiply(a, b);
    void * restrict p = malloc(s);
    if (p == NULL) {
        myerror("malloc failed (%zu bytes)", s);
    }
    return p;
}

void *
myrealloc(void *old, size_t a, size_t b)
{
    const size_t s = size_multiply(a, b);
    void *p = realloc(old, s);
    if (p == NULL) {
        myerror("realloc failed (%zu bytes)", s);
    }
    return p;
}
