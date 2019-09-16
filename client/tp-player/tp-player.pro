TEMPLATE = app
TARGET = tp-player

QT += core gui widgets

HEADERS += \
    dlgmessage.h \
    mainwindow.h \
    bar.h \
    thr_download.h \
    thr_play.h \
    update_data.h \
    record_format.h \
    rle.h

SOURCES += \
    dlgmessage.cpp \
    main.cpp \
    mainwindow.cpp \
    bar.cpp \
    thr_download.cpp \
    thr_play.cpp \
    update_data.cpp \
    rle.c

RESOURCES += \
    tp-player.qrc

RC_FILE += \
    tp-player.rc

FORMS += \
    dlgmessage.ui \
    mainwindow.ui
