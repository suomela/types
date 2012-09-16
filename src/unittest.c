#undef NDEBUG
#include <assert.h>
#include <stdio.h>
#include "config.h"
#include "random.h"
#include "stat.h"
#include "util.h"

const char * const TOOL = "types-store";

int
main(int argc, char **argv)
{
    assert(argc == 2);
    const char *rngstatefile = argv[1];
    
    // stat: type size
    
    assert(sizeof(stat_8_t) == 2);
    assert(sizeof(stat_16_t) == 4);
    assert(sizeof(stat_32_t) == 8);
    
    // util: split

    for (unsigned total = 1; total < 1000; total += 13) {
        for (unsigned n = 1; n < 50; n++) {
            assert(split(total, n, 0) == 0);
            assert(split(total, n, n) == total);
            for (unsigned i = 0; i < n; i++) {
                assert(split(total, n, i) <= split(total, n, i+1));
            }
        }
    }

    // rng: sanity checking

    myfile_t f = myopen(rngstatefile, false);
    rng_state_t * restrict rng_state = rng_state_read(&f);
    myclose(&f);
    unsigned ITER = 2000000 / NGEN;
    unsigned TOL = 2000;
    for (unsigned n = 1; n < 15; n++) {
        unsigned w[n];
        for (unsigned i = 0; i < n; i++) {
            w[i] = 0;
        }
        for (unsigned gen = 0; gen < NGEN; gen++) {
            unsigned v[n];
            for (unsigned i = 0; i < n; i++) {
                v[i] = 0;
            }
            for (unsigned j = 0; j < ITER; j++) {
                unsigned i = myrand_n(&rng_state[gen], n);
                assert(i < n);
                v[i]++;
                w[i]++;
            }
            for (unsigned i = 0; i < n; i++) {
                assert(v[i] > 0);
            }
        }
        int expected = NGEN*ITER/n;
        for (unsigned i = 0; i < n; i++) {
            assert(w[i] > expected - TOL);
            assert(w[i] < expected + TOL);
        }
    }
    free(rng_state);

    return EXIT_SUCCESS;
}
