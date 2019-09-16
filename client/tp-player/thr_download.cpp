#include "thr_download.h"
#include <QDebug>

ThreadDownload::ThreadDownload(const QString& url)
{
    m_url = url;
    m_need_stop = false;
}

void ThreadDownload::stop() {
    if(!isRunning())
        return;
    m_need_stop = true;
    wait();
    qDebug() << "download thread end.";
}

bool ThreadDownload::prepare(QString& path_base, QString& msg) {
    path_base = m_path_base;
    return true;
}


void ThreadDownload::run() {
    for(int i = 0; i < 500; i++) {
        if(m_need_stop)
            break;
        msleep(100);

        if(i == 50) {
            m_path_base = "/Users/apex/Desktop/tp-testdata/";
        }
    }
}
