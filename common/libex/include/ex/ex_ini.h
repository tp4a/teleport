#ifndef __EX_INI_H__
#define __EX_INI_H__

/*
�ر�ע�⣺

1. �� �ֺ�';' ���� ����'#' ��Ϊע���еĵ�һ���ַ�
2. ��֧������ע��
3. ֵ���Ե�һ���Ⱥŷָ����Ⱥ�ǰ������пո�ᱻ���ԣ�֮��Ŀո�ᱣ����������β�ո�
4. ����в�����ĳ��С�ڵ�ֵ�ԣ�����ʹ��GetDumySection()��ȡ
   DumySection��Ҫ��Ϊ���ܹ����ݼ򵥵�Python�ļ��������ļ���
*/

#include "ex_str.h"
#include <map>

typedef std::map<ex_wstr, ex_wstr> ex_ini_kvs;

class ExIniSection
{
public:
	ExIniSection();
	ExIniSection(const ex_wstr& strSectionName);
	~ExIniSection();

	void ClearUp(void);

	ex_wstr Name(void) { return m_strName; }

	void GetStr(const ex_wstr& strKey, ex_wstr& strValue, const ex_wstr& strDefault);
	bool GetStr(const ex_wstr& strKey, ex_wstr& strValue);

	void GetInt(const ex_wstr& strKey, int& iValue, int iDefault);
	bool GetInt(const ex_wstr& strKey, int& iValue);

	void GetBool(const ex_wstr& strKey, bool& bValue, bool bDefault);
	bool GetBool(const ex_wstr& strKey, bool& bValue);
	
	bool SetValue(const ex_wstr& strKey, const ex_wstr& strValue, bool bAddIfNotExists = false);

	ex_ini_kvs& GetKeyValues(void) { return m_kvs; }

	int Count(void) const
	{
		return (int)m_kvs.size();
	}
	void Save(FILE* file, int codepage);
#ifdef EX_DEBUG
	void Dump(void);
#endif

protected:
	bool _IsKeyExists(const ex_wstr& strKey);

private:
	ex_wstr m_strName;
	ex_ini_kvs m_kvs;
};


typedef std::map<ex_wstr, ExIniSection*> ex_ini_sections;

// Ini file
class ExIniFile
{
public:
	enum PARSE_RV
	{
		PARSE_ERROR,
		PARSE_SECTION,
		PARSE_KEYVALUE,
		PARSE_COMMENT,
		PARSE_OTHER
	};

public:
	ExIniFile();
	~ExIniFile();

	const ex_wstr& get_filename(void){return m_file_path;}

	void ClearUp(void);

	// Read and parse special file.
	bool LoadFromFile(const ex_wstr& strFileName, bool bClearOld = true);
	bool LoadFromMemory(const ex_wstr& strData, bool bClearOld = true);

	ex_ini_sections& GetAllSections(void) { return m_secs; }

	ExIniSection* GetSection(const ex_wstr& strName, bool bCreateIfNotExists = false);
	ExIniSection* GetDumySection(void) { return &m_dumy_sec; }

	int Count(void) const
	{
		return (int)(m_secs.size());
	}
	void Save(int codepage = EX_CODEPAGE_UTF8);
#ifdef EX_DEBUG
	void Dump(void);
#endif

protected:
	static PARSE_RV _ParseLine(const ex_wstr& strLine, ex_wstr& strKey, ex_wstr& strValue);
	bool _ProcessLine(const ex_wstr strLine, ExIniSection** pCurSection);

private:
	ex_ini_sections m_secs;
	ExIniSection m_dumy_sec;
	ex_wstr m_file_path;
};

#endif // __EX_INI_H__
