#include "version.h"
#include "config.h"
#include <stdio.h>

const char *VERSION = "2012-09-16";
const char *YEAR = "2012";

void
version(void)
{
    printf(
        "%s (Type and hapax accumulation curves), version %s\n"
        "Copyright (C) %s  Jukka Suomela\n",
        TOOL, VERSION, YEAR
    );
}

