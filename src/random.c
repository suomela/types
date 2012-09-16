#include "random.h"
#include "config.h"
#include "io.h"
#include "malloc.h"
#include "util.h"
#include <stdlib.h>
#include <stdio.h>

rng_state_t *
rng_state_read(myfile_t * restrict f)
{
    rng_state_t *rng_state_init;
    assert(is_open(f));
    MYFREAD_MALLOC(f, rng_state_init, rng_state_t, NGEN);
    myfread_zero_exact(f);
    return rng_state_init;
}

void
rng_state_write(myfile_t * restrict f, const rng_state_t * restrict rng_state)
{
    myfwrite(f, rng_state, sizeof(rng_state_t), NGEN);
}

unsigned
get_generator(unsigned processes, unsigned id)
{
    assert(id >= 1);
    return split(NGEN, processes, id-1);
}

unsigned
get_iteration(unsigned iterations, unsigned part)
{
    return split(iterations, NGEN, part);
}
