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

#define TS_SSH_DATA_FROM_CLIENT		1
#define TS_SSH_DATA_FROM_SERVER		2

typedef struct TS_SSH_CHANNEL_INFO
{
	int type;	// TS_SSH_CHANNEL_TYPE_SHELL or TS_SSH_CHANNEL_TYPE_SFTP
	ssh_channel channel;

	TS_SSH_CHANNEL_INFO()
	{
		type = TS_SSH_CHANNEL_TYPE_UNKNOWN;
		channel = NULL;
	}
}TS_SSH_CHANNEL_INFO;

typedef std::map<ssh_channel, TS_SSH_CHANNEL_INFO*> ts_ssh_channel_map;

class SshProxy;

class SshSession : public ExThreadBase
{
public:
	SshSession(SshProxy* proxy, ssh_session sess_client);
	virtual ~SshSession();

	SshProxy* get_proxy(void) { return m_proxy; }


	TS_SSH_CHANNEL_INFO* _get_cli_channel(ssh_channel srv_channel);
	TS_SSH_CHANNEL_INFO* _get_srv_channel(ssh_channel cli_channel);

	void client_ip(const char* ip) { m_client_ip = ip; }
	const char* client_ip(void) const { return m_client_ip.c_str(); }
	void client_port(ex_u16 port) { m_client_port = port; }
	ex_u16 client_port(void) const { return m_client_port; }

	void flush_record();

protected:
	// 继承自 TppSessionBase
	bool _on_session_begin(const TPP_CONNECT_INFO* info);
	bool _on_session_end(void);


	void _thread_loop(void);
	void _set_stop_flag(void);

	void _process_ssh_command(int from, const ex_u8* data, int len);
	void _process_sftp_command(const ex_u8* data, int len);

private:
	void _run(void);

	void _close_channels(void);

	void _enter_sftp_mode(void);

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
	int m_retcode;
	int m_db_id;

	TppSshRec m_rec;

	SshProxy* m_proxy;
	ssh_session m_cli_session;
	ssh_session m_srv_session;

	ExThreadLock m_lock;

	ex_astr m_client_ip;
	ex_u16 m_client_port;

	ex_astr m_sid;
	ex_astr m_conn_ip;
	ex_u16 m_conn_port;
	ex_astr m_acc_name;
	ex_astr m_acc_secret;
	int m_auth_type;

	bool m_is_first_server_data;
	bool m_is_sftp;

	bool m_is_logon;
	// 一个ssh_session中可以打开多个ssh_channel
	ts_ssh_channel_map m_channel_cli_srv;	// 通过客户端通道查找服务端通道
	ts_ssh_channel_map m_channel_srv_cli;	// 通过服务端通道查找客户端通道

	bool m_have_error;

	bool m_recving_from_srv;		// 是否正在从服务器接收数据？
	bool m_recving_from_cli;		// 是否正在从客户端接收数据？

	struct ssh_server_callbacks_struct m_srv_cb;
	struct ssh_channel_callbacks_struct m_cli_channel_cb;
	struct ssh_channel_callbacks_struct m_srv_channel_cb;

	int m_command_flag;

	std::list<char> m_cmd_char_list;
	std::list<char>::iterator m_cmd_char_pos;
};

#endif // __SSH_SESSION_H__
