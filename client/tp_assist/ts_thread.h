#ifndef __TS_THREAD_H__
#define __TS_THREAD_H__

#include <ex.h>
#include <list>

#ifdef EX_OS_WIN32
#	include <process.h>
typedef HANDLE TS_THREAD_HANDLE;
#else
#	include <pthread.h>
typedef pthread_t TS_THREAD_HANDLE;
#endif

class TsThreadManager;

class TsThreadBase
{
public:
	TsThreadBase(TsThreadManager* tm, const char* thread_name);
	virtual ~TsThreadBase();

	bool is_running(void) { return m_is_running; }

	// 创建并启动线程（执行被重载了的run()函数）
	bool start(void);
	// 结束线程（等待wait_timeout_ms毫秒，如果wait_timeout_ms为0，则无限等待）
	bool stop(void);
	// 直接结束线程（强杀，不建议使用）
	bool terminate(void);

protected:
	// 线程循环
	virtual void _thread_loop(void) = 0;
	// 设置停止标志，让线程能够正常结束
	virtual void _set_stop_flag(void) = 0;

#ifdef EX_OS_WIN32
	static unsigned int WINAPI _thread_func(LPVOID lpParam);
#else
	static void* _thread_func(void * pParam);
#endif

protected:
	TsThreadManager* m_thread_manager;
	ex_astr m_thread_name;
	TS_THREAD_HANDLE m_handle;
	bool m_is_running;
	bool m_stop_by_request;
};


// 线程锁（进程内使用）
class TsThreadLock
{
public:
	TsThreadLock();
	virtual ~TsThreadLock();

	void lock(void);
	void unlock(void);

private:
#ifdef EX_OS_WIN32
	CRITICAL_SECTION m_locker;
#else
	pthread_mutex_t m_locker;
#endif
};

// 线程锁辅助类
class TsThreadSmartLock
{
public:
	TsThreadSmartLock(TsThreadLock& lock) : m_lock(lock)
	{
		m_lock.lock();
	}
	~TsThreadSmartLock()
	{
		m_lock.unlock();
	}

private:
	TsThreadLock& m_lock;
};

typedef std::list<TsThreadBase*> ts_threads;

class TsThreadManager
{
	friend class TsThreadBase;

public:
	TsThreadManager();
	virtual ~TsThreadManager();

	void stop_all(void);

private:
	void _add_thread(TsThreadBase* tb);
	void _remove_thread(TsThreadBase* tb);

private:
	TsThreadLock m_lock;
	ts_threads m_threads;
};


// 原子操作
int ts_atomic_add(volatile int* pt, int t);
int ts_atomic_inc(volatile int* pt);
int ts_atomic_dec(volatile int* pt);

#endif // __TS_THREAD_H__
