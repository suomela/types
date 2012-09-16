#ifndef TYPES_ARRAY_H
#define TYPES_ARRAY_H

typedef struct {
    unsigned n;
    unsigned sum;
    unsigned * restrict data;
} array_t;

#define ARRAY_NULL { 0, 0, NULL }
extern const array_t ARRAY_NULL_C;

array_t
init_array(unsigned n);

void
array_set(array_t * restrict arary, unsigned i, unsigned v);

void
free_array(const array_t * restrict array);

#endif
