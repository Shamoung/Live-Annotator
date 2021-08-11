"""

RT Annotator (Real Time Annotator)
Programmed by: Shamoun Gergi
Recently updated: 09-08-2021

"""



import sys

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, \
    QSlider, QStyle, QSizePolicy, QFileDialog, QSpacerItem, QCheckBox, QComboBox, QRadioButton, QStyleOptionTitleBar
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QIcon, QPalette, QKeySequence, QPainter, QPen, QFont
from PyQt5.QtCore import Qt, QUrl, QRect
from PyQt5.QtWidgets import QMessageBox, QShortcut, QTableWidget, QDesktopWidget, QAction, QStackedLayout, QFrame, QMainWindow

import bisect

from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

import csv

# The module below belongs to "Matplotlib". But I have changed some code in the class. The module "animation.py" should be in the same directory as "RTAnnotator.py".
from animation import *


# ------------------------------------------------------------------------------------------------------------------------------------------


class MplCanvas(FigureCanvas):
    """This class helps to create a widget/ canvas for the plotting-area. It's namely a part of the integration
    between PyQt5 and Matplotlib (the plotting library)."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        #self.axes.hold(False)

        super(MplCanvas, self).__init__(fig)

        #self.compute_initial_figure()

        #FigureCanvas.__init__(self, fig)
        #self.setParent(parent)


        #def compute_initial_figure(self):
        #pass


class Window(QWidget):
    """ This class is about the main window. An object of this class is namely the window."""

    # Init methods: ------------------------------------------------------------------------------------------------------------------
    
    def __init__(self):
        super().__init__()

        self.setWindowTitle("RT Annotator")
        self.setMouseTracking(True)



        # Maximize screen size
        titleBarHeight = self.style().pixelMetric(QStyle.PM_TitleBarHeight,QStyleOptionTitleBar(),self)
        self.geometry = app.desktop().availableGeometry()
        #self.geometry.setHeight(self.geometry.height() - (titleBarHeight * 2))
        self.setGeometry(self.geometry)
        #self.setFixedWidth(self.geometry.width())
        self.showMaximized()

        self.setWindowIcon(QIcon('player.png'))

        p = self.palette()
        p.setColor(QPalette.Window, Qt.white)
        self.setPalette(p)

        # Calling some init-methods
        self.init_attributes()
        self.init_ui()
        self.init_diagram()
        self.init_layout()
        self.mediaConnection()
        self.keyShortcuts()

        self.show()

    def init_attributes(self):
        """ This method initializes some attributes to some initial values."""

        # Creats two lists: one for x-values, one for y-valuse
        self.xValues = []
        self.yValues = []
        self.colors = []

        # Colors of the graph
        self.saveColor = "limegreen"
        self.currentColor = "r"
        self.unsavedColor = "royalblue"

        # Initialization of some other attributes
        self.filename = None
        self.mouseY = 0

        self.startIndex = 0
        self.current_position = 0
        self.position_index = 0

        self.savedRecently = False
        self.videoOpened = False

        self.animation = None
        self.curve = None
        self.k = 25
        self.dt = self.k
    
    def init_ui(self):
        """ This method is responsible of all the graphical elements, eg. buttons, videoplayer, diagram, widgets, etc."""

        # create media player object
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        # create videowidget object
        self.videowidget = QVideoWidget()

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

        # create "new file" button
        self.newFileBtn = QPushButton(" New File")
        self.newFileBtn.clicked.connect(self.newFile)
        self.newFileBtn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))

        # create a help button
        self.HelpBtn = QPushButton(" Help")
        self.HelpBtn.clicked.connect(self.show_help)
        self.HelpBtn.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxQuestion))

        # create button for playing
        self.playBtn = QPushButton()
        self.playBtn.setEnabled(False)
        self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playBtn.clicked.connect(self.play_video)

        # create button for stop
        self.stopBtn = QPushButton()
        self.stopBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stopBtn.clicked.connect(self.stop_video)

        # create checkbox for record
        self.recordLabel = QLabel("Record: ")
        self.recordLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.checkbox = QCheckBox()

        # Create radio buttons for view mode
        self.radioLabel = QLabel(" x-axis range: ")
        self.zoomRadio = QRadioButton("Zoom")
        self.zoomRadio.setChecked(True)
        self.wideRadio = QRadioButton("Wide")
        self.wideRadio.setEnabled(False)

        # create video slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.set_position)

        # Creating a container that includes the videoplayer and the label that shows the value of the slider.
        self.container = QWidget()
        lay = QVBoxLayout(self.container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.videowidget)

        # Create a label that shows the percentage of engagement.
        self.numLabel = QLabel("0", self.container)
        self.numLabel.setFont(QFont('Times', 40))
        self.numLabel.setStyleSheet("background-color: white")
        height = round(self.geometry.height()/20)
        width = round(self.geometry.width()/16)
        self.numLabel.setGeometry(QRect(80, 50, width , height))

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

        # Create label for video duration. It displays the duration of the video.
        self.durationLabel = QLabel("0:0")
        self.durationLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        # Create a label for video length. It displays the length of the video.
        self.lengthLabel = QLabel("/ 0:0")
        self.lengthLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        # create label for error handling
        self.errorLabel = QLabel()
        self.errorLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        # create spacers
        self.spacerItem1 = QSpacerItem(128, 17, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.spacerItem2 = QSpacerItem(128, 17, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.spacerItem3 = QSpacerItem(300, 0)

    def init_diagram(self):
        """This method is about creating the diagram and initializing the axes. """

        # Create a canvas for the diagram, using the MplCanvas-class that is defined above.
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)

        self.curve = self.canvas.axes.scatter([], [], s=25 , c=[])

        self.canvas.axes.set_xlabel("Time (ms)")
        self.canvas.axes.set_ylabel("Engagement (%)")
        self.canvas.axes.set_xlim(-5000,5000)
        self.canvas.axes.set_ylim(0,100)

        self.vline = self.canvas.axes.axvline(x=self.mediaPlayer.position(), color='gray',linestyle=":")
        self.hline = self.canvas.axes.axhline(y=self.mouseY, color='gray',linestyle=":")

        
        # Animation:

        # This formaula below makes sure that "self.update" is updated more often if the playback rate is larger, and updated less often if the playback rate is smaller.
        self.dt = self.k/float(self.speedCombo.currentText())

        self.animation = FuncAnimation(self.canvas.figure, self.update, blit = True, interval=self.dt)

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
        upper_hbox.addWidget(self.HelpBtn)

        upper_hbox.addItem(self.spacerItem1)

        upper_hbox.addWidget(self.radioLabel)
        upper_hbox.addWidget(self.zoomRadio)
        upper_hbox.addWidget(self.wideRadio)

        upper_hbox.addItem(self.spacerItem2)
        upper_hbox.addWidget(self.resetBtn)
        upper_hbox.addWidget(self.errorLabel)


        # ---------------------------------------------------------------------------------------

        # create hbox layout (middle horizontal box).
        middle_hbox = QHBoxLayout()
        middle_hbox.setContentsMargins(0, 0, 0, 0)
                 
        # set widgets to the hbox layout
        middle_hbox.addWidget(self.canvas)
        middle_hbox.addItem(self.spacerItem3)
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
        lower_hbox.addWidget(self.durationLabel)
        lower_hbox.addWidget(self.lengthLabel)


        # ---------------------------------------------------------------------------------------

        # create vbox layout (vertical box)
        vboxLayout = QVBoxLayout()
        vboxLayout.addLayout(upper_hbox)
        vboxLayout.addLayout(middle_hbox)
        vboxLayout.addLayout(lower_hbox)

        #self.setLayout(vboxLayout)
        self.setLayout(vboxLayout)

    def mediaConnection(self):
        """ This method connects the Qmediaplayer object "self.mediaPlayer" to the functions and attributes in
        this class (Window)."""

        self.mediaPlayer.setVideoOutput(self.videowidget)

        # media player signals
        self.mediaPlayer.stateChanged.connect(self.mediastate_changed)
        self.mediaPlayer.positionChanged.connect(self.position_changed)
        self.mediaPlayer.durationChanged.connect(self.duration_changed)


    
    
    # Event methods: ------------------------------------------------------------------------------------------------------------------

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
            if self.checkbox.isChecked() and self.checkbox.isEnabled():
                self.checkbox.setChecked(False)
            elif not self.checkbox.isChecked() and self.checkbox.isEnabled():
                self.checkbox.setChecked(True)

        # Fast forward 0.005s: C
        if e.key() == Qt.Key_C:
            self.set_position(self.mediaPlayer.position() + 50)


        # Fast bakward 0.005s: Z
        if e.key() == Qt.Key_Z:
            self.set_position(self.mediaPlayer.position() - 50)

        # Fast forward 0.2s: D
        if e.key() == Qt.Key_D:
            self.set_position(self.mediaPlayer.position() + 200)

        # Fast bakward 0.2s: A
        if e.key() == Qt.Key_A:
            self.set_position(self.mediaPlayer.position() - 200)

        # Fast forward 5s: E
        if e.key() == Qt.Key_E:
            self.set_position(self.mediaPlayer.position() + 5000)

        # Fast bakward 5: Q
        if e.key() == Qt.Key_Q:
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

        # Shortcuts: CTRl+C
        self.resetSc = QShortcut(QKeySequence('Ctrl+C'), self)
        self.resetSc.activated.connect(self.reset_annotation)

        # Shortcuts: CTRl+M
        self.resetSc = QShortcut(QKeySequence('Ctrl+M'), self)
        self.resetSc.activated.connect(self.show_help)

    def mouseMoveEvent(self, event):
        """ This method tracks the mouse movement and saves its y-coordinate into self.mouseY.
        It also converts the coordinate to 0-100 scale and displays the number on the number label"""

        margin = self.geometry.height()/6
        # The formula below makes the topmost y-coordinate 100, and the bottommost y-coordinate 0.
        
        if event.y() < (5*self.geometry.height()/6) and event.y() > (self.geometry.height()/6):
            if event.x() > (self.geometry.width()/2-150) and event.x() < (self.geometry.width()/2+25):
                self.mouseY = round(100/(margin-(self.geometry.height()-margin)) * (event.y()-margin) + 100)
                #self.mouseY = (100/(margin-(self.geometry.height()-margin)) * (event.y()-margin) + 100)

                self.numLabel.setText(str(self.mouseY))

    def mousePressEvent(self, QMouseEvent):
        """ This method is about mouse click events. Right click = the video plays/ pauses. Click on the wheel = toggle record mode. """
        if QMouseEvent.button() == Qt.RightButton:
            if self.playBtn.isEnabled():
                self.play_video()

        if QMouseEvent.button() == Qt.MiddleButton:
            if self.checkbox.isChecked() and self.checkbox.isEnabled():
                self.checkbox.setChecked(False)
            elif not self.checkbox.isChecked() and self.checkbox.isEnabled():
                self.checkbox.setChecked(True)       

    def wheelEvent(self,event):
        """ This method is responsible for mouse scroll. Scroll up = fast forward. Scroll down = fast backwards."""

        steps = event.angleDelta().y() // 120
        vector = steps and steps // abs(steps) # 0, 1, or -1
        for step in range(1, abs(steps) + 1):
            self.set_position(self.mediaPlayer.position() + 200*vector)

    def mouseDoubleClickEvent(self, QMouseEvent):
        "Dubble click = save annotation"
        if QMouseEvent.button() == Qt.LeftButton:
            self.save_annotation()
  
    def paintEvent(self, event):
        """This method draws the blue rectangle in the middle of the screen. It is the boarder of the mouse tracking area."""

        painter = QPainter(self)

        painter.setPen(QPen(Qt.cyan, 3, Qt.DotLine))

        x = round(self.geometry.width()/2 - 150)
        y = round(self.geometry.height()/6)
        height = round(4*self.geometry.height()/6)
        
        painter.drawRect(x, y, 175, height)
        painter.end()
    



    # Update methods: ------------------------------------------------------------------------------------------------------------------

    def update(self, i):
        """ This method updates the graph. It runs every 25 ms (if playback rate is 1). It is the largest and the most important method in the program. """

        self.current_position = self.mediaPlayer.position()



        """ "Record mode" and "wide x-axis mode" shouls not work together. Wide mode is only for reading data, not writing data. 
        The user is not allowed to write data when 16 000 points are displayed (wide mode) on tha diagram. If he does so, the frequency of the graph points decreases with time. """
        if self.checkbox.isChecked():
            self.wideRadio.setEnabled(False)
        if not self.checkbox.isChecked():
            self.wideRadio.setEnabled(True)
        if self.wideRadio.isChecked():
            self.checkbox.setEnabled(False)
        if not self.wideRadio.isChecked():
            self.checkbox.setEnabled(True)



        if self.checkbox.isChecked() and self.mediaPlayer.state() == QMediaPlayer.PlayingState:
                        
            self.savedRecently = False


            self.current_position = self.mediaPlayer.position()

            if self.xValues == []:
                # "If the list of xValues is empty". This happens only in the start of the plotting process.
                self.xValues.append(self.current_position)
                self.yValues.append(self.mouseY)
                self.colors.append(self.currentColor)

                self.position_index = self.xValues.index(self.current_position)

            if self.xValues != []:

                if self.current_position > max(self.xValues):
                    # "If the point is bigger than the last point". I.e if the point will be plotted in the end of the current graph.

                    self.xValues.append(self.current_position)
                    self.yValues.append(self.mouseY)
                    self.colors.append(self.currentColor)

                    self.position_index = self.xValues.index(self.current_position)

                if self.current_position < max(self.xValues):
                    # "If the point is smaller than the last point". I.e if the point will be plotted in the middle of the current graph.

                    if self.mediaPlayer.position() < 100:
                        """ This if-statement solves a bug. The program has a problem of deleting a point if x=0. Thanks to this if statemnt,
                        the problem is solved."""
                        self.xValues.pop(0)
                        self.yValues.pop(0)
                        self.colors.pop(0)
                    
                    
                    bisect.insort(self.xValues,self.current_position)  # Through this method, the element is inserted in order.
                    self.yValues.insert(self.xValues.index(self.current_position), self.mouseY)
                    self.colors.insert(self.xValues.index(self.current_position), self.currentColor)

                    self.position_index = self.xValues.index(self.current_position)

                    
                    # The graph cleans the points infront of the pointer.
                    cleaning_distance = 150 *float(self.speedCombo.currentText())


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



        # View modes: zoom or wide.

        if self.zoomRadio.isChecked():
            self.canvas.axes.set_ylim(0, 100)
            self.canvas.axes.set_xlim(self.current_position-5000, self.current_position+5000)

            self.update_tempLists()
            self.curve = self.canvas.axes.scatter(self.tempXList, self.tempYList, s=10 , c=self.tempCList)

        if self.wideRadio.isChecked():
            self.canvas.axes.set_ylim(0, 100)

            if self.mediaPlayer.duration() != 0:
                self.canvas.axes.set_xlim(0, self.mediaPlayer.duration())

            self.curve = self.canvas.axes.scatter(self.xValues, self.yValues, s=10 , c=self.colors)
        

        # I remove the previous hline and vline. If I do not remove the previous lines, the program gets slower and slower, and the frequency of the points decreases with time.
        self.hline.remove()
        self.vline.remove()
        
        # New vertical line and horizontal line are created and updated to the correct values.
        self.vline = self.canvas.axes.axvline(x=self.mediaPlayer.position(), color='gray',linestyle=":")
        self.hline = self.canvas.axes.axhline(y=self.mouseY, color='gray',linestyle=":")


        return [self.curve] + [self.vline] + [self.hline]

    def update_tempLists(self):
        """ This method updates the temporary lists that are plotted."""
        self.current_position = self.mediaPlayer.position()

        # I add the current value, calculates its index, and removes it. This method is used to know which index the pointer is at.
        bisect.insort(self.xValues,self.current_position)
        self.position_index = self.xValues.index(self.current_position)
        self.xValues.remove(self.current_position)

        n = 120
        if self.position_index < n:       
            self.tempXList = self.xValues[:self.position_index + n]
            self.tempYList = self.yValues[:self.position_index + n]
            self.tempCList = self.colors[:self.position_index + n]
        else:
            self.tempXList = self.xValues[self.position_index - n :self.position_index + n]
            self.tempYList = self.yValues[self.position_index - n :self.position_index + n]
            self.tempCList = self.colors[self.position_index - n :self.position_index + n]



    
    # File management methods: ------------------------------------------------------------------------------------------------------------------
    
    def open_file(self):
        """ This method opens a video file and activates the play and save button"""

        
        self.filename_temp, _ = QFileDialog.getOpenFileName(self, "Open Video")

        if self.filename_temp != '':
            if self.filename_temp[-3:] == "mp4" or self.filename_temp[-3:] == "wav" or self.filename_temp[-3:] == "wmv" or self.filename_temp[-3:] == "mov":
                self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(self.filename_temp)))
                self.playBtn.setEnabled(True)
                self.saveBtn.setEnabled(True)
                self.videoOpened = True
                self.reset_annotation()
                self.filename = self.filename_temp
            else:
                message = QMessageBox()
                message.setWindowTitle("Fail")
                message.setText("Please choose a file with one of the following extensions:\nmp4, wav, mov or wmv.")
                x = message.exec_()  # this will show our messagebox
        elif self.filename_temp == '' and self.videoOpened:
            self.filename = self.filename
        elif self.filename_temp == '' and not self.videoOpened:
            self.filename = None

    def reset_annotation(self):
        """ This method clears the graph. It sets the xValues, yValues and colors 
        to empty lists and stops the video."""

        self.xValues = []
        self.yValues = []
        self.colors = []

        self.stop_video()

    def newFile(self):
        """ This methods closes the current file and opens a new one."""
        self.animation._stop()
        self.close()
        self.__init__()
  
    def show_help(self):
        """ This method shows all the shorcuts on a pop-up window"""

        message = QMessageBox()
        message.setWindowTitle("Help")
        message.setMinimumHeight(1000)
        message.setMinimumWidth(1000)

        message.setText("How to annotate:\n"
                        "Move the mouse up and down between the doted rectangle.\n\n\n"
                        "Mouse shortcuts (inside the blue box):\n\n"
                        "Right click\tPlay/pause\n"
                        "Scroll\t\tFast forward/ backward\n"
                        "Dubble click\tSave\n"
                        "Wheel click\tToggle record mode\n\n\n"                        
                        "Keyboard shortcuts:\n\n"
                        "CTRL+S\t\tSave\n"
                        "CTRL+O\t\tOpen video\n"
                        "CTRL+I\t\tOpen annotation\n"
                        "CTRL+N\t\tNew file\n"
                        "CTRL+C\t\tClear annotation\n"
                        "CTRL+Q\t\tQuit\n"
                        "CTRL+M\t\tShortcuts\n\n"
                        "S\t\tPlay/ stop\n"
                        "Z\t\tFast bakward 50 ms\n"
                        "C\t\tFast forward 50 ms\n"
                        "A\t\tFast bakward 200 ms\n"
                        "D\t\tFast forward 200 ms\n"
                        "Q\t\tFast bakward 5 s\n"
                        "E\t\tFast forward 5 s\n"
                        "R\t\tToggle record mode\n\n"
                        "1\t\tPlayback rate: 0.5\n"
                        "2\t\tPlayback rate: 0.75\n"
                        "3\t\tPlayback rate: 1\n"
                        "4\t\tPlayback rate: 1.25\n"
                        "5\t\tPlayback rate: 1.5\n"
                        "6\t\tPlayback rate: 1.75\n")

        x = message.exec_()  # this will show our messagebox

    def save_annotation(self):
        """ This method saves annotation into a csv-file in the same directory"""

        if self.filename != None and self.videoOpened:
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
        if not self.videoOpened:
            message = QMessageBox()
            message.setWindowTitle("Fail!")
            message.setText("No video has been opened yet.")
            x = message.exec_()  # this will show our messagebox

    def open_annotation(self):
        """ This method opens a csv-annotation and the video which has the same name"""

        
        self.checkbox.setChecked(False)
        # The try-except statements check weather the file is a csv-file. Otherwise an error message is shown in a separate window.


        self.annotationFile, _ = QFileDialog.getOpenFileName(self, "Open Annotation")

        if self.annotationFile[-3:] == "csv":

            # Reset the lists
            self.xValues = []
            self.yValues = []
            self.colors = []

            with open(self.annotationFile, newline='') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')

                for row in spamreader:
                    tempList = row[0].split(",")


                    try:
                        # This try-except statements checks weather the element is an integer. If it is a string (the column titles) we continue to the next element.

                        self.xValues.append(int(tempList[0]))
                        self.yValues.append(int(tempList[1]))
                        self.colors.append(self.saveColor)


                        self.playBtn.setEnabled(True)
                        self.saveBtn.setEnabled(True)

                        try:
                            self.videoOpened = True
                            self.filename = self.annotationFile.replace("csv", "mp4")
                            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(self.filename)))


                        except:
                            message = QMessageBox()
                            message.setWindowTitle("Fail")
                            message.setText("There is no video file in the same directory as the csv-file.")
                            x = message.exec_()  # this will show our messagebox

                    except:
                        #  If the element is a string (the column titles) we continue to the next element.
                        continue
        
        elif self.annotationFile[-3:] != "csv" and self.annotationFile != "":
            message = QMessageBox()
            message.setWindowTitle("Fail")
            message.setText("Please choose a csv-file")
            x = message.exec_()  # this will show our messagebox



    # Media methods: ------------------------------------------------------------------------------------------------------------------

    def play_video(self):
        """ This method plays a video and shifts between PLAY and PAUSE. It also activates and inactivates different
        graphical elements"""


        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            # If the video was playing: pause.
            self.mediaPlayer.pause()
            
            # Enabling all the buttons.
            self.enable_btns()


        else:
            
            # Converts all red graph points to blue points
            for n in range(len(self.colors)):
                if self.colors[n] == self.currentColor:
                    self.colors[n] = self.unsavedColor


            # If the video was paused or stopped: play.
            self.mediaPlayer.play()
            
            # Playback rate is set to the value of the speedCombo.
            self.mediaPlayer.setPlaybackRate(float(self.speedCombo.currentText()))
            
            # This formaula below makes sure that "self.update()" is updated faster if the playback rate is larger, and updated slower if the playback rate is smaller.
            # Currently, self.k = 25
            self.dt = self.k / float(self.speedCombo.currentText())

            # SetInterval() is a method that I wrote in a matplotlib class. It updates the interval of the function "self.update()".
            self.animation.setInterval(self.dt)

            # Disabling all the buttons, the speedCombo and the checkbox
            self.disable_btns()
         
    def stop_video(self):
        """ This method stops a video. It also activates different graphical elements"""

        # Enabling all the buttons, the speedCombo and the checkbox
        self.enable_btns()

        if self.mediaPlayer.state() == QMediaPlayer.PlayingState or self.mediaPlayer.state() == QMediaPlayer.PausedState:
            self.mediaPlayer.stop()
        else:
            pass

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
        

        # Updates the duration of the video.
        self.durationLabel.setText(str((position//1000)//60) + ":"+ str((position//1000)%60))

    def duration_changed(self, duration):
        self.slider.setRange(0, duration)

        # Updates the maximal length of the video.
        self.lengthLabel.setText("/ "+str((duration//1000)//60) + ":"+ str((duration//1000)%60))

    def set_position(self, position):
        self.mediaPlayer.setPosition(position)

    def enable_btns(self):
        """ This method enables all the buttons and other graphical elements that that should be enabled. """
        self.saveBtn.setEnabled(True)
        self.openVideoBtn.setEnabled(True)
        self.openAnnotationBtn.setEnabled(True)
        self.resetBtn.setEnabled(True)
        self.speedCombo.setEnabled(True)
        self.newFileBtn.setEnabled(True)
        self.HelpBtn.setEnabled(True)

    def disable_btns(self):
        """ This method disables all the buttons and other graphical elements that that should be disabled. """
        self.saveBtn.setEnabled(False)
        self.openVideoBtn.setEnabled(False)
        self.openAnnotationBtn.setEnabled(False)
        self.resetBtn.setEnabled(False)
        self.speedCombo.setEnabled(False)
        self.newFileBtn.setEnabled(False)
        self.HelpBtn.setEnabled(False)

    
    # Error handling: ------------------------------------------------------------------------------------------------------------------
    def handle_errors(self):
        self.playBtn.setEnabled(False)
        self.errorLabel.setText("Error: " + self.mediaPlayer.errorString())



app = QApplication(sys.argv)
window = Window()
sys.exit(app.exec_())