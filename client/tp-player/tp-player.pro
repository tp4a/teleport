TEMPLATE = app
TARGET = tp-player

QT += core gui widgets network

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

win32: {
    INCLUDEPATH += $$PWD/../../external/zlib
    INCLUDEPATH += $$PWD/../../external/zlib/build
    DEPENDPATH += $$PWD/../../external/zlib
    DEPENDPATH += $$PWD/../../external/zlib/build
}
win32:CONFIG(release, debug|release): {
    DEFINES += QT_NO_DEBUG_OUTPUT
    LIBS += -L$$PWD/../../external/zlib/build/release/ -lzlib
    DESTDIR = $$PWD/../../out/client/x86/Release
}
else:win32:CONFIG(debug, debug|release): {
    LIBS += -L$$PWD/../../external/zlib/build/debug/ -lzlibd
    DESTDIR = $$PWD/../../out/client/x86/Debug
}


macx: {
    CONFIG+=sdk_no_version_check
    INCLUDEPATH += $$PWD/../../external/macos/release/include
}
macx:CONFIG(release, debug|release): {
    DEFINES += QT_NO_DEBUG_OUTPUT
    LIBS += -L$$PWD/../../external/macos/release/lib/ -lz
    DESTDIR = $$PWD/../../out/client/x64/release

    UI_DIR += $$PWD/../../out/_tmp_/tp-player/release
    RCC_DIR += $$PWD/../../out/_tmp_/tp-player/release
    MOC_DIR += $$PWD/../../out/_tmp_/tp-player/release
    OBJECTS_DIR += $$PWD/../../out/_tmp_/tp-player/release
}
else:macx:CONFIG(debug, debug|release): {
    LIBS += -L$$PWD/../../external/macos/release/lib/ -lz
    DESTDIR = $$PWD/../../out/client/x64/debug

    UI_DIR += $$PWD/../../out/_tmp_/tp-player/debug
    RCC_DIR += $$PWD/../../out/_tmp_/tp-player/debug
    MOC_DIR += $$PWD/../../out/_tmp_/tp-player/debug
    OBJECTS_DIR += $$PWD/../../out/_tmp_/tp-player/debug
}



#win32-g++:CONFIG(release, debug|release): PRE_TARGETDEPS += $$PWD/../../external/zlib/build/release/libzlibstatic.a
#else:win32-g++:CONFIG(debug, debug|release): PRE_TARGETDEPS += $$PWD/../../external/zlib/build/debug/libzlibstaticd.a
#else:win32:!win32-g++:CONFIG(release, debug|release): PRE_TARGETDEPS += $$PWD/../../external/zlib/build/release/zlibstatic.lib
#else:win32:!win32-g++:CONFIG(debug, debug|release): PRE_TARGETDEPS += $$PWD/../../external/zlib/build/debug/zlibstaticd.lib
