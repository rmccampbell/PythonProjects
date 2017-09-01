#!/usr/bin/env python3
import sys, os
from PyQt4 import QtGui, QtCore
from PyQt4.phonon import Phonon
from PyQt4.QtCore import Qt
#from volumecontrol import VolumeControl

APP_NAME = 'Video Player'
# Window size including borders
WIDTH = 960 + 18
HEIGHT = 540 + 69
STEP = 5000
BIGSTEP = 20000
VOLSTEP = 0.1
FS_CONTROLS_MARGINS = (6, 6, 6, 6)

class VideoPlayer(QtGui.QMainWindow):
    def __init__(self, file=None):
        super().__init__()
        self.resize(WIDTH, HEIGHT)
        self.setWindowTitle(APP_NAME)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction('&Open File...', self.openFile, 'Ctrl+O')
        fileMenu.addAction('Open &URL...', self.openUrl, 'Ctrl+U')
        fileMenu.addAction('E&xit', self.close, 'Ctrl+Q')
        self.addActions(fileMenu.actions())

        cwidget = QtGui.QWidget()
        self.setCentralWidget(cwidget)

        self.media = Phonon.MediaObject()
        self.media.stateChanged.connect(self.handleStateChanged)
        self.media.tick.connect(self.handleTick)
        self.media.totalTimeChanged.connect(self.handleTotalTimeChanged)
        self.video = Phonon.VideoWidget()
        self.video.setFocusPolicy(Qt.StrongFocus)
        self.video.installEventFilter(self)
        self.audio = Phonon.AudioOutput(Phonon.VideoCategory)
        Phonon.createPath(self.media, self.audio)
        Phonon.createPath(self.media, self.video)

        self.playIcon = self.style().standardIcon(QtGui.QStyle.SP_MediaPlay)
        self.pauseIcon = self.style().standardIcon(QtGui.QStyle.SP_MediaPause)
        self.playButton = QtGui.QPushButton(self.playIcon, '')
        self.playButton.clicked.connect(self.togglePlay)
        self.volslider = Phonon.VolumeSlider(self.audio)
        #self.volcontrol = VolumeControl(self.audio, autoRaise=True)
        self.slider = Phonon.SeekSlider(self.media)
        self.slider.setSingleStep(STEP)
        self.slider.setPageStep(BIGSTEP)
        self.timeLabel = QtGui.QLabel('0:00')
        self.totTimeLabel = QtGui.QLabel('0:00')

        self.controls = QtGui.QWidget()
        layout = QtGui.QHBoxLayout(self.controls)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.playButton)
        layout.addWidget(self.volslider)
        #layout.addWidget(self.volcontrol)
        layout.addWidget(self.timeLabel)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.totTimeLabel)
        self.vlayout = QtGui.QVBoxLayout(cwidget)
        self.vlayout.addWidget(self.video, 1)
        self.vlayout.addWidget(self.controls)

        self.margins = self.vlayout.contentsMargins()
        self.spacing = self.vlayout.spacing()
        self.dir = QtGui.QDesktopServices.storageLocation(
            QtGui.QDesktopServices.MoviesLocation)

        if file:
            self.setSource(file)

    def setSource(self, file):
        self.setWindowTitle('')
        self.setWindowFilePath(file)
        if '://' in file:
            file = QtCore.QUrl(file)
        else:
            self.dir = os.path.dirname(file)
        self.media.setCurrentSource(Phonon.MediaSource(file))
        self.media.play()

    def openFile(self):
        path = QtGui.QFileDialog.getOpenFileName(self, directory=self.dir)
        if path:
            self.setSource(path)

    def openUrl(self):
        url, ok = QtGui.QInputDialog.getText(self, 'Open URL', 'Video URL:')
        if url:
            if '://' not in url:
                url = 'http://' + url
            self.setSource(url)

    def togglePlay(self):
        if self.media.state() in (Phonon.PlayingState, Phonon.BufferingState):
            self.media.pause()
        else:
            self.media.play()

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

    def handleStateChanged(self, newstate, oldstate):
        if newstate == Phonon.ErrorState:
            QtGui.QMessageBox.warning(
                self, 'Error', 'Error: %s\n%s' %
                (self.windowFilePath(), self.media.errorString()))
        if newstate in (Phonon.PlayingState, Phonon.BufferingState):
            self.playButton.setIcon(self.pauseIcon)
        else:
            self.playButton.setIcon(self.playIcon)

    def handleTick(self, time):
        secs = time // 1000
        mins, secs = divmod(secs, 60)
        self.timeLabel.setText('%d:%02d' % (mins, secs))

    def handleTotalTimeChanged(self, totTime):
        secs = totTime // 1000
        mins, secs = divmod(secs, 60)
        self.totTimeLabel.setText('%d:%02d' % (mins, secs))

    def keyPressEvent(self, event):
        key = event.key()
        mod = event.modifiers()
        step = BIGSTEP if mod & Qt.CTRL else STEP
        if key == Qt.Key_Space:
            self.togglePlay()
        elif key == Qt.Key_Right:
            self.media.seek(min(self.media.currentTime() + step,
                                self.media.totalTime()))
        elif key == Qt.Key_Left:
            self.media.seek(max(self.media.currentTime() - step, 0.0))
        elif key == Qt.Key_Home:
            self.media.seek(0)
        elif key == Qt.Key_End:
            self.media.seek(self.media.totalTime())
        elif key == Qt.Key_Up:
            self.audio.setVolume(min(self.audio.volume() + VOLSTEP, 1.0))
        elif key == Qt.Key_Down:
            self.audio.setVolume(max(self.audio.volume() - VOLSTEP, 0.0))
        elif key == Qt.Key_M:
            self.audio.setMuted(not self.audio.isMuted())
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
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    window = VideoPlayer(file)
    window.show()
    sys.exit(app.exec_())
