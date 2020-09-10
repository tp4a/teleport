#include "tpssh_channel.h"
#include "tpssh_session.h"
#include "tpp_env.h"
#include <teleport_const.h>

//===============================================================
// SshChannelPair
//===============================================================
SshChannelPair::SshChannelPair(SshSession *owner, ssh_channel channel_tp2cli, ssh_channel channel_tp2srv) :
    m_owner(owner),
    channel_tp2cli(channel_tp2cli),
    channel_tp2srv(channel_tp2srv)
{
    last_access_timestamp = (ex_u32) time(nullptr);

    state = TP_SESS_STAT_RUNNING;
    db_id = 0;
    channel_id = 0;

    win_width = 0;
    is_first_server_data = true;
    need_close = false;

    server_ready = false;
    maybe_cmd = false;
    process_srv = false;
    client_single_char = false;

    cmd_char_pos = cmd_char_list.begin();
}

SshChannelPair::~SshChannelPair() {

}

bool SshChannelPair::record_begin() {
#ifndef TEST_SSH_SESSION_000000
    if (!g_ssh_env.session_begin(m_conn_info, &(db_id))) {
        EXLOGE("[ssh] can not save to database, channel begin failed.\n");
        return false;
    }
    else {
        channel_id = db_id;
        //EXLOGD("[ssh] [channel:%d] channel begin\n", cp->channel_id);
    }


    if (!g_ssh_env.session_update(db_id, m_conn_info->protocol_sub_type, TP_SESS_STAT_STARTED)) {
        EXLOGE("[ssh] [channel:%d] can not update state, channel begin failed.\n", channel_id);
        return false;
    }


    rec.begin(g_ssh_env.replay_path.c_str(), L"tp-ssh", db_id, m_conn_info);
#endif
    return true;
}

void SshChannelPair::record_end() {
#ifndef TEST_SSH_SESSION_000000
    if (db_id > 0) {
        //EXLOGD("[ssh] [channel:%d] channel end with code: %d\n", channel_id, state);

        // 如果会话过程中没有发生错误，则将其状态改为结束，否则记录下错误值
        if (state == TP_SESS_STAT_RUNNING || state == TP_SESS_STAT_STARTED)
            state = TP_SESS_STAT_END;

        g_ssh_env.session_end(m_sid.c_str(), db_id, state);

        db_id = 0;
    }
    else {
        //EXLOGD("[ssh] [channel:%d] when channel end, no db-id.\n", channel_id);
    }
#endif
}

void SshChannelPair::update_session_state(int protocol_sub_type, int state) {
    // g_ssh_env.session_update(db_id, protocol_sub_type, state);
}

void SshChannelPair::close() {
    need_close = true;

    if (channel_tp2cli) {
        if (!ssh_channel_is_closed(channel_tp2cli))
            ssh_channel_close(channel_tp2cli);
        channel_tp2cli = nullptr;
    }

    if (channel_tp2srv) {
        if (!ssh_channel_is_closed(channel_tp2srv))
            ssh_channel_close(channel_tp2srv);
        channel_tp2srv = nullptr;
    }
}

