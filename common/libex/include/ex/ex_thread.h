#ifndef __EX_THREAD_H__
#define __EX_THREAD_H__

#include "ex_str.h"

#include <list>

#ifdef EX_OS_WIN32
#   include <process.h>
typedef HANDLE EX_THREAD_HANDLE;
#   define EX_THREAD_NULL NULL
#else

#   include <pthread.h>
#   include <sys/time.h>

typedef pthread_t EX_THREAD_HANDLE;

#   if defined(EX_OS_LINUX)
#       define EX_THREAD_NULL 0
#   elif defined(EX_OS_MACOS)
#       define EX_THREAD_NULL nullptr
#   endif

#endif

class ExThreadBase
{
public:
    explicit ExThreadBase(const char* thread_name);
    virtual ~ExThreadBase();

    bool is_running() const
    {
        return m_is_running;
    }

    // 创建并启动线程（执行被重载了的run()函数）
    bool start();
    // 结束线程（等待wait_timeout_ms毫秒，如果wait_timeout_ms为0，则无限等待）
    bool stop();
    // 直接结束线程（强杀，不建议使用）
    bool terminate();

protected:
    // main loop of this thread.
    virtual void _thread_loop() = 0;

    // called by another thread when thread ready to stop.
    virtual void _on_stop()
    {
    };

    // called inside thread when thread fully stopped.
    virtual void _on_stopped()
    {
    };

#ifdef EX_OS_WIN32
    static unsigned int WINAPI _thread_func(LPVOID lpParam);
#else
    static void* _thread_func(void* pParam);
#endif

protected:
    ex_astr          m_thread_name;
    EX_THREAD_HANDLE m_handle;
    bool             m_is_running;
    bool             m_need_stop;
};


// 线程锁（进程内使用）
class ExThreadLock
{
public:
    ExThreadLock();
    virtual ~ExThreadLock();

    void lock();
    void unlock();

private:
#ifdef EX_OS_WIN32
    CRITICAL_SECTION m_locker;
#else
    pthread_mutex_t m_locker;
#endif
};

// 线程锁辅助类
class ExThreadSmartLock
{
public:
    explicit ExThreadSmartLock(ExThreadLock& lock) :
        m_lock(lock)
    {
        m_lock.lock();
    }

    ~ExThreadSmartLock()
    {
        m_lock.unlock();
    }

private:
    ExThreadLock& m_lock;
};

typedef std::list<ExThreadBase*> ex_threads;

class ExThreadManager
{
    friend class ExThreadBase;

public:
    ExThreadManager();
    virtual ~ExThreadManager();

    void stop_all();

    //private:
    void add(ExThreadBase* tb);
    void remove(ExThreadBase* tb);

private:
    ExThreadLock m_lock;
    ex_threads   m_threads;
};

// Event
class ExEventHelper;

class ExEvent
{
    friend class ExEventHelper;

public:
    ExEvent()
    {
#ifdef EX_OS_WIN32
#else
        pthread_mutex_init(&m_mutex, nullptr);
        pthread_cond_init(&m_cond, nullptr);
#endif
    }

    ~ExEvent()
    {
#ifdef EX_OS_WIN32
#else
        pthread_mutex_destroy(&m_mutex);
        pthread_cond_destroy(&m_cond);
#endif
    }

    void wait()
    {
#ifdef EX_OS_WIN32
#else
        pthread_cond_wait(&m_cond, &m_mutex);
#endif
    }

    void wait_timeout_ms(int timeout_ms)
    {
#ifdef EX_OS_WIN32
#else
        // timeval.tv_usec ==== ms
        // timespec.tv_nsec === nano-second
        struct timeval now = {0};
        struct timespec out_time = {0};
        gettimeofday(&now, nullptr);

        uint64_t abs_time_ms = now.tv_sec * 1000ll + now.tv_usec + timeout_ms;
        out_time.tv_sec = abs_time_ms / 1000ll;
        out_time.tv_nsec = (long)((abs_time_ms % 1000ll) * 1000ll);

        pthread_cond_timedwait(&m_cond, &m_mutex, &out_time);
#endif
    }

    void signal()
    {
#ifdef EX_OS_WIN32
#else
        pthread_cond_signal(&m_cond);
#endif
    }

private:
#ifdef EX_OS_WIN32
#else
    pthread_mutex_t m_mutex;
    pthread_cond_t m_cond;
#endif
};

class ExEventHelper
{
public:
    explicit ExEventHelper(ExEvent& event) :
            m_event(event)
    {
#ifdef EX_OS_WIN32
#else
        pthread_mutex_lock(&m_event.m_mutex);
#endif
    }

    ~ExEventHelper()
    {
#ifdef EX_OS_WIN32
#else
        pthread_mutex_unlock(&m_event.m_mutex);
#endif
    }

private:
    ExEvent& m_event;
};

// 原子操作
int ex_atomic_add(volatile int* pt, int t);

int ex_atomic_inc(volatile int* pt);

int ex_atomic_dec(volatile int* pt);

// 线程相关操作
uint64_t ex_get_thread_id();

#endif // __EX_THREAD_H__
