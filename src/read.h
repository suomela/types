#ifndef TYPES_READ_H
#define TYPES_READ_H

#include "input.h"
#include "plan.h"

void
read_raw_input(input_t * restrict pinput, const plan_t * restrict pplan);

void
postprocess_type_word_count(input_t * restrict pinput, const plan_t * restrict pplan);

void
postprocess_collections(input_t * restrict pinput, const plan_t * restrict pplan);

#endif
