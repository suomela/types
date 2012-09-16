#ifndef TYPES_DB_H
#define TYPES_DB_H

#include "io.h"
#include <stdbool.h>
#include <stdint.h>

typedef enum {
    DB_PARAM_LAST,
    DB_PARAM_RECURSE,
    DB_PARAM_STRING,
    DB_PARAM_INT,
    DB_PARAM_DOUBLE,
} db_param_type;

typedef struct db_param db_param_t;

struct db_param {
    db_param_type type;
    union {
        const db_param_t * v_recurse;
        const char * v_string;
        int64_t v_int;
        double v_double;
    } value;
};

#define LAST       (db_param_t){ .type = DB_PARAM_LAST }
#define RECURSE(v) (db_param_t){ .type = DB_PARAM_RECURSE, .value.v_recurse = v }
#define STRING(v)  (db_param_t){ .type = DB_PARAM_STRING,  .value.v_string = v  }
#define INT(v)     (db_param_t){ .type = DB_PARAM_INT,     .value.v_int = v     }
#define DOUBLE(v)  (db_param_t){ .type = DB_PARAM_DOUBLE,  .value.v_double = v  }

#define NOBIND    (db_param_t[]){ LAST }
#define BIND(...) (db_param_t[]){ __VA_ARGS__, LAST }

void
db_open(const char * restrict filename, bool readwrite);

void
db_close(void);

unsigned
db_getuint(const char * restrict sql, const db_param_t * restrict param);

int64_t
db_getint(const char * restrict sql, const db_param_t * restrict param);

bool
db_getint_or_empty(const char * restrict sql, const db_param_t * restrict param, int64_t * restrict result);

void
db_exec(const char * restrict sql, const db_param_t * restrict param);

void
db_create_cache(const char * restrict sql);

void
db_exec_cache(const db_param_t * restrict param);

void
db_close_cache(void);

void
db_storearray(
    myfile_t * restrict f,
    unsigned nrow,
    unsigned ncol,
    const char * restrict sql,
    const db_param_t * restrict param
);

int64_t
db_last_insert_rowid(void);

#endif
