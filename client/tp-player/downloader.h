#ifndef DOWNLOADER_H
#define DOWNLOADER_H

#include <QFile>
#include <QNetworkAccessManager>

class Downloader : public QObject {
    Q_OBJECT

public:
    enum EndCode{
        codeUnknown = 0,
        codeSuccess,
        codeDownloading,
        codeFailed
    };

public:
    // 从url下载数据，写入到filename文件中，如果filename为空字符串，则保存在内存中，可通过 data() 获取。
    Downloader();
    ~Downloader();

    void run(QNetworkAccessManager* nam, QString& url, QString& sid, QString& filename);
    void abort();
    void reset();
    QByteArray& data(){return m_data;}

    EndCode code() {return m_code;}

private slots:
    void _on_data_ready();  // 有数据可读了，读取并写入文件
    void _on_finished();    // 下载结束了

private:
    QString m_filename;
    QFile m_file;
    QByteArray m_data;

    QNetworkReply* m_reply;

    EndCode m_code;
};

typedef struct DownloadParam {
    QString url;
    QString sid;
    QString fname;
}DownloadParam;

#endif
