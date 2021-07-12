#ifndef TP_PLAYER_UTIL_H
#define TP_PLAYER_UTIL_H

#include <QElapsedTimer>

class TimeUseTest {
public:
    TimeUseTest() {
        m_used_ms = 0;
        m_count = 0;
    }
    ~TimeUseTest() {}

    void begin() {
        m_time.start();
    }
    void end() {
        m_count++;
        m_used_ms += m_time.elapsed();
    }

    uint32_t used() const {return m_used_ms;}
    uint32_t count() const {return m_count;}

private:
    QElapsedTimer m_time;
    uint32_t m_used_ms;
    uint32_t m_count;
};

#define LOCAL8BIT(x) QString::fromLocal8Bit(x)

#endif // TP_PLAYER_UTIL_H
