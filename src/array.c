#include "array.h"
#include "io.h"
#include "malloc.h"
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

const array_t ARRAY_NULL_C = ARRAY_NULL;

array_t
init_array(unsigned n)
{
    array_t array = ARRAY_NULL;
    array.n = n;
    MYMALLOCZ(array.data, unsigned, array.n, 0);
    return array;
}

void
array_set(array_t * array, unsigned i, unsigned v)
{
    if (array->sum + v < array->sum) {
        myerror("overflow: the sum of elements exceeds %u", UINT_MAX);
    }
    array->sum += v;
    array->data[i] = v;
}

void
free_array(const array_t * restrict array)
{
    if (array->data) {
        free(array->data);
    }
}
