#include "downloader.h"
#include "record_format.h"

#include <QEventLoop>
#include <QNetworkReply>
#include <qelapsedtimer.h>

Downloader::Downloader() : QObject () {
    m_data = nullptr;
    m_reply = nullptr;
    m_result = false;
}

Downloader::~Downloader() {
}

bool Downloader::request(const QString& url, const QString& sid, const QString& filename) {
    return _request(url, sid, filename, nullptr);
}

bool Downloader::request(const QString& url, const QString& sid, QByteArray* data) {
    QString fname;
    return _request(url, sid, fname, data);
}

bool Downloader::_request(const QString& url, const QString& sid, const QString& filename, QByteArray* data) {
    if(filename.isEmpty() && data == nullptr)
        return false;
    if(!filename.isEmpty() && data != nullptr)
        return false;
    m_data = data;

    if(!filename.isEmpty()) {
        m_file.setFileName(filename);
        if(!m_file.open(QIODevice::WriteOnly | QFile::Truncate)){
            qDebug("open file for write failed.");
            return false;
        }
    }

    QString cookie = QString("_sid=%1\r\n").arg(sid);

    QNetworkRequest req;
    req.setUrl(QUrl(url));
    req.setRawHeader("Cookie", cookie.toLatin1());

    QNetworkAccessManager* nam = new QNetworkAccessManager();
    QEventLoop eloop;
    m_reply = nam->get(req);

    connect(m_reply, &QNetworkReply::finished, &eloop, &QEventLoop::quit);
    connect(m_reply, &QNetworkReply::finished, this, &Downloader::_on_finished);
    connect(m_reply, &QIODevice::readyRead, this, &Downloader::_on_data_ready);

//    qDebug("before eventLoop.exec(%p)", &eloop);
    eloop.exec();
//    qDebug("after eventLoop.exec()");

    disconnect(m_reply, &QNetworkReply::finished, &eloop, &QEventLoop::quit);
    disconnect(m_reply, &QNetworkReply::finished, this, &Downloader::_on_finished);
    disconnect(m_reply, &QIODevice::readyRead, this, &Downloader::_on_data_ready);

    delete m_reply;
    m_reply = nullptr;
    delete nam;

    qDebug("Downloader::_request() end.");
    return m_result;
}

void Downloader::_on_data_ready() {
//    qDebug("Downloader::_on_data_ready(%p).", this);
    QNetworkReply *reply = reinterpret_cast<QNetworkReply*>(sender());

    if(m_data != nullptr) {
        m_data->push_back(reply->readAll());
    }
    else {
        m_file.write(reply->readAll());
    }
}

void Downloader::abort() {
    if(m_reply) {
        qDebug("Downloader::abort().");
        m_reply->abort();
    }
}

void Downloader::_on_finished() {
//    qDebug("Downloader::_on_finished(%p).", this);
    QNetworkReply *reply = reinterpret_cast<QNetworkReply*>(sender());

    QVariant statusCode = reply->attribute(QNetworkRequest::HttpStatusCodeAttribute);

    if (reply->error() != QNetworkReply::NoError) {
        // reply->abort() got "Operation canceled"
        //QString strError = reply->errorString();
        qDebug() << "ERROR:" << reply->errorString();
        if(m_data == nullptr) {
            m_file.flush();
            m_file.close();
        }
        m_result = false;
        return;
    }

    if(m_data != nullptr) {
        m_data->push_back(reply->readAll());
    }
    else {
        m_file.write(reply->readAll());
        m_file.flush();
        m_file.close();
    }

    reply->deleteLater();

    m_result = true;
}
