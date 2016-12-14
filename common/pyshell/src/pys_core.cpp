#include <pys.h>
#include "pys_core.h"
#include "pys_util.h"

#ifdef PYS_USE_PYLIB_SHARED
//========================================================
// WIN32
//========================================================
#define DECLPROC(name) \
    __PROC__ ## name pylib_ ## name = NULL;

#define GETPROCOPT(lib, name, sym) \
	pylib_ ## name = (__PROC__ ## name)GetProcAddress(lib, #sym)

#define GETPROC(lib, name) \
	GETPROCOPT(lib, name, name); \
if(!pylib_ ## name) { \
	EXLOGE("[pys] can not GetProcAddress for " #name "\n"); \
	return -1;\
}

#pragma warning(disable:4054)

#define DECLVAR(name) \
    __VAR__ ## name* pylib_ ## name = NULL;
#define GETVAR(lib, name) \
    pylib_ ## name = (__VAR__ ## name*)GetProcAddress(lib, #name); \
    if (!pylib_ ## name) { \
        EXLOGE("[pys] can not GetProcAddress for " #name "\n"); \
        return -1; \
    }


static int _pys_map_python_lib(DYLIB_HANDLE handle);
static DYLIB_HANDLE _pys_dlopen(const wchar_t* dylib_path);

static int pys_pylib_load(const wchar_t* lib_path)
{
	DYLIB_HANDLE lib = NULL;

	EXLOGD(L"[pys] py-lib: %ls\n", lib_path);

	lib = _pys_dlopen(lib_path);
	if (NULL == lib)
		return -1;

	if (0 != _pys_map_python_lib(lib))
		return -1;

	return 0;
}


DYLIB_HANDLE _pys_dlopen(const wchar_t* dylib_path)
{
	DYLIB_HANDLE handle = NULL;
#ifdef EX_OS_WIN32
	// PYSLOGW(L"[pys] py-lib: %ls\n", dylib_path);
	handle = LoadLibraryExW(dylib_path, NULL, LOAD_WITH_ALTERED_SEARCH_PATH);
	if (NULL == handle)
	{
		EXLOGE(L"[pys] can not load python lib: %ls.\n", dylib_path);
		return NULL;
	}
#else
	ex_astr path;
	if (!ex_wstr2astr(dylib_path, path, EX_CODEPAGE_UTF8))
	{
		EXLOGE("[pys] convert dylib_path failed.\n");
		return NULL;
	}

	EXLOGD("[pys] py-lib-a: %s\n", path);

	handle = dlopen(path.c_str(), RTLD_NOW | RTLD_GLOBAL);

	if (NULL == handle)
	{
		EXLOGE("[pys] dlopen() failed: %s.\n", dlerror());
		return NULL;
	}
#endif

	return handle;
}


int _pys_map_python_lib(DYLIB_HANDLE handle)
{
	GETVAR(handle, Py_DontWriteBytecodeFlag);
	GETVAR(handle, Py_FileSystemDefaultEncoding);
	GETVAR(handle, Py_FrozenFlag);
	GETVAR(handle, Py_IgnoreEnvironmentFlag);
	GETVAR(handle, Py_NoSiteFlag);
	GETVAR(handle, Py_NoUserSiteDirectory);
	GETVAR(handle, Py_OptimizeFlag);
	GETVAR(handle, Py_VerboseFlag);


	GETPROC(handle, Py_BuildValue);
	GETPROC(handle, Py_DecRef);
	GETPROC(handle, Py_Finalize);
	GETPROC(handle, Py_IncRef);
	GETPROC(handle, Py_Initialize);
	GETPROC(handle, Py_SetPath);
	GETPROC(handle, Py_SetProgramName);
	GETPROC(handle, Py_SetPythonHome);
	GETPROC(handle, PySys_SetArgvEx);

	GETPROC(handle, PyImport_ImportModule);
	GETPROC(handle, PyObject_GetAttrString);

	//GETPROC(handle, _Py_char2wchar);
	//GETPROC(handle, PyUnicode_FromWideChar);


	GETPROC(handle, PyErr_Clear);
	GETPROC(handle, PyErr_Occurred);
	GETPROC(handle, PyErr_Print);

	//GETPROC(handle, PyMem_RawFree);
	GETPROC(handle, PyObject_Call);
	GETPROC(handle, PyArg_Parse);

	GETPROC(handle, PyObject_CallFunction);
	GETPROC(handle, PyModule_GetDict);
	GETPROC(handle, PyDict_GetItemString);
	GETPROC(handle, PyDict_SetItemString);
	GETPROC(handle, PyLong_AsLong);
	GETPROC(handle, PyLong_FromLong);
	GETPROC(handle, PyLong_FromUnsignedLong);
	GETPROC(handle, PyLong_FromUnsignedLongLong);
	GETPROC(handle, PyBytes_FromString);
	GETPROC(handle, PyBytes_FromStringAndSize);
	GETPROC(handle, PyUnicode_FromString);
	GETPROC(handle, PyBool_FromLong);

	GETPROC(handle, PyImport_ExtendInittab);
	GETPROC(handle, PyModule_Create2);
	GETPROC(handle, PyArg_ParseTuple);
	GETPROC(handle, PyTuple_Pack);
	return 0;
}


DECLVAR(Py_DontWriteBytecodeFlag);
DECLVAR(Py_FileSystemDefaultEncoding);
DECLVAR(Py_FrozenFlag);
DECLVAR(Py_IgnoreEnvironmentFlag);
DECLVAR(Py_NoSiteFlag);
DECLVAR(Py_NoUserSiteDirectory);
DECLVAR(Py_OptimizeFlag);
DECLVAR(Py_VerboseFlag);


DECLPROC(Py_BuildValue);
DECLPROC(Py_DecRef);
DECLPROC(Py_Finalize);
DECLPROC(Py_IncRef);
DECLPROC(Py_Initialize);
DECLPROC(Py_SetPath);
DECLPROC(Py_SetProgramName);
DECLPROC(Py_SetPythonHome);
DECLPROC(PySys_SetArgvEx);

DECLPROC(PyImport_ImportModule);
DECLPROC(PyObject_GetAttrString);

//DECLPROC(_Py_char2wchar);
//DECLPROC(PyUnicode_FromWideChar);

DECLPROC(PyErr_Clear);
DECLPROC(PyErr_Occurred);
DECLPROC(PyErr_Print);

//DECLPROC(PyMem_RawFree);
DECLPROC(PyObject_Call);
DECLPROC(PyArg_Parse);

DECLPROC(PyObject_CallFunction);
DECLPROC(PyModule_GetDict);
DECLPROC(PyDict_GetItemString);
DECLPROC(PyDict_SetItemString);
DECLPROC(PyLong_AsLong);
DECLPROC(PyLong_FromLong);
DECLPROC(PyLong_FromUnsignedLong);
DECLPROC(PyLong_FromUnsignedLongLong);
DECLPROC(PyBytes_FromString);
DECLPROC(PyBytes_FromStringAndSize);
DECLPROC(PyUnicode_FromString);
DECLPROC(PyBool_FromLong);

DECLPROC(PyImport_ExtendInittab);
DECLPROC(PyModule_Create2);
DECLPROC(PyArg_ParseTuple);
DECLPROC(PyTuple_Pack);


#else
int pys_pylib_load(const wchar_t* lib_path)
{
	EXLOGD("[pys] link to python static lib.\n");
	return 0;
}

#endif


//================================================================
//
//================================================================

namespace pys
{
	BuiltinModuleInfo g_builtin_module_info;

	BuiltinModuleInfo::BuiltinModuleInfo()
	{}

	BuiltinModuleInfo::~BuiltinModuleInfo()
	{
		builtin_module_infos::iterator it = m_infos.begin();
		for (; it != m_infos.end(); ++it)
		{
			delete[] (*it)->method_def;
			delete (*it)->module_def;
			delete (*it);
		}
		m_infos.clear();
	}

	void BuiltinModuleInfo::add(PyMethodDef* method_def, PyModuleDef* module_def)
	{
		BUILTIN_MODULE_INFO* info = new BUILTIN_MODULE_INFO;
		info->method_def = method_def;
		info->module_def = module_def;
		m_infos.push_back(info);
	}

	//================================================================
	//
	//================================================================

	Core::Core()
	{
		m_init_tab = NULL;
	}

	Core::~Core()
	{
		if (NULL != m_init_tab)
			delete[] m_init_tab;
	}

	bool Core::init(const wchar_t* exec_file, const wchar_t* runtime_path)
	{
// 		if (!ex_exec_file(m_exec_file))
// 			return false;

		m_exec_file = exec_file;

		m_exec_path = m_exec_file;
		if (!ex_dirname(m_exec_path))
			return false;

		m_runtime_path = runtime_path;
		return _load_dylib();
	}

	bool Core::set_startup_file(const wchar_t* filename)
	{
		if (NULL == filename)
			return false;
		ex_wstr fname = filename;
		if (!ex_is_abspath(fname.c_str()))
			ex_abspath(fname);
		if (!ex_is_file_exists(fname.c_str()))
			return false;

		ex_wstr ext;
		if (!ex_path_ext_name(fname, ext))
			return false;

		m_start_file = fname;

		if (ext == L"zip")
		{
			m_is_zipped_app = true;
			// 将.zip文件加入搜索路径
			m_search_path.push_back(m_start_file);
		}
		else
		{
			m_is_zipped_app = false;

			// 将.py文件所在路径加入搜索路径
			ex_wstr tmp_path(m_start_file);
			ex_dirname(tmp_path);
			m_search_path.push_back(tmp_path);

			// 如果尚未设置启动模块名称，则以.py文件的文件名作为启动模块名称
			if (m_bootstrap_module.empty())
			{
				ex_wstr wmod(m_start_file);
				wmod.assign(m_start_file, tmp_path.length() + 1, m_start_file.length() - tmp_path.length() - 1 - 3);
				ex_wstr2astr(wmod, m_bootstrap_module);
			}
		}

		return true;
	}

	bool Core::add_builtin_module(const char* module_name, pys_init_module_func init_func)
	{
		builtin_modules::iterator it = m_builtin_modules.find(module_name);
		if (it != m_builtin_modules.end())
			return false;

		m_builtin_modules.insert(std::make_pair(module_name, init_func));
		return true;
	}

	bool Core::get_builtin_module_by_init_func(pys_init_module_func init_func, ex_astr& module_name)
	{
		builtin_modules::iterator it = m_builtin_modules.begin();
		for (; it != m_builtin_modules.end(); ++it)
		{
			if (init_func == it->second)
			{
				module_name = it->first;
				return true;
			}
		}

		return false;
	}

	bool Core::_load_dylib(void)
	{
#ifdef PYS_USE_PYLIB_SHARED
		ex_wstr ver_file = m_runtime_path;
		if (!ex_path_join(ver_file, true, L"python.ver", NULL))
			return false;
		FILE* f = pys_open_file(ver_file.c_str(), L"rb");
		if (NULL == f)
		{
			EXLOGE(L"[pys] can not open file: %ls\n", ver_file.c_str());
			return false;
		}
		fseek(f, 0L, SEEK_SET);
		char dll_name[64] = { 0 };
		size_t read_size = fread(dll_name, 1, 64, f);
		fclose(f);
		if (64 != read_size)
		{
			EXLOGE(L"[pys] read file failed, need 64B, read %dB\n", read_size);
			return false;
		}

		ex_wstr wstr_dll;
		if (!ex_astr2wstr(dll_name, wstr_dll))
			return false;

		ex_wstr dll_file = m_runtime_path;
		if (!ex_path_join(dll_file, true, wstr_dll.c_str(), NULL))
			return false;

		if (0 != pys_pylib_load(dll_file.c_str()))
		{
			return false;
		}
#endif
		return true;
	}

	bool Core::add_search_path(const wchar_t* wpath)
	{
		ex_wstr wstr_path = wpath;
		if (!ex_abspath(wstr_path))
		{
			EXLOGE(L"can not get abspath of `%ls`.\n", wpath);
			return false;
		}

		pys_wstr_list::iterator it = m_search_path.begin();
		for (; it != m_search_path.end(); ++it)
		{
			// TODO: windows平台不区分大小写比较
			if (wstr_path == (*it))
				return false;
		}

		m_search_path.push_back(wstr_path);
		return true;
	}

	bool Core::add_search_path(const char* apath, int code_page)
	{
		ex_wstr wstr_path;
		if (!ex_astr2wstr(apath, wstr_path, code_page))
			return false;
		return add_search_path(wstr_path.c_str());
	}


	bool Core::_run_prepare(void)
	{
		if(m_bootstrap_module.empty())
			m_bootstrap_module = "pysmain";
		if(m_bootstrap_func.empty())
			m_bootstrap_func = "main";

#ifdef PYS_USE_PYLIB_SHARED
		*pylib_Py_NoSiteFlag = 1;
		*pylib_Py_OptimizeFlag = 2;			// 进行操作码优化（编译成操作码，去掉assert及doc-string）
		*pylib_Py_FrozenFlag = 1;
		*pylib_Py_DontWriteBytecodeFlag = 1;	// 对于加载的.py脚本，内存中编译为操作码，但不要保存.pyo缓存文件
		*pylib_Py_NoUserSiteDirectory = 1;
		*pylib_Py_IgnoreEnvironmentFlag = 1;
		*pylib_Py_VerboseFlag = 0;
#else
		pylib_Py_NoSiteFlag = 1;
		pylib_Py_OptimizeFlag = 2;
		pylib_Py_FrozenFlag = 1;
		pylib_Py_DontWriteBytecodeFlag = 1;
		pylib_Py_NoUserSiteDirectory = 1;
		pylib_Py_IgnoreEnvironmentFlag = 1;
		pylib_Py_VerboseFlag = 0;
#endif

		ex_wstr tmp_path = m_runtime_path;
		ex_path_join(tmp_path, true, L"modules", NULL);
		add_search_path(tmp_path.c_str());

		tmp_path = m_runtime_path;
		ex_path_join(tmp_path, true, L"python.zip", NULL);
		add_search_path(tmp_path.c_str());

		if (m_search_path.size() > 0)
		{
			pys_wstr_list::iterator it = m_search_path.begin();
			for (; it != m_search_path.end(); ++it)
			{
				add_search_path(it->c_str());
			}
		}

		return true;
	}

	void Core::_run_set_program(void)
	{
		if(m_prog_name.empty())
			pylib_Py_SetProgramName((wchar_t*)m_exec_file.c_str());
		else
			pylib_Py_SetProgramName((wchar_t*)m_prog_name.c_str());
	}

	void Core::_run_set_path(void)
	{
		pys_wstr_list::iterator it = m_search_path.begin();
		for (; it != m_search_path.end(); ++it)
		{
			if (!m_search_path_tmp.empty())
				m_search_path_tmp += EX_PATH_SEP_STR;
			m_search_path_tmp += (*it);
		}

		EXLOGD(L"[pys] search path: %ls\n", m_search_path_tmp.c_str());
		pylib_Py_SetPath((wchar_t*)m_search_path_tmp.c_str());
	}

	void Core::_run_set_argv(void)
	{
		int tmp_argc = m_py_args.size();
		wchar_t** tmp_wargv = (wchar_t**)calloc(tmp_argc + 1, sizeof(wchar_t*));
		if (!tmp_wargv)
			return;

		int i = 0;
		pys_wstr_list::iterator it = m_py_args.begin();
		for (; it != m_py_args.end(); ++it)
		{
			tmp_wargv[i] = ex_wcsdup(it->c_str());
			i++;
		}

		pylib_PySys_SetArgvEx(tmp_argc, tmp_wargv, 0);

		ex_free_wargv(tmp_argc, tmp_wargv);
	}

	bool Core::_run_init_builtin_modules(void)
	{
		m_init_tab = NULL;
		int cnt = m_builtin_modules.size();
		if (0 == cnt)
			return true;

		m_init_tab = new struct _inittab[cnt + 1];
		memset(m_init_tab, 0, sizeof(struct _inittab)*(cnt + 1));
		int i = 0;
		builtin_modules::iterator it = m_builtin_modules.begin();
		for (; it != m_builtin_modules.end(); ++it, ++i)
		{
			m_init_tab[i].name = it->first.c_str();
			m_init_tab[i].initfunc = it->second;
		}

		if (-1 == pylib_PyImport_ExtendInittab(m_init_tab))
		{
			EXLOGE("[pys] can not init builtin module.\n");
			return false;
		}

		return true;
	}


	int Core::run(void)
	{
		int ret = 0;

		PyObject* pModule = NULL;
		PyObject* pDict = NULL;
		PyObject* pFunc = NULL;
		PyObject* pModuleName = NULL;
		PyObject* pRunArgs = NULL;
		PyObject* pyRet = NULL;
		PYS_BOOL has_error = PYS_TRUE;

		if (!_run_init_builtin_modules())
			return PYSR_FAILED;

		if (!_run_prepare())
			return PYSR_FAILED;
		_run_set_program();
		_run_set_path();

		// Py_Initialize()必须在初始化内建模块之后进行
		pylib_Py_Initialize();

		_run_set_argv();

		for (;;)
		{
			pModule = pylib_PyImport_ImportModule(m_bootstrap_module.c_str());
			if (pModule == NULL)
			{
				EXLOGE("[pys] can not import module: %s\n", m_bootstrap_module.c_str());

				ret = -1;
				break;
			}

			pDict = pylib_PyModule_GetDict(pModule); /* NO ref added */
			if (pDict == NULL)
			{
				EXLOGE("[pys] can not get module dict: %s\n", m_bootstrap_module.c_str());
				ret = -1;
				break;
			}

			pFunc = pylib_PyDict_GetItemString(pDict, (char*)m_bootstrap_func.c_str());
			if (pFunc == NULL)
			{
				EXLOGE("[pys] module [%s] have no function named `%s`.\n", m_bootstrap_module.c_str(), m_bootstrap_func.c_str());
				ret = -1;
				break;
			}

			pyRet = pylib_PyObject_CallFunction(pFunc, "");
			if (pyRet == NULL)
			{
				EXLOGE("[pys] %s.%s() return nothing.\n", m_bootstrap_module.c_str(), m_bootstrap_func.c_str());
				ret = -1;
				break;
			}

			pylib_PyErr_Clear();
			ret = pylib_PyLong_AsLong(pyRet);

			has_error = PYS_FALSE;

			break;
		}

		if (pylib_PyErr_Occurred())
			pylib_PyErr_Print();
		pylib_PyErr_Clear();

		if (pFunc) { PYLIB_DECREF(pFunc); }
		if (pModule) { PYLIB_DECREF(pModule); }
		if (pModuleName) { PYLIB_DECREF(pModuleName); }
		if (pRunArgs) { PYLIB_DECREF(pRunArgs); }
		if (pyRet) { PYLIB_DECREF(pyRet); }

		pylib_Py_Finalize();
		EXLOGD("[pys] python finalized. ExitCode=%d\n", ret);

		return ret;
	}

}
