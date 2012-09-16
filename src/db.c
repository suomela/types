#include "db.h"
#include "io.h"
#include <assert.h>
#include <errno.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>
#include <sqlite3.h>

/*
    Global database handle.
    Initialise with db_open.
    Closed automatically at exit.
    Can be closed explicitly with db_close.
*/
static sqlite3 *db = NULL;

typedef struct {
    sqlite3_stmt * restrict stmt;
    const char * restrict sql;
} db_cache_t;

static db_cache_t db_cache = { NULL, NULL };

static bool atexit_registered = false;

_Noreturn static void
db_error_stmt_exit(sqlite3_stmt * restrict stmt)
{
    sqlite3_finalize(stmt);
    exit(EXIT_FAILURE);
}

_Noreturn static void
db_error(const char * restrict sql)
{
    myerror("%s -- statement: '%s'", sqlite3_errmsg(db), sql);
}

_Noreturn static void
db_error_filename(const char * restrict filename)
{
    myerror("%s -- database: %s", sqlite3_errmsg(db), filename);
}

_Noreturn static void
db_error_stmt(sqlite3_stmt * restrict stmt, const char * restrict sql)
{
    myerror_noexit("%s -- statement: '%s'", sqlite3_errmsg(db), sql);
    db_error_stmt_exit(stmt);
}

static void
db_check_error(const char * restrict sql, int result)
{
    if (result) {
        db_error(sql);
    }
}

static void
db_check_error_stmt(sqlite3_stmt * restrict stmt, const char * restrict sql, int result)
{
    if (result) {
        db_error_stmt(stmt, sql);
    }
}

static bool
db_step(sqlite3_stmt * restrict stmt, const char * restrict sql, int expected_columns, bool close_when_done)
{
    int result = sqlite3_step(stmt);
    if (result == SQLITE_DONE) {
        if (close_when_done) {
            db_check_error(sql, sqlite3_finalize(stmt));
        }
        return false;
    } else if (result == SQLITE_ROW) {
        if (expected_columns < 0) {
            myerror_noexit("too many rows available -- statement: '%s'", sql);
            db_error_stmt_exit(stmt);
        }
        int columns = sqlite3_column_count(stmt);
        if (columns != expected_columns) {
            myerror_noexit("expected %d columns, got %d columns -- statement: '%s'", expected_columns, columns, sql);
            db_error_stmt_exit(stmt);
        }
        return true;
    } else {
        db_error_stmt(stmt, sql);
    }
}

static void
db_step_done(sqlite3_stmt * restrict stmt, const char * restrict sql)
{
    db_step(stmt, sql, -1, true);
}

static void
db_step_done_keep_open(sqlite3_stmt * restrict stmt, const char * restrict sql)
{
    db_step(stmt, sql, -1, false);
}

static void
db_step_row(sqlite3_stmt * restrict stmt, const char * restrict sql, int expected_columns)
{
    if (!db_step(stmt, sql, expected_columns, false)) {
        myerror_noexit("too few rows available -- statement: '%s'", sql);
        db_error_stmt_exit(stmt);
    }
}

static unsigned
db_bind_string(sqlite3_stmt * restrict stmt, const char * restrict sql, int index, const char * restrict value)
{
    if (sqlite3_bind_text(stmt, index, value, -1, SQLITE_STATIC)) {
        myerror_noexit("%s -- statement: '%s', parameter %d = '%s'", sqlite3_errmsg(db), sql, index, value);
        db_error_stmt_exit(stmt);
    }
    return index + 1;
}

static unsigned
db_bind_int(sqlite3_stmt * restrict stmt, const char * restrict sql, int index, int64_t value)
{
    if (sqlite3_bind_int64(stmt, index, value)) {
        myerror_noexit("%s -- statement: '%s', parameter %d = %lld", sqlite3_errmsg(db), sql, index, (long long int)value);
        db_error_stmt_exit(stmt);
    }
    return index + 1;
}

static unsigned
db_bind_double(sqlite3_stmt * restrict stmt, const char * restrict sql, int index, double value)
{
    if (sqlite3_bind_double(stmt, index, value)) {
        myerror_noexit("error: %s -- statement: '%s', parameter %d: %f", sqlite3_errmsg(db), sql, index, value);
        db_error_stmt_exit(stmt);
    }
    return index + 1;
}

static unsigned
db_bind_recurse(
    sqlite3_stmt * restrict stmt,
    const char * restrict sql,
    unsigned start,
    const db_param_t * restrict param
);

static unsigned
db_bind_recurse(
    sqlite3_stmt * restrict stmt,
    const char * restrict sql,
    unsigned index,
    const db_param_t * restrict param
)
{
    for (unsigned i = 0; param[i].type != DB_PARAM_LAST; i++) {
        switch (param[i].type) {
        case DB_PARAM_RECURSE:
            index = db_bind_recurse(stmt, sql, index, param[i].value.v_recurse);
            break;
        case DB_PARAM_STRING:
            index = db_bind_string(stmt, sql, index, param[i].value.v_string);
            break;
        case DB_PARAM_INT:
            index = db_bind_int(stmt, sql, index, param[i].value.v_int);
            break;
        case DB_PARAM_DOUBLE:
            index = db_bind_double(stmt, sql, index, param[i].value.v_double);
            break;
        case DB_PARAM_LAST:
        default:
            assert(false);
        }
    }
    return index;
}

