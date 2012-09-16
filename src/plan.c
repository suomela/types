#include "plan.h"
#include "calculate.h"
#include <stdio.h>
#include <stdlib.h>

static unsigned
execution_plan_one(const yxbool_t * restrict need, bool * restrict flags, unsigned common)
{
    bool ytype  = need->yx[YX_TYPE_WORD]  || need->yx[YX_TYPE_TOKEN];
    bool yhapax = need->yx[YX_HAPAX_WORD] || need->yx[YX_HAPAX_TOKEN];
    bool xword  = need->yx[YX_TYPE_WORD]  || need->yx[YX_HAPAX_WORD];
    bool xtoken = need->yx[YX_TYPE_TOKEN] || need->yx[YX_HAPAX_TOKEN];

    flags[ALG_TYPEHAPAX_WT] =  yhapax &&  ytype &&  xword &&  xtoken;
    flags[ALG_TYPEHAPAX_W]  =  yhapax &&  ytype &&  xword && !xtoken;
    flags[ALG_TYPEHAPAX_T]  =  yhapax &&  ytype && !xword &&  xtoken;
    flags[ALG_HAPAX_WT]     =  yhapax && !ytype &&  xword &&  xtoken;
    flags[ALG_HAPAX_W]      =  yhapax && !ytype &&  xword && !xtoken;
    flags[ALG_HAPAX_T]      =  yhapax && !ytype && !xword &&  xtoken;
    flags[ALG_TYPE_WT]      = !yhapax &&  ytype &&  xword &&  xtoken;
    flags[ALG_TYPE_W]       = !yhapax &&  ytype &&  xword && !xtoken;
    flags[ALG_TYPE_T]       = !yhapax &&  ytype && !xword &&  xtoken;

    flags[ALG_TOKEN_W]      = need->yx[YX_TOKEN_WORD];

    unsigned requirements = 0;
    for (unsigned i = 0; i < NALG; i++) {
        if (flags[i]) {
            requirements |= common;
            requirements |= ALG[i].requirements;
        }
    }
    return requirements;
}

void
execution_plan(const input_t * restrict pinput, plan_t * restrict pplan)
{
    pplan->requirements = 0;
    pplan->requirements |= execution_plan_one(&pinput->curves,   pplan->calg, WITH_CURVES);
    pplan->requirements |= execution_plan_one(&pinput->permtest, pplan->palg, WITH_PERMTEST | WITH_COLLECTIONS);

    if (pplan->requirements & WITH_CURVES) {
        if (pinput->xres == 0) {
            myerror("--x required with these options");
        }
        if (pinput->yres == 0) {
            myerror("--y required with these options");
        }
    }
}
