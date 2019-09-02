#ifndef UPDATE_DATA_H
#define UPDATE_DATA_H

#include <QObject>

class update_data : public QObject
{
    Q_OBJECT
public:
    explicit update_data(QObject *parent = nullptr);
    virtual ~update_data();

    void alloc_data(uint32_t len);
    void attach_data(const uint8_t* dat, uint32_t len);

    void data_type(int dt) {m_data_type = dt;}
    int data_type() const {return m_data_type;}

    uint8_t* data_buf() {return m_data_buf;}
    uint32_t data_len() const {return m_data_len;}

signals:

public slots:


private:
    int m_data_type;
    uint8_t* m_data_buf;
    uint32_t m_data_len;
};

#endif // UPDATE_DATA_H
