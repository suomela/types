#ifndef TYPES_STAT_H
#define TYPES_STAT_H

#include "yx.h"
#include <stdint.h>

typedef struct {
    unsigned lower;
    unsigned upper;
} stat_t;

typedef struct yxstat_s yxstat_t;
struct yxstat_s {
    stat_t * restrict yx[NYX];
    yx_t elements;
    yxstat_t *next;
};

#define STAT_NULL { 0, 0 }
#define YXSTAT_NULL { { FOREACH_YX(NULL) }, YX_NULL, NULL }

extern const stat_t STAT_NULL_C;
extern const yxstat_t YXSTAT_NULL_C;

yxstat_t *
alloc_stat(const yxbool_t * restrict create, const yx_t * restrict elements);

yxstat_t *
alloc_stat_uniform(const yxbool_t * restrict create, unsigned elements);

void
free_stat(const yxstat_t * restrict pyxstat);

//// Compressed file format

enum {
    STAT_END            = 0x00,         // end of file
    STAT_ZEROCOUNT_MAX  = 0xEB,         // number of zeroes, between 1 and STAT_ZEROCOUNT_MAX
    STAT_4              = 0xEC,         // next byte is aaaabbbb = (a, b)
    STAT_8              = 0xED,         // stat_8_t follows
    STAT_16             = 0xEE,         // stat_16_t follow
    STAT_32             = 0xEF,         // stat_32_t follows
    STAT_2_MASK         = 0xF0,         // 1111aabb = (a, b)
};

typedef struct {
    uint8_t lower;
    uint8_t upper;
} stat_8_t;

typedef struct {
    uint16_t lower;
    uint16_t upper;
} stat_16_t;

typedef struct {
    uint32_t lower;
    uint32_t upper;
} stat_32_t;

#endif
