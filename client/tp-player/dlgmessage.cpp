#include "dlgmessage.h"
#include "ui_dlgmessage.h"

DlgMessage::DlgMessage(QWidget *parent) :
    QDialog(parent),
    ui(new Ui::DlgMessage)
{
    ui->setupUi(this);
}

DlgMessage::~DlgMessage()
{
    delete ui;
}

void DlgMessage::set_text(const QString& text) {
    // TODO: 根据文字长度，父窗口宽度，调节对话框宽度，最大不超过父窗口宽度的 2/3。
    // 调节label的宽度和高度，并调节对话框高度，最后将对话框调整到父窗口居中的位置。

    ui->label->setText(text);
}
