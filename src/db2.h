#ifndef TYPES_DB2_H
#define TYPES_DB2_H

#include "db.h"

void
recreate_corpus(const char * restrict corpuscode);

unsigned
create_temp_sample(const char * restrict corpuscode);

unsigned
create_temp_collection(const char * restrict corpuscode);

unsigned
create_temp_token(const char * restrict corpuscode, const char * restrict datasetcode);

unsigned
create_temp_sample_collection(const char * restrict corpuscode);

unsigned
create_temp_sample_token(const char * restrict corpuscode, const char * restrict datasetcode);

#endif
