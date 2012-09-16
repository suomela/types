#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "config.h"
#include "io.h"
#include "jump.h"
#include "malloc.h"
#include "random.h"
#include "seed.h"
#include "version.h"
#include "SFMT.h"
#include "SFMT-jump.h"

const char * const TOOL = "types-rng";

_Noreturn static void
usage(void)
{
    short_version();
    printf(
        "\n"
        "Generate the initial state for the random number generator.\n"
        "\n"
        "Usage: %s <RNG-STATE-FILE>\n"
        "\n",
        TOOL);
    exit(EXIT_SUCCESS);
}

int
main(int argc, char **argv)
{
    if (argc == 1) {
        usage();
    }
    if (argc != 2) {
        myerror("wrong number of parameters");
    }
    const char *rng_state_file = argv[1];

    // Setup seed

    rng_state_t *rng_state;
    MYMALLOC(rng_state, rng_state_t, NGEN);
    uint32_t seed[SEED_LENGTH];
    memcpy(seed, SEED, sizeof(seed));

    // First generate 0, 100, 200, ... sequentially
    
    fprintf(stderr, "%s: ", TOOL);
    sfmt_init_by_array(&rng_state[0], seed, SEED_LENGTH);
    for (unsigned i = JUMP_FACTOR; i < NGEN; i += JUMP_FACTOR) {
        fprintf(stderr, ":");
        rng_state[i] = rng_state[i-JUMP_FACTOR];
        SFMT_jump(&rng_state[i], JUMP_MANY);
    }

    // Then generate in parallel:
    // -   1,   2,   3, ...,  99
    // - 101, 102, 102, ..., 199

    #pragma omp parallel for
    for (unsigned i = 0; i < NGEN; i += JUMP_FACTOR) {
        for (unsigned j = i+1; j < i+JUMP_FACTOR && j < NGEN; j++) {
            fprintf(stderr, ".");
            rng_state[j] = rng_state[j-1];
            SFMT_jump(&rng_state[j], JUMP_ONE);
        }
    }
    fprintf(stderr, "\n");

    myfile_t f = myopen(rng_state_file, true);
    rng_state_write(&f, rng_state);
    myclose(&f);
    free(rng_state);

    return EXIT_SUCCESS;
}
