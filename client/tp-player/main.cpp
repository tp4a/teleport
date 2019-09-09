#include "mainwindow.h"
#include <QApplication>

// 编译出来的可执行程序复制到单独目录，然后执行 windeployqt 应用程序文件名
// 即可自动将依赖的动态库等复制到此目录中。有些文件是多余的，可以酌情删除。

int main(int argc, char *argv[])
{
//#if (QT_VERSION >= QT_VERSION_CHECK(5, 6, 0))
//    QCoreApplication::setAttribute(Qt::AA_EnableHighDpiScaling);
//#endif

    QApplication a(argc, argv);
    MainWindow w;
    w.show();

    return a.exec();
}
