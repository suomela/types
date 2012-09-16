#ifndef TYPES_MATRIX_H
#define TYPES_MATRIX_H

#include "vector.h"

typedef struct {
    unsigned nrow;    // 1 .. INT_MAX
    unsigned ncol;    // 1 .. INT_MAX
    unsigned nvector;
    unsigned nnonzero;
    unsigned sum;
    unsigned * restrict rowsum;
    vector_t * restrict b;
    zom_t * restrict zom;

    // Let j = sparse_start[i], and k = sparse_start[i+1].
    // Then sparse_incidence[j], sparse_incidence[j+1], ..., sparse_incidence[k-1]
    // contain the non-zero entries of row i:
    // - Lowest-order bit = 1 if the value is > 1.
    // - Higher-order bits contain the column number.
    // Array sparse_start is safe to over-index by 1.
    unsigned * restrict sparse_incidence;
    unsigned * restrict sparse_start;
} matrix_t;

#define MATRIX_NULL { 0, 0, 0, 0, 0, NULL, NULL, NULL, NULL, NULL }
extern const matrix_t MATRIX_NULL_C;

inline static size_t
matrix_pos(const matrix_t * restrict matrix, unsigned row, unsigned col)
{
    return (size_t)row * matrix->nvector + get_msb_index(col);
}

inline static bool
matrix_element_b(const matrix_t * restrict matrix, unsigned row, unsigned col)
{
    return get_lsb_bool(matrix->b[matrix_pos(matrix, row, col)], col);
}

matrix_t
init_matrix(unsigned nrow, unsigned ncol, bool binary, bool zom, bool rowsums);

void
matrix_set(matrix_t * restrict matrix, unsigned i, unsigned j, unsigned v);

void
init_sparse_matrix(matrix_t * restrict matrix);

void
free_matrix(const matrix_t * restrict matrix);

#endif
