#ifndef __TS_UTILS_H__
#define __TS_UTILS_H__

#include <ex.h>

int ts_url_decode(const char *src, int src_len, char *dst, int dst_len, int is_form_url_encoded);

#endif // __TS_UTILS_H__
