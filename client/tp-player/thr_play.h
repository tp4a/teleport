#ifndef THR_PLAY_H
#define THR_PLAY_H

#include <QThread>
#include "update_data.h"
#include "thr_download.h"

class ThreadPlay : public QThread
{
    Q_OBJECT
public:
    ThreadPlay(const QString& res);
    ~ThreadPlay();

    virtual void run();
    void stop();
    void pause() {m_need_pause = true;}
    void resume() {m_need_pause = false;}
    void speed(int s) {if(s >= 1 && s <= 16) m_speed = s;}

private:
    void _notify_message(const QString& msg);
    void _notify_error(const QString& err_msg);

signals:
    void signal_update_data(update_data*);

private:
    bool m_need_stop;
    bool m_need_pause;
    int m_speed;

    QString m_res;
    bool m_need_download;

    ThreadDownload* m_thr_download;
};

#endif // THR_PLAY_H
