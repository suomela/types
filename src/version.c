#include "version.h"
#include "config.h"
#include <stdio.h>

const char *VERSION = "2012-09-16";
const char *YEAR = "2012";

void
short_version(void)
{
    printf(
        "%s (Type and hapax accumulation curves), version %s\n"
        "Copyright (C) %s  Jukka Suomela\n",
        TOOL, VERSION, YEAR
    );
}

void
version(void)
{
    short_version();
    printf(
        "\n"
        "This program comes with ABSOLUTELY NO WARRANTY.\n"
        "This is free software, and you are welcome to redistribute it\n"
        "under the terms of the GNU General Public License\n"
        "<http://www.gnu.org/licenses/gpl.html>.\n\n"
    );
}

