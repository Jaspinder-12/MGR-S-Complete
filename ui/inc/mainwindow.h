#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QTimer>
#include "ApplicationController.h"

namespace Ui {
class MainWindow;
}

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void updateDashboard();
    void handleExit();

private:
    void initializeUI();
    void setupConnections();
    void showFirstLaunchDialog();
    void logMessage(const QString &message);

    Ui::MainWindow *ui;
    ApplicationController m_controller;
    QTimer m_updateTimer;
    bool m_firstLaunch;
};

#endif // MAINWINDOW_H
