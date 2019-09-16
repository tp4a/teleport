#ifndef DLGMESSAGE_H
#define DLGMESSAGE_H

#include <QDialog>

namespace Ui {
class DlgMessage;
}

class DlgMessage : public QDialog
{
    Q_OBJECT

public:
    explicit DlgMessage(QWidget *parent = nullptr);
    ~DlgMessage();

    void set_text(const QString& text);

private:
    Ui::DlgMessage *ui;
};

#endif // DLGMESSAGE_H
