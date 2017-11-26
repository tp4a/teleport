#include <ex/ex_ini.h>
#include <ex/ex_log.h>
#include <ex/ex_util.h>

ExIniSection::ExIniSection(const ex_wstr& strSectionName)
{
	m_kvs.clear();
	m_strName = strSectionName;
}

ExIniSection::ExIniSection()
{
	m_kvs.clear();
	m_strName = L"N/A";
}

ExIniSection::~ExIniSection()
{
	m_kvs.clear();
}

bool ExIniSection::_IsKeyExists(const ex_wstr& strKey)
{
	return (m_kvs.end() != m_kvs.find(strKey));
}

void ExIniSection::GetStr(const ex_wstr& strKey, ex_wstr& strValue, const ex_wstr& strDefault)
{
	ex_ini_kvs::iterator it = m_kvs.find(strKey);
	if (m_kvs.end() == it)
		strValue = strDefault;
	else
		strValue = (*it).second;
}

bool ExIniSection::GetStr(const ex_wstr& strKey, ex_wstr& strValue)
{
	ex_ini_kvs::iterator it = m_kvs.find(strKey);
	if (m_kvs.end() == it)
		return false;

	strValue = (*it).second;
	return true;
}

void ExIniSection::GetInt(const ex_wstr& strKey, int& iValue, int iDefault)
{
	ex_ini_kvs::iterator it = m_kvs.find(strKey);
	if (m_kvs.end() == it)
	{
		iValue = iDefault;
		return;
	}

#ifdef EX_OS_WIN32
	iValue = _wtoi(it->second.c_str());
#else
    ex_astr tmp;
    ex_wstr2astr(it->second, tmp);
	iValue = atoi(tmp.c_str());
#endif
}

bool ExIniSection::GetInt(const ex_wstr& strKey, int& iValue)
{
	ex_ini_kvs::iterator it = m_kvs.find(strKey);
	if (m_kvs.end() == it)
		return false;

#ifdef EX_OS_WIN32
	iValue = _wtoi(it->second.c_str());
#else
    ex_astr tmp;
    ex_wstr2astr(it->second, tmp);
	iValue = atoi(tmp.c_str());
#endif

	return true;
}

void ExIniSection::GetBool(const ex_wstr& strKey, bool& bValue, bool bDefault)
{
	ex_ini_kvs::iterator it = m_kvs.find(strKey);
	if (m_kvs.end() == it)
	{
		bValue = bDefault;
		return;
	}

	if (
		it->second == L"1"
#ifdef EX_OS_WIN32
		|| 0 == _wcsicmp(it->second.c_str(), L"true")
#else
		|| 0 == wcscasecmp(it->second.c_str(), L"true")
#endif
		)
		bValue = true;
	else
		bValue = false;
}

bool ExIniSection::GetBool(const ex_wstr& strKey, bool& bValue)
{
	ex_ini_kvs::iterator it = m_kvs.find(strKey);
	if (m_kvs.end() == it)
		return false;

	if (
		it->second == L"1"
#ifdef EX_OS_WIN32
		|| 0 == _wcsicmp(it->second.c_str(), _T("true"))
#else
		|| 0 == wcscasecmp(it->second.c_str(), L"true")
#endif
		)
		bValue = true;
	else
		bValue = false;

	return true;
}


bool ExIniSection::SetValue(const ex_wstr& strKey, const ex_wstr& strValue, bool bAddIfNotExists)
{
	ex_ini_kvs::iterator it = m_kvs.find(strKey);
	if (it != m_kvs.end())
	{
		it->second = strValue;
		return true;
	}

	if (bAddIfNotExists)
	{
		m_kvs.insert(std::make_pair(strKey, strValue));
		return true;
	}

	return false;
}

void ExIniSection::ClearUp(void)
{
	m_kvs.clear();
}

void ExIniSection::Save(FILE* file, int codepage) 
{
	ex_ini_kvs::iterator it = m_kvs.begin();
	for (; it != m_kvs.end(); ++it)
	{
		ex_wstr temp;
		temp += it->first.c_str();
		temp += L"=";
		temp += it->second.c_str();
		temp += L"\n";
		ex_astr temp2;
		ex_wstr2astr(temp, temp2, codepage);
		fwrite(temp2.c_str(), temp2.size(), 1, file);
	}
	return;
}

#ifdef EX_DEBUG
void ExIniSection::Dump(void)
{
	ex_ini_kvs::iterator it = m_kvs.begin();
	for (; it != m_kvs.end(); ++it)
	{
		EXLOGD(_T("   [%s]=[%s]\n"), it->first.c_str(), it->second.c_str());
	}
}
#endif

ExIniFile::ExIniFile()
{
}

ExIniFile::~ExIniFile()
{
	ClearUp();
}

