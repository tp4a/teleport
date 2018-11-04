#include <ex/ex_thread.h>
#include <ex/ex_log.h>

//=========================================================
//
//=========================================================


#ifdef EX_OS_WIN32
unsigned int WINAPI ExThreadBase::_thread_func(LPVOID pParam)
#else

void *ExThreadBase::_thread_func(void *pParam)
#endif
{
    ExThreadBase *_this = (ExThreadBase *) pParam;

    _this->m_is_running = true;
    _this->_thread_loop();
    _this->m_is_running = false;
    _this->m_handle = 0;

    EXLOGV("  # thread [%s] exit.\n", _this->m_thread_name.c_str());
    _this->_on_stopped();
    return 0;
}

ExThreadBase::ExThreadBase(const char *thread_name) :
        m_handle(0),
        m_is_running(false),
        m_need_stop(false) {
    m_thread_name = thread_name;
}

ExThreadBase::~ExThreadBase() {
    if(m_is_running) {
        EXLOGE("  # thread [%s] not stop before destroy.\n", m_thread_name.c_str());
    }
}

bool ExThreadBase::start(void) {
    m_need_stop = false;
    EXLOGV("  . thread [%s] starting.\n", m_thread_name.c_str());
#ifdef WIN32
    HANDLE h = (HANDLE)_beginthreadex(NULL, 0, _thread_func, (void*)this, 0, NULL);

    if (NULL == h)
    {
        return false;
    }
    m_handle = h;
#else
    pthread_t ptid = 0;
    int ret = pthread_create(&ptid, NULL, _thread_func, (void *) this);
    if (ret != 0) {
        return false;
    }
    m_handle = ptid;

#endif

    return true;
}

bool ExThreadBase::stop(void) {
    if (m_handle == 0) {
        EXLOGW("[thread] thread [%s] already stopped.\n", m_thread_name.c_str());
        return true;
    }

    EXLOGV("[thread] try to stop thread [%s].\n", m_thread_name.c_str());
    m_need_stop = true;
    _on_stop();

    EXLOGV("[thread] wait thread [%s] exit.\n", m_thread_name.c_str());

#ifdef EX_OS_WIN32
    if (WaitForSingleObject(m_handle, INFINITE) != WAIT_OBJECT_0)
    {
        return false;
    }
#else
    if (pthread_join(m_handle, NULL) != 0) {
        return false;
    }
#endif

    return true;
}

bool ExThreadBase::terminate(void) {
#ifdef EX_OS_WIN32
    return (TerminateThread(m_handle, 1) == TRUE);
#else
    return (pthread_cancel(m_handle) == 0);
#endif
}

//=========================================================
//
//=========================================================

ExThreadManager::ExThreadManager() {}

ExThreadManager::~ExThreadManager() {
    if (!m_threads.empty()) {
        EXLOGE("when destroy thread manager, there are %d thread not exit.\n", m_threads.size());
        stop_all();
    }
}

void ExThreadManager::stop_all(void) {
    ExThreadSmartLock locker(m_lock);

    ex_threads::iterator it = m_threads.begin();
    for (; it != m_threads.end(); ++it) {
        (*it)->stop();
    }
    m_threads.clear();
}

void ExThreadManager::add(ExThreadBase *tb) {
    ExThreadSmartLock locker(m_lock);

    ex_threads::iterator it = m_threads.begin();
    for (; it != m_threads.end(); ++it) {
        if ((*it) == tb) {
            EXLOGE("when add thread to manager, it already exist.\n");
            return;
        }
    }

    m_threads.push_back(tb);
}

void ExThreadManager::remove(ExThreadBase *tb) {
    ExThreadSmartLock locker(m_lock);

    ex_threads::iterator it = m_threads.begin();
    for (; it != m_threads.end(); ++it) {
        if ((*it) == tb) {
            m_threads.erase(it);
            return;
        }
    }
    EXLOGE("thread not hold by thread-manager while remove it.\n");
}

//=========================================================
//
//=========================================================

ExThreadLock::ExThreadLock() {
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

ExThreadLock::~ExThreadLock() {
#ifdef EX_OS_WIN32
    DeleteCriticalSection(&m_locker);
#else
    pthread_mutex_destroy(&m_locker);
#endif
}

void ExThreadLock::lock(void) {
#ifdef EX_OS_WIN32
    EnterCriticalSection(&m_locker);
#else
    pthread_mutex_lock(&m_locker);
#endif
}

void ExThreadLock::unlock(void) {
#ifdef EX_OS_WIN32
    LeaveCriticalSection(&m_locker);
#else
    pthread_mutex_unlock(&m_locker);
#endif
}

//=========================================================
//
//=========================================================

int ex_atomic_add(volatile int *pt, int t) {
#ifdef EX_OS_WIN32
    return (int)InterlockedExchangeAdd((long*)pt, (long)t);
#else
    return __sync_add_and_fetch(pt, t);
#endif
}

int ex_atomic_inc(volatile int *pt) {
#ifdef EX_OS_WIN32
    return (int)InterlockedIncrement((long*)pt);
#else
    return __sync_add_and_fetch(pt, 1);
#endif
}

int ex_atomic_dec(volatile int *pt) {
#ifdef EX_OS_WIN32
    return (int)InterlockedDecrement((long*)pt);
#else
    return __sync_add_and_fetch(pt, -1);
#endif
}


ex_u64 ex_get_thread_id(void) {
#ifdef EX_OS_WIN32
    return GetCurrentThreadId();
#else
    return (ex_u64) pthread_self();
#endif
}
