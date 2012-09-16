#ifndef TYPES_SLOT_H
#define TYPES_SLOT_H

#include <assert.h>

inline static size_t
slot_raw(size_t ny, size_t nx, size_t yslot, size_t xslot)
{
    assert(yslot < ny);
    assert(xslot < nx);
    return yslot * nx + xslot;

    // We could also use the following alternative,
    // but it is much less L1-cache-friendly.
    // return xslot * ny + yslot;
}

#endif
