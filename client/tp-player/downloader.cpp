#include "downloader.h"
#include "record_format.h"

#include <QNetworkReply>
#include <qelapsedtimer.h>


// TODO: 将Downloader的实现代码迁移到ThrData线程中
// 使用局部event循环的方式进行下载
/*
QEventLoop eventLoop;
connect(netWorker, &NetWorker::finished,
        &eventLoop, &QEventLoop::quit);
QNetworkReply *reply = netWorker->get(url);
replyMap.insert(reply, FetchWeatherInfo);
eventLoop.exec();
*/


//=================================================================
// Downloader
//=================================================================
Downloader::Downloader() {
    m_reply = nullptr;
    m_code = codeUnknown;
}

Downloader::~Downloader() {
}

void Downloader::run(QNetworkAccessManager* nam, QString& url, QString& sid, QString& filename) {
    m_filename = filename;

    if(!m_filename.isEmpty()) {
        m_file.setFileName(m_filename);
        if(!m_file.open(QIODevice::WriteOnly | QFile::Truncate)){
            qDebug("open file for write failed.");
            return;
        }
    }

    m_code = codeDownloading;
    QString cookie = QString("_sid=%1\r\n").arg(sid);

    QNetworkRequest req;
    req.setUrl(QUrl(url));
    req.setRawHeader("Cookie", cookie.toLatin1());

    m_reply = nam->get(req);
    connect(m_reply, &QNetworkReply::finished, this, &Downloader::_on_finished);
    connect(m_reply, &QIODevice::readyRead, this, &Downloader::_on_data_ready);
}

void Downloader::_on_data_ready() {
    QNetworkReply *reply = reinterpret_cast<QNetworkReply*>(sender());

    if(m_filename.isEmpty()) {
        m_data += reply->readAll();
    }
    else {
        m_file.write(reply->readAll());
    }
}

void Downloader::reset() {
    m_code = codeUnknown;
}

void Downloader::abort() {
    if(m_reply)
        m_reply->abort();
}

void Downloader::_on_finished() {
    qDebug("download finished");
    QNetworkReply *reply = reinterpret_cast<QNetworkReply*>(sender());

    QVariant statusCode = reply->attribute(QNetworkRequest::HttpStatusCodeAttribute);

    if (reply->error() != QNetworkReply::NoError) {
        // reply->abort() got "Operation canceled"
        //QString strError = reply->errorString();
        //qDebug() << strError;
        m_file.flush();
        m_file.close();
        m_code = codeFailed;
        return;
    }

    disconnect(m_reply, &QNetworkReply::finished, this, &Downloader::_on_finished);
    disconnect(m_reply, &QIODevice::readyRead, this, &Downloader::_on_data_ready);
//    reply->deleteLater();

    if(m_filename.isEmpty()) {
        m_data += reply->readAll();
    }
    else {
        m_file.write(reply->readAll());
        m_file.flush();
        m_file.close();
    }

    reply->deleteLater();

    m_code = codeSuccess;
}
