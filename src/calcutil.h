#ifndef TYPES_CALCUTIL_H
#define TYPES_CALCUTIL_H

#include "permutation.h"
#include "random.h"
#include "util.h"

typedef struct {
    unsigned lower;
    unsigned upper;
} bounds_t;

#define BOUNDS_NULL { 0, 0 }

typedef struct {
    bounds_t ytype;
} type_bounds_t;

typedef struct {
    bounds_t yhapax;
} hapax_bounds_t;

typedef struct {
    bounds_t ytype;
    bounds_t yhapax;
} typehapax_bounds_t;

typedef struct {
    bounds_t ytoken;
} token_bounds_t;

inline static type_bounds_t
calculate_bounds_type_dense(const input_t * restrict pinput,
                            unsigned id,
                            vector_t * restrict accum_vector,
                            unsigned * restrict paccum_type)
{
    const vector_t * restrict vector = pinput->types.b + (size_t)id * pinput->types.nvector;

    unsigned type_total = 0;
    for (unsigned j = 0; j < pinput->types.nvector; j++) {
        accum_vector[j] |= vector[j];
        type_total += bitcount(accum_vector[j]);
    }

    assert(*paccum_type <= type_total);

    type_bounds_t r;
    r.ytype.lower = *paccum_type;
    r.ytype.upper = type_total;
    *paccum_type = type_total;

    return r;
}

inline static hapax_bounds_t
calculate_bounds_hapax_dense(const input_t * restrict pinput,
                             unsigned id,
                             zom_t * restrict accum_zom,
                             unsigned * restrict paccum_hapax)
{
    const zom_t * restrict zom = pinput->types.zom + (size_t)id * pinput->types.nvector;

    unsigned hapax_total_removed = 0;
    unsigned hapax_total_created = 0;
    unsigned hapax_total_temporary = 0;
    for (unsigned j = 0; j < pinput->types.nvector; j++) {
        const zom_t current = zom[j];
        const zom_t accum_old = accum_zom[j];
        const zom_t accum_new = zom_add(accum_old, current);
        accum_zom[j] = accum_new;

        const vector_t hapax_old = zom_exactly_1(accum_old);
        const vector_t hapax_new = zom_exactly_1(accum_new);
        const vector_t hapax_temporary = ~accum_old.at_least_1 & current.at_least_2;
        assert((hapax_old & hapax_temporary) == 0);
        assert((hapax_new & hapax_temporary) == 0);
        hapax_total_temporary += bitcount(hapax_temporary);
        hapax_total_removed += bitcount(hapax_old & ~hapax_new);
        hapax_total_created += bitcount(~hapax_old & hapax_new);
    }

    assert(*paccum_hapax >= hapax_total_removed);
    assert(*paccum_hapax + hapax_total_created + hapax_total_temporary <= pinput->types.ncol);

    hapax_bounds_t r;
    r.yhapax.lower = *paccum_hapax - hapax_total_removed;
    r.yhapax.upper = *paccum_hapax + hapax_total_created + hapax_total_temporary;
    *paccum_hapax = *paccum_hapax + hapax_total_created - hapax_total_removed;
    
    return r;
}

inline static typehapax_bounds_t
calculate_bounds_typehapax_dense(const input_t * restrict pinput,
                                 unsigned id,
                                 zom_t * restrict accum_zom,
                                 unsigned * restrict paccum_type,
                                 unsigned * restrict paccum_hapax)
{
    const zom_t * restrict zom = pinput->types.zom + (size_t)id * pinput->types.nvector;

    unsigned type_total = 0;
    unsigned hapax_total_removed = 0;
    unsigned hapax_total_created = 0;
    unsigned hapax_total_temporary = 0;
    for (unsigned j = 0; j < pinput->types.nvector; j++) {
        const zom_t current = zom[j];
        const zom_t accum_old = accum_zom[j];
        const zom_t accum_new = zom_add(accum_old, current);
        accum_zom[j] = accum_new;

        type_total += bitcount(accum_new.at_least_1);

        const vector_t hapax_old = zom_exactly_1(accum_old);
        const vector_t hapax_new = zom_exactly_1(accum_new);
        const vector_t hapax_temporary = ~accum_old.at_least_1 & current.at_least_2;
        assert((hapax_old & hapax_temporary) == 0);
        assert((hapax_new & hapax_temporary) == 0);
        hapax_total_temporary += bitcount(hapax_temporary);
        hapax_total_removed += bitcount(hapax_old & ~hapax_new);
        hapax_total_created += bitcount(~hapax_old & hapax_new);
    }

    assert(*paccum_type <= type_total);

    typehapax_bounds_t r;
    r.ytype.lower = *paccum_type;
    r.ytype.upper = type_total;
    *paccum_type = type_total;

    assert(*paccum_hapax >= hapax_total_removed);
    assert(*paccum_hapax + hapax_total_created + hapax_total_temporary <= pinput->types.ncol);

    r.yhapax.lower = *paccum_hapax - hapax_total_removed;
    r.yhapax.upper = *paccum_hapax + hapax_total_created + hapax_total_temporary;
    *paccum_hapax = *paccum_hapax + hapax_total_created - hapax_total_removed;
    
    return r;
}

