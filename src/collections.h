#ifndef TYPES_COLLECTIONS_H
#define TYPES_COLLECTIONS_H

#include "input.h"

typedef struct {
    y_t y;
    x_t x;
} collection_t;

#define COLLECTION_NULL { Y_NULL, X_NULL }

extern const collection_t COLLECTION_NULL_C;

#endif
