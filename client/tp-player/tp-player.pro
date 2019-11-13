TEMPLATE = app
TARGET = tp-player

QT += core gui widgets network

#DEFINES += QT_NO_DEBUG_OUTPUT

HEADERS += \
    mainwindow.h \
    bar.h \
    thr_play.h \
    thr_data.h \
    update_data.h \
    record_format.h \
    rle.h \
    util.h \
    downloader.h \
    thr_download.h

SOURCES += \
    main.cpp \
    mainwindow.cpp \
    bar.cpp \
    thr_play.cpp \
    thr_data.cpp \
    update_data.cpp \
    rle.c \
    util.cpp \
    downloader.cpp \
    thr_download.cpp

RESOURCES += \
    tp-player.qrc

RC_FILE += \
    tp-player.rc

FORMS += \
    mainwindow.ui

win32:CONFIG(release, debug|release): LIBS += -L$$PWD/../../external/zlib/build/release/ -lzlibstatic
else:win32:CONFIG(debug, debug|release): LIBS += -L$$PWD/../../external/zlib/build/debug/ -lzlibstaticd

INCLUDEPATH += $$PWD/../../external/zlib
INCLUDEPATH += $$PWD/../../external/zlib/build
DEPENDPATH += $$PWD/../../external/zlib
DEPENDPATH += $$PWD/../../external/zlib/build

win32-g++:CONFIG(release, debug|release): PRE_TARGETDEPS += $$PWD/../../external/zlib/build/release/libzlibstaticd.a
else:win32-g++:CONFIG(debug, debug|release): PRE_TARGETDEPS += $$PWD/../../external/zlib/build/debug/libzlibstaticd.a
else:win32:!win32-g++:CONFIG(release, debug|release): PRE_TARGETDEPS += $$PWD/../../external/zlib/build/release/zlibstaticd.lib
else:win32:!win32-g++:CONFIG(debug, debug|release): PRE_TARGETDEPS += $$PWD/../../external/zlib/build/debug/zlibstaticd.lib
