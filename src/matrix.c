#include "matrix.h"
#include "io.h"
#include "malloc.h"
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

const matrix_t MATRIX_NULL_C = MATRIX_NULL;

matrix_t
init_matrix(unsigned nrow, unsigned ncol, bool binary, bool zom, bool rowsums)
{
    matrix_t matrix = MATRIX_NULL;
    matrix.nrow = nrow;
    matrix.ncol = ncol;
    matrix.nvector = number_of_vectors(matrix.ncol);
    if (binary) {
        MYMALLOC2Z(matrix.b, vector_t, matrix.nrow, matrix.nvector, 0);
    }
    if (zom) {
        MYMALLOC2Z(matrix.zom, zom_t, matrix.nrow, matrix.nvector, ZOM_NULL_C);
    }
    if (rowsums) {
        MYMALLOCZ(matrix.rowsum, unsigned, matrix.nrow, 0);
    }
    return matrix;
}

void
matrix_set(matrix_t * restrict matrix, unsigned i, unsigned j, unsigned v)
{
    if (matrix->sum + v < matrix->sum) {
        myerror("overflow: the sum of elements exceeds %u", UINT_MAX);
    }
    matrix->sum += v;
    matrix->nnonzero++;
    if (matrix->rowsum) {
        matrix->rowsum[i] += v;
    }
    size_t pos = matrix_pos(matrix, i, j);
    vector_t mask = get_lsb_bit(j);
    if (matrix->b) {
        assert((matrix->b[pos] & mask) == 0);
        matrix->b[pos] |= mask;
    }
    if (matrix->zom) {
        assert((matrix->zom[pos].at_least_1 & mask) == 0);
        matrix->zom[pos].at_least_1 |= mask;
        if (v > 1) {
            matrix->zom[pos].at_least_2 |= mask;
        }
    }
}

void
init_sparse_matrix(matrix_t * restrict matrix)
{
    assert(matrix->b || matrix->zom);
    MYMALLOCZ(matrix->sparse_incidence, unsigned, matrix->nnonzero, 0);
    MYMALLOCZ(matrix->sparse_start, unsigned, matrix->nrow + 1, 0);
    unsigned k = 0;
    for (unsigned i = 0; i < matrix->nrow; i++) {
        matrix->sparse_start[i] = k;
        for (unsigned j = 0; j < matrix->ncol; j++) {
            size_t pos = matrix_pos(matrix, i, j);
            bool at_least_1 = false;
            bool at_least_2 = false;
            if (matrix->zom) {
                at_least_1 = get_lsb_bool(matrix->zom[pos].at_least_1, j);
                at_least_2 = get_lsb_bool(matrix->zom[pos].at_least_2, j);
            } else {
                at_least_1 = get_lsb_bool(matrix->b[pos], j);
            }
            if (at_least_1) {
                matrix->sparse_incidence[k] = (j << 1) | at_least_2;
                k++;
            }
        }
    }
    assert(k == matrix->nnonzero);
    matrix->sparse_start[matrix->nrow] = k;
}

void
free_matrix(const matrix_t * restrict matrix)
{
    if (matrix->rowsum) {
        free(matrix->rowsum);
    }
    if (matrix->b) {
        free(matrix->b);
    }
    if (matrix->zom) {
        free(matrix->zom);
    }
    if (matrix->sparse_incidence) {
        free(matrix->sparse_incidence);
    }
    if (matrix->sparse_start) {
        free(matrix->sparse_start);
    }
}
