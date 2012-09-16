#ifndef TYPES_IO_H
#define TYPES_IO_H

#include <errno.h>
#include <stdbool.h>
#include <stdio.h>

typedef struct {
    FILE *file;
    const char *filename;
    bool standard_stream;
} myfile_t;

#define MYFILE_NULL { NULL, "(no file)", false }
extern const myfile_t MYFILE_NULL_C;

inline static bool
is_open(const myfile_t * restrict f)
{
    return f->file != NULL;
}

void
myinfo(const char * restrict format, ...);

void
myerror_noexit(const char * restrict format, ...);

_Noreturn void
myerror(const char * restrict format, ...);

_Noreturn void
myioerror(const myfile_t * restrict f, int errnum, const char * restrict context);

myfile_t
myopen_stdin(void);

myfile_t
myopen_stdout(void);

myfile_t
myopen(const char * restrict filename, bool write);

void
myclose(myfile_t * restrict f);

void
myclose_if_needed(myfile_t * restrict f);

void
myfprintf(const myfile_t * restrict f,
          const char * restrict format, ...);

int
read_int_minmax(const myfile_t * restrict f, const char * restrict description, int min, int max);

void
read_eof(const myfile_t * restrict f);

void
myfread(const myfile_t * restrict f, void * restrict ptr, size_t size, size_t nitems);

void
myfread_exact(const myfile_t * restrict f, void * restrict ptr, size_t size, size_t nitems);

void
myfread_zero_exact(const myfile_t * restrict f);

void
myfwrite(const myfile_t * restrict f, const void * restrict ptr, size_t size, size_t nitems);

inline static unsigned
myfread_uint(const myfile_t * restrict f)
{
    unsigned tmp;
    myfread(f, &tmp, sizeof(unsigned), 1);
    return tmp;
}

inline static void
myfwrite_uint(const myfile_t * restrict f, unsigned v)
{
    unsigned tmp = v;
    myfwrite(f, &tmp, sizeof(unsigned), 1);
}

inline static void
myfwrite_uchar(const myfile_t * restrict f, unsigned char v)
{
    errno = 0;
    int result = putc(v, f->file);
    if (result == EOF) {
        myioerror(f, errno, "putc");
    }
}

inline static unsigned char
myfread_uchar(const myfile_t * restrict f)
{
    errno = 0;
    int result = getc(f->file);
    if (result == EOF) {
        if (ferror(f->file)) {
            myioerror(f, errno, "getc");
        } else {
            myerror("%s: unexpected EOF", f->filename);
        }
    }
    return (unsigned char)result;
}

#define MYFREAD_MALLOC(f, target, type, count) \
    do { \
        size_t my_count = count; \
        type *my_result = mymalloc(sizeof(type), my_count); \
        target = my_result; \
        myfread(f, target, sizeof(type), my_count); \
    } while (0)

#endif
