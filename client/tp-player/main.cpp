#include "mainwindow.h"
#include <QApplication>
#include <QCommandLineParser>
#include <QDebug>
#include <QMessageBox>
#include <QTextCodec>

// 编译出来的可执行程序复制到单独目录，然后执行 windeployqt 应用程序文件名
// 即可自动将依赖的动态库等复制到此目录中。有些文件是多余的，可以酌情删除。

int main(int argc, char *argv[])
{
//#if (QT_VERSION >= QT_VERSION_CHECK(5, 6, 0))
//    QCoreApplication::setAttribute(Qt::AA_EnableHighDpiScaling);
//#endif

    QApplication a(argc, argv);

    QGuiApplication::setApplicationDisplayName("TP-Player");

    QCommandLineParser parser;
    const QCommandLineOption opt_help = parser.addHelpOption();

    parser.addPositionalArgument("RESOURCE", "teleport record resource to be play.");

    if(!parser.parse(QCoreApplication::arguments())) {
        QMessageBox::warning(nullptr, QGuiApplication::applicationDisplayName(),
                             //"<html><head/><body><h2 style=\"color:#ff0000;\">" + parser.errorText() + "</h2><pre>"
                             "<html><head/><body><h2>" + parser.errorText() + "</h2><pre>"
                             + parser.helpText() + "</pre></body></html>");
        return 1;
    }

    if(parser.isSet(opt_help)) {
        QMessageBox::warning(nullptr, QGuiApplication::applicationDisplayName(),
                             "<html><head/><body><pre>"
                             + parser.helpText()
                             + "\n\n"
                             + "RESOURCE could be:\n"
                             + "    teleport record file (.tpr).\n"
                             + "    a directory contains .tpr file.\n"
                             + "    an URL for download teleport record file."
                             + "</pre></body></html>");
        return 2;
    }

    const QStringList args = parser.positionalArguments();
    QString resource = args.at(0);
    qDebug() << resource;


//    QTextCodec::setCodecForTr(QTextCodec::codecForName("GB2312"));
//    QTextCodec::setCodecForLocale(QTextCodec::codecForName("GBK"));
//    QTextCodec::setCodecForCStrings(QTextCodec::codecForName("GB2312"));

    MainWindow w;
    w.set_resource(resource);
    w.show();
    return a.exec();
}
