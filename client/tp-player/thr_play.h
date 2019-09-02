#ifndef THR_PLAY_H
#define THR_PLAY_H

#include <QThread>
#include "update_data.h"


class ThreadPlay : public QThread
{
    Q_OBJECT
public:
    ThreadPlay();

    virtual void run();
    void stop();


signals:
    void signal_update_data(update_data*);

private:
    bool m_need_stop;
};

#endif // THR_PLAY_H
