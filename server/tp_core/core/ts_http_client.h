#ifndef __TS_HTTP_CLIENT_H__
#define __TS_HTTP_CLIENT_H__

#include <ex.h>

void ts_url_encode(const char *src, ex_astr& out);
bool ts_http_get(const ex_astr& url, ex_astr& body);

#endif // __TS_HTTP_CLIENT_H__