inline static type_bounds_t
calculate_bounds_type_sparse(const input_t * restrict pinput,
                             unsigned id,
                             vector_t * restrict accum_vector,
                             unsigned * restrict paccum_type)
{
    unsigned ja = pinput->types.sparse_start[id];
    unsigned jb = pinput->types.sparse_start[id + 1];

    type_bounds_t r;
    r.ytype.lower = *paccum_type;
    r.ytype.upper = *paccum_type;

    for (unsigned j = ja; j < jb; j++) {
        unsigned i = pinput->types.sparse_incidence[j] >> 1;
        unsigned pos = get_msb_index(i);
        unsigned bit = get_lsb_index(i);
        vector_t mask = VECTOR_ONE << bit;

        bool old = (accum_vector[pos] & mask) >> bit;
        accum_vector[pos] |= mask;
        bool type_created = !old;

        *paccum_type += type_created;
        r.ytype.upper += type_created;
    }

    return r;
}

inline static hapax_bounds_t
calculate_bounds_hapax_sparse(const input_t * restrict pinput,
                              unsigned id,
                              zom_t * restrict accum_zom,
                              unsigned * restrict paccum_hapax)
{
    unsigned ja = pinput->types.sparse_start[id];
    unsigned jb = pinput->types.sparse_start[id + 1];

    hapax_bounds_t r;
    r.yhapax.lower = *paccum_hapax;
    r.yhapax.upper = *paccum_hapax;

    for (unsigned j = ja; j < jb; j++) {
        unsigned i = pinput->types.sparse_incidence[j] >> 1;
        bool at_least_2_this = pinput->types.sparse_incidence[j] & 1;
        unsigned pos = get_msb_index(i);
        unsigned bit = get_lsb_index(i);
        vector_t mask = VECTOR_ONE << bit;

        bool at_least_1_old = (accum_zom[pos].at_least_1 >> bit) & 1;
        bool at_least_2_old = (accum_zom[pos].at_least_2 >> bit) & 1;
        bool hapax_old = at_least_1_old && !at_least_2_old;

        bool at_least_2_new = at_least_1_old || at_least_2_this;
        bool hapax_new = !at_least_2_new;
        
        vector_t at_least_2_new_v = at_least_2_new;
        at_least_2_new_v <<= bit;

        accum_zom[pos].at_least_1 |= mask;
        accum_zom[pos].at_least_2 |= at_least_2_new_v;

        bool hapax_temporary = !at_least_1_old && at_least_2_new;
        bool hapax_removed = hapax_old && !hapax_new;
        bool hapax_created = !hapax_old && hapax_new;

        *paccum_hapax += hapax_created;
        *paccum_hapax -= hapax_removed;
        r.yhapax.lower -= hapax_removed;
        r.yhapax.upper += hapax_created;
        r.yhapax.upper += hapax_temporary;
    }

    return r;
}

inline static typehapax_bounds_t
calculate_bounds_typehapax_sparse(const input_t * restrict pinput,
                                  unsigned id,
                                  zom_t * restrict accum_zom,
                                  unsigned * restrict paccum_type,
                                  unsigned * restrict paccum_hapax)
{
    unsigned ja = pinput->types.sparse_start[id];
    unsigned jb = pinput->types.sparse_start[id + 1];

    typehapax_bounds_t r;
    r.ytype.lower = *paccum_type;
    r.ytype.upper = *paccum_type;
    r.yhapax.lower = *paccum_hapax;
    r.yhapax.upper = *paccum_hapax;

    for (unsigned j = ja; j < jb; j++) {
        unsigned i = pinput->types.sparse_incidence[j] >> 1;
        bool at_least_2_this = pinput->types.sparse_incidence[j] & 1;
        unsigned pos = get_msb_index(i);
        unsigned bit = get_lsb_index(i);
        vector_t mask = VECTOR_ONE << bit;

        bool at_least_1_old = (accum_zom[pos].at_least_1 >> bit) & 1;
        bool at_least_2_old = (accum_zom[pos].at_least_2 >> bit) & 1;
        bool hapax_old = at_least_1_old && !at_least_2_old;

        bool at_least_2_new = at_least_1_old || at_least_2_this;
        bool hapax_new = !at_least_2_new;
        
        vector_t at_least_2_new_v = at_least_2_new;
        at_least_2_new_v <<= bit;

        accum_zom[pos].at_least_1 |= mask;
        accum_zom[pos].at_least_2 |= at_least_2_new_v;

        bool type_created = !at_least_1_old;
        bool hapax_temporary = !at_least_1_old && at_least_2_new;
        bool hapax_removed = hapax_old && !hapax_new;
        bool hapax_created = !hapax_old && hapax_new;

        *paccum_type += type_created;
        *paccum_hapax += hapax_created;
        *paccum_hapax -= hapax_removed;
        r.ytype.upper += type_created;
        r.yhapax.lower -= hapax_removed;
        r.yhapax.upper += hapax_created;
        r.yhapax.upper += hapax_temporary;
    }

    return r;
}

inline static token_bounds_t
calculate_bounds_token(const input_t * restrict pinput,
                       unsigned id,
                       unsigned * restrict paccum_token)
{
    token_bounds_t r;
    r.ytoken.lower = *paccum_token;
    *paccum_token += pinput->SAMPLES_TOKEN[id];
    r.ytoken.upper = *paccum_token;
    return r;
}

#endif
