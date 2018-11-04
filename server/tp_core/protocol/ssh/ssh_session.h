#ifndef __SSH_SESSION_H__
#define __SSH_SESSION_H__

#include "ssh_recorder.h"

#include <ex.h>

#include <libssh/libssh.h>
#include <libssh/server.h>
#include <libssh/callbacks.h>
#include <libssh/sftp.h>

#include <vector>
#include <list>

#define TS_SSH_CHANNEL_TYPE_UNKNOWN		0
#define TS_SSH_CHANNEL_TYPE_SHELL		1
#define TS_SSH_CHANNEL_TYPE_SFTP		2

#define TP_SSH_CLIENT_SIDE		1
#define TP_SSH_SERVER_SIDE		2

class SshProxy;
class SshSession;

class TP_SSH_CHANNEL_PAIR {

	friend class SshSession;

public:
	TP_SSH_CHANNEL_PAIR();

private:
	int type;	// TS_SSH_CHANNEL_TYPE_SHELL or TS_SSH_CHANNEL_TYPE_SFTP

	ssh_channel cli_channel;
	ssh_channel srv_channel;

	TppSshRec rec;
	ex_u32 last_access_timestamp;

	int state;
	int db_id;
	int channel_id;	// for debug only.

	int win_width; // window width, in char count.

	bool is_first_server_data;
	bool need_close;

	// for ssh command record cache.
	bool server_ready;
	bool maybe_cmd;
	bool process_srv;
	bool client_single_char;
	std::list<char> cmd_char_list;
	std::list<char>::iterator cmd_char_pos;
};

typedef std::list<TP_SSH_CHANNEL_PAIR*> tp_channels;

class SshSession : public ExThreadBase
{
public:
	SshSession(SshProxy* proxy, ssh_session sess_client);
	virtual ~SshSession();

	SshProxy* get_proxy(void) { return m_proxy; }

	TP_SSH_CHANNEL_PAIR* _get_channel_pair(int channel_side, ssh_channel channel);

	void client_ip(const char* ip) { m_client_ip = ip; }
	const char* client_ip(void) const { return m_client_ip.c_str(); }
	void client_port(ex_u16 port) { m_client_port = port; }
	ex_u16 client_port(void) const { return m_client_port; }

	// save record cache into file. be called per 5 seconds.
	void save_record();
	// 
	void check_noop_timeout(ex_u32 t_now, ex_u32 timeout);

	const ex_astr& sid() { return m_sid; }

protected:
	void _thread_loop();
	void _on_stop();
    void _on_stopped();

	// record an error when session connecting or auth-ing.
	void _session_error(int err_code);
	// when client<->server channel created, start to record.
	bool _record_begin(TP_SSH_CHANNEL_PAIR* cp);
	// stop record because channel closed.
	void _record_end(TP_SSH_CHANNEL_PAIR* cp);

	void _process_ssh_command(TP_SSH_CHANNEL_PAIR* cp, int from, const ex_u8* data, int len);
	void _process_sftp_command(TP_SSH_CHANNEL_PAIR* cp, const ex_u8* data, int len);

private:
	void _run(void);

	void _close_channels(void);
	void _check_channels(void);

	static int _on_auth_password_request(ssh_session session, const char *user, const char *password, void *userdata);
	static ssh_channel _on_new_channel_request(ssh_session session, void *userdata);
	static int _on_client_pty_request(ssh_session session, ssh_channel channel, const char *term, int x, int y, int px, int py, void *userdata);
	static int _on_client_shell_request(ssh_session session, ssh_channel channel, void *userdata);
	static void _on_client_channel_close(ssh_session session, ssh_channel channel, void* userdata);
	static int _on_client_channel_data(ssh_session session, ssh_channel channel, void *data, unsigned int len, int is_stderr, void *userdata);
	static int _on_client_pty_win_change(ssh_session session, ssh_channel channel, int width, int height, int pxwidth, int pwheight, void *userdata);

	static int _on_client_channel_subsystem_request(ssh_session session, ssh_channel channel, const char *subsystem, void *userdata);
	static int _on_client_channel_exec_request(ssh_session session, ssh_channel channel, const char *command, void *userdata);

	static int _on_server_channel_data(ssh_session session, ssh_channel channel, void *data, unsigned int len, int is_stderr, void *userdata);
	static void _on_server_channel_close(ssh_session session, ssh_channel channel, void* userdata);

private:
	SshProxy* m_proxy;
	ssh_session m_cli_session;
	ssh_session m_srv_session;

	ExThreadLock m_lock;

	ex_astr m_client_ip;
	ex_u16 m_client_port;

	TPP_CONNECT_INFO* m_conn_info;

	ex_astr m_sid;
	ex_astr m_conn_ip;
	ex_u16 m_conn_port;
	ex_astr m_acc_name;
	ex_astr m_acc_secret;
    ex_u32 m_flags;
	int m_auth_type;

	bool m_is_logon;

	int m_ssh_ver;

	// 一个ssh_session中可以打开多个ssh_channel
	tp_channels m_channels;

	bool m_have_error;

	bool m_recving_from_srv;		// 是否正在从服务器接收数据？
	bool m_recving_from_cli;		// 是否正在从客户端接收数据？

	struct ssh_server_callbacks_struct m_srv_cb;
	struct ssh_channel_callbacks_struct m_cli_channel_cb;
	struct ssh_channel_callbacks_struct m_srv_channel_cb;
};

#endif // __SSH_SESSION_H__