void SshChannelPair::process_ssh_command(ssh_channel ch, const ex_u8 *data, uint32_t len) {

    EXLOGD("[ssh] -- cp 1.\n");

    if (len == 0)
        return;

    if (ch == channel_tp2cli) {
        if (len >= 2) {
            if (((ex_u8 *) data)[len - 1] == 0x0d) {
                // 疑似复制粘贴多行命令一次性执行，将其记录到日志文件中
                ex_astr str((const char *) data, len - 1);
                rec.record_command(1, str);

                // cp->process_srv = false;
                return;
            }
        }

        // 客户端输入回车时，可能时执行了一条命令，需要根据服务端返回的数据进行进一步判断
        maybe_cmd = (data[len - 1] == 0x0d);
        // 		if (cp->maybe_cmd)
        // 			EXLOGD("[ssh]   maybe cmd.\n");

        // 有时在执行类似top命令的情况下，输入一个字母'q'就退出程序，没有输入回车，可能会导致后续记录命令时将返回的命令行提示符作为命令
        // 记录下来了，要避免这种情况，排除的方式是：客户端单个字母，后续服务端如果收到的是控制序列 1b 5b xx xx，就不计做命令。
        client_single_char = (len == 1 && isprint(data[0]));

        // cp->process_srv = true;
    }
    else if (ch == channel_tp2srv) {
//        if (!cp->process_srv)
//            return;

        int offset = 0;
        bool esc_mode = false;
        int esc_arg = 0;
        for (; offset < len;) {
            ex_u8 ch = data[offset];

            if (esc_mode) {
                switch (ch) {
                    case '0':
                    case '1':
                    case '2':
                    case '3':
                    case '4':
                    case '5':
                    case '6':
                    case '7':
                    case '8':
                    case '9':
                        esc_arg = esc_arg * 10 + (ch - '0');
                        break;

                    case 0x3f:
                    case ';':
                    case '>':
                        cmd_char_list.clear();
                        cmd_char_pos = cmd_char_list.begin();
                        return;
                        break;

                    case 0x4b: {    // 'K'
                        if (0 == esc_arg) {
                            // 删除光标到行尾的字符串
                            cmd_char_list.erase(cmd_char_pos, cmd_char_list.end());
                            cmd_char_pos = cmd_char_list.end();
                        }
                        else if (1 == esc_arg) {
                            // 删除从开始到光标处的字符串
                            cmd_char_list.erase(cmd_char_list.begin(), cmd_char_pos);
                            cmd_char_pos = cmd_char_list.end();
                        }
                        else if (2 == esc_arg) {
                            // 删除整行
                            cmd_char_list.clear();
                            cmd_char_pos = cmd_char_list.begin();
                        }

                        esc_mode = false;
                        break;
                    }
                    case 0x43: {// ^[C
                        // 光标右移
                        if (esc_arg == 0)
                            esc_arg = 1;
                        for (int j = 0; j < esc_arg; ++j) {
                            if (cmd_char_pos != cmd_char_list.end())
                                cmd_char_pos++;
                        }
                        esc_mode = false;
                        break;
                    }
                    case 0x44: { // ^[D
                        // 光标左移
                        if (esc_arg == 0)
                            esc_arg = 1;
                        for (int j = 0; j < esc_arg; ++j) {

                            if (cmd_char_pos != cmd_char_list.begin())
                                cmd_char_pos--;
                        }
                        esc_mode = false;
                        break;
                    }

                    case 0x50: {    // 'P' 删除指定数量的字符

                        if (esc_arg == 0)
                            esc_arg = 1;
                        for (int j = 0; j < esc_arg; ++j) {
                            if (cmd_char_pos != cmd_char_list.end())
                                cmd_char_pos = cmd_char_list.erase(cmd_char_pos);
                        }
                        esc_mode = false;
                        break;
                    }

                    case 0x40: {    // '@' 插入指定数量的空白字符
                        if (esc_arg == 0)
                            esc_arg = 1;
                        for (int j = 0; j < esc_arg; ++j)
                            cmd_char_pos = cmd_char_list.insert(cmd_char_pos, ' ');
                        esc_mode = false;
                        break;
                    }

                    default:
                        esc_mode = false;
                        break;
                }

                //d += 1;
                //l -= 1;
                offset++;
                continue;
            }

            switch (ch) {
                case 0x07:
                    // 响铃
                    break;
                case 0x08: {
                    // 光标左移
                    if (cmd_char_pos != cmd_char_list.begin())
                        cmd_char_pos--;
                    break;
                }
                case 0x1b: {
                    if (offset + 1 < len) {
                        if (data[offset + 1] == 0x5b || data[offset + 1] == 0x5d) {
                            if (offset == 0 && client_single_char) {
                                cmd_char_list.clear();
                                cmd_char_pos = cmd_char_list.begin();
                                maybe_cmd = false;
                                process_srv = false;
                                client_single_char = false;
                                return;
                            }
                        }

                        if (data[offset + 1] == 0x5b) {
                            esc_mode = true;
                            esc_arg = 0;

                            offset += 1;
                        }
                    }

                    break;
                }
                case 0x0d: {
                    if (offset + 1 < len && data[offset + 1] == 0x0a) {
                        // 					if (cp->maybe_cmd)
                        // 						EXLOGD("[ssh]   maybe cmd.\n");
                        if (maybe_cmd) {
                            if (!cmd_char_list.empty()) {
                                ex_astr str(cmd_char_list.begin(), cmd_char_list.end());
                                // 							EXLOGD("[ssh]   --==--==-- save cmd: [%s]\n", str.c_str());
                                rec.record_command(0, str);
                            }

                            cmd_char_list.clear();
                            cmd_char_pos = cmd_char_list.begin();
                            maybe_cmd = false;
                        }
                    }
                    else {
                        cmd_char_list.clear();
                        cmd_char_pos = cmd_char_list.begin();
                    }
                    process_srv = false;
                    return;
                    break;
                }
                default:
                    if (cmd_char_pos != cmd_char_list.end()) {
                        cmd_char_pos = cmd_char_list.erase(cmd_char_pos);
                        cmd_char_pos = cmd_char_list.insert(cmd_char_pos, ch);
                        cmd_char_pos++;
                    }
                    else {
                        cmd_char_list.push_back(ch);
                        cmd_char_pos = cmd_char_list.end();
                    }
            }

            offset++;
        }
    }
}

