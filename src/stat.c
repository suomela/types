#include "stat.h"

#include "malloc.h"
#include <stdlib.h>

const stat_t STAT_NULL_C = STAT_NULL;
const yxstat_t YXSTAT_NULL_C = YXSTAT_NULL;

yxstat_t *
alloc_stat(const yxbool_t * restrict create, const yx_t * restrict elements)
{
    yxstat_t * restrict pyxstat;
    MYMALLOCZ(pyxstat, yxstat_t, 1, YXSTAT_NULL_C);
    for (unsigned i = 0; i < NYX; i++) {
        if (create->yx[i]) {
            pyxstat->elements.yx[i] = elements->yx[i];
            MYMALLOCZ(pyxstat->yx[i], stat_t, elements->yx[i], STAT_NULL_C);
        }
    }
    return pyxstat;
}

yxstat_t *
alloc_stat_uniform(const yxbool_t * restrict create, unsigned elements)
{
    yxstat_t * restrict pyxstat;
    MYMALLOCZ(pyxstat, yxstat_t, 1, YXSTAT_NULL_C);
    for (unsigned i = 0; i < NYX; i++) {
        if (create->yx[i]) {
            pyxstat->elements.yx[i] = elements;
            MYMALLOCZ(pyxstat->yx[i], stat_t, elements, STAT_NULL_C);
        }
    }
    return pyxstat;
}

void
free_stat(const yxstat_t * restrict pyxstat)
{
    for (unsigned i = 0; i < NYX; i++) {
        if (pyxstat->yx[i]) {
            free(pyxstat->yx[i]);
        }
    }
}
