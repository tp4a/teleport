#include "downloader.h"
#include "record_format.h"

#include <QEventLoop>
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
    m_code = codeDownloading;
}

Downloader::~Downloader() {
//    qDebug("Downloader destroied.");
}

void Downloader::run(QNetworkAccessManager* nam, const QString& url, const QString& sid, const QString& filename) {
    m_code = codeDownloading;
    m_filename = filename;

    if(!m_filename.isEmpty()) {
        m_file.setFileName(m_filename);
        if(!m_file.open(QIODevice::WriteOnly | QFile::Truncate)){
            qDebug("open file for write failed.");
            m_code = codeFailed;
            return;
        }
    }

    QString cookie = QString("_sid=%1\r\n").arg(sid);

    QNetworkRequest req;
    req.setUrl(QUrl(url));
    req.setRawHeader("Cookie", cookie.toLatin1());

    QEventLoop eventLoop;
    m_reply = nam->get(req);
    connect(m_reply, &QNetworkReply::finished, &eventLoop, &QEventLoop::quit);
    connect(m_reply, &QNetworkReply::finished, this, &Downloader::_on_finished);
    connect(m_reply, &QIODevice::readyRead, this, &Downloader::_on_data_ready);

    eventLoop.exec();

    disconnect(m_reply, &QNetworkReply::finished, &eventLoop, &QEventLoop::quit);
    disconnect(m_reply, &QNetworkReply::finished, this, &Downloader::_on_finished);
    disconnect(m_reply, &QIODevice::readyRead, this, &Downloader::_on_data_ready);
    delete m_reply;
    m_reply = nullptr;
    qDebug("Downloader::run(%p) end.", this);
}

void Downloader::_on_data_ready() {
//    qDebug("Downloader::_on_data_ready(%p).", this);
    QNetworkReply *reply = reinterpret_cast<QNetworkReply*>(sender());

    if(m_filename.isEmpty()) {
        m_data += reply->readAll();
    }
    else {
        m_file.write(reply->readAll());
    }
}

void Downloader::abort() {
    if(m_reply) {
        qDebug("Downloader::abort(%p);", this);
        m_reply->abort();
        m_code = codeAbort;
    }
}

void Downloader::_on_finished() {
//    qDebug("Downloader::_on_finished(%p).", this);
    QNetworkReply *reply = reinterpret_cast<QNetworkReply*>(sender());

    QVariant statusCode = reply->attribute(QNetworkRequest::HttpStatusCodeAttribute);

    if (reply->error() != QNetworkReply::NoError) {
        // reply->abort() got "Operation canceled"
        //QString strError = reply->errorString();
        //qDebug() << strError;
        m_file.flush();
        m_file.close();
        if(m_code != codeDownloading)
            m_code = codeFailed;
        return;
    }

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
