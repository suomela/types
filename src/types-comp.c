#include "config.h"
#include "driver.h"
#include <stdlib.h>

const char * const TOOL = "types-comp";

int
main(int argc, char **argv)
{
    input_t input = INPUT_NULL_C;
    plan_t plan;
    parse_command_line(&input, argc, argv);
    execution_plan(&input, &plan);
    process_input(&input, &plan);
    execute_all(&input, &plan);
    free_input(&input);
    return EXIT_SUCCESS;
}
