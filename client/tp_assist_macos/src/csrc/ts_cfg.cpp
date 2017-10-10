#include "ts_cfg.h"
#include "ts_env.h"

TsCfg g_cfg;

TsCfg::TsCfg()
{}

TsCfg::~TsCfg()
{}

bool TsCfg::init(void) {
	ex_astr file_content;
	if(!ex_read_text_file(g_env.m_cfg_file, file_content)) {
		EXLOGE("can not load config file.\n");
		return false;
	}
	
	if(!_load(file_content))
		return false;

	return true;
}

bool TsCfg::save(const ex_astr& new_value)
{
	if(!_load(new_value))
		return false;
	
	Json::StyledWriter jwriter;
	ex_astr val = jwriter.write(m_root);
	
	if(!ex_write_text_file(g_env.m_cfg_file, val)) {
		EXLOGE("can not save config file.\n");
		return false;
	}

	return true;
}

bool TsCfg::_load(const ex_astr& str_json) {
	Json::Reader jreader;

	if (!jreader.parse(str_json.c_str(), m_root)) {
		EXLOGE("can not parse new config data, not in json format?\n");
		return false;
	}

	if (!m_root["term"].isObject()) {
		EXLOGE("invalid config, error 1.\n");
		return false;
	}
	
	if(	!m_root["term"]["selected"].isString()) {
		EXLOGE("invalid config, error 2.\n");
		return false;
	}

	term_name = m_root["term"]["selected"].asCString();
	
	if(!m_root["term"]["available"].isArray() || m_root["term"]["available"].size() == 0) {
		EXLOGE("invalid config, error 3.\n");
		return false;
	}

	int i = 0;
	for (i = 0; i < m_root["term"]["available"].size(); ++i) {

		if(
		   !m_root["term"]["available"][i]["name"].isString()
		   || !m_root["term"]["available"][i]["app"].isString()
		   || !m_root["term"]["available"][i]["profile"].isString()
		   ) {
			EXLOGE("invalid config, error 4.\n");
			return false;
		}
		
		if(m_root["term"]["available"][i]["name"].asCString() != term_name)
			continue;

		if(m_root["term"]["available"][i]["disp"].isString()) {
			term_display = m_root["term"]["available"][i]["display"].asCString();
		} else if(m_root["term"]["available"][i]["disp"].isNull()) {
			m_root["term"]["available"][i]["disp"] = term_name;
			term_display = term_name;
		} else {
			EXLOGE("invalid config, error 5.\n");
			return false;
		}
		
		term_app = m_root["term"]["available"][i]["app"].asCString();
		term_profile = m_root["term"]["available"][i]["profile"].asCString();

		break;
	}

	if(term_name.length() == 0 || term_app.length() == 0 || term_profile.length() == 0) {
		EXLOGE("invalid config, error 6.\n");
		return false;
	}
	
	return true;
}
