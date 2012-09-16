#ifndef TYPES_CONFIG_H
#define TYPES_CONFIG_H

//// Heuristic parameter

#define SPARSITY_HEURISTIC 50.0

//// Number of parallel generators

#define NGEN 2000

//// File formats

#define INPUT_MAGIC  0xEEE118E9u
#define OUTPUT_MAGIC 0x591E8AC1u

//// Each tool has to define this

extern const char * const TOOL;

#endif
