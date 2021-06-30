"""

RT Annotator (Real Time Annotator)
Shamoun Gergi
Recently updated: 30-06-2021

"""


from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, \
    QSlider, QStyle, QSizePolicy, QFileDialog, QSpacerItem, QCheckBox, QComboBox, QRadioButton
import sys
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QIcon, QPalette, QPainter, QFont#, QKeySequence
from PyQt5.QtCore import Qt, QUrl, QRect
from PyQt5.QtWidgets import QMessageBox, QAction, QStackedLayout, QFrame, QMainWindow

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
        self.setGeometry(350, 100, 1920, 1080)
        self.setWindowIcon(QIcon('player.png'))

        p = self.palette()
        p.setColor(QPalette.Window, Qt.white)
        self.setPalette(p)

        self.init_ui()
        self.init_layout()
        self.mediaConnection()

        # Create menu bar and add action


        self.show()

    def init_ui(self):
        """ This method is responsible of all the graphical elements, eg. buttons, videoplayer, diagram, widgets, etc."""


        # Creats two lists: one for x-values, one for y-valuse
        self.xValues = []
        self.yValues = []


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

        # create reset button
        self.resetProBtn = QPushButton(" Reset")
        self.resetProBtn.clicked.connect(self.reset_pro)
        self.resetProBtn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))

        # create button for playing
        self.playBtn = QPushButton()
        self.playBtn.setEnabled(False)
        self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playBtn.clicked.connect(self.play_video)

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
        self.speedComboLabel = QLabel(" |   Playback speed: ")
        self.speedComboLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.speedCombo = QComboBox()
        self.speedCombo.addItem("0.25")
        self.speedCombo.addItem("0.5")
        self.speedCombo.addItem("0.75")
        self.speedCombo.addItem("1")
        self.speedCombo.addItem("1.25")
        self.speedCombo.addItem("1.5")
        self.speedCombo.addItem("1.75")
        self.speedCombo.addItem("2")
        self.speedCombo.setCurrentIndex(3)

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
        self.x = np.linspace(0, 100, 10)
        self.y = np.linspace(0, 100, 10)
        self.line, = self.canvas.axes.plot(self.x, self.y, animated=True, lw=2)

        keyboard.on_press_key("a", lambda _: self.set_position(self.mediaPlayer.position() - 5000))
        keyboard.on_press_key("s", lambda _: self.play_video())
        keyboard.on_press_key("d", lambda _: self.set_position(self.mediaPlayer.position() + 5000))
        keyboard.on_press_key("r", lambda _: self.r_clicked())


    def r_clicked(self):
        if self.checkbox.isChecked():
            self.checkbox.setChecked(False)
        else:
            self.checkbox.setChecked(True)

    def s_clicked(self):
        if self.playBtn.isEnabled():
            print("video played")
            self.play_video()

    def init_layout(self):
        """This method sets the layout of the window. It places the buttons, sliders and widgets
        in an organised layout."""

        # create hbox layout (upper horizontal box).
        upper_hbox = QHBoxLayout()
        upper_hbox.setContentsMargins(0, 0, 0, 0)

        # set widgets to the hbox layout
        upper_hbox.addWidget(self.openVideoBtn)
        upper_hbox.addWidget(self.openAnnotationBtn)
        upper_hbox.addWidget(self.saveBtn)
        upper_hbox.addItem(self.spacerItem)

        upper_hbox.addWidget(self.viewComboLabel)
        upper_hbox.addWidget(self.viewCombo)

        #upper_hbox.addWidget(toolbar)
        upper_hbox.addItem(self.spacerItem2)

        upper_hbox.addWidget(self.resetProBtn)
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

    def mediaConnection(self):
        self.mediaPlayer.setVideoOutput(self.videowidget)

        # media player signals
        self.mediaPlayer.stateChanged.connect(self.mediastate_changed)
        self.mediaPlayer.positionChanged.connect(self.position_changed)
        self.mediaPlayer.durationChanged.connect(self.duration_changed)


    """ Other methods: """

    def update_line(self, i):

        """ This method updates the graph. It runs every 20 ms (if playback rate is 1)"""

        #print(self.mediaPlayer.position(), " ms \t \t", self.VerticalSlider.value(), " %")

        #self.y = np.linspace(0, self.mediaPlayer.duration(), 10)

        current_position = self.mediaPlayer.position()

        if self.checkbox.isChecked() and self.mediaPlayer.state() == QMediaPlayer.PlayingState:

            current_position = self.mediaPlayer.position()


            if self.xValues == []:
                # "If the list of xValues is empty". This happens only in the start of the plotting process.
                self.xValues.append(current_position)
                self.yValues.append(self.VerticalSlider.value())

            if self.xValues != []:

                if current_position > max(self.xValues):
                    # "If the point is bigger than the last point". I.e if the point will be plotted in the end of the current graph.

                    self.xValues.append(current_position)
                    self.yValues.append(self.VerticalSlider.value())

                if current_position < max(self.xValues):
                    # "If the point is smaller than the last point". I.e if the point will be plotted in the middle of the current graph.

                    bisect.insort(self.xValues,current_position)  # Through this method, the element is inserted in order.
                    self.yValues.insert(self.xValues.index(current_position), self.VerticalSlider.value())

                    position_index = self.xValues.index(current_position)


                    if current_position == 0:
                        current_position = 10
                        self.set_position(10)
                        # This if-statement solves a bug. The program has a problem when the current position is 0.


                    #print(self.xValues[position_index + 1] - current_position)

                    if position_index < (len(self.xValues)-1):
                        if (self.xValues[position_index + 1] - current_position) < 100:
                            self.xValues.pop(position_index + 1)
                            self.yValues.pop(position_index + 1)

                    if position_index < (len(self.xValues)-2):
                        if (self.xValues[position_index + 2] - current_position) < 200:
                            self.xValues.pop(position_index + 2)
                            self.yValues.pop(position_index + 2)

                    if position_index < (len(self.xValues)-3):
                        if (self.xValues[position_index + 3] - current_position) < 300:
                            self.xValues.pop(position_index + 3)
                            self.yValues.pop(position_index + 3)



                    """
                    if self.xValues[position_index + 1] - current_position < 100:

                        if position_index < (len(self.xValues) - 1):
                            self.xValues.pop(position_index + 1)
                            self.yValues.pop(position_index + 1)

                            if position_index < (len(self.xValues) - 2):
                                self.xValues.pop(position_index + 2)
                                self.yValues.pop(position_index + 2)

                                if position_index < (len(self.xValues) - 3):
                                    self.xValues.pop(position_index + 3)
                                    self.yValues.pop(position_index + 3)
                    """


        # View modes
        if self.viewCombo.currentText() == "(now - 10s, now)":
            self.canvas.axes.set_ylim(0, 100)
            self.canvas.axes.set_xlim(current_position-10000, current_position)

        if self.viewCombo.currentText() == "(now - 5s, now + 5s)":
            self.canvas.axes.set_ylim(0, 100)
            self.canvas.axes.set_xlim(current_position-5000, current_position+5000)

        if self.viewCombo.currentText() == "(0, now)":
            self.canvas.axes.set_ylim(0, 100)
            if current_position == 0:
                self.canvas.axes.set_xlim(0, 1000)
            else:
                self.canvas.axes.set_xlim(0, current_position)


        if self.viewCombo.currentText() == "(0, end)":
            self.canvas.axes.set_ylim(0, 100)
            self.canvas.axes.set_xlim(0, self.mediaPlayer.duration())

        self.line, = self.canvas.axes.plot(self.xValues, self.yValues, "r", marker='.')

        self.show()

        return [self.line]

    """

    def update_pointer(self, i):


        self.canvas.axes.cla()
        self.pointer, = self.canvas.axes.plot([self.mediaPlayer.position(), self.mediaPlayer.position()], [0,100], '#1dff00')

        #self.pointer.set_data(self.mediaPlayer.position(), 100)
        
    """
        



    def gen1(self):
        i = 0.5
        while (True):
            yield i
            i += 0.1

    def gen2(self):
        j = 0
        while (True):
            yield j
            j += 1




    def open_file(self):
        """ This method opens a video file and activates the play and save button"""

        self.filename, _ = QFileDialog.getOpenFileName(self, "Open Video")

        if self.filename != '':
            if self.filename[-3:] == "mp4" or self.filename[-3:] == "wav" or self.filename[-3:] == "wmv" or self.filename[-3:] == "mov":
                print(self.filename[-3:])
                self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(self.filename)))
                self.playBtn.setEnabled(True)
                self.saveBtn.setEnabled(True)

                #keyboard.on_press_key("a", lambda _: self.set_position(self.mediaPlayer.position() - 5000))
                #keyboard.on_press_key("x", lambda _: self.play_video())
                #keyboard.on_press_key("d", lambda _: self.set_position(self.mediaPlayer.position() + 5000))

            else:
                message = QMessageBox()
                message.setWindowTitle("Fail")
                message.setText("Please choose a file with one of the following extensions:\nmp4, wav, mov or wmv.")
                x = message.exec_()  # this will show our messagebox



    def play_video(self):
        """ This method plays a video and shifts between PLAY and PAUSE. It also activates and inactivates different
        graphical elements"""

        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
            #self.ani._stop()

            # Enabling all the buttons, the speedCombo and the checkbox
            self.saveBtn.setEnabled(True)
            self.openVideoBtn.setEnabled(True)
            self.openAnnotationBtn.setEnabled(True)
            self.resetBtn.setEnabled(True)
            self.speedCombo.setEnabled(True)

        else:
            self.mediaPlayer.play()

            # Through the formula below, the update time (ms) is depended on the playback speed.
            # If playback speed is 1 ==> the line updates every 20 ms
            # If playback speed is 0.25 ==> the line updates every 80 ms
            # If playback speed is 2 ==> the line updates every 10 ms, etc.

            #interval_value = 20/float(self.speedCombo.currentText())

            if float(self.speedCombo.currentText()) == 1:
                interval_value = 20

            if self.speedCombo.currentText() == "0.25":
                print("0.25")
                interval_value = 1000

            if float(self.speedCombo.currentText()) == 2:
                interval_value = 1/20


            self.ani = FuncAnimation(self.canvas.figure, self.update_line, blit=True, interval=25)
            #self.ani = FuncAnimation(self.canvas.figure, self.update_line, self.gen2, interval=interval_value)

            # Disabling all the buttons, the speedCombo and the checkbox
            self.saveBtn.setEnabled(False)
            self.openVideoBtn.setEnabled(False)
            self.openAnnotationBtn.setEnabled(False)
            self.resetBtn.setEnabled(False)
            self.speedCombo.setEnabled(False)


            # Playback speed is set to the value of the speedCombo.
            self.mediaPlayer.setPlaybackRate(float(self.speedCombo.currentText()))




    def stop_video(self):
        """ This method stops a video. It also activates different graphical elements"""

        #print(self.xValues)

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

    def reset_pro(self):
        self.close()
        self.__init__()



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

        with open(self.filename.replace(".mp4",".csv"), "w", newline="\n") as file:
            writer = csv.writer(file)
            writer.writerow(["Time (ms)", "Engagement (%)"])

            for n in range(len(self.xValues)):
                writer.writerow([self.xValues[n], self.yValues[n]])

        message = QMessageBox()
        message.setWindowTitle("Success!")
        message.setText("The annotation is saved successfully as a csv-file. It is saved in the same directory as the source video file. \n \nThe directory is: "+ self.filename.replace(".mp4",".csv"))
        x = message.exec_()  # this will show our messagebox

    def open_annotation(self):
        """ This method opens a csv-annotation and the video which has the same name"""

        # The try-except statements check weather the file is a csv-file. Otherwise an error message is shown in a separate window.
        try:

            self.annotationFile, _ = QFileDialog.getOpenFileName(self, "Open Annotation")

            self.xValues = []
            self.yValues = []

            with open(self.annotationFile, newline='') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')

                for row in spamreader:
                    tempList = row[0].split(",")


                    # The try-except statements check weather the element is an integer. If it is a string (the title) we continue to the next element.
                    try:
                        self.xValues.append(int(tempList[0]))
                        self.yValues.append(int(tempList[1]))


                        self.playBtn.setEnabled(True)
                        self.saveBtn.setEnabled(True)

                        try:
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