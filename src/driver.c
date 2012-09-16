#include "driver.h"
#include "calculate.h"
#include "collections.h"
#include "config.h"
#include "jump.h"
#include "malloc.h"
#include "print.h"
#include "random.h"
#include "read.h"
#include "util.h"

// -------- Input --------

void
process_input(input_t * restrict pinput, const plan_t * restrict pplan)
{
    read_raw_input(pinput, pplan);
    postprocess_type_word_count(pinput, pplan);
    postprocess_collections(pinput, pplan);
}

// -------- Merging (generic) --------

static void
merge_stat_one(const stat_t * restrict source,
               stat_t * restrict target,
               unsigned elements)
{
    if (source != NULL) {
        assert(target != NULL);
        #pragma omp parallel for
        for (unsigned j = 0; j < elements; j++) {
            target[j].lower += source[j].lower;
            target[j].upper += source[j].upper;
        }
    } else {
        assert(target == NULL);
    }
}

static void
merge_stat(yxstat_t * restrict yxtarget,
           const yxstat_t * restrict yxsource)
{
    for (unsigned i = 0; i < NYX; i++) {
        assert(yxsource->elements.yx[i] == yxtarget->elements.yx[i]);
        merge_stat_one(yxsource->yx[i], yxtarget->yx[i], yxsource->elements.yx[i]);
    }
}

static yxstat_t
merge_all(yxstat_t **ppyxstat_head,
          unsigned result_count)
{
    // Convert to vector
    assert(result_count >= 1);
    yxstat_t yxstat_vector[result_count];
    for (unsigned i = 0; i < result_count; i++) {
        yxstat_t *pyxstat = *ppyxstat_head;
        assert(pyxstat != NULL);
        yxstat_vector[i] = *pyxstat;
        yxstat_vector[i].next = NULL;
        *ppyxstat_head = pyxstat->next;
        free(pyxstat);
    }
    assert(*ppyxstat_head == NULL);

    // Merge results
    while (result_count > 1) {
        unsigned half = result_count / 2;
        unsigned a = result_count - 2 * half;
        unsigned b = result_count - half;
        #pragma omp parallel for
        for (unsigned i = 0; i < half; i++) {
            unsigned from = b + i;
            unsigned to = a + i;
            merge_stat(&yxstat_vector[to], &yxstat_vector[from]);
            free_stat(&yxstat_vector[from]);
        }
        result_count = b;
    }
    
    return yxstat_vector[0];
}

// -------- Permutation testing --------

static void
summarise_collections(const input_t * restrict pinput, collection_t * restrict pcoll, const algv_t * restrict algv)
{
    #pragma omp parallel for
    for (unsigned c = 0; c < pinput->collections.ncol; c++) {
        algv->summarise_collection(pinput, pcoll, c);
    }
}

static unsigned
calculate_permtest_parallel(const input_t * restrict pinput,
                            const rng_state_t * restrict rng_state_init,
                            const collection_t * restrict pcoll,
                            yxstat_t **ppyxstat_head,
                            const alg_t * restrict alg,
                            const algv_t * restrict algv)
{
    unsigned result_count = 0;
    unsigned gen_from = get_generator(pinput->processes, pinput->id);
    unsigned gen_to = get_generator(pinput->processes, pinput->id + 1);

    #pragma omp parallel
    {
        yxstat_t *pyxstat = alloc_stat_uniform(&alg->outputs, pinput->collections.ncol);
        #pragma omp critical
        {
            pyxstat->next = *ppyxstat_head;
            *ppyxstat_head = pyxstat;
            result_count++;
        }
        #pragma omp for nowait
        for (unsigned part = gen_from; part < gen_to; part++) {
            algv->calculate_permtest(pinput, rng_state_init, pcoll, pyxstat, part);
        }
    }

    return result_count;
}

static yxstat_t
calculate_permtest(const input_t * restrict pinput,
                   const rng_state_t * restrict rng_state_init,
                   const collection_t * restrict pcoll,
                   const alg_t * restrict alg,
                   const algv_t * restrict algv)
{
    yxstat_t *yxstat_head = NULL;
    unsigned result_count = calculate_permtest_parallel(pinput, rng_state_init, pcoll, &yxstat_head, alg, algv);
    return merge_all(&yxstat_head, result_count);
}

static void
print_permtest(input_t * restrict pinput, const yxstat_t * restrict pyxstat)
{
    for (unsigned i = 0; i < NYX; i++) {
        print_permtest_one(pinput, pyxstat->yx[i], i);
    }
}

static void
calculate_and_print_permtest(input_t * restrict pinput,
                             const rng_state_t * restrict rng_state_init,
                             const alg_t * restrict alg,
                             const algv_t * restrict algv)
{
    collection_t * restrict pcoll;
    MYMALLOCZ(pcoll, collection_t, pinput->collections.ncol, COLLECTION_NULL_C);
    summarise_collections(pinput, pcoll, algv);
    yxstat_t yxstat = calculate_permtest(pinput, rng_state_init, pcoll, alg, algv);
    print_permtest(pinput, &yxstat);
    free_stat(&yxstat);
    free(pcoll);
    if (pinput->progress) {
        fprintf(stderr, "P");
    }
}


// -------- Curves --------

static unsigned
calculate_curves_parallel(const input_t * restrict pinput,
                          const rng_state_t * restrict rng_state_init,
                          const grid_t * restrict pgrid, 
                          yxstat_t **ppyxstat_head,
                          const alg_t * restrict alg,
                          const algv_t * restrict algv)
{
    unsigned result_count = 0;
    unsigned gen_from = get_generator(pinput->processes, pinput->id);
    unsigned gen_to = get_generator(pinput->processes, pinput->id + 1);

    #pragma omp parallel
    {
        yxstat_t *pyxstat = alloc_stat(&alg->outputs, &pgrid->elements);
        #pragma omp critical
        {
            pyxstat->next = *ppyxstat_head;
            *ppyxstat_head = pyxstat;
            result_count++;
        }
        #pragma omp for nowait
        for (unsigned part = gen_from; part < gen_to; part++) {
            algv->calculate_curves(pinput, rng_state_init, pgrid, pyxstat, part);
        }
    }

    return result_count;
}

static yxstat_t
calculate_curves(const input_t * restrict pinput,
                 const rng_state_t * restrict rng_state_init,
                 const grid_t * restrict pgrid,
                 const alg_t * restrict alg,
                 const algv_t * restrict algv)
{
    yxstat_t *yxstat_head = NULL;
    unsigned result_count = calculate_curves_parallel(pinput, rng_state_init, pgrid, &yxstat_head, alg, algv);
    return merge_all(&yxstat_head, result_count);
}

static void
print_curves(input_t * restrict pinput, const grid_t * restrict pgrid, const yxstat_t * restrict pyxstat)
{
    for (unsigned i = 0; i < NYX; i++) {
        print_curves_one(pinput, pgrid, pyxstat->yx[i], i);
    }
}

static void
calculate_and_print_curves(input_t * restrict pinput,
                           const rng_state_t * restrict rng_state_init,
                           const grid_t * restrict pgrid,
                           const alg_t * restrict alg,
                           const algv_t * restrict algv)
{
    yxstat_t yxstat = calculate_curves(pinput, rng_state_init, pgrid, alg, algv);
    print_curves(pinput, pgrid, &yxstat);
    free_stat(&yxstat);
    if (pinput->progress) {
        fprintf(stderr, "C");
    }
}

// -------- Driver --------

void
execute_all(input_t * restrict pinput, const plan_t * restrict pplan)
{
    rng_state_t *rng_state_init = rng_state_read(&pinput->rng_state_file);
    myclose(&pinput->rng_state_file);

    print_head(pinput);

    const algv_t * restrict algv = pinput->sparse ? ALG_SPARSE : ALG_DENSE;

    if (pplan->requirements & WITH_PERMTEST) {
        for (unsigned i = 0; i < NALG; i++) {
            if (pplan->palg[i]) {
                calculate_and_print_permtest(pinput, rng_state_init, ALG + i, algv + i);
            }
        }
    }

    if (pplan->requirements & WITH_CURVES) {
        grid_t grid = GRID_NULL;
        setup_grid(pinput, pplan, &grid);
        for (unsigned i = 0; i < NALG; i++) {
            if (pplan->calg[i]) {
                calculate_and_print_curves(pinput, rng_state_init, &grid, ALG + i, algv + i);
            }
        }
    }

    // Header
    myfwrite_uint(&pinput->raw_output_file, CLASS_NONE);
    myclose(&pinput->raw_output_file);

    if (rng_state_init != NULL) {
        free(rng_state_init);
    }
}
