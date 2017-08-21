#include "ts_http_client.h"
#include <mongoose.h>

#include <ex/ex_str.h>

void ts_url_encode(const char *src, ex_astr& out)
{
	static const char *dont_escape = "._-$,;~()/";
	static const char *hex = "0123456789abcdef";

	size_t s_len = strlen(src);
	size_t dst_len = s_len * 3 + 1;
	char* dst = new char[dst_len];
	memset(dst, 0, dst_len);

	size_t i = 0, j = 0;

	for (i = j = 0; dst_len > 0 && i < s_len && j + 2 < dst_len - 1; i++, j++) {
		if (isalnum(*(const unsigned char *)(src + i)) ||
			strchr(dont_escape, *(const unsigned char *)(src + i)) != NULL) {
			dst[j] = src[i];
		}
		else if (j + 3 < dst_len) {
			dst[j] = '%';
			dst[j + 1] = hex[(*(const unsigned char *)(src + i)) >> 4];
			dst[j + 2] = hex[(*(const unsigned char *)(src + i)) & 0xf];
			j += 2;
		}
	}

	dst[j] = '\0';
	out = dst;
	delete []dst;
}

typedef struct HTTP_DATA {
	bool exit_flag;
	bool have_error;
	ex_astr body;
}HTTP_DATA;

static void ev_handler(struct mg_connection *nc, int ev, void *ev_data)
{
	HTTP_DATA* hdata = (HTTP_DATA*)nc->user_data;
	struct http_message *hm = (struct http_message *) ev_data;

	switch (ev) {
	case MG_EV_CONNECT:
		if (*(int *)ev_data != 0) {
			hdata->exit_flag = true;
			hdata->have_error = true;
		}
		break;
	case MG_EV_HTTP_REPLY:
		nc->flags |= MG_F_CLOSE_IMMEDIATELY;
		hdata->exit_flag = true;
		hdata->body.assign(hm->body.p, hm->body.len);
		break;
	case MG_EV_CLOSE:
// 		if (s_exit_flag == 0) {
// 			printf("Server closed connection\n");
// 			s_exit_flag = 1;
// 		}
		hdata->exit_flag = true;
		break;
	default:
		break;
	}
}

bool ts_http_get(const ex_astr& url, ex_astr& body)
{
	struct mg_mgr mgr;
	mg_mgr_init(&mgr, NULL);

	mg_connection* nc = mg_connect_http(&mgr, ev_handler, url.c_str(), NULL, NULL);
	if (NULL == nc)
		return false;

	HTTP_DATA* hdata = new HTTP_DATA;
	hdata->exit_flag = false;
	hdata->have_error = false;

	nc->user_data = hdata;

//	int count = 0;
	while (!hdata->exit_flag)
	{
		mg_mgr_poll(&mgr, 100);
// 		count++;
// 		if (count > 2)
// 			break;
	}

	bool ret = !hdata->have_error;
	if (ret)
		body = hdata->body;

	delete hdata;
	mg_mgr_free(&mgr);
	return ret;
}
