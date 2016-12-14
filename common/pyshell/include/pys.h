#ifndef __PYS_H__
#define __PYS_H__

#include <ex.h>

//=========================================================================
// Type define
//=========================================================================
#if defined(EX_OS_WIN32)
#	define DYLIB_HANDLE		HINSTANCE
#else
#	define DYLIB_HANDLE		void*
#endif

//=========================================================================
// Python API
//=========================================================================
#define MS_NO_COREDLL 1
#ifdef __cplusplus
extern "C" {
#endif

#if defined(EX_OS_WIN32)
#	define PYS_USE_PYLIB_SHARED
#	include <Python.h>
#elif defined(EX_OS_LINUX)
#	define PYS_USE_PYLIB_STATIC
#	include <Python.h>
#else
#	error This platform not supported yet.
#endif

#ifdef __cplusplus
}
#endif

#ifdef PYS_USE_PYLIB_SHARED
//========================================================
// WIN32
//========================================================
#define EXTDECLPROC(result, name, args) \
    typedef result (__cdecl* __PROC__ ## name) args; \
    extern __PROC__ ## name pylib_ ## name;

#define EXTDECLVAR(vartyp, name) \
    typedef vartyp __VAR__ ## name; \
    extern __VAR__ ## name* pylib_ ## name;


EXTDECLVAR(int, Py_FrozenFlag);
EXTDECLVAR(int, Py_NoSiteFlag);
EXTDECLVAR(int, Py_OptimizeFlag);
EXTDECLVAR(const char*, Py_FileSystemDefaultEncoding);
EXTDECLVAR(int, Py_VerboseFlag);
EXTDECLVAR(int, Py_IgnoreEnvironmentFlag);
EXTDECLVAR(int, Py_DontWriteBytecodeFlag);
EXTDECLVAR(int, Py_NoUserSiteDirectory);

EXTDECLPROC(void, Py_Initialize, (void));
EXTDECLPROC(void, Py_Finalize, (void));
EXTDECLPROC(void, Py_IncRef, (PyObject *));
EXTDECLPROC(void, Py_DecRef, (PyObject *));
EXTDECLPROC(void, Py_SetProgramName, (wchar_t *));
EXTDECLPROC(void, Py_SetPythonHome, (wchar_t *));
EXTDECLPROC(void, Py_SetPath, (wchar_t *));  /* new in Python 3 */
EXTDECLPROC(int, PySys_SetArgvEx, (int, wchar_t **, int));
EXTDECLPROC(PyObject *, PyImport_ImportModule, (const char *));
EXTDECLPROC(PyObject *, PyObject_GetAttrString, (PyObject *, const char *));

// in python3.0~3.4, it is _Py_char2wchar, but renamed to Py_DecodeLocale in python3.5.  WTF.
//EXTDECLPROC(wchar_t *, _Py_char2wchar, (char *, size_t *));

//EXTDECLPROC(PyObject*, PyUnicode_FromWideChar, (const wchar_t*, size_t size	));

EXTDECLPROC(PyObject *, Py_BuildValue, (char *, ...));

EXTDECLPROC(void, PyErr_Clear, (void));
EXTDECLPROC(PyObject *, PyErr_Occurred, (void));
EXTDECLPROC(void, PyErr_Print, (void));

EXTDECLPROC(PyObject *, PyObject_Call, (PyObject *callable_object, PyObject *args, PyObject *kw));
EXTDECLPROC(int, PyArg_Parse, (PyObject *, const char *, ...));

EXTDECLPROC(PyObject *, PyObject_CallFunction, (PyObject *, char *, ...));
EXTDECLPROC(PyObject *, PyModule_GetDict, (PyObject *));
EXTDECLPROC(PyObject *, PyDict_GetItemString, (PyObject *, char *));
EXTDECLPROC(int, PyDict_SetItemString, (PyObject *dp, const char *key, PyObject *item));
EXTDECLPROC(long, PyLong_AsLong, (PyObject *));
EXTDECLPROC(PyObject *, PyLong_FromLong, (long));
EXTDECLPROC(PyObject *, PyLong_FromUnsignedLong, (unsigned long));
EXTDECLPROC(PyObject *, PyLong_FromUnsignedLongLong, (unsigned PY_LONG_LONG));
EXTDECLPROC(PyObject *, PyBytes_FromString, (const char *));
EXTDECLPROC(PyObject *, PyBytes_FromStringAndSize, (const char *, Py_ssize_t));
EXTDECLPROC(PyObject *, PyUnicode_FromString, (const char *));
EXTDECLPROC(PyObject *, PyBool_FromLong, (long));


EXTDECLPROC(int, PyImport_ExtendInittab, (struct _inittab *newtab));
EXTDECLPROC(PyObject *, PyModule_Create2, (struct PyModuleDef*, int apiver));
EXTDECLPROC(int, PyArg_ParseTuple, (PyObject *, const char *, ...));
EXTDECLPROC(PyObject *, PyTuple_Pack, (Py_ssize_t, ...));


#else // for linux, link to static python lib.

#define pylib_Py_FrozenFlag Py_FrozenFlag
#define pylib_Py_NoSiteFlag Py_NoSiteFlag
#define pylib_Py_OptimizeFlag Py_OptimizeFlag
#define pylib_Py_FileSystemDefaultEncoding Py_FileSystemDefaultEncoding
#define pylib_Py_VerboseFlag Py_VerboseFlag
#define pylib_Py_IgnoreEnvironmentFlag Py_IgnoreEnvironmentFlag
#define pylib_Py_DontWriteBytecodeFlag Py_DontWriteBytecodeFlag
#define pylib_Py_NoUserSiteDirectory Py_NoUserSiteDirectory
#define pylib_Py_Initialize Py_Initialize
#define pylib_Py_Finalize Py_Finalize
#define pylib_Py_IncRef Py_IncRef
#define pylib_Py_DecRef Py_DecRef
#define pylib_Py_SetProgramName Py_SetProgramName
#define pylib_Py_SetPythonHome Py_SetPythonHome
#define pylib_Py_SetPath Py_SetPath
#define pylib_PySys_SetArgvEx PySys_SetArgvEx
#define pylib_PyImport_ImportModule PyImport_ImportModule
#define pylib_PyObject_GetAttrString PyObject_GetAttrString
#define pylib_Py_BuildValue Py_BuildValue
#define pylib_PyErr_Clear PyErr_Clear
#define pylib_PyErr_Occurred PyErr_Occurred
#define pylib_PyErr_Print PyErr_Print
#define pylib_PyObject_Call PyObject_Call
#define pylib_PyArg_Parse PyArg_Parse
#define pylib_PyObject_CallFunction PyObject_CallFunction
#define pylib_PyModule_GetDict PyModule_GetDict
#define pylib_PyDict_GetItemString PyDict_GetItemString
#define pylib_PyDict_SetItemString PyDict_SetItemString
#define pylib_PyLong_AsLong PyLong_AsLong
#define pylib_PyLong_FromLong PyLong_FromLong
#define pylib_PyLong_FromUnsignedLong PyLong_FromUnsignedLong
#define pylib_PyLong_FromUnsignedLongLong PyLong_FromUnsignedLongLong
#define pylib_PyBytes_FromString PyBytes_FromString
#define pylib_PyBytes_FromStringAndSize PyBytes_FromStringAndSize
#define pylib_PyUnicode_FromString PyUnicode_FromString
#define pylib_PyBool_FromLong PyBool_FromLong
#define pylib_PyImport_ExtendInittab PyImport_ExtendInittab
#define pylib_PyModule_Create2 PyModule_Create2
#define pylib_PyArg_ParseTuple PyArg_ParseTuple
#define pylib_PyTuple_Pack PyTuple_Pack

#define pylib_Py_IncRef Py_IncRef
#define pylib_Py_DecRef Py_DecRef
#define pylib_PyBool_FromLong PyBool_FromLong
#define pylib_PyBool_FromLong PyBool_FromLong

#endif

#define PYLIB_XINCREF(o)    pylib_Py_IncRef(o)
#define PYLIB_XDECREF(o)    pylib_Py_DecRef(o)
#define PYLIB_DECREF(o)     PYLIB_XDECREF(o)
#define PYLIB_INCREF(o)     PYLIB_XINCREF(o)

#define PYLIB_RETURN_TRUE return pylib_PyBool_FromLong(1)
#define PYLIB_RETURN_FALSE return pylib_PyBool_FromLong(0)


typedef int PYS_BOOL;
#define PYS_TRUE      1
#define PYS_FALSE     0


//=========================================================================
// PyShell API
//=========================================================================
typedef unsigned long PYS_RET;
#define PYSR_OK			0x00000000
#define PYSR_FAILED		0x00000005

#if 0
#ifdef EX_OS_WIN32
#	ifdef EX_DEBUG
#		if defined(_M_X64)
#			pragma comment(lib, "pys_64d.lib")
#		elif defined(_M_IX86)
#			pragma comment(lib, "pys_32d.lib")
#		else
#			error unsupport platform.
#		endif
#	else
#		if defined(_M_X64)
#			pragma comment(lib, "pys_64.lib")
#		elif defined(_M_IX86)
#			pragma comment(lib, "pys_32.lib")
#		else
#			error unsupport platform.
#		endif
#	endif
#endif
#endif

#ifdef __cplusplus
extern "C" {
#endif

	typedef void* PYS_HANDLE;

	// 创建一个PyShell句柄，所有操作均对应此句柄进行（一个进程仅有一个句柄）
	PYS_HANDLE pys_create(void);
	// 销毁一个PyShell句柄
	void pys_destroy(PYS_HANDLE* pysh);

	// 使用指定的运行时路径进行初始化（运行时路径中包含pythonXX.dll/python.zip/modules等等）
	PYS_BOOL pys_init_runtime(PYS_HANDLE pysh, const wchar_t* exec_file, const wchar_t* runtime_path);

	// 设置python包搜索路径，可多次调用进行追加（可省略）
	PYS_BOOL pys_add_search_path(PYS_HANDLE pysh, const wchar_t* path);

	// 设置python运行时的命令行参数（可省略）
	void pys_set_argv(PYS_HANDLE pysh, int argc, wchar_t** argv);
	// 追加python运行时的命令行参数（可省略）
	void pys_add_arg(PYS_HANDLE pysh, const wchar_t* arg);
	// 设置python解释器名称（可省略，默认为当前可执行程序文件名的绝对路径）
	void pys_set_program(PYS_HANDLE pysh, const wchar_t* program_name);

	// 设置入口脚本文件名，可以是一个.py文件，也可以是一个.zip文件
	void pys_set_startup_file(PYS_HANDLE pysh, const wchar_t* filename);

	// 设置启动模块名和入口函数名，func_name为NULL时默认执行指定模块中的main函数
	// 本函数可以省略，默认情况下：
	// 如果startup_file是一个.py文件，则默认module_name就是.py文件的文件名本身，
	// 如果startup_file是一个.zip文件，则默认module_name是`pysmain`。
	void pys_set_bootstrap_module(PYS_HANDLE pysh, const char* module_name, const char* func_name);

	// 初始化模块的函数原型
	typedef PyObject* (*pys_init_module_func)(void);

	typedef struct PYS_BUILTIN_FUNC
	{
		const char* py_func_name;	// Python中调用时使用的函数名
		PyCFunction c_func_addr;	// 对应的C的函数
		PYS_BOOL have_args;			// 此函数是否需要参数
		const char* py_func_desc;	// 此函数的文档注释，可以为NULL。
	}PYS_BUILTIN_FUNC;

	typedef enum PYS_CONST_TYPE
	{
		PYS_CONST_BOOL,		// Python中得到 True/False 的值
		PYS_CONST_LONG,		// Python中得到一个整数
		PYS_CONST_STRING,	// Python中得到一个字符串
		PYS_CONST_BYTES		// Python中得到一个Bytes类型数据
	}PYS_CONST_TYPE;

	typedef struct PYS_BUILTIN_CONST
	{
		char* py_const_name;	// Python中调用时使用的变量名
		PYS_CONST_TYPE type;	// 常量类型
		size_t size;			// 常量数据的长度
		void* buffer;			// 常量数据的内容
	}PYS_BUILTIN_CONST;

	// 增加一个内建模块，其中，如果没有函数或常量，那么对应的funcs/consts可以为NULL。
	// 可多次调用本函数来创建多个内建模块。如果多次调用时使用相同的模块名，则函数和常量会追加到此模块中
	// 同一个模块中，函数名和常量名不能重复（但可以通过大小写区分）
	PYS_BOOL pys_add_builtin_module(PYS_HANDLE pysh, const char* module_name, pys_init_module_func init_func);

	PyObject* pys_create_module(const char* module_name, PYS_BUILTIN_FUNC* funcs);
	void pys_builtin_const_bool(PyObject* mod, const char* name, PYS_BOOL val);
	void pys_builtin_const_long(PyObject* mod, const char* name, long val);
	void pys_builtin_const_utf8(PyObject* mod, const char* name, const char* val);		// val 必须是utf8编码的字符串
	void pys_builtin_const_wcs(PyObject* mod, const char* name, const wchar_t* val);
	void pys_builtin_const_bin(PyObject* mod, const char* name, const ex_u8* val, size_t size);

	// 运行python解释器
	int pys_run(PYS_HANDLE pysh);

#ifdef __cplusplus
}
#endif

#ifdef __cplusplus
class PysHandleHolder
{
public:
	PysHandleHolder(PYS_HANDLE h) :m_handle(h) { }
	~PysHandleHolder() { pys_destroy(&m_handle); }
private:
	PYS_HANDLE m_handle;
};
#endif

#endif // __PYS_H__
