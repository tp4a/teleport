#ifndef THR_DOWNLOAD_H
#define THR_DOWNLOAD_H

#include <QThread>
#include <QNetworkReply>
#include <QFile>
#include <QEventLoop>

class ThrDownload : public QThread {
    Q_OBJECT

//public:
//    enum State {
//        statStarting,
//        statDownloading,
//        statInvalidParam,
//        statFailDone,
//        statSuccessDone
//    };

public:
    ThrDownload();
    ~ThrDownload();

    bool init(const QString& local_data_path_base, const QString& res);

    virtual void run();
    void stop();

    bool is_running() const {return m_running;}

    bool is_tpr_downloaded() const {return m_have_tpr;}
    bool is_tpk_downloaded() const {return m_have_tpk;}
    bool is_tpd_downloaded(uint32_t file_idx) const;
    bool get_data_path(QString& path) const {
        if(m_data_path.isEmpty())
            return false;
        path = m_data_path;
        return true;
    }

private:
    void _run();

    bool _download_tpr();
    bool _download_tpk();

    bool _download_file(const QString& url, const QString filename);
    bool _download_file(const QString& url, QByteArray& data);

private:
    bool m_need_stop;

    QString m_data_path_base;

    QString m_url_base;
    QString m_sid;
    QString m_rid;
    QString m_data_path;

    bool m_running;
    bool m_have_tpr;
    bool m_have_tpk;
    bool m_need_tpk;

    uint32_t m_tpd_count;
    bool* m_have_tpd;

    QString m_error;
};

#endif // THR_DOWNLOAD_H
