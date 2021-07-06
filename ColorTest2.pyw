"""

RT Annotator (Real Time Annotator)
Shamoun Gergi
Recently updated: 30-06-2021

"""


from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, \
    QSlider, QStyle, QSizePolicy, QFileDialog, QSpacerItem, QCheckBox, QComboBox, QRadioButton, QStyleOptionTitleBar
import sys
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QIcon, QPalette, QKeySequence, QPainter, QFont#, QKeySequence
from PyQt5.QtCore import Qt, QUrl, QRect
from PyQt5.QtWidgets import QMessageBox, QShortcut, QTableWidget, QDesktopWidget, QAction, QStackedLayout, QFrame, QMainWindow

#from aqt import mw


import bisect
from time import *

import keyboard

# import random
from itertools import count
# import pandas as pd
# import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

import csv


import numpy as np


class MplCanvas(FigureCanvas):
    """This class helps to create a widget/ canvas for the plotting-area. It's namely a part of the integration
    between PyQt5 and the plotting libraries"""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        # self.axes.hold(False)

        self.compute_initial_figure()

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)






    def compute_initial_figure(self):
        pass


class Window(QWidget):
    """ This class is about the main window. An object of this class is namely the window."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("RT Annotator")
        #self.setGeometry(350, 100, 1920, 1080)

        # Fullscreen
        titleBarHeight = self.style().pixelMetric(QStyle.PM_TitleBarHeight,QStyleOptionTitleBar(),self)
        geometry = app.desktop().availableGeometry()
        geometry.setHeight(geometry.height() - (titleBarHeight * 2))
        self.setGeometry(geometry)

        self.setWindowIcon(QIcon('player.png'))

        p = self.palette()
        p.setColor(QPalette.Window, Qt.white)
        self.setPalette(p)

        self.init_ui()
        self.init_layout()
        self.mediaConnection()
        self.keyShortcuts()

        # Create menu bar and add action


        self.show()

    def init_ui(self):
        """ This method is responsible of all the graphical elements, eg. buttons, videoplayer, diagram, widgets, etc."""


        # Creats two lists: one for x-values, one for y-valuse
        self.xValues = []
        self.yValues = []
        self.colors = []

        # Colors
        self.saveColor = "limegreen"
        self.currentColor = "r"
        self.unsavedColor = "royalblue"

        # Initialization of some attributes
        self.filename = None

        self.startIndex = 0
        self.current_position = 0
        self.position_index = 0

        self.savedRecently = False

        self.neverPlayed = True
        self.ani = None
        self.line = None


        # create media player object
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)


        # create videowidget object
        self.videowidget = QVideoWidget()

        ##########################################################################

        # create "open video" button
        self.openVideoBtn = QPushButton(' Open Video')
        self.openVideoBtn.clicked.connect(self.open_file)
        self.openVideoBtn.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))

        # create "open annotation" button
        self.openAnnotationBtn = QPushButton(' Open csv')
        self.openAnnotationBtn.clicked.connect(self.open_annotation)
        self.openAnnotationBtn.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))

        # create save button
        self.saveBtn = QPushButton(' Save Annotation')
        self.saveBtn.clicked.connect(self.save_annotation)
        self.saveBtn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.saveBtn.setEnabled(False)

        # create reset button
        self.resetBtn = QPushButton(" Clear Annotation")
        self.resetBtn.clicked.connect(self.reset_annotation)
        self.resetBtn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))

        # create new file button
        self.newFileBtn = QPushButton(" New File")
        self.newFileBtn.clicked.connect(self.newFile)
        self.newFileBtn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))

        # create a shortcuts button
        self.shortcutsBtn = QPushButton(" Shortcuts")
        self.shortcutsBtn.clicked.connect(self.shortcuts)
        self.shortcutsBtn.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxQuestion))

        # create button for playing
        self.playBtn = QPushButton()
        self.playBtn.setEnabled(False)
        self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playBtn.clicked.connect(self.play_video)
        #self.playBtn.clicked.connect(lambda : keyboard.press("s"))


        # create button for stop
        self.stopBtn = QPushButton()
        self.stopBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stopBtn.clicked.connect(self.stop_video)

        # create button for record
        self.recordLabel = QLabel("Record: ")
        self.recordLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.checkbox = QCheckBox()

        # create slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.set_position)

        # Creating a container that includes the videoplayer and the label that shows the value of the slider.
        self.container = QWidget()
        lay = QVBoxLayout(self.container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.videowidget)
        self.numLabel = QLabel("0", self.container)
        self.numLabel.setGeometry(QRect(80, 50, 150, 150))
        self.numLabel.setFont(QFont('Times', 50))
        self.numLabel.setStyleSheet("background-color: white")
        #rgba(0,0,0,0%)

        # Create vertical slider
        self.VerticalSlider = QSlider(Qt.Vertical)
        self.VerticalSlider.sliderMoved['int'].connect(self.numLabel.setNum)

        # Create combobox for Playback rate
        self.speedComboLabel = QLabel(" |   Playback rate: ")
        self.speedComboLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.speedCombo = QComboBox()
        #self.speedCombo.addItem("0.25")
        self.speedCombo.addItem("0.5")
        self.speedCombo.addItem("0.75")
        self.speedCombo.addItem("1")
        self.speedCombo.addItem("1.25")
        self.speedCombo.addItem("1.5")
        self.speedCombo.addItem("1.75")
        #self.speedCombo.addItem("2")
        self.speedCombo.setCurrentIndex(2)

        # Create combobox for view mode
        self.viewComboLabel = QLabel(" x-axis range: ")
        self.viewCombo = QComboBox()
        self.viewCombo.addItem("(now - 10s, now)")
        self.viewCombo.addItem("(now - 5s, now + 5s)")
        self.viewCombo.addItem("(0, now)")
        self.viewCombo.addItem("(0, end)")
        self.viewCombo.setCurrentIndex(1)

        # Create Radio buttons for the "Plot mode".
        self.radioLabel = QLabel(" Plot Mode: ")
        self.radioBtn1 = QRadioButton("Zoom view")
        self.radioBtn1.setChecked(True)
        self.radioBtn2 = QRadioButton("Shrinking axis")
        self.radioBtn3 = QRadioButton("Entire video")

        # create label
        self.label = QLabel()
        self.label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        # create spacers
        self.spacerItem = QSpacerItem(128, 17, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.spacerItem2 = QSpacerItem(128, 17, QSizePolicy.Expanding, QSizePolicy.Minimum)


        #--------------------------------------------------------------------------------------------------

        # Create a canvas for the diagram, using the MplCanvas-class above.
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)

        # Defining the x and y axis:
        self.x = np.linspace(0, 100, 50)
        self.y = np.linspace(0, 100, 50)
        self.line, = self.canvas.axes.plot(self.x, self.y, animated=True, lw=2)
        #self.canvas.axes.grid(color="g", axis = "x")

        # Sets the vertical line that points towards the current position
        self.vline = self.canvas.axes.axvline(x=50, ymin=0, ymax=100, color='gray',linestyle=":")







    def init_layout(self):
        """This method sets the layout of the window. It places the buttons, sliders and widgets
        in an organised layout."""

        # create hbox layout (upper horizontal box).
        upper_hbox = QHBoxLayout()
        upper_hbox.setContentsMargins(0, 0, 0, 0)

        # set widgets to the hbox layout
        upper_hbox.addWidget(self.newFileBtn)
        upper_hbox.addWidget(self.openVideoBtn)
        upper_hbox.addWidget(self.openAnnotationBtn)
        upper_hbox.addWidget(self.saveBtn)
        upper_hbox.addWidget(self.shortcutsBtn)

        upper_hbox.addItem(self.spacerItem)

        upper_hbox.addWidget(self.viewComboLabel)
        upper_hbox.addWidget(self.viewCombo)

        #upper_hbox.addWidget(toolbar)
        upper_hbox.addItem(self.spacerItem2)

        upper_hbox.addWidget(self.resetBtn)

        # ---------------------------------------------------------------------------------------

        # create hbox layout (middle horizontal box).
        middle_hbox = QHBoxLayout()
        middle_hbox.setContentsMargins(0, 0, 0, 0)

        # set widgets to the hbox layout
        middle_hbox.addWidget(self.canvas)
        middle_hbox.addWidget(self.VerticalSlider)
        middle_hbox.addWidget(self.container)

        # ---------------------------------------------------------------------------------------

        # create hbox layout (lower horizontal box).
        lower_hbox = QHBoxLayout()
        lower_hbox.setContentsMargins(0, 0, 0, 0)

        # set widgets to the hbox layout
        lower_hbox.addWidget(self.playBtn)
        lower_hbox.addWidget(self.stopBtn)
        lower_hbox.addWidget(self.recordLabel)
        lower_hbox.addWidget(self.checkbox)
        lower_hbox.addWidget(self.speedComboLabel)
        lower_hbox.addWidget(self.speedCombo)
        lower_hbox.addWidget(self.slider)


        # ---------------------------------------------------------------------------------------

        # create vbox layout (vertical box)
        vboxLayout = QVBoxLayout()
        vboxLayout.addLayout(upper_hbox)
        vboxLayout.addLayout(middle_hbox)
        vboxLayout.addLayout(lower_hbox)

        #self.setLayout(vboxLayout)
        self.setLayout(vboxLayout)

    def keyPressEvent(self, e):
        """ This method is responsible for keyboard press buttons. It is resposible for one-button-pressings at the
        time (not shortcuts as CTRL+S)"""

        #keyboard.on_press_key("s", lambda _: self.play_video())

        #"""
        # Pause/ play: S
        if e.key() == Qt.Key_S:
            if self.playBtn.isEnabled():
                self.play_video()
        #"""

        # Record: R
        if e.key() == Qt.Key_R:
            if self.checkbox.isChecked():
                self.checkbox.setChecked(False)
            else:
                self.checkbox.setChecked(True)

        # Fast forward 5s: D
        if e.key() == Qt.Key_D:
            self.set_position(self.mediaPlayer.position() + 5000)

        # Fast bakward 5s: A
        if e.key() == Qt.Key_A:
            self.set_position(self.mediaPlayer.position() - 5000)

        # Playback rate: 1, 2, 3, 4, 5, 6.
        if e.key() == Qt.Key_1:
            if self.mediaPlayer.state() != QMediaPlayer.PlayingState:
                self.speedCombo.setCurrentIndex(0)

        if e.key() == Qt.Key_2:
            if self.mediaPlayer.state() != QMediaPlayer.PlayingState:
                self.speedCombo.setCurrentIndex(1)

        if e.key() == Qt.Key_3:
            if self.mediaPlayer.state() != QMediaPlayer.PlayingState:
                self.speedCombo.setCurrentIndex(2)

        if e.key() == Qt.Key_4:
            if self.mediaPlayer.state() != QMediaPlayer.PlayingState:
                self.speedCombo.setCurrentIndex(3)

        if e.key() == Qt.Key_5:
            if self.mediaPlayer.state() != QMediaPlayer.PlayingState:
                self.speedCombo.setCurrentIndex(4)

        if e.key() == Qt.Key_6:
            if self.mediaPlayer.state() != QMediaPlayer.PlayingState:
                self.speedCombo.setCurrentIndex(5)




    def keyShortcuts(self):
        """ This method is responsible for keyboard shortcuts (more than one button at a time)"""

        # Open file: CTRl+O
        self.openVideoSc = QShortcut(QKeySequence('Ctrl+O'), self)
        self.openVideoSc.activated.connect(self.open_file)

        # Quit: CTRl+Q
        self.quitSc = QShortcut(QKeySequence('Ctrl+Q'), self)
        self.quitSc.activated.connect(self.close)

        # Open annotation: CTRl+I
        self.openAnnotationSc = QShortcut(QKeySequence('Ctrl+I'), self)
        self.openAnnotationSc.activated.connect(self.open_annotation)

        # Save annotation: CTRl+S
        self.saveSc = QShortcut(QKeySequence('Ctrl+S'), self)
        self.saveSc.activated.connect(self.save_annotation)

        # Reset program: CTRl+R
        self.resetSc = QShortcut(QKeySequence('Ctrl+N'), self)
        self.resetSc.activated.connect(self.newFile)

        # Shortcuts: CTRl+M
        self.resetSc = QShortcut(QKeySequence('Ctrl+M'), self)
        self.resetSc.activated.connect(self.shortcuts)


    def mediaConnection(self):
        """ This method connects the Qmediaplayer object "self.mediaPlayer" to the functions and attributes in
        this class (Window)."""

        self.mediaPlayer.setVideoOutput(self.videowidget)

        # media player signals
        self.mediaPlayer.stateChanged.connect(self.mediastate_changed)
        self.mediaPlayer.positionChanged.connect(self.position_changed)
        self.mediaPlayer.durationChanged.connect(self.duration_changed)


    """ Other methods: """

    def update_line(self, i):

        """ This method updates the graph. It runs every 20 ms (if playback rate is 1)"""

        self.current_position = self.mediaPlayer.position()

        if self.checkbox.isChecked() and self.mediaPlayer.state() == QMediaPlayer.PlayingState:

            self.savedRecently = False


            self.current_position = self.mediaPlayer.position()

            if self.xValues == []:
                # "If the list of xValues is empty". This happens only in the start of the plotting process.
                self.xValues.append(self.current_position)
                self.yValues.append(self.VerticalSlider.value())
                self.colors.append(self.currentColor)

                self.position_index = self.xValues.index(self.current_position)

            if self.xValues != []:

                if self.current_position > max(self.xValues):
                    # "If the point is bigger than the last point". I.e if the point will be plotted in the end of the current graph.

                    self.xValues.append(self.current_position)
                    self.yValues.append(self.VerticalSlider.value())
                    self.colors.append(self.currentColor)

                    self.position_index = self.xValues.index(self.current_position)

                if self.current_position < max(self.xValues):
                    # "If the point is smaller than the last point". I.e if the point will be plotted in the middle of the current graph.

                    bisect.insort(self.xValues,self.current_position)  # Through this method, the element is inserted in order.
                    self.yValues.insert(self.xValues.index(self.current_position), self.VerticalSlider.value())
                    self.colors.insert(self.xValues.index(self.current_position), self.currentColor)

                    self.position_index = self.xValues.index(self.current_position)



                    if self.current_position == 0:
                        self.current_position = 1
                        self.set_position(1)
                        # This if-statement solves a bug. The program has a problem when the current position is 0.



                    
                    # The graph cleans the points infront of the pointer.
                    cleaning_distance = 300 *float(self.speedCombo.currentText())


                    if self.position_index < (len(self.xValues)-1):
                        if (self.xValues[self.position_index + 1] - self.current_position) < cleaning_distance:
                            self.xValues.pop(self.position_index + 1)
                            self.yValues.pop(self.position_index + 1)
                            self.colors.pop(self.position_index + 1)


                    if self.position_index < (len(self.xValues)-2):
                        if (self.xValues[self.position_index + 2] - self.current_position) < cleaning_distance:
                            self.xValues.pop(self.position_index + 2)
                            self.yValues.pop(self.position_index + 2)
                            self.colors.pop(self.position_index + 2)


                    if self.position_index < (len(self.xValues)-3):
                        if (self.xValues[self.position_index + 3] - self.current_position) < cleaning_distance:
                            self.xValues.pop(self.position_index + 3)
                            self.yValues.pop(self.position_index + 3)
                            self.colors.pop(self.position_index + 3)


                    if self.position_index < (len(self.xValues)-4):
                        if (self.xValues[self.position_index + 4] - self.current_position) < cleaning_distance:
                            self.xValues.pop(self.position_index + 4)
                            self.yValues.pop(self.position_index + 4)
                            self.colors.pop(self.position_index + 4)




        # View modes

        if self.viewCombo.currentText() == "(now - 10s, now)":
            self.canvas.axes.set_ylim(0, 100)
            self.canvas.axes.set_xlim(self.current_position-10000, self.current_position)

        if self.viewCombo.currentText() == "(now - 5s, now + 5s)":
            self.canvas.axes.set_ylim(0, 100)
            self.canvas.axes.set_xlim(self.current_position-5000, self.current_position+5000)

        if self.viewCombo.currentText() == "(0, now)":
            self.canvas.axes.set_ylim(0, 100)
            if self.current_position == 0:
                self.canvas.axes.set_xlim(0, 1000)
            else:
                self.canvas.axes.set_xlim(0, self.current_position)


        if self.viewCombo.currentText() == "(0, end)":
            self.canvas.axes.set_ylim(0, 100)
            self.canvas.axes.set_xlim(0, self.mediaPlayer.duration())


        #self.line, = self.canvas.axes.plot(self.xValues, self.yValues, c="r", marker='.')
        #self.line, = self.canvas.axes.plot(self.xValues, self.yValues, c="black")
        self.line = self.canvas.axes.scatter(self.xValues, self.yValues, s=25 , c=self.colors)
        self.line2 = self.canvas.axes.plot(self.xValues, self.yValues,"black")



        self.neverPlayed = False



        #return [self.line]
        return [self.line]

        


    def open_file(self):
        """ This method opens a video file and activates the play and save button"""

        self.filename, _ = QFileDialog.getOpenFileName(self, "Open Video")

        if self.filename != '':
            if self.filename[-3:] == "mp4" or self.filename[-3:] == "wav" or self.filename[-3:] == "wmv" or self.filename[-3:] == "mov":
                self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(self.filename)))
                self.playBtn.setEnabled(True)
                self.saveBtn.setEnabled(True)
            else:
                message = QMessageBox()
                message.setWindowTitle("Fail")
                message.setText("Please choose a file with one of the following extensions:\nmp4, wav, mov or wmv.")
                x = message.exec_()  # this will show our messagebox
        else:
            self.filename = None




    def play_video(self):
        """ This method plays a video and shifts between PLAY and PAUSE. It also activates and inactivates different
        graphical elements"""


        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()


            # Enabling all the buttons, the speedCombo and the checkbox
            self.saveBtn.setEnabled(True)
            self.openVideoBtn.setEnabled(True)
            self.openAnnotationBtn.setEnabled(True)
            self.resetBtn.setEnabled(True)
            self.speedCombo.setEnabled(True)


        else:
            # Converts all red points to blue points
            for n in range(len(self.colors)):
                if self.colors[n] == self.currentColor:
                    self.colors[n] = self.unsavedColor




            self.mediaPlayer.play()

            # Playback speed is set to the value of the speedCombo.
            self.mediaPlayer.setPlaybackRate(float(self.speedCombo.currentText()))

            # Through the formula below, the update time (ms) is depended on the playback speed.
            # If playback speed is 1 ==> the line updates every 30 ms
            # If playback speed is 0.5 ==> the line updates every 60 ms
            # If playback speed is 1.75 ==> the line updates every 17.14 ms, etc.

            interval_value = 30/float(self.speedCombo.currentText())


            """
            if float(self.speedCombo.currentText()) == 1:
                interval_value = 100

            if float(self.speedCombo.currentText()) == 0.5:
                interval_value = 400

            if float(self.speedCombo.currentText()) == 2:
                interval_value = 50
                
            """



            if self.neverPlayed:
                """The plot should be created only the first time the video is played, not every time it is played"""
                self.ani = FuncAnimation(self.canvas.figure, self.update_line, blit=True, interval=interval_value)


            # Updates the interval value, in case the playback rate is changed.
            if self.ani != None:
                self.ani.setInterval(interval_value)
                #print("interval set")

            self.neverPlayed = False

            #self.ani = FuncAnimation(self.canvas.figure, self.update_line, self.gen2, interval=interval_value)

            # Disabling all the buttons, the speedCombo and the checkbox
            self.saveBtn.setEnabled(False)
            self.openVideoBtn.setEnabled(False)
            self.openAnnotationBtn.setEnabled(False)
            self.resetBtn.setEnabled(False)
            self.speedCombo.setEnabled(False)





    def stop_video(self):
        """ This method stops a video. It also activates different graphical elements"""


        # Enabling all the buttons, the speedCombo and the checkbox
        self.saveBtn.setEnabled(True)
        self.openVideoBtn.setEnabled(True)
        self.openAnnotationBtn.setEnabled(True)
        self.resetBtn.setEnabled(True)
        self.speedCombo.setEnabled(True)



        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.stop()
            #self.ani._stop()

        if self.mediaPlayer.state() == QMediaPlayer.PausedState:
            self.mediaPlayer.stop()
        else:
            pass

    def reset_annotation(self):
        """ This method clears the graph. It sets the xValues and yValues to empty lists and stops the video."""

        self.xValues = []
        self.yValues = []
        self.canvas.axes.set_xlim(0, 1000)
        self.stop_video()

        #self.canvas.axes.cla()
        #self.y = np.linspace(0, 100, 10)

    def newFile(self):
        """ This methods closes the current file and opens a new one."""
        self.close()
        self.__init__()
        self.neverPlayed = False

    def shortcuts(self):
        """ This method shows all the shorcuts on a pop-up window"""

        message = QMessageBox()
        message.setWindowTitle("Shortcuts")
        message.setMinimumHeight(1000)
        message.setMinimumWidth(1000)

        message.setText("Keyboard shortcuts:\n\n"
                        "CTRL+S\t\tSave\n"
                        "CTRL+O\t\tOpen video\n"
                        "CTRL+I\t\tOpen annotation\n"
                        "CTRL+N\t\tNew file\n"
                        "CTRL+Q\t\tQuit\n"
                        "CTRL+M\tShortcuts\n\n"
                        "S\t\tPlay/ stop\n"
                        "A\t\tFast bakward 5s\n"
                        "D\t\tFast forward 5s\n"
                        "R\t\tToggle record mode\n\n"
                        "1\t\tPlayback rate: 0.5\n"
                        "2\t\tPlayback rate: 0.75\n"
                        "3\t\tPlayback rate: 1\n"
                        "4\t\tPlayback rate: 1.25\n"
                        "5\t\tPlayback rate: 1.5\n"
                        "6\t\tPlayback rate: 1.75\n")

        x = message.exec_()  # this will show our messagebox



    def mediastate_changed(self, state):
        """ This method is responsible of the change between PLAY and PAUSE. The icons of the play-pause-button
        are shifted here."""

        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playBtn.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause)

            )

        else:
            self.playBtn.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPlay)

            )

    def position_changed(self, position):
        self.slider.setValue(position)


    def duration_changed(self, duration):
        self.slider.setRange(0, duration)

    def set_position(self, position):
        self.mediaPlayer.setPosition(position)

    def save_annotation(self):
        """ This method saves annotation into a csv-file in the same directory"""

        if self.filename != None:
            with open(self.filename.replace(".mp4",".csv"), "w", newline="\n") as file:
                writer = csv.writer(file)
                writer.writerow(["Time (ms)", "Engagement (%)"])

                if self.xValues != [] and self.yValues != []:
                    for n in range(len(self.xValues)):
                        writer.writerow([self.xValues[n], self.yValues[n]])
                        self.colors[n] = self.saveColor

                    self.savedRecently = True
                    message = QMessageBox()
                    message.setWindowTitle("Success!")
                    message.setText("The annotation is saved successfully as a csv-file. It is saved in the same directory as the source video file. \n \nThe directory is: "+ self.filename.replace(".mp4",".csv"))
                    x = message.exec_()  # this will show our messagebox

                else:
                    message = QMessageBox()
                    message.setWindowTitle("Fail!")
                    message.setText("There is no annotation to save.")
                    x = message.exec_()  # this will show our messagebox
        if self.filename == None:
            message = QMessageBox()
            message.setWindowTitle("Fail!")
            message.setText("No video has been opened yet.")
            x = message.exec_()  # this will show our messagebox

    def open_annotation(self):
        """ This method opens a csv-annotation and the video which has the same name"""

        # The try-except statements check weather the file is a csv-file. Otherwise an error message is shown in a separate window.
        try:

            self.annotationFile, _ = QFileDialog.getOpenFileName(self, "Open Annotation")

            # Reset the lists
            self.xValues = []
            self.yValues = []
            self.colors = []

            with open(self.annotationFile, newline='') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')

                for row in spamreader:
                    tempList = row[0].split(",")


                    # The try-except statements check weather the element is an integer. If it is a string (the title) we continue to the next element.
                    try:
                        self.xValues.append(int(tempList[0]))
                        self.yValues.append(int(tempList[1]))
                        self.colors.append(self.saveColor)


                        self.playBtn.setEnabled(True)
                        self.saveBtn.setEnabled(True)

                        try:
                            self.neverPlayed = True
                            self.filename = self.annotationFile.replace("csv", "mp4")
                            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(self.filename)))


                        except:
                            message = QMessageBox()
                            message.setWindowTitle("Fail")
                            message.setText("There is no video file in the same directory as the csv-file.")
                            x = message.exec_()  # this will show our messagebox

                    except:
                        continue
        except:
            message = QMessageBox()
            message.setWindowTitle("Fail")
            message.setText("Please choose a csv-file")
            x = message.exec_()  # this will show our messagebox





    def handle_errors(self):
        self.playBtn.setEnabled(False)
        self.label.setText("Error: " + self.mediaPlayer.errorString())



app = QApplication(sys.argv)
window = Window()
sys.exit(app.exec_())

"""
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = Window()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
"""
