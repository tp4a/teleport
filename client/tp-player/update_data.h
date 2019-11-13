#ifndef UPDATE_DATA_H
#define UPDATE_DATA_H

#include <QObject>
#include <QVector>
#include "record_format.h"

#define TYPE_UNKNOWN            0
#define TYPE_HEADER_INFO        1

#define TYPE_DISABLE_DRAW       5
#define TYPE_ENABLE_DRAW        6

#define TYPE_POINTER            10
#define TYPE_IMAGE              11
#define TYPE_KEYFRAME           12
#define TYPE_PLAYED_MS          20
#define TYPE_DOWNLOAD_PERCENT   21
#define TYPE_END                50
#define TYPE_MESSAGE            90
#define TYPE_ERROR              91


typedef struct UPDATE_IMAGE {
    int x;
    int y;
    int w;
    int h;
    QImage* img;
}UPDATE_IMAGE;

typedef QVector<UPDATE_IMAGE> UpdateImages;

class UpdateData : public QObject
{
    Q_OBJECT
public:
    explicit UpdateData();
    explicit UpdateData(int data_type);
    explicit UpdateData(int data_type, uint32_t time_ms);
    explicit UpdateData(const TS_RECORD_HEADER& hdr);
    //explicit UpdateData(uint16_t screen_w, uint16_t screen_h);
    virtual ~UpdateData();

    void set_pointer(uint32_t ts, const TS_RECORD_RDP_POINTER* p);

//    bool parse(const TS_RECORD_PKG& pkg, const QByteArray& data);
    TS_RECORD_HEADER* get_header() {return m_hdr;}
    TS_RECORD_RDP_POINTER* get_pointer() {return m_pointer;}
    UpdateImages& get_images() {return m_images;}
    const UpdateImages& get_images() const {return m_images;}

    uint32_t get_time() {return m_time_ms;}

    void alloc_data(uint32_t len);
    void attach_data(const uint8_t* dat, uint32_t len);

    int data_type() const {return m_data_type;}

    uint8_t* data_buf() {return m_data_buf;}
    uint32_t data_len() const {return m_data_len;}

    void played_ms(uint32_t ms) {m_played_ms = ms;}
    uint32_t played_ms() {return m_played_ms;}

    void message(const QString& msg) {m_msg = msg;}
    const QString message(){return m_msg;}

private:
    void _init(void);

signals:

public slots:


private:
    int m_data_type;
    uint32_t m_time_ms;
    uint8_t* m_data_buf;
    uint32_t m_data_len;
    uint32_t m_played_ms;
    QString m_msg;

    // for HEADER
    TS_RECORD_HEADER* m_hdr;
    // for POINTER
    TS_RECORD_RDP_POINTER* m_pointer;
    // for IMAGE
//    QImage* m_img;
//    int m_img_x;
//    int m_img_y;
//    int m_img_w;
//    int m_img_h;
    UpdateImages m_images;

//    TS_RECORD_RDP_IMAGE_INFO* m_img_info;

    uint16_t m_screen_w;
    uint16_t m_screen_h;
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
