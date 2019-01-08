#include "stdafx.h"
#include "ts_cfg.h"
#include "ts_env.h"


TsCfg g_cfg;

TsCfg::TsCfg()
{}

TsCfg::~TsCfg()
{}

bool TsCfg::init(void) {
	ex_astr file_content;
	if (!ex_read_text_file(g_env.m_cfg_file, file_content)) {
		EXLOGE("can not load config file.\n");
		return false;
	}

	if (!_load(file_content))
		return false;

	return true;
}

bool TsCfg::save(const ex_astr& new_value)
{
	if (!_load(new_value))
		return false;

	Json::StyledWriter jwriter;
	ex_astr val = jwriter.write(m_root);

	if (!ex_write_text_file(g_env.m_cfg_file, val)) {
		EXLOGE("can not save config file.\n");
		return false;
	}

	return true;
}

bool TsCfg::_load(const ex_astr& str_json) {
	Json::Reader jreader;

	if (!jreader.parse(str_json.c_str(), m_root)) {
		EXLOGE("can not parse new config data, not in json format? %s\n", jreader.getFormattedErrorMessages().c_str());
		return false;
	}

	ex_astr sel_name;
	size_t i = 0;
	ex_astr tmp;

	//===================================
	// check ssh config
	//===================================

	if (!m_root["ssh"].isObject()) {
		EXLOGE("invalid config, error 1.\n");
		return false;
	}

	if (!m_root["ssh"]["selected"].isString()) {
		EXLOGE("invalid config, error 2.\n");
		return false;
	}

	sel_name = m_root["ssh"]["selected"].asCString();

	if (!m_root["ssh"]["available"].isArray() || m_root["ssh"]["available"].size() == 0) {
		EXLOGE("invalid config, error 3.\n");
		return false;
	}

	for (i = 0; i < m_root["ssh"]["available"].size(); ++i) {

		if (
			!m_root["ssh"]["available"][i]["name"].isString()
			|| !m_root["ssh"]["available"][i]["app"].isString()
			|| !m_root["ssh"]["available"][i]["cmdline"].isString()
			) {
			EXLOGE("invalid config, error 4.\n");
			return false;
		}

		if (m_root["ssh"]["available"][i]["display"].isNull()) {
			m_root["ssh"]["available"][i]["display"] = m_root["ssh"]["available"][i]["name"];
		}

		if (m_root["ssh"]["available"][i]["name"].asCString() != sel_name)
			continue;

		tmp = m_root["ssh"]["available"][i]["app"].asCString();
		ex_astr2wstr(tmp, ssh_app, EX_CODEPAGE_UTF8);
		tmp = m_root["ssh"]["available"][i]["cmdline"].asCString();
		ex_astr2wstr(tmp, ssh_cmdline, EX_CODEPAGE_UTF8);

		break;
	}

	if (ssh_app.length() == 0 || ssh_cmdline.length() == 0) {
		EXLOGE("invalid config, error 6.\n");
		return false;
	}

	//===================================
	// check sftp config
	//===================================

	if (!m_root["scp"].isObject()) {
		EXLOGE("invalid config, error 1.\n");
		return false;
	}

	if (!m_root["scp"]["selected"].isString()) {
		EXLOGE("invalid config, error 2.\n");
		return false;
	}

	sel_name = m_root["scp"]["selected"].asCString();

	if (!m_root["scp"]["available"].isArray() || m_root["scp"]["available"].size() == 0) {
		EXLOGE("invalid config, error 3.\n");
		return false;
	}

	for (i = 0; i < m_root["scp"]["available"].size(); ++i) {

		if (
			!m_root["scp"]["available"][i]["name"].isString()
			|| !m_root["scp"]["available"][i]["app"].isString()
			|| !m_root["scp"]["available"][i]["cmdline"].isString()
			) {
			EXLOGE("invalid config, error 4.\n");
			return false;
		}

		if (m_root["scp"]["available"][i]["display"].isNull()) {
			m_root["scp"]["available"][i]["display"] = m_root["scp"]["available"][i]["name"];
		}

		if (m_root["scp"]["available"][i]["name"].asCString() != sel_name)
			continue;

		tmp = m_root["scp"]["available"][i]["app"].asCString();
		ex_astr2wstr(tmp, scp_app, EX_CODEPAGE_UTF8);
		tmp = m_root["scp"]["available"][i]["cmdline"].asCString();
		ex_astr2wstr(tmp, scp_cmdline, EX_CODEPAGE_UTF8);

		break;
	}

	if (scp_app.length() == 0 || scp_cmdline.length() == 0) {
		EXLOGE("invalid config, error 6.\n");
		return false;
	}

	//===================================
	// check telnet config
	//===================================

	if (!m_root["telnet"].isObject()) {
		EXLOGE("invalid config, error 1.\n");
		return false;
	}

	if (!m_root["telnet"]["selected"].isString()) {
		EXLOGE("invalid config, error 2.\n");
		return false;
	}

	sel_name = m_root["telnet"]["selected"].asCString();

	if (!m_root["telnet"]["available"].isArray() || m_root["telnet"]["available"].size() == 0) {
		EXLOGE("invalid config, error 3.\n");
		return false;
	}

	for (i = 0; i < m_root["telnet"]["available"].size(); ++i) {

		if (
			!m_root["telnet"]["available"][i]["name"].isString()
			|| !m_root["telnet"]["available"][i]["app"].isString()
			|| !m_root["telnet"]["available"][i]["cmdline"].isString()
			) {
			EXLOGE("invalid config, error 4.\n");
			return false;
		}

		if (m_root["telnet"]["available"][i]["display"].isNull()) {
			m_root["telnet"]["available"][i]["display"] = m_root["telnet"]["available"][i]["name"];
		}

		if (m_root["telnet"]["available"][i]["name"].asCString() != sel_name)
			continue;

		tmp = m_root["telnet"]["available"][i]["app"].asCString();
		ex_astr2wstr(tmp, telnet_app, EX_CODEPAGE_UTF8);
		tmp = m_root["telnet"]["available"][i]["cmdline"].asCString();
		ex_astr2wstr(tmp, telnet_cmdline, EX_CODEPAGE_UTF8);

		break;
	}

	if (telnet_app.length() == 0 || telnet_cmdline.length() == 0) {
		EXLOGE("invalid config, error 6.\n");
		return false;
	}

	//===================================
	// check rdp config
	//===================================

	if (!m_root["rdp"].isObject()) {
		EXLOGE("invalid config, error 1.\n");
		return false;
	}

	if (!m_root["rdp"]["selected"].isString()) {
		EXLOGE("invalid config, error 2.\n");
		return false;
	}

	sel_name = m_root["rdp"]["selected"].asCString();

	if (!m_root["rdp"]["available"].isArray() || m_root["rdp"]["available"].size() == 0) {
		EXLOGE("invalid config, error 3.\n");
		return false;
	}

	for (i = 0; i < m_root["rdp"]["available"].size(); ++i) {

		if (
			!m_root["rdp"]["available"][i]["name"].isString()
			|| !m_root["rdp"]["available"][i]["app"].isString()
			|| !m_root["rdp"]["available"][i]["cmdline"].isString()
			) {
			EXLOGE("invalid config, error 4.\n");
			return false;
		}

		if (m_root["rdp"]["available"][i]["display"].isNull()) {
			m_root["rdp"]["available"][i]["display"] = m_root["rdp"]["available"][i]["name"];
		}

		if (m_root["rdp"]["available"][i]["name"].asCString() != sel_name)
			continue;

		tmp = m_root["rdp"]["available"][i]["app"].asCString();
		ex_astr2wstr(tmp, rdp_app, EX_CODEPAGE_UTF8);
		tmp = m_root["rdp"]["available"][i]["cmdline"].asCString();
		ex_astr2wstr(tmp, rdp_cmdline, EX_CODEPAGE_UTF8);
		tmp = m_root["rdp"]["available"][i]["name"].asCString();
		ex_astr2wstr(tmp, rdp_name, EX_CODEPAGE_UTF8);

		break;
	}

	if (rdp_app.length() == 0 || rdp_cmdline.length() == 0 || rdp_name.length() == 0) {
		EXLOGE("invalid config, error 6.\n");
		return false;
	}

	return true;
}
