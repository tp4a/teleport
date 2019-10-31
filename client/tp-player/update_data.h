#ifndef UPDATE_DATA_H
#define UPDATE_DATA_H

#include <QObject>

#define TYPE_HEADER_INFO        0
#define TYPE_DATA               1
#define TYPE_PLAYED_MS          2
#define TYPE_DOWNLOAD_PERCENT   3
#define TYPE_END                4
#define TYPE_MESSAGE            5
#define TYPE_ERROR              6

class UpdateData : public QObject
{
    Q_OBJECT
public:
    explicit UpdateData(int data_type, QObject *parent = nullptr);
    virtual ~UpdateData();

    void alloc_data(uint32_t len);
    void attach_data(const uint8_t* dat, uint32_t len);

    int data_type() const {return m_data_type;}

    uint8_t* data_buf() {return m_data_buf;}
    uint32_t data_len() const {return m_data_len;}

    void played_ms(uint32_t ms) {m_played_ms = ms;}
    uint32_t played_ms() {return m_played_ms;}

    void message(const QString& msg) {m_msg = msg;}
    const QString message(){return m_msg;}

signals:

public slots:


private:
    int m_data_type;
    uint8_t* m_data_buf;
    uint32_t m_data_len;
    uint32_t m_played_ms;
    QString m_msg;
};

class UpdateDataHelper {
public:
    UpdateDataHelper(UpdateData* data) {
        m_data = data;
    }
    ~UpdateDataHelper() {
        if(m_data)
            delete m_data;
    }

private:
    UpdateData* m_data;
};


#endif // UPDATE_DATA_H
