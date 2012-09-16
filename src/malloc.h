#ifndef TYPES_MALLOC_H
#define TYPES_MALLOC_H

#include "util.h"
#include <stdlib.h>

// Allocate "count" elements of "type",
// store the pointer to "target".
#define MYMALLOC(target, type, count) \
    do { \
        size_t my_count = count; \
        type *my_result = mymalloc(sizeof(type), my_count); \
        target = my_result; \
    } while (0)

// Allocate "count" elements of "type",
// initialise each element to "init",
// store the pointer to "target".
#define MYMALLOCZ(target, type, count, init) \
    do { \
        size_t my_count = count; \
        type *my_result = mymalloc(sizeof(type), my_count); \
        for (size_t my_i = 0; my_i < my_count; my_i++) { \
            my_result[my_i] = init; \
        } \
        target = my_result; \
    } while (0)

// Allocate "count1" * "count2" elements of "type",
// store the pointer to "target".
#define MYMALLOC2(target, type, count1, count2) \
    MYMALLOC(target, type, size_multiply(count1, count2))

// Allocate "count1" * "count2" elements of "type",
// initialise each element to "init",
// store the pointer to "target".
#define MYMALLOC2Z(target, type, count1, count2, init) \
    MYMALLOCZ(target, type, size_multiply(count1, count2), init)

// Allocate "a" times "b" bytes; exit with failure if out of memory.
void *
mymalloc(size_t a, size_t b);

void *
myrealloc(void *old, size_t a, size_t b);

#endif
