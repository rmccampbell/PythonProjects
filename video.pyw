#!/usr/bin/python3
import sys, os, subprocess
from PyQt5 import QtWidgets, QtCore, QtMultimedia
from PyQt5.QtWidgets import QStyle, QSizePolicy
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QUrl

APP_NAME = 'Video Player'
WIDTH = 1280
HEIGHT = 720
STEP = 5000
BIGSTEP = 30000
VOLSTEP = 10
CONTROLS_MARGINS = (6, 6, 6, 6)

windows = []


class VideoPlayer(QtWidgets.QMainWindow):
    def __init__(self, file=None, show=True):
        super().__init__()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction('&Open File...', self.openFile, 'Ctrl+O')
        fileMenu.addAction('Open &URL...', self.openUrl, 'Ctrl+U')
        fileMenu.addAction('&New Window', self.newWindow, 'Ctrl+N')
        fileMenu.addAction('E&xit', self.close, 'Ctrl+Q')
        self.addActions(fileMenu.actions())

        cwidget = QtWidgets.QWidget()
        self.setCentralWidget(cwidget)

        self.media = QMediaPlayer()
        self.video = QVideoWidget()
        self.media.setVideoOutput(self.video)
        self.video.setFocusPolicy(Qt.StrongFocus)
        self.video.installEventFilter(self)

        self.playIcon = self.style().standardIcon(QStyle.SP_MediaPlay)
        self.pauseIcon = self.style().standardIcon(QStyle.SP_MediaPause)
        self.playButton = QtWidgets.QPushButton(self.playIcon, '')
        self.playButton.clicked.connect(self.togglePlay)

        self.volIcon = self.style().standardIcon(QStyle.SP_MediaVolume)
        self.muteIcon = self.style().standardIcon(QStyle.SP_MediaVolumeMuted)
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
        self.speedLabel = QtWidgets.QLabel()

        self.controls = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(self.controls)
        layout.setContentsMargins(*CONTROLS_MARGINS)
        layout.addWidget(self.playButton)
        layout.addWidget(self.volButton)
        layout.addWidget(self.volSlider)
        layout.addWidget(self.posLabel)
        layout.addWidget(self.posSlider, 1)
        layout.addWidget(self.durLabel)
        layout.addWidget(self.speedLabel)

        self.vlayout = QtWidgets.QVBoxLayout(cwidget)
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.vlayout.setSpacing(0)
        self.vlayout.addWidget(self.video, 1)
        self.vlayout.addWidget(self.controls)

        self.video.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.video.resize(WIDTH, HEIGHT)
        self.video.setMinimumSize(WIDTH, HEIGHT)
        self.adjustSize()
        self.video.setMinimumSize(0, 0)

        self.media.stateChanged.connect(self.handleStateChanged)
        self.media.positionChanged.connect(self.handlePositionChanged)
        self.media.durationChanged.connect(self.handleDurationChanged)
        self.media.playbackRateChanged.connect(self.handlePlaybackRateChanged)
        self.media.mutedChanged.connect(self.handleMutedChanged)
        self.media.volumeChanged.connect(self.handleVolumeChanged)
        self.media.error.connect(self.handleError)
        # By default this is 0 for some reason
        self.media.setPlaybackRate(1.0)

        self.positionChanging = False

        videodirs = QtCore.QStandardPaths.standardLocations(
            QtCore.QStandardPaths.MoviesLocation)
        self.directory = videodirs[0] if videodirs else ''

        # self.audioProbe = QtMultimedia.QAudioProbe(self)
        # self.audioProbe.audioBufferProbed.connect(self.processAudioBuffer)
        # self.audioProbe.setSource(self.media)

        self.setAcceptDrops(True)

        windows.append(self)

        if show:
            self.show()

        if file:
            self.setSourceValidate(QUrl.fromUserInput(file, '.'), file)

    def setSource(self, url):
        self.setWindowFilePath(url.path())
        if url.isLocalFile():
            self.directory = os.path.dirname(url.toLocalFile())
        else:
            url = QUrl(youtubedl_resolve_url(url.toString()))
        self.media.setMedia(QtMultimedia.QMediaContent(url))
        self.media.play()

    def setSourceValidate(self, url, urlstr=None):
        if url.isValid():
            self.setSource(url)
        else:
            urlstr = urlstr or url.toString()
            msg = f'Error: Invalid URL: "{urlstr}"'
            QtWidgets.QMessageBox.warning(self, 'Error', msg)

    def openFile(self):
        dir = QUrl.fromLocalFile(self.directory)
        url, filt = QtWidgets.QFileDialog.getOpenFileUrl(self, directory=dir)
        if url.isValid():
            self.setSource(url)

    def openUrl(self):
        urlstr, ok = QtWidgets.QInputDialog.getText(
            self, 'Open URL', 'Video URL:')
        if urlstr:
            self.setSourceValidate(QUrl.fromUserInput(urlstr), urlstr)

    def newWindow(self):
        VideoPlayer()

    def togglePlay(self):
        if self.media.state() == QMediaPlayer.PlayingState:
            self.media.pause()
        else:
            self.media.play()

    def toggleMuted(self):
        self.media.setMuted(not self.media.isMuted())

    def toggleFullscreen(self):
        self.menuBar().setVisible(self.isFullScreen())
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
        self.posLabel.setText(f'{mins}:{secs:02}')

    def handleDurationChanged(self, duration):
        self.posSlider.setMaximum(duration)
        secs = duration // 1000
        mins, secs = divmod(secs, 60)
        self.durLabel.setText(f'{mins}:{secs:02}')

    def handlePlaybackRateChanged(self, rate):
        self.speedLabel.setText('' if rate == 1 else f'{rate:.3g}x')

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
        estr = self.media.errorString()
        if not estr:
            m = QMediaPlayer.staticMetaObject
            estr = m.enumerator(m.indexOfEnumerator('Error')).valueToKey(error)
        QtWidgets.QMessageBox.warning(self, 'Error', f'Error: {estr}')

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
        elif key in (Qt.Key_BracketLeft, Qt.Key_Less):
            self.media.setPlaybackRate(max(self.media.playbackRate() - .25, .25))
        elif key in (Qt.Key_BracketRight, Qt.Key_Greater):
            self.media.setPlaybackRate(min(self.media.playbackRate() + .25, 4.0))
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

    # def processAudioBuffer(self, buffer):
    #     pass

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls() and event.mimeData().urls():
            self.setSource(event.mimeData().urls()[0])

    def closeEvent(self, event):
        self.media.stop()
        windows.remove(self)