void SshChannelPair::process_sftp_command(ssh_channel ch, const ex_u8 *data, uint32_t len) {
    // SFTP protocol: https://tools.ietf.org/html/draft-ietf-secsh-filexfer-13
    //EXLOG_BIN(data, len, "[sftp] client channel data");

    // TODO: 根据客户端的请求和服务端的返回，可以进一步判断用户是如何操作文件的，比如读、写等等，以及操作的结果是成功还是失败。
    // 记录格式：  time-offset,flag,action,result,file-path,[file-path]
    //   其中，flag目前总是为0，可以忽略（为保证与ssh-cmd格式一致），time-offset/action/result 都是数字
    //        file-path是被操作的对象，规格为 长度:实际内容，例如，  13:/root/abc.txt


    if (len < 9)
        return;

    int pkg_len = (int) ((data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]);
    if (pkg_len + 4 != len)
        return;

    ex_u8 sftp_cmd = data[4];

    if (sftp_cmd == 0x01) {
        // 0x01 = 1 = SSH_FXP_INIT
        rec.record_command(0, "SFTP INITIALIZE\r\n");
        return;
    }

    // 需要的数据至少14字节
    // uint32 + byte + uint32 + (uint32 + char + ...)
    // pkg_len + cmd + req_id + string( length + content...)
    if (len < 14)
        return;

    ex_u8 *str1_ptr = (ex_u8 *) data + 9;
    int str1_len = (int) ((str1_ptr[0] << 24) | (str1_ptr[1] << 16) | (str1_ptr[2] << 8) | str1_ptr[3]);
    // 	if (str1_len + 9 != pkg_len)
    // 		return;
    ex_u8 *str2_ptr = nullptr;// (ex_u8*)data + 13;
    int str2_len = 0;// (int)((data[9] << 24) | (data[10] << 16) | (data[11] << 8) | data[12]);


    switch (sftp_cmd) {
        case 0x03:
            // 0x03 = 3 = SSH_FXP_OPEN
            break;
            // 	case 0x0b:
            // 		// 0x0b = 11 = SSH_FXP_OPENDIR
            // 		act = "open dir";
            // 		break;
        case 0x0d:
            // 0x0d = 13 = SSH_FXP_REMOVE
            break;
        case 0x0e:
            // 0x0e = 14 = SSH_FXP_MKDIR
            break;
        case 0x0f:
            // 0x0f = 15 = SSH_FXP_RMDIR
            break;
        case 0x12:
            // 0x12 = 18 = SSH_FXP_RENAME
            // rename操作数据中包含两个字符串
            str2_ptr = str1_ptr + str1_len + 4;
            str2_len = (int) ((str2_ptr[0] << 24) | (str2_ptr[1] << 16) | (str2_ptr[2] << 8) | str2_ptr[3]);
            break;
        case 0x15:
            // 0x15 = 21 = SSH_FXP_LINK
            // link操作数据中包含两个字符串，前者是新的链接文件名，后者是现有被链接的文件名
            str2_ptr = str1_ptr + str1_len + 4;
            str2_len = (int) ((str2_ptr[0] << 24) | (str2_ptr[1] << 16) | (str2_ptr[2] << 8) | str2_ptr[3]);
            break;
        default:
            return;
    }

    int total_len = 5 + str1_len + 4;
    if (str2_len > 0)
        total_len += str2_len + 4;
    if (total_len > pkg_len)
        return;

    char msg[2048] = {0};
    if (str2_len == 0) {
        ex_astr str1((char *) ((ex_u8 *) data + 13), str1_len);
        ex_strformat(msg, 2048, "%d,%d,%s", sftp_cmd, 0, str1.c_str());
    }
    else {
        ex_astr str1((char *) (str1_ptr + 4), str1_len);
        ex_astr str2((char *) (str2_ptr + 4), str2_len);
        ex_strformat(msg, 2048, "%d,%d,%s:%s", sftp_cmd, 0, str1.c_str(), str2.c_str());
    }

    rec.record_command(0, msg);
}
