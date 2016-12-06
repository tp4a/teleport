#ifndef __TS_INI_H__
#define __TS_INI_H__

#include <ex.h>

typedef std::map<ex_wstr, ex_wstr> ts_ini_kvs;

class TsIniSection
{
public:
	TsIniSection();
	TsIniSection(const ex_wstr& strSectionName);
	~TsIniSection();

	void ClearUp(void);

	ex_wstr Name(void) { return m_strName; }

	void GetStr(const ex_wstr& strKey, ex_wstr& strValue, const ex_wstr& strDefault);
	bool GetStr(const ex_wstr& strKey, ex_wstr& strValue);

	void GetInt(const ex_wstr& strKey, int& iValue, int iDefault);
	bool GetInt(const ex_wstr& strKey, int& iValue);

	void GetBool(const ex_wstr& strKey, bool& bValue, bool bDefault);
	bool GetBool(const ex_wstr& strKey, bool& bValue);
	
	bool SetValue(const ex_wstr& strKey, const ex_wstr& strValue, bool bAddIfNotExists = false);

	ts_ini_kvs& GetKeyValues(void) { return m_kvs; }

	int Count(void) const
	{
		return m_kvs.size();
	}
	void Save(FILE* file, int codepage);
#ifdef _DEBUG
	void Dump(void);
#endif

protected:
	bool _IsKeyExists(const ex_wstr& strKey);

private:
	ex_wstr m_strName;
	ts_ini_kvs m_kvs;
};


typedef std::map<ex_wstr, TsIniSection*> ts_ini_sections;

// Ini file
class TsIniFile
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
	TsIniFile();
	~TsIniFile();

	void ClearUp(void);

	// Read and parse special file.
	bool LoadFromFile(const ex_wstr& strFileName, bool bClearOld = true);
	bool LoadFromMemory(const ex_wstr& strData, bool bClearOld = true);

	TsIniSection* GetSection(const ex_wstr& strName, bool bCreateIfNotExists = false);

	int Count(void) const
	{
		return m_secs.size();
	}
	void Save(int codepage = EX_CODEPAGE_UTF8);
#ifdef _DEBUG
	void Dump(void);
#endif

protected:
	static PARSE_RV _ParseLine(const ex_wstr& strLine, ex_wstr& strKey, ex_wstr& strValue);
	bool _ProcessLine(const ex_wstr strLine, TsIniSection** pCurSection);

private:
	ts_ini_sections m_secs;
	ex_wstr m_file_path;
};

#endif // __TS_INI_H__
