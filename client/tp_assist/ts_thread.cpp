#include "stdafx.h"
#include "ts_thread.h"

//=========================================================
//
//=========================================================


#ifdef EX_OS_WIN32
unsigned int WINAPI TsThreadBase::_thread_func(LPVOID lpParam)
{
	TsThreadBase* p = (TsThreadBase*)lpParam;
	p->m_is_running = true;
	p->_thread_loop();
	p->m_is_running = false;
	//_endthreadex(0);
	if(!p->m_stop_by_request)
		p->m_thread_manager->_remove_thread(p);
	return 0;
}
#else
void* TsThreadBase::_thread_func(void* pParam)
{
	TsThreadBase* p = (TsThreadBase*)pParam;
	p->m_is_running = true;
	p->_thread_loop();
	p->m_is_running = false;
	if(!p->m_stop_by_request)
		p->m_thread_manager->_remove_thread(p);
	return NULL;
}
#endif

TsThreadBase::TsThreadBase(TsThreadManager* tm, const char* thread_name) :
	m_thread_manager(tm),
	m_handle(0),
	m_is_running(false),
	m_stop_by_request(false)
{
	m_thread_name = thread_name;
	m_thread_manager->_add_thread(this);
}

TsThreadBase::~TsThreadBase()
{
}

bool TsThreadBase::start(void)
{
	TSLOGV(" -- thread [%s] starting.\n", m_thread_name.c_str());
#ifdef WIN32
	HANDLE h = (HANDLE)_beginthreadex(NULL, 0, _thread_func, (void*)this, 0, NULL);

	if (NULL == h)
	{
		return false;
	}
	m_handle = h;
#else
	pthread_t ptid = 0;
	int ret = pthread_create(&ptid, NULL, _thread_func, (void*)this);
	if (ret != 0)
	{
		return false;
	}
	m_handle = ptid;

#endif

	return true;
}

bool TsThreadBase::stop(void)
{
	TSLOGV(" . try to stop thread [%s].\n", m_thread_name.c_str());
	m_stop_by_request = true;
	_set_stop_flag();

	TSLOGV(" . wait thread [%s] end.\n", m_thread_name.c_str());

#ifdef EX_OS_WIN32
	if (WaitForSingleObject(m_handle, INFINITE) != WAIT_OBJECT_0)
	{
		return false;
	}
#else
	if (pthread_join(m_handle, NULL) != 0)
	{
		return false;
	}
#endif
	TSLOGV(" ## thread [%s] end.\n", m_thread_name.c_str());

	return true;
}

bool TsThreadBase::terminate(void)
{
#ifdef EX_OS_WIN32
	return TerminateThread(m_handle, 1) ? true : false;
#else
	return pthread_cancel(m_handle) == 0 ? true : false;
#endif
}


//=========================================================
//
//=========================================================

TsThreadManager::TsThreadManager()
{}

TsThreadManager::~TsThreadManager()
{
	if (m_threads.size() > 0)
	{
		TSLOGE("[ERROR] when destroy thread manager, there are %d thread not exit.\n", m_threads.size());
		stop_all();
	}
}

void TsThreadManager::stop_all(void)
{
	TsThreadSmartLock locker(m_lock);

	ts_threads::iterator it = m_threads.begin();
	for (; it != m_threads.end(); ++it)
	{
		(*it)->stop();
		delete (*it);
	}
	m_threads.clear();
}

void TsThreadManager::_add_thread(TsThreadBase* tb)
{
	TsThreadSmartLock locker(m_lock);

	ts_threads::iterator it = m_threads.begin();
	for (; it != m_threads.end(); ++it)
	{
		if ((*it) == tb)
		{
			TSLOGE("[ERROR] when add thread to manager, it already exist.\n");
			return;
		}
	}

	m_threads.push_back(tb);
}

void TsThreadManager::_remove_thread(TsThreadBase* tb)
{
	TsThreadSmartLock locker(m_lock);

	ts_threads::iterator it = m_threads.begin();
	for (; it != m_threads.end(); ++it)
	{
		if ((*it) == tb)
		{
			delete (*it);
			m_threads.erase(it);
			return;
		}
	}
	TSLOGE("[ERROR] when remove thread from manager, it not exist.\n");
}

//=========================================================
//
//=========================================================

TsThreadLock::TsThreadLock()
{
#ifdef EX_OS_WIN32
	InitializeCriticalSection(&m_locker);
#else
	pthread_mutexattr_t attr;
	pthread_mutexattr_init(&attr);
	pthread_mutexattr_settype(&attr, PTHREAD_MUTEX_RECURSIVE);
	pthread_mutex_init(&m_locker, &attr);
	pthread_mutexattr_destroy(&attr);
#endif
}

TsThreadLock::~TsThreadLock()
{
#ifdef EX_OS_WIN32
	DeleteCriticalSection(&m_locker);
#else
	pthread_mutex_destroy(&m_locker);
#endif
}

void TsThreadLock::lock(void)
{
#ifdef EX_OS_WIN32
	EnterCriticalSection(&m_locker);
#else
	pthread_mutex_lock(&m_locker);
#endif
}

void TsThreadLock::unlock(void)
{
#ifdef EX_OS_WIN32
	LeaveCriticalSection(&m_locker);
#else
	pthread_mutex_unlock(&m_locker);
#endif
}

//=========================================================
//
//=========================================================

int ts_atomic_add(volatile int* pt, int t)
{
#ifdef EX_OS_WIN32
	return (int)InterlockedExchangeAdd((long*)pt, (long)t);
#else
	return __sync_add_and_fetch(pt, t);
#endif
}

int ts_atomic_inc(volatile int* pt)
{
#ifdef EX_OS_WIN32
	return (int)InterlockedIncrement((long*)pt);
#else
	return __sync_add_and_fetch(pt, 1);
#endif
}

int ts_atomic_dec(volatile int* pt)
{
#ifdef EX_OS_WIN32
	return (int)InterlockedDecrement((long*)pt);
#else
	return __sync_add_and_fetch(pt, -1);
#endif
}


