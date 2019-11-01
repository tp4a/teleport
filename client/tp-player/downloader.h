#ifndef DOWNLOADER_H
#define DOWNLOADER_H

#include <QFile>
#include <QNetworkAccessManager>

class Downloader : public QObject {
    Q_OBJECT

public:
    // 从url下载数据，写入到filename文件中，或放入data中。
    Downloader();
    ~Downloader();

    bool request(const QString& url, const QString& sid, const QString& filename);
    bool request(const QString& url, const QString& sid, QByteArray* data);
    void abort();

private:
    bool _request(const QString& url, const QString& sid, const QString& filename, QByteArray* data);

private slots:
    void _on_data_ready();  // 有数据可读了，读取并写入文件
    void _on_finished();    // 下载结束了

private:
    QFile m_file;
    QByteArray* m_data;

    bool m_result;
    QNetworkReply* m_reply;
};

typedef struct DownloadParam {
    QString url;
    QString sid;
    QString fname;
}DownloadParam;

#endif
