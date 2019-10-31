#include "mainwindow.h"
#include <QApplication>
#include <QCommandLineParser>
#include <QDebug>
#include <QMessageBox>
#include <QTextCodec>

// 编译出来的可执行程序复制到单独目录，然后执行 windeployqt 应用程序文件名
// 即可自动将依赖的动态库等复制到此目录中。有些文件是多余的，可以酌情删除。

// 命令行参数格式：
// ## 本地文件或目录
//  tp-player.exe  path/of/tp-rdp.tpr         一个 .tpr 文件的文件名
//  tp-player.exe  path/contains/tp-rdp.tpr   包含 .tpr 文件的路径
//
// ## 从TP服务器上下载
//	(废弃) tp-player.exe "http://127.0.0.1:7190"   1234      "tp_1491560510_ca67fceb75a78c9d"    "000000256-admin-administrator-218.244.140.14-20171209-020047"
//  (废弃)               TP服务器地址                记录编号   session-id（仅授权用户可下载）          合成的名称，用于本地生成路径来存放下载的文件
//
// ## 从TP服务器上下载
//	tp-player.exe http://teleport.domain.com:7190/{sub/path/}tp_1491560510_ca67fceb75a78c9d/1234 (注意，并不直接访问此URI，实际上其并不存在)
//                TP服务器地址(可能包含子路径哦，例如上例中的{sub/path}部分)/session-id(用于判断当前授权用户)/录像会话编号
//    按 “/” 进行分割后，去掉最后两个项，剩下部分是TP服务器的WEB地址，用于合成后续的文件下载URL。
//    根据下载的.tpr文件内容，本地合成类似于 "000000256-admin-administrator-218.244.140.14-20171209-020047" 的路径来存放下载的文件
//    特别注意，如果账号是 domain\user 这种形式，需要将 "\" 替换为下划线，否则此符号作为路径分隔符，会导致路径不存在而无法保存下载的文件。
//       - 获取文件大小: http://127.0.0.1:7190/audit/get-file?act=size&type=rdp&rid=yyyyy&f=file-name
//          - 'act'为`size`表示获取文件大小（返回一个数字字符串，就是指定的文件大小）
//          - 'type'可以是`rdp`或`ssh`，目前仅用了`rdp`
//          - 'rid'是录像会话编号（在服务端，一个会话的录像文件均放在录像会话编号命名的目录下）
//          - 'f' 是文件名，即会话编号目录下的指定文件，例如 'tp-rdp.tpr'
//       - 读取文件内容: http://127.0.0.1:7190/audit/get-file?act=read&type=rdp&rid=yyyyy&f=file-name&offset=1234&length=1024
//          - 'act'为`read`表示获取文件内容
//          - 'offset'表示要读取的偏移，如果未指定，则表示从文件起始处开始读取，即默认为 offset=0
//          - 'length'表示要读取的大小，如果未指定，表示读取整个文件，即默认为 length=-1（服务端对length=-1做完全读取处理）
//          - 搭配使用 offst 和 length 可以做到分块下载、断点续传。


void show_usage(QCommandLineParser& parser) {
    QMessageBox::warning(nullptr, QGuiApplication::applicationDisplayName(),
                         "<html><head/><body><pre>"
                         + parser.helpText()
                         + "\n\n"
                         + "RESOURCE could be:\n"
                         + "    teleport record file (.tpr).\n"
                         + "    a directory contains .tpr file.\n"
                         + "    an URL to download teleport record file."
                         + "</pre></body></html>");
}

int main(int argc, char *argv[])
{
//#if (QT_VERSION >= QT_VERSION_CHECK(5, 6, 0))
//    QCoreApplication::setAttribute(Qt::AA_EnableHighDpiScaling);
//#endif


    QApplication a(argc, argv);

//#ifdef __APPLE__
//    QString data_path_base = QStandardPaths::writableLocation(QStandardPaths::DesktopLocation);
//    data_path_base += "/tp-testdata/";
//#else
//    QString data_path_base = QCoreApplication::applicationDirPath() + "/record";
//#endif
//    qDebug("data-path-base: %s", data_path_base.toStdString().c_str());
//    return 0;

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
        show_usage(parser);
//        QMessageBox::warning(nullptr, QGuiApplication::applicationDisplayName(),
//                             "<html><head/><body><pre>"
//                             + parser.helpText()
//                             + "\n\n"
//                             + "RESOURCE could be:\n"
//                             + "    teleport record file (.tpr).\n"
//                             + "    a directory contains .tpr file.\n"
//                             + "    an URL for download teleport record file."
//                             + "</pre></body></html>");
        return 2;
    }

    const QStringList args = parser.positionalArguments();
    if(0 == args.size()) {
        show_usage(parser);
        return 2;
    }

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
