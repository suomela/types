#include "io.h"
#include "config.h"
#include <assert.h>
#include <errno.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>

const myfile_t MYFILE_NULL_C = MYFILE_NULL;

void
myinfo(const char * restrict format, ...)
{
    fprintf(stderr, "%s: ", TOOL);
    va_list ap;
    va_start(ap, format);
    vfprintf(stderr, format, ap);
    va_end(ap);
    fprintf(stderr, "\n");
}

void
myerror_noexit(const char * restrict format, ...)
{
    fprintf(stderr, "%s: error: ", TOOL);
    va_list ap;
    va_start(ap, format);
    vfprintf(stderr, format, ap);
    va_end(ap);
    fprintf(stderr, "\n");
}

_Noreturn void
myerror(const char * restrict format, ...)
{
    fprintf(stderr, "%s: error: ", TOOL);
    va_list ap;
    va_start(ap, format);
    vfprintf(stderr, format, ap);
    va_end(ap);
    fprintf(stderr, "\n");
    exit(EXIT_FAILURE);
}

_Noreturn void
myioerror(const myfile_t * restrict f, int errnum, const char * restrict context)
{
    myerror("%s: %s: %s", f->filename, context, strerror(errnum));
}

myfile_t
myopen_stdin(void)
{
    myfile_t f = MYFILE_NULL;
    f.file = stdin;
    f.filename = "(stdin)";
    f.standard_stream = true;
    return f;
}

myfile_t
myopen_stdout(void)
{
    myfile_t f = MYFILE_NULL;
    f.file = stdout;
    f.filename = "(stdout)";
    f.standard_stream = true;
    return f;
}

myfile_t
myopen(const char * restrict filename, bool write)
{
    myfile_t f = MYFILE_NULL;
    f.filename = filename;
    if (write) {
        f.file = fopen(filename, "w");
        if (f.file == NULL) {
            myioerror(&f, errno, "open for writing");
        }
    } else {
        f.file = fopen(filename, "r");
        if (f.file == NULL) {
            myioerror(&f, errno, "open for reading");
        }
    }
    return f;
}

void
myclose(myfile_t * restrict f)
{
    assert (f->file != NULL);
    if (f->standard_stream) {
        if (f->file != stdin) {
            if (fflush(f->file)) {
                myioerror(f, errno, "flush");
            }
        }
    } else {
        if (fclose(f->file)) {
            myioerror(f, errno, "close");
        }
    }
    *f = MYFILE_NULL_C;
}

void
myclose_if_needed(myfile_t * restrict f)
{
    if (is_open(f)) {
        myclose(f);
    }
}

void
myfprintf(const myfile_t * restrict f,
          const char * restrict format, ...)
{
    va_list ap;
    va_start(ap, format);
    int result = vfprintf(f->file, format, ap);
    va_end(ap);

    if (result < 0) {
        myioerror(f, errno, "write");
    }
}

int
read_int_minmax(const myfile_t * restrict f, const char * restrict description, int min, int max)
{
    int v;
    errno = 0;
    int result = fscanf(f->file, "%d", &v);
    if (result == EOF && ferror(f->file)) {
        myioerror(f, errno, "read");
    }
    if (errno == ERANGE) {
        myerror("%s: %s: integer overflow", f->filename, description);
    }
    if (result == EOF) {
        myerror("%s: %s: expected an integer, but got an end of file", f->filename, description);
    }
    if (result == 0) {
        myerror("%s: %s: expected an integer, but got nothing", f->filename, description);
    }
    assert(result == 1);
    if (v < min) {
        myerror("%s: %s: got %d, has to be at least %d", f->filename, description, v, min);
    }
    if (v > max) {
        myerror("%s: %s: got %d, has to be at most %d", f->filename, description, v, max);
    }
    return v;
}

void
read_eof(const myfile_t * restrict f)
{
    int result = fscanf(f->file, "%*s");
    if (result == EOF && ferror(f->file)) {
        myioerror(f, errno, "read");
    }
    if (result != EOF) {
        myerror("%s: expected end of input, but there is still some data in the file", f->filename);
    }
}

void
myfread(const myfile_t * restrict f, void * restrict ptr, size_t size, size_t nitems)
{
    errno = 0;
    size_t result = fread(ptr, size, nitems, f->file);
    if (result < nitems) {
        if (ferror(f->file)) {
            myioerror(f, errno, "read");
        } else {
            myerror("%s: expected %zu items of length %zu, got only %zu items", f->filename, nitems, size, result);
        }
    }
}

void
myfread_zero_exact(const myfile_t * restrict f)
{
    errno = 0;
    char c;
    size_t result = fread(&c, 1, 1, f->file);
    if (result == 1) {
        myerror("%s: expected end of input, but there is still some data in the file", f->filename);
    }
    if (ferror(f->file)) {
        myioerror(f, errno, "read");
    }
}

void
myfread_exact(const myfile_t * restrict f, void * restrict ptr, size_t size, size_t nitems)
{
    myfread(f, ptr, size, nitems);
    myfread_zero_exact(f);
}

void
myfwrite(const myfile_t * restrict f, const void * restrict ptr, size_t size, size_t nitems)
{
    errno = 0;
    size_t result = fwrite(ptr, size, nitems, f->file);
    if (result < nitems) {
        myioerror(f, errno, "write");
    }
}