static void
db_bind(sqlite3_stmt * restrict stmt, const char * restrict sql, const db_param_t * restrict param)
{
    db_bind_recurse(stmt, sql, 1, param);
}

static sqlite3_stmt*
db_prepare(const char * restrict sql, const db_param_t * restrict param)
{
    sqlite3_stmt *stmt;
    db_check_error(sql, sqlite3_prepare_v2(db, sql, -1, &stmt, NULL));
    db_bind(stmt, sql, param);
    return stmt;
}

static unsigned
db_column_uint(sqlite3_stmt * restrict stmt, const char * restrict sql, int column)
{
    int64_t v = sqlite3_column_int64(stmt, column);
    if (v < 0) {
        myerror_noexit("expected a nonnegative number -- statement: '%s', column %d", sql, column);
        db_error_stmt_exit(stmt);
    }
    if (v > UINT_MAX) {
        myerror_noexit("integer overflow -- statement: '%s', column %d", sql, column);
        db_error_stmt_exit(stmt);
    }
    return (unsigned)v;
}

unsigned
db_getuint(const char * restrict sql, const db_param_t * restrict param)
{
    sqlite3_stmt *stmt = db_prepare(sql, param);
    db_step_row(stmt, sql, 1);
    unsigned i = db_column_uint(stmt, sql, 0);
    db_step_done(stmt, sql);
    return i;
}

int64_t
db_getint(const char * restrict sql, const db_param_t * restrict param)
{
    sqlite3_stmt *stmt = db_prepare(sql, param);
    db_step_row(stmt, sql, 1);
    int64_t i = sqlite3_column_int64(stmt, 0);
    db_step_done(stmt, sql);
    return i;
}

bool
db_getint_or_empty(const char * restrict sql, const db_param_t * restrict param, int64_t * restrict result)
{
    sqlite3_stmt *stmt = db_prepare(sql, param);
    if (!db_step(stmt, sql, 1, true)) {
        return false;
    } else {
        *result = sqlite3_column_int64(stmt, 0);
        db_step_done(stmt, sql);
        return true;
    }
}

void
db_exec(const char * restrict sql, const db_param_t * restrict param)
{
    sqlite3_stmt *stmt = db_prepare(sql, param);
    db_step_done(stmt, sql);
}

void
db_create_cache(const char * restrict sql)
{
    if (db_cache.sql) {
        myerror("internal error: tried to create another prepared statement");
    }
    assert(db_cache.stmt == NULL);
    db_cache.sql = sql;
}

void
db_exec_cache(const db_param_t * restrict param)
{
    assert(db_cache.sql);
    if (db_cache.stmt == NULL) {
        db_cache.stmt = db_prepare(db_cache.sql, param);
    } else {
        db_check_error_stmt(db_cache.stmt, db_cache.sql, sqlite3_reset(db_cache.stmt));
        db_check_error_stmt(db_cache.stmt, db_cache.sql, sqlite3_clear_bindings(db_cache.stmt));
        db_bind(db_cache.stmt, db_cache.sql, param);
    }
    db_step_done_keep_open(db_cache.stmt, db_cache.sql);
}

void
db_close_cache(void)
{
    if (db_cache.stmt) {
        db_check_error(db_cache.sql, sqlite3_finalize(db_cache.stmt));
    }
    db_cache.stmt = NULL;
    db_cache.sql = NULL;
}

void
db_storearray(
    myfile_t * restrict f,
    unsigned nrow,
    unsigned ncol,
    const char * restrict sql,
    const db_param_t * restrict param
)
{
    sqlite3_stmt *stmt = db_prepare(sql, param);
    for (unsigned i = 0; i < nrow; i++) {
        db_step_row(stmt, sql, ncol);
        for (unsigned j = 0; j < ncol; j++) {
            myfwrite_uint(f, db_column_uint(stmt, sql, j));
        }
    }
    db_step_done(stmt, sql);
}

void db_close(void)
{
    if (db_cache.stmt) {
        // there are still unfinalised statements, closing...
        db_close_cache();
    }
    if (db) {
        if (sqlite3_close(db)) {
            myerror_noexit("closing database failed: %s", sqlite3_errmsg(db));
        }
        db = NULL;
    }
}

void
db_open(const char * restrict filename, bool readwrite)
{
    if (!atexit_registered) {
        errno = 0;
        if (atexit(db_close)) {
            myerror("atexit failed: %s", strerror(errno));
        }
        atexit_registered = true;
    }

    if (db) {
        myerror("internal error: tried to open another database connection");
    }

    if (sqlite3_open_v2(filename, &db, readwrite ? SQLITE_OPEN_READWRITE : SQLITE_OPEN_READONLY, NULL)) {
        db_error_filename(filename);
    }
    db_exec("PRAGMA foreign_keys = ON", NOBIND);
}

int64_t
db_last_insert_rowid(void)
{
    return sqlite3_last_insert_rowid(db);
}
