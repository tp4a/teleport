#include <pys.h>
#include "pys_core.h"
#include "pys_util.h"

#include <ex/ex_log.h>

PYS_HANDLE pys_create(void)
{
	pys::Core* core = new pys::Core;
	return core;
}

void pys_destroy(PYS_HANDLE* pysh)
{
	if (NULL == pysh)
		return;
	if (NULL == *pysh)
		return;
	pys::Core* core = (pys::Core*)*pysh;
	delete core;
	*pysh = NULL;
}

PYS_BOOL pys_init_runtime(PYS_HANDLE pysh, const wchar_t* exec_file, const wchar_t* runtime_path)
{
	pys::Core* core = (pys::Core*)pysh;
	if (!core->init(exec_file, runtime_path))
		return PYS_FALSE;

	return PYS_TRUE;
}

int pys_run(PYS_HANDLE pysh)
{
	pys::Core* core = (pys::Core*)pysh;
	return core->run();
}

PYS_BOOL pys_add_search_path(PYS_HANDLE pysh, const wchar_t* path)
{
	pys::Core* core = (pys::Core*)pysh;
	core->add_search_path(path);
	return PYS_TRUE;
}


void pys_set_program(PYS_HANDLE pysh, const wchar_t* program_name)
{
	pys::Core* core = (pys::Core*)pysh;
	core->m_prog_name = program_name;
}

void pys_set_startup_file(PYS_HANDLE pysh, const wchar_t* filename)
{
	pys::Core* core = (pys::Core*)pysh;
	core->set_startup_file(filename);
}

void pys_set_bootstrap_module(PYS_HANDLE pysh, const char* module_name, const char* func_name)
{
	pys::Core* core = (pys::Core*)pysh;
	if(NULL != module_name)
		core->m_bootstrap_module = module_name;
	if (NULL != func_name)
		core->m_bootstrap_func = func_name;
}

void pys_set_argv(PYS_HANDLE pysh, int argc, wchar_t** argv)
{
	pys::Core* core = (pys::Core*)pysh;
	core->m_py_args.clear();

	int i = 0;
	for (i = 0; i < argc; ++i)
	{
		core->m_py_args.push_back(argv[i]);
	}
}

void pys_add_arg(PYS_HANDLE pysh, const wchar_t* arg)
{
	if (NULL == arg)
		return;

	pys::Core* core = (pys::Core*)pysh;
	core->m_py_args.push_back(arg);
}

PYS_BOOL pys_add_builtin_module(PYS_HANDLE pysh, const char* module_name, pys_init_module_func init_func)
{
	pys::Core* core = (pys::Core*)pysh;
	if (!core->add_builtin_module(module_name, init_func))
		return PYS_FALSE;
	return PYS_TRUE;
}

PyObject* pys_create_module(const char* module_name, PYS_BUILTIN_FUNC* funcs)
{
	PyMethodDef* _method_def = NULL;
	PyModuleDef* _module_def = NULL;

	int i = 0;
	int func_count = 0;

	if (funcs != NULL)
	{
		for (i = 0; ; ++i)
		{
			if (funcs[i].py_func_name == NULL)
				break;
			func_count++;
		}
	}

	_method_def = new PyMethodDef[func_count + 1];
	memset(_method_def, 0, sizeof(PyMethodDef)*(func_count + 1));
	for (i = 0; i < func_count; ++i)
	{
		_method_def[i].ml_name = funcs[i].py_func_name;
		_method_def[i].ml_meth = funcs[i].c_func_addr;
		_method_def[i].ml_doc = funcs[i].py_func_desc;
		if(funcs[i].have_args)
			_method_def[i].ml_flags = METH_VARARGS;
		else
			_method_def[i].ml_flags = METH_NOARGS;
	}

	_module_def = new PyModuleDef;
	memset(_module_def, 0, sizeof(PyModuleDef));
	_module_def->m_name = module_name;
	_module_def->m_size = -1;
	_module_def->m_methods = _method_def;

	// 托管这两个动态分配的变量
	pys::g_builtin_module_info.add(_method_def, _module_def);

	PyObject* module = pylib_PyModule_Create2(_module_def, PYTHON_API_VERSION);

	if (NULL == module)
	{
		EXLOGE("[pys]: can not create builtin module `%s`.\n", module_name);
		return NULL;
	}

	return module;
}

void pys_builtin_const_bool(PyObject* mod, const char* name, PYS_BOOL val)
{
	PyObject* dict = NULL;
	PyObject* tmp_obj = NULL;
	if (NULL == (dict = pylib_PyModule_GetDict(mod)))
		return;
	tmp_obj = pylib_PyBool_FromLong(val);
	pylib_PyDict_SetItemString(dict, name, tmp_obj);
	PYLIB_DECREF(tmp_obj);
}

void pys_builtin_const_long(PyObject* mod, const char* name, long val)
{
	PyObject* dict = NULL;
	PyObject* tmp_obj = NULL;
	if (NULL == (dict = pylib_PyModule_GetDict(mod)))
		return;
	tmp_obj = pylib_PyLong_FromLong(val);
	pylib_PyDict_SetItemString(dict, name, tmp_obj);
	PYLIB_DECREF(tmp_obj);
}

void pys_builtin_const_utf8(PyObject* mod, const char* name, const char* val)		// val 必须是utf8编码的字符串
{
	PyObject* dict = NULL;
	PyObject* tmp_obj = NULL;
	if (NULL == (dict = pylib_PyModule_GetDict(mod)))
		return;
	tmp_obj = pylib_PyUnicode_FromString(val);
	pylib_PyDict_SetItemString(dict, name, tmp_obj);
	PYLIB_DECREF(tmp_obj);
}

void pys_builtin_const_wcs(PyObject* mod, const char* name, const wchar_t* val)
{
	ex_astr strval;
	if (!ex_wstr2astr(val, strval, EX_CODEPAGE_UTF8))
		return;

	PyObject* dict = NULL;
	PyObject* tmp_obj = NULL;
	if (NULL == (dict = pylib_PyModule_GetDict(mod)))
		return;
	tmp_obj = pylib_PyUnicode_FromString(strval.c_str());
	pylib_PyDict_SetItemString(dict, name, tmp_obj);
	PYLIB_DECREF(tmp_obj);
}

void pys_builtin_const_bin(PyObject* mod, const char* name, const ex_u8* val, size_t size)
{
	PyObject* dict = NULL;
	PyObject* tmp_obj = NULL;
	if (NULL == (dict = pylib_PyModule_GetDict(mod)))
		return;
	tmp_obj = pylib_PyBytes_FromStringAndSize((char*)val, size);
	pylib_PyDict_SetItemString(dict, name, tmp_obj);
	PYLIB_DECREF(tmp_obj);
}
