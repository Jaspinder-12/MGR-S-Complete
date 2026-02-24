#include "mainwindow.h"
#include "ui_mainwindow.h"
#include <QMessageBox>
#include <QSettings>

MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow),
    m_firstLaunch(true)
{
    ui->setupUi(this);
    initializeUI();
    setupConnections();
    showFirstLaunchDialog();
    m_controller.initialize();
    updateDashboard();
    m_updateTimer.start(5000); // Update every 5 seconds
}

MainWindow::~MainWindow()
{
    delete ui;
}

void MainWindow::initializeUI()
{
    // Set window properties
    setWindowTitle("MGR-S");
    resize(800, 600);

    // Initialize UI elements
    ui->stateLabel->setText("STARTING");
    ui->apiVersionLabel->setText("Unavailable");
    ui->gpuCountLabel->setText("Unavailable");
    ui->authorityGpuLabel->setText("Unavailable");
    ui->logTextEdit->setReadOnly(true);
}

void MainWindow::setupConnections()
{
    connect(&m_updateTimer, &QTimer::timeout, this, &MainWindow::updateDashboard);
    connect(ui->exitButton, &QPushButton::clicked, this, &MainWindow::handleExit);
}

void MainWindow::showFirstLaunchDialog()
{
    QSettings settings("MGR-S", "MGR-S");
    if (settings.value("firstLaunch", true).toBool()) {
        QMessageBox::information(this, "Welcome to MGR-S",
                                 "MGR-S is a Multi-GPU Runtime System designed to improve "
                                 "performance on systems with multiple GPUs (e.g., iGPU + dGPU).\n\n"
                                 "Key limitations:\n"
                                 "- This is NOT SLI or CrossFire\n"
                                 "- Performance gains are application-specific\n"
                                 "- Only Vulkan applications are supported\n"
                                 "- Some systems may not see any improvement\n\n"
                                 "Click OK to continue.");
        settings.setValue("firstLaunch", false);
    }
}

void MainWindow::updateDashboard()
{
    // Update state
    auto state = m_controller.getState();
    QString stateString = QString::fromStdString(m_controller.getStateString());
    ui->stateLabel->setText(stateString);

    // Set state color
    switch (state) {
    case ApplicationController::RuntimeState::RUNNING:
        ui->stateLabel->setStyleSheet("color: green; font-weight: bold;");
        break;
    case ApplicationController::RuntimeState::DEGRADED:
        ui->stateLabel->setStyleSheet("color: orange; font-weight: bold;");
        break;
    case ApplicationController::RuntimeState::ERROR:
        ui->stateLabel->setStyleSheet("color: red; font-weight: bold;");
        break;
    default:
        ui->stateLabel->setStyleSheet("color: black;");
    }

    // Update metrics
    ui->apiVersionLabel->setText(QString::fromStdString(m_controller.getApiVersionString()));
    ui->gpuCountLabel->setText(QString::fromStdString(m_controller.getGpuCountString()));
    ui->authorityGpuLabel->setText(QString::fromStdString(m_controller.getAuthorityGpuString()));

    // Update log
    logMessage("Dashboard updated - " + QDateTime::currentDateTime().toString(Qt::ISODate));
}

void MainWindow::logMessage(const QString &message)
{
    ui->logTextEdit->appendPlainText(message);
    ui->logTextEdit->verticalScrollBar()->setValue(ui->logTextEdit->verticalScrollBar()->maximum());
}

void MainWindow::handleExit()
{
    m_controller.shutdown();
    close();
}