bool ExIniFile::LoadFromFile(const ex_wstr& strFileName, bool bClearOld)
{
#ifdef EX_OS_WIN32
	HANDLE hFile = ::CreateFileW(strFileName.c_str(), GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
	if (INVALID_HANDLE_VALUE == hFile)
		return false;

	ULONG ulFileSize = GetFileSize(hFile, NULL);
	if (INVALID_FILE_SIZE == ulFileSize)
	{
		CloseHandle(hFile);
		return false;
	}

	std::vector<char> vFile;
	vFile.resize(ulFileSize + 1);
	ZeroMemory(&vFile[0], ulFileSize + 1);

	DWORD dwRead = 0;
	if (!ReadFile(hFile, &vFile[0], ulFileSize, &dwRead, NULL) || ulFileSize != dwRead)
	{
		CloseHandle(hFile);
		return false;
	}

	CloseHandle(hFile);

	m_file_path = strFileName;
#else
	FILE* f = NULL;
    ex_astr _fname;
    ex_wstr2astr(strFileName, _fname);
	f = fopen(_fname.c_str(), "rb");
	if(f == NULL)
		return false;
	fseek(f, 0L, SEEK_END);
	unsigned long ulFileSize = (unsigned long)ftell(f);
	if(-1 == ulFileSize)
	{
		fclose(f);
		return false;
	}

	std::vector<char> vFile;
	vFile.resize(ulFileSize + 1);
	memset(&vFile[0], 0, ulFileSize + 1);

	fseek(f, 0L, SEEK_SET);
	fread(&vFile[0], 1, ulFileSize, f);
	fclose(f);

	m_file_path = strFileName;
#endif

	char *pOffset = &vFile[0];
	if ((ulFileSize > 3) && (0 == memcmp(pOffset, "\xEF\xBB\xBF", 3)))
	{
		pOffset += 3;
	}
	// 配置文件均使用UTF8编码
	ex_wstr fileData;
	if (!ex_astr2wstr(pOffset, fileData, EX_CODEPAGE_UTF8))
		return false;

	return LoadFromMemory(fileData, bClearOld);
}

bool ExIniFile::LoadFromMemory(const ex_wstr& strData, bool bClearOld)
{
	if (strData.empty())
		return false;

	ex_wstr strAll(strData);
	bool bRet = true;
	ExIniSection* pCurSection = NULL;

	do {
		// Clear old data.
		if (bClearOld)
			ClearUp();

		ex_wstr strKey(L"");
		ex_wstr strValue(L"");

		ex_wstr strLine(L"");
		ex_wstr::size_type posCR = ex_wstr::npos;
		ex_wstr::size_type posLF = ex_wstr::npos;
		for (;;)
		{
			posCR = ex_wstr::npos;
			posLF = ex_wstr::npos;
			posCR = strAll.find(L"\r");
			posLF = strAll.find(L"\n");

			if(posCR == ex_wstr::npos && posLF == ex_wstr::npos) {
				if (strAll.empty())
					break;
				strLine = strAll;
				strAll.clear();
			} else if(posCR != ex_wstr::npos && posLF != ex_wstr::npos) {
				if(posLF != posCR + 1) {
					if(posLF < posCR) {
						strLine.assign(strAll, 0, posLF);
						strAll.erase(0, posLF + 1);
					} else {
						strLine.assign(strAll, 0, posCR);
						strAll.erase(0, posCR + 1);
					}
				} else {
					strLine.assign(strAll, 0, posCR);
					strAll.erase(0, posCR + 2);
				}
			} else {
				if(posCR != ex_wstr::npos) {
					strLine.assign(strAll, 0, posCR);
					strAll.erase(0, posCR + 1);
				} else {
					strLine.assign(strAll, 0, posLF);
					strAll.erase(0, posLF + 1);
				}
			}

//			if (ex_wstr::npos == pos)
//			{
//				pos = strAll.find(L'\n');
//				if (ex_wstr::npos == pos)
//				{
//					if (strAll.empty())
//						break;
//
//					strLine = strAll;
//					strAll.clear();
//				}
//				else
//				{
//					strLine.assign(strAll, 0, pos);
//					strAll.erase(0, pos + 1);
//				}
//			}
//			else
//			{
//				strLine.assign(strAll, 0, pos);
//				strAll.erase(0, pos + 2);
//			}

			if (ex_only_white_space(strLine))
				continue;

			if (!_ProcessLine(strLine, &pCurSection))
			{
				bRet = false;
				break;
			}
		}

	} while (false);

	return bRet;
}

void ExIniFile::Save(int codepage/* = EX_CODEPAGE_UTF8*/)
{
	//ex_astr temp;
	//ex_wstr2astr(m_file_path, temp);

	//FILE* file = NULL;
	//fopen(temp.c_str(), "wt");
	//fopen_s(&file, temp.c_str(), "wt");
    FILE* file = ex_fopen(m_file_path, L"wt");

	if (file == NULL)
	{
		return;
	}

	// 如果有不属于任何小节的值对，先保存之
	if (m_dumy_sec.Count() > 0)
		m_dumy_sec.Save(file, codepage);

	ex_ini_sections::iterator it = m_secs.begin();
	for (; it != m_secs.end(); ++it)
	{
		EXLOGD(L"{%s}\n", it->first.c_str());
		ex_wstr temp;
		temp += L"[";
		temp += it->first.c_str();
		temp += L"]\n";
		ex_astr temp2;
		ex_wstr2astr(temp, temp2, codepage);
		fwrite(temp2.c_str(), temp2.size(), 1, file);
	
		it->second->Save(file, codepage);
	}
	fclose(file);
}

#ifdef EX_DEBUG
void ExIniFile::Dump(void)
{
	ex_ini_sections::iterator it = m_secs.begin();
	for (; it != m_secs.end(); ++it)
	{
		EXLOGD(_T("{%s}\n"), it->first.c_str());
		it->second->Dump();
	}
}
#endif

void ExIniFile::ClearUp(void)
{
	ex_ini_sections::iterator it = m_secs.begin();
	for (; it != m_secs.end(); ++it)
	{
		delete it->second;
	}
	m_secs.clear();
}

ExIniSection* ExIniFile::GetSection(const ex_wstr& strName, bool bCreateIfNotExists)
{
	ex_ini_sections::iterator it = m_secs.find(strName);
	if (it != m_secs.end())
		return it->second;

	if (!bCreateIfNotExists)
		return NULL;

	ExIniSection* pSec = new ExIniSection(strName);
	m_secs.insert(std::make_pair(strName, pSec));
	return pSec;
}

// static function.
// 解析一行，返回值为 [节名/值对/注释/什么也不是/出错了]
// 节名 => strKey = [section_name]
// 值对 => strKey = strValue
ExIniFile::PARSE_RV ExIniFile::_ParseLine(const ex_wstr& strOrigLine, ex_wstr& strKey, ex_wstr& strValue)
{
	// 首先去掉行首的空格或者 TAB 控制
	ex_wstr strLine(strOrigLine);
	ex_remove_white_space(strLine, EX_RSC_BEGIN);

	// 判断是否为注释。 .ini 文件以 分号';'/'#' 作为注释行的第一个字符
	if (';' == strLine[0] || '#' == strLine[0])
	{
		return PARSE_COMMENT;
	}

	if ('[' == strLine[0])
	{
		// 这是一个节(section)
		ex_wstr::size_type startPos = strLine.find('[');
		ex_wstr::size_type endPos = strLine.rfind(']');
		strLine.erase(endPos);
		strLine.erase(startPos, 1);

		strKey = strLine;
		return PARSE_SECTION;
	}
	else
	{
		// 看看能否找到等号(=)，这是 key=value 的判别方法
		ex_wstr::size_type pos = strLine.find('=');
		if (ex_wstr::npos == pos)
		{
			//return PARSE_OTHER;	// 没有等号
			ex_remove_white_space(strLine);
			strKey = strLine;
			strValue.clear();
			return PARSE_KEYVALUE;
		}

		// 将等号前面的与等号后面的分割
		strKey.assign(strLine, 0, pos);
		strValue.assign(strLine, pos + 1, strLine.length() - pos);
		ex_remove_white_space(strKey);

		// 等号后面的应该原封不动，不应该移除空白字符
		ex_remove_white_space(strValue, EX_RSC_BEGIN);

		return PARSE_KEYVALUE;
	}

	return PARSE_OTHER;
}

bool ExIniFile::_ProcessLine(const ex_wstr strLine, ExIniSection** pCurSection)
{
	if (strLine.empty())
		return true;

	ex_wstr strKey;//(_T(""));
	ex_wstr strValue;//(_T(""));

	PARSE_RV parse_rv = PARSE_ERROR;

	parse_rv = _ParseLine(strLine, strKey, strValue);

	bool bError = false;

	switch (parse_rv)
	{
	case PARSE_ERROR:
		bError = true;
		break;
	case PARSE_SECTION:
	{
		// 创建一个节
		ExIniSection* pSection = GetSection(strKey, true);
		if (NULL == pSection)
		{
			bError = true;
			break;
		}

		*pCurSection = pSection;
	}
	break;
	case PARSE_KEYVALUE:
		if (NULL == pCurSection || NULL == *pCurSection)
		{
			//bError = true;
			//break;
			*pCurSection = &m_dumy_sec;
		}

		// 创建一个值对
		if (!(*pCurSection)->SetValue(strKey, strValue, true))
		{
			bError = true;
			break;
		}

		break;

	case PARSE_COMMENT:
	case PARSE_OTHER:
	default:
		break;
	}

	return (!bError);
}
