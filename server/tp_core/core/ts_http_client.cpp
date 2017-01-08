#include "ts_http_client.h"
#include <mongoose.h>

#include<map>
using namespace std;

map<unsigned int, unsigned int> session_map;

int s_exit_flag = 0;

static void ev_handler(struct mg_connection *nc, int ev, void *ev_data)
{
	struct http_message *hm = (struct http_message *) ev_data;

	switch (ev) {
	case MG_EV_CONNECT:
		if (*(int *)ev_data != 0) {
			s_exit_flag = 1;
		}
		break;
	case MG_EV_HTTP_REPLY:
		nc->flags |= MG_F_CLOSE_IMMEDIATELY;
		s_exit_flag = 1;
		break;
	default:
		break;
	}
}

bool ts_http_get(ex_astr url)
{
	struct mg_mgr mgr;
	mg_mgr_init(&mgr, NULL);

	mg_connection* con = mg_connect_http(&mgr, ev_handler, url.c_str(), NULL, NULL);
	if (NULL == con)
		return false;

	int count = 0;
	while (s_exit_flag == 0)
	{
		mg_mgr_poll(&mgr, 1000);
		count++;
		if (count > 2)
			break;
	}

	mg_mgr_free(&mgr);
	return true;
}
