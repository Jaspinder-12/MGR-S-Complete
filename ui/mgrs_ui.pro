QT       += core gui

greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

TARGET = mgrs_app
TEMPLATE = app

DEFINES += QT_DEPRECATED_WARNINGS

SOURCES += src/mainwindow.cpp \
    src/main.cpp \
    ../app/ApplicationController.cpp

HEADERS += inc/mainwindow.h \
    ../app/ApplicationController.h

FORMS += ui/mainwindow.ui

RESOURCES += resources/mgrs_resources.qrc

INCLUDEPATH += $$PWD/../app \
    $$PWD/../runtime/include \
    $$PWD/../vulkan/include

LIBS += -L$$PWD/../build/Debug -lmgrs