def youtubedl_resolve_url(url):
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    try:
        return subprocess.run(
            ['youtube-dl', '--get-url', url],
            capture_output=True, check=True, text=True, creationflags=flags
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return url


# Modified from http://code.qt.io/cgit/%7bgraveyard%7d/qtphonon.git/tree/src/3rdparty/phonon/phonon/swiftslider.cpp
class SwiftSlider(QtWidgets.QSlider):
    def mousePressEvent(self, event):
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        hr = self.style().subControlRect(
            QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
        gr = self.style().subControlRect(
            QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)
        if event.button() == Qt.LeftButton and not hr.contains(event.pos()):
            event.accept()
            if self.orientation() == Qt.Horizontal:
                sliderPos = event.pos().x() - gr.x() - hr.width()//2
                sliderSpan = gr.width() - hr.width()
            else:
                sliderPos = event.pos().y() - gr.y() - hr.height()//2
                sliderSpan = gr.height() - hr.height()
            self.setSliderPosition(QStyle.sliderValueFromPosition(
                self.minimum(), self.maximum(), sliderPos,
                sliderSpan, opt.upsideDown))
        else:
            super().mousePressEvent(event)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    files = sys.argv[1:] or [None]
    for file in files:
        window = VideoPlayer(file)
    sys.exit(app.exec_())
