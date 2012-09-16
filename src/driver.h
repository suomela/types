#ifndef TYPES_DRIVER_H
#define TYPES_DRIVER_H

#include "input.h"
#include "plan.h"

void
process_input(input_t * restrict pinput, const plan_t * restrict pplan);

void
execute_all(input_t * restrict pinput, const plan_t * restrict pplan);

#endif
