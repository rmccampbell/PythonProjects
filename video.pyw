#!/usr/bin/env python3
import sys, os
from PyQt5 import QtWidgets, QtCore, QtMultimedia
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QUrl
try:
    from swiftslider import SwiftSlider
except ImportError:
    from PyQt5.QtWidgets import QSlider as SwiftSlider

APP_NAME = 'Video Player'
# Window size including borders
WIDTH = 960 + 18
HEIGHT = 540 + 69
STEP = 5000
BIGSTEP = 20000
VOLSTEP = 10
FS_CONTROLS_MARGINS = (6, 6, 6, 6)

class VideoPlayer(QtWidgets.QMainWindow):
    def __init__(self, file=None):
        super().__init__()
        self.resize(WIDTH, HEIGHT)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction('&Open File...', self.openFile, 'Ctrl+O')
        fileMenu.addAction('Open &URL...', self.openUrl, 'Ctrl+U')
        fileMenu.addAction('E&xit', self.close, 'Ctrl+Q')
        self.addActions(fileMenu.actions())

        cwidget = QtWidgets.QWidget()
        self.setCentralWidget(cwidget)

        self.media = QMediaPlayer()
        self.media.stateChanged.connect(self.handleStateChanged)
        self.media.positionChanged.connect(self.handlePositionChanged)
        self.media.durationChanged.connect(self.handleDurationChanged)
        self.media.mutedChanged.connect(self.handleMutedChanged)
        self.media.volumeChanged.connect(self.handleVolumeChanged)
        self.media.error.connect(self.handleError)

        self.video = QVideoWidget()
        self.media.setVideoOutput(self.video)
        self.video.setFocusPolicy(Qt.StrongFocus)
        self.video.installEventFilter(self)

        self.playIcon = self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay)
        self.pauseIcon = self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause)
        self.playButton = QtWidgets.QPushButton(self.playIcon, '')
        self.playButton.clicked.connect(self.togglePlay)

        self.volIcon = self.style().standardIcon(QtWidgets.QStyle.SP_MediaVolume)
        self.muteIcon = self.style().standardIcon(QtWidgets.QStyle.SP_MediaVolumeMuted)
        self.volButton = QtWidgets.QPushButton(self.volIcon, '')
        self.volButton.clicked.connect(self.toggleMuted)

        self.volSlider = SwiftSlider(Qt.Horizontal)
        self.volSlider.setMaximum(100)
        self.volSlider.setValue(100)
        self.volSlider.valueChanged.connect(self.handleVolSliderChanged)

        self.posSlider = SwiftSlider(Qt.Horizontal)
        self.posSlider.setMaximum(0)
        self.posSlider.setSingleStep(STEP)
        self.posSlider.setPageStep(BIGSTEP)
        self.posSlider.valueChanged.connect(self.handlePosSliderChanged)

        self.posLabel = QtWidgets.QLabel('0:00')
        self.durLabel = QtWidgets.QLabel('0:00')

        self.controls = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(self.controls)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.playButton)
        layout.addWidget(self.volButton)
        layout.addWidget(self.volSlider)
        layout.addWidget(self.posLabel)
        layout.addWidget(self.posSlider, 1)
        layout.addWidget(self.durLabel)
        self.vlayout = QtWidgets.QVBoxLayout(cwidget)
        self.vlayout.addWidget(self.video, 1)
        self.vlayout.addWidget(self.controls)

        self.margins = self.vlayout.contentsMargins()
        self.spacing = self.vlayout.spacing()
        videodirs = QtCore.QStandardPaths.standardLocations(
            QtCore.QStandardPaths.MoviesLocation)
        self.dir = videodirs[0] if videodirs else ''

        self.positionChanging = False

        if file:
            url = QUrl.fromUserInput(file, '.')
            if url.isValid():
                self.setSource(url)
            else:
                QtWidgets.QMessageBox.warning(
                    self, 'Error', 'Error: Invalid URL: "%s"' % file)

    def setSource(self, url):
        self.setWindowFilePath(url.path())
        if url.isLocalFile():
            self.dir = os.path.dirname(url.toLocalFile())
        self.media.setMedia(QtMultimedia.QMediaContent(url))
        self.media.play()

    def openFile(self):
        dir = QUrl.fromLocalFile(self.dir).toString()
        url, filt = QtWidgets.QFileDialog.getOpenFileUrl(self, directory=dir)
        if url.isValid():
            self.setSource(url)

    def openUrl(self):
        urls, ok = QtWidgets.QInputDialog.getText(self, 'Open URL', 'Video URL:')
        if urls:
            url = QUrl.fromUserInput(urls)
            if url.isValid():
                self.setSource(url)
            else:
                QtWidgets.QMessageBox.warning(
                    self, 'Error', 'Error: Invalid URL: "%s"' % urls)

    def togglePlay(self):
        if self.media.state() == QMediaPlayer.PlayingState:
            self.media.pause()
        else:
            self.media.play()

    def toggleMuted(self):
        self.media.setMuted(not self.media.isMuted())

    def toggleFullscreen(self):
        self.menuBar().setVisible(self.isFullScreen())
        if self.isFullScreen():
            self.vlayout.setContentsMargins(self.margins)
            self.vlayout.setSpacing(self.spacing)
            self.controls.setContentsMargins(0, 0, 0, 0)
        else:
            self.vlayout.setContentsMargins(0, 0, 0, 0)
            self.vlayout.setSpacing(0)
            self.controls.setContentsMargins(*FS_CONTROLS_MARGINS)
        self.setWindowState(self.windowState() ^ Qt.WindowFullScreen)

    def handleStateChanged(self, state):
        playing = state == QMediaPlayer.PlayingState
        self.playButton.setIcon(self.pauseIcon if playing else self.playIcon)

    def handlePositionChanged(self, position):
        self.positionChanging = True
        self.posSlider.setValue(position)
        self.positionChanging = False
        secs = position // 1000
        mins, secs = divmod(secs, 60)
        self.posLabel.setText('%d:%02d' % (mins, secs))

    def handleDurationChanged(self, duration):
        self.posSlider.setMaximum(duration)
        secs = duration // 1000
        mins, secs = divmod(secs, 60)
        self.durLabel.setText('%d:%02d' % (mins, secs))

    def handleMutedChanged(self, muted):
        self.volButton.setIcon(self.muteIcon if muted else self.volIcon)

    def handleVolumeChanged(self, volume):
        self.volSlider.setValue(volume)

    def handleVolSliderChanged(self, value):
        self.media.setVolume(value)

    def handlePosSliderChanged(self, value):
        if not self.positionChanging:
            self.media.setPosition(value)

    def handleError(self, error):
        QtWidgets.QMessageBox.warning(
            self, 'Error', 'Error: %s' % self.media.errorString())

    def keyPressEvent(self, event):
        key = event.key()
        mod = event.modifiers()
        step = BIGSTEP if mod & Qt.CTRL else STEP
        if key == Qt.Key_Space:
            self.togglePlay()
        elif key == Qt.Key_Right:
            self.media.setPosition(min(self.media.position() + step,
                                       self.media.duration()))
        elif key == Qt.Key_Left:
            self.media.setPosition(max(self.media.position() - step, 0.0))
        elif key == Qt.Key_Home:
            self.media.setPosition(0)
        elif key == Qt.Key_End:
            self.media.setPosition(self.media.duration())
        elif key == Qt.Key_Up:
            self.media.setVolume(min(self.media.volume() + VOLSTEP, 100))
        elif key == Qt.Key_Down:
            self.media.setVolume(max(self.media.volume() - VOLSTEP, 0))
        elif key == Qt.Key_M:
            self.toggleMuted()
        elif (key in (Qt.Key_F, Qt.Key_F11) or
              key == Qt.Key_Escape and self.isFullScreen()):
            self.toggleFullscreen()
        elif key == Qt.Key_W and mod & Qt.CTRL:
            self.close()
        else:
            super().keyPressEvent(event)

    def eventFilter(self, watched, event):
        if watched is self.video:
            if (event.type() == QtCore.QEvent.MouseButtonRelease and
                    event.button() == Qt.LeftButton):
                self.togglePlay()
                return True
            elif (event.type() == QtCore.QEvent.MouseButtonDblClick and
                    event.button() == Qt.LeftButton):
                self.toggleFullscreen()
                return True
        return super().eventFilter(watched, event)

if __name__ == '__main__':
    file = sys.argv[1] if len(sys.argv) >= 2 else None
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    window = VideoPlayer(file)
    window.show()
    sys.exit(app.exec())
