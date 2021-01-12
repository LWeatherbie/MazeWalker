import sys
import ctypes
import time
import cv2 as cv
import numpy as np
import random
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
# from PyQt5.QtGui import QDesktopWidget
from CLProcessor import CLProcessor as clp
# from mzWalker import process_maze as procMaze
from MazeWalker import process_maze as processMaze
from MazeWalker import solve_maze as solveMaze

class QCommandButton(QtWidgets.QPushButton):

    """ Command Button Class

        This class defines a command button and is used to save
        repetitive input of the button size and captions. Tt also
        sets some other "common" features used in this program
        like making the button clickable, hiding it when the program
        first starts (Next button) or setting it disabled until certain
        conditions are met (e.g. Solve Maze is disabled until a file is
        read in).

        Input:
        ------
        caption   := string containing the caption the button will show.
        visible   := Boolean indicating whether the button is shown
                     default is True
        enabled   := Boolean indicating whether the button is enabled
                     default is True
        checkable := Boolean indicating whether the button is clickable
                     defaull is False

        Output:
        -------
        PyQt5 QPushButton instance.

    """

    def __init__(self, caption, visible=True, enabled=True, checkable=False):
        super().__init__()
        self.setFixedSize(QtCore.QSize(120,30))
        self.caption = caption
        self.setText(caption)
        self.setVisible(visible)
        self.setEnabled(enabled)
        self.setCheckable(checkable)

class QTabbedImages(QTabWidget):

    """ Tabbed Image Display Class

        This class defines a tabbed display that shows the various
        images of the maze, the initial file that was read in (referred
        to as the File Image, an image of what the program  scanned from
        the file into the Maze_Cell structure (referred to as the
        Scanned Image) and, if the maze has a solution, an image showing
        the path the program found through the maze (referred to as the
        Solved Image).

        NOTE: If the program cannot find a successful solution to the
        maze, it will try to find edits (single wall removals) that
        would make the maze solvable. If it finds such edits, the image
        displayed as the Solved Image will be the Scanned Image with
        the appropriate walls circled.

        This class also stores the name of the input file as well as the
        computer-generated names of the scanned and solved files and
        copies of the QPixmaps of the images (both with and without
        coordinates for the file image and scanned image) so that they
        can be saved if he user so requests without having to be
        generated each time.

        Input:
        ------
        None.

        Output:
        -------
        QTabWidget      := Displays three tabs to show the File Image,
                           the Scanned Image and the Solved Image.
        File Image      := The image read in from the file. Two copies
                           are stored, one showing the maze as read from
                           the file and one with indices (row, col)
                           displayed in each cell.
        Scanned Image   := The image of what the program scanned and
                           will use to navigate through the maze.
                           Two copies are stored, one showing the maze
                           as scanned and one with indices (row, col)
                           displayed in each cell.
        Solution Image  := The image of the solved maze with the path
                           displayed or suggested edits to make it
                           solvable if no path through the maze was
                           found).

    """

    # Define a signal that will be sent when the display tab changes.
    # This will send the image_message associated with the image (by
    # default, this will be the file name).  In the case of the solved
    # image, if it is not solvable, a string pointing out the suggested
    # edits will be appended to the file name displayed.
    tabMessage = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        # Set a signal for tab change
        self.currentChanged.connect(self.tab_changed)

        # Define a loading Boolean to keep "data changed" triggers
        # from firing while the form initially loads.  For example,
        # we do not want the draw_coordinates to fire when the
        # program first reads in an image from a file and calculates
        # the width and height of the maze. It will update the detail
        # spinboxes but we will want to wait until it is done to call
        # the draw_coordinates method manually. If the user changes one
        # or both of the values during a program run, however, we will
        # want to call the method.
        self.file_loading = True

        # Set the size of the image window (width and height will be the
        # same so, set a single variable that will be used for both
        # dimensions).
        self.image_size = 900

        # Define the attributes for the input file.
        self.maze_image =  np.zeros((1,1), dtype=int)
        self.file_image = QtWidgets.QLabel(self)
        self.file_image_name = ""
        self.file_image_message = ""
        # Initialize the image as blank
        self.file_pixmap = QtGui.QPixmap(self.image_size,
                                         self.image_size)
        self.file_pixmap.fill(QtGui.QColor('white'))
        self.file_image.setPixmap(self.file_pixmap.scaled(
                                  self.image_size,
                                  self.image_size,
                                  Qt.KeepAspectRatio))
        self.file_image.resize(self.file_pixmap.width(),
                               self.file_pixmap.height())

        # Define the attributes for the scanned image.
        self.scanned_image = QtWidgets.QLabel(self)
        self.scanned_image_name = ""
        self.scanned_image_message = ""
        # Initialize the image as blank
        pixmap = QtGui.QPixmap(self.image_size, self.image_size)
        pixmap.fill(QtGui.QColor('white'))
        self.scanned_pixmap = pixmap.scaled(
                              self.image_size,
                              self.image_size,
                              Qt.KeepAspectRatio)
        self.scanned_image.setPixmap(self.scanned_pixmap)
        self.scanned_image.resize(pixmap.width(),pixmap.height())
        # Make a copy of the "main" image to the image that will store
        # the indices of the row, col coordinates.
        self.scanned_pixmap_coords = self.scanned_pixmap. copy(0,0,
                                                               self.image_size,
                                                               self.image_size)

        # Define the attributes for the solved image.
        self.solved_image = QtWidgets.QLabel(self)
        self.solved_image_name = ""
        self.solved_image_message = ""
        # Initialize the image as blank
        self.solved_image.setPixmap(pixmap.scaled(self.image_size,
                                                  self.image_size,
                                                  Qt.KeepAspectRatio))
        self.solved_image.resize(pixmap.width(),pixmap.height())

        # Add the three tabs and assign the appropriate image names to
        # them.
        self.setDocumentMode(True)
        self.setTabPosition(QTabWidget.North)
        self.setMovable(True)
        self.addTab(self.file_image, "File Image")
        self.addTab(self.scanned_image, "Scanned Image")
        self.addTab(self.solved_image, "Solution Image")

    def __make_new_filename(self,filename, add_string):
        """ Make New Filename Method (private)

        Splits the passed filename at the last period, appends the
        add_string to the leading string then re-applies the trailing
        piece (assumed to be the extension). If no extension is found
        (i.e. no period in the filename), add_string is added along
        with the ".jpg" extension.

        Note that this is the same code that is included in the
        CLProcessor class as it is required there for batch processing
        and here for interactive processing.

        Inputs:
        -------
        filename      := The filename to be modified.
        add_string    := The text to add to filename before the extension.

        Output:
        -------
        Passed filename with the contents of add_string inserted before the
        extension.

        Examples:
        --------
            >>> __make_new_filename("TestMaze.png", " Solved")
            "TestMaze Solved.png"
        """
        dotpos = filename.rfind(".")
        if dotpos == -1:
            return filename + add_string + ".jpg"
        else:
            return filename[:dotpos - len(filename)] + add_string + \
                   filename[dotpos:]

    def set_file_image(self, image_name,
                             maze_width,
                             maze_height,
                             showCoords=False,
                             message=""):
        """ Set File Image Method

            This takes the name of the file specified by the user and
            displays it on the File Image tab. It also stores the passed
            file name and generates and stores the "default" names for
            the other image files (Scanned Image = File Image name with
            " Scanned" added before the extension and Solved Image =
            File Image name with " Solved" added before the
            extension).

            Input:
            ------
            image_name := Name of the file containing the File Image
            maze_width := Width of the maze in cells.
            maze_height:= Height of the maze in cells.
            showCoords := Boolean representing the checked state of the
                          Show Coordinates button on the main screen.
                          This will be used to determine which image to
                          display.
            message    := Optional message to be associated with the
                          image. If left blank, this will default to the
                          name of the file.

            Output:
            -------
            file_pixmap and file_pixmap_coords are updated with the
            appropriate images. This method will also call the
            show_file_image method to display the image.
        """

        # Set the file names for each of the images and read the file
        # image into the file_pixmap.
        self.file_image_name = image_name
        self.file_image_message = image_name
        self.scanned_image_name = self.scanned_image_message \
                                = self.__make_new_filename(image_name,
                                                           " Scanned")
        self.solved_image_name = self.solved_image_message \
                               = self.__make_new_filename(image_name,
                                                          " Solution")
        self.file_pixmap = QtGui.QPixmap(image_name).scaled(self.image_size,
                                                            self.image_size,
                                                            Qt.KeepAspectRatio)

        self.show_file_image(self.file_pixmap)

        # A new image file is being read in so we need to clear out any
        # previously-generated images stored in the scanned_image and
        # solved_image attributes.
        pixmap = QtGui.QPixmap(self.image_size, self.image_size)
        pixmap.fill(QtGui.QColor('white'))
        self.scanned_image.setPixmap(pixmap)
        self.scanned_image.resize(pixmap.width(),pixmap.height())
        self.scanned_image_message = ""
        self.solved_image.setPixmap(pixmap)
        self.solved_image.resize(pixmap.width(),pixmap.height())
        self.solved_image_message = ""

    def show_file_image(self, pixmap, message=""):
        """ Show File Image Method

            This takes the image generated by the program using the
            details about the maze it has calculated from the File Image
            and displays it on the Scanned Image tab.

            Input:
            ------
            pixmap := Pixmap to be displayed on the File Image tab.
            message:= Text to be displayed in the status bar under the
                      image this is generally the file name but can
                      also include other comments on the image.

            Output:
            -------
            File Image tab is updated to display the passed image and
            the message is displayed on the status bar of the main
            window.
        """

        self.file_image.setPixmap(pixmap)
        if message == "":
            self.file_image_message = self.file_image_name
        else:
            self.file_image_message = message

        # Call the tab_changed method with the current tab index to
        # ensure the correct message is displayed on the main screen.
        self.tab_changed(self.currentIndex())

    def set_scanned_image(self, image,
                                coord_image,
                                showCoords,
                                message=""):
        """ Set Scanned Image Method

            Stores the image generated by the program using the details
            about the maze it has calculated from the File Image and
            calls draw_coordinates to produce the indexed version of the
            scanned image. Once the images are stored, the appropriate
            image will be displayed on the Scanned Image tab.

            Input:
            ------
            image       := Image created by the draw_maze() function.
            coord_image := Image created by the draw_maze() function
                           with the row and column of each cell
                           indicated.
            showCoords  := Boolean representing the checked state of the
                           Show Coordinates button on the main screen.
                           This will be used to determine which image to
                           display.
            message     := Optional message to be associated with the
                           image. If left blank, this will default to
                           the name of the file.

            Output:
            -------
            scanned_pixmap and scanned_pixmap_coords are updated with
            the appropriate images. This method will also call the
            show_file_image method to display the image.
        """

        self.scanned_pixmap = QtGui.QPixmap(image).scaled(self.image_size,
                                                          self.image_size,
                                                          Qt.KeepAspectRatio)
        self.scanned_pixmap_coords = QtGui.QPixmap(coord_image).scaled(self.image_size,
                                                                       self.image_size,
                                                                       Qt.KeepAspectRatio)

        # Display the correct scanned image, based on the value of
        # showCoords
        if showCoords:
            self.show_scanned_image(self.scanned_pixmap_coords)
        else:
            self.show_scanned_image(self.scanned_pixmap)
        if message == "":
            self.scanned_image_message = self.scanned_image_name
        else:
            self.scanned_image_message = message

    def show_scanned_image(self, pixmap, message=""):
        """ Show File Image Method

            Displays the image specified by pixmap on the Scanned Image
            tab along with the associated message.

            Input:
            ------
            pixmap := The pixmap to be displayed on the Scanned Image
                      tab.
            message:= Text to be displayed in the status bar under the
                      image. If left blank, the message stored in the
                      tabbed images instance will be used.

            Output:
            -------
            Scanned Image tab is updated to display the passed image and
            the appropriate message is displayed on the status bar of
            the main window.
        """

        self.scanned_image.setPixmap(pixmap)
        if message == "":
            self.scanned_image_message = self.scanned_image_name
        else:
            self.scanned_image_message = message

        # Call the tab_changed method with the current tab index to
        # ensure the correct message is displayed on the main screen.
        self.tab_changed(self.currentIndex())

    def set_solved_image(self, image, message=""):
        """ Set Solved Image Method

            Stores the image generated by the program using the
            details about the path through the maze it has calculated
            after running navigate_maze() on the scanned maze.

            Input:
            ------
            image  := Image generated by the Maze Reader navigate_maze()
                      function.
            message:= Text to be displayed in the status bar under the
                      image this is generally the file name but can
                      also include other comments on the image.
            Output:
            -------
            Solved Image tab is updated to display the passed image and
            the message is displayed on the status bar of the main
            window.
        """

        self.solved_pixmap = QtGui.QPixmap(image).scaled(self.image_size,
                                                         self.image_size,
                                                         Qt.KeepAspectRatio)
        if message == "":
            self.scanned_image_message = self.scanned_image_name
        else:
            self.scanned_image_message = message

        self.show_solved_image(message)

    def show_solved_image(self, message=""):
        """ Show File Image Method

            Displays the image specified by solved_pixmap on the Solved
            Image tab along with the associated message.

            Note that this method differs slightly from the others that
            show an image in that it does not take a pixmap. This is
            because there will only be one solved image - either the
            image showing the path through the maze or the image showing
            possible edits to make the maze solvable.

            Input:
            ------
            message:= Text to be displayed in the status bar under the
                      image. If left blank, the message stored in the
                      tabbed images instance will be used.

            Output:
            -------
            Solved Image tab is updated to display the solved_pixmap and
            the appropriate message is displayed on the status bar of
            the main window.
        """

        self.solved_image.setPixmap(self.solved_pixmap)
        if message == "":
            self.solved_image_message = self.solved_image_name
        else:
            self.solved_image_message = message

        # Call the tab_changed method with the current tab index to
        # ensure the correct message is displayed on the main screen.
        self.tab_changed(self.currentIndex())

    def save_scanned_image(self, filename, showCoords=False):
        """ Save Scanned Image Method

            saves the Scanned Image using the passed filename.

            Input:
            ------
            filename := Name of the file the Scanned Image will be saved
            to.
            showCoords := Boolean that represents the state of the Show
                          Coordinates button. If it is pressed, meaning
                          the cell indices are displayed then the image
                          containing the coordinates is saved, otherwise
                          the image without the coordinates is saved.

            Output:
            -------
            File containing the Scanned Image.
        """

        if showCoords:
            self.scanned_pixmap_coords.save(filename)
        else:
            self.scanned_pixmap.save(filename)

    def save_solved_image(self, filename):
        """ Save Solved Image Method

            Saves the Solved Image using the passed filename.

            Input:
            ------
            filename := Name of the file the Solved Image will be saved
            to.

            Output:
            -------
            File containing the Solved Image.
        """

        self.solved_pixmap.save(filename)

    def tab_changed(self,i):
        """ Tab Changed Method

            Called when the currentChanged signal occurs. It intercepts
            the signal and emits its own signal that contains the image
            message associated with the tab that is now visible.

            Input:
            ------
            currentChanged signal.

            Output:
            -------
            message    := A string containing the contents of the
                          image_message attribute of the tab that is
                          currently being displayed.
        """
        if i==0:  # Original Image
            self.tabMessage.emit(self.file_image_message)
        elif i==1:
            self.tabMessage.emit(self.scanned_image_message)
        else:
            self.tabMessage.emit(self.solved_image_message)

class QMazeDetails(QGroupBox):

    """ Maze Details Groupbox Class

        This class defines a group box that allows the user to input
        details of the maze that the program needs to successfully
        navigate through it. This includes the size (width and height)
        of the maze in cells as well as the start and finish cells
        (specified as the x and y coordinates of the cells, which can be
        displayed by clicking the "Show Coordinates" button).

        Width and Height will initially be set to 1 and all other values
        are set to 0. Setting the width and height will also limit the
        start_cell and finish_cell x and y maximum values to one less
        than the width (for the x value) and one less than the height
        (for the y values) since the upper right cell in the maze is
        indexed as (0,0).

        By default, this groupbox is initialized as "disabled" since the
        user should not be allowed to enter any data about a given maze
        until the initial file is read into and processed by the
        program.

        Input:
        ------
        None.

        Output:
        -------
        PyQt5 QGroupBox containing spinboxes that accept the width,
        height and start and finish cell values.

    """
    sizeChanged = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()

        self.setTitle("Maze Details")
        self.setEnabled(False)
        self.setGeometry(QtCore.QRect(0, 20, 135, 230))
        self.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|
                          QtCore.Qt.AlignVCenter)

        # Maze width and height displays
        self.lblSize = QtWidgets.QLabel(self)
        self.lblSize.setGeometry(QtCore.QRect(10, 20, 40, 20))
        self.lblSize.setText("Size")
        self.sbxWidth = QtWidgets.QSpinBox(self)
        self.sbxWidth.setGeometry(QtCore.QRect(10, 40, 40, 20))
        self.sbxWidth.setAlignment(QtCore.Qt.AlignCenter)
        self.sbxWidth.setMinimum(1)
        self.sbxWidth.setProperty("value", 1)
        self.sbxWidth.valueChanged.connect(self.__updateMaxWidth)
        self.sbxWidth.editingFinished.connect(self.__sendSignal)
        self.lblWidth = QtWidgets.QLabel(self)
        self.lblWidth.setGeometry(QtCore.QRect(10, 60, 40, 20))
        self.lblWidth.setAlignment(QtCore.Qt.AlignCenter)
        self.lblWidth.setText("Width")
        self.sbxHeight = QtWidgets.QSpinBox(self)
        self.sbxHeight.setGeometry(QtCore.QRect(70, 40, 40, 20))
        self.sbxHeight.setAlignment(QtCore.Qt.AlignCenter)
        self.sbxHeight.setMinimum(1)
        self.sbxHeight.setProperty("value", 1)
        self.sbxHeight.valueChanged.connect(self.__updateMaxHeight)
        self.sbxHeight.editingFinished.connect(self.__sendSignal)
        self.lblHeight = QtWidgets.QLabel(self)
        self.lblHeight.setGeometry(QtCore.QRect(70, 60, 40, 20))
        self.lblHeight.setAlignment(QtCore.Qt.AlignCenter)
        self.lblHeight.setText("Height")

        # Maze Start Cell (x and y)
        self.lblStart = QtWidgets.QLabel(self)
        self.lblStart.setGeometry(QtCore.QRect(10, 90, 50, 20))
        self.lblStart.setText("Start Cell")
        self.sbxStartRow = QtWidgets.QSpinBox(self)
        self.sbxStartRow.setGeometry(QtCore.QRect(10, 110, 40, 20))
        self.sbxStartRow.setAlignment(QtCore.Qt.AlignCenter)
        self.sbxStartRow.setMinimum(0)
        self.sbxStartRow.setMaximum(0)
        self.sbxStartRow.setProperty("value", 0)
        self.lblStartRow = QtWidgets.QLabel(self)
        self.lblStartRow.setGeometry(QtCore.QRect(10, 130, 41, 20))
        self.lblStartRow.setAlignment(QtCore.Qt.AlignCenter)
        self.lblStartRow.setText("Row")
        self.sbxStartCol = QtWidgets.QSpinBox(self)
        self.sbxStartCol.setGeometry(QtCore.QRect(70, 110, 40, 20))
        self.sbxStartCol.setAlignment(QtCore.Qt.AlignCenter)
        self.sbxStartCol.setMinimum(0)
        self.sbxStartCol.setMaximum(0)
        self.sbxStartCol.setProperty("value", 0)
        self.lblStartCol = QtWidgets.QLabel(self)
        self.lblStartCol.setGeometry(QtCore.QRect(70, 130, 40, 20))
        self.lblStartCol.setAlignment(QtCore.Qt.AlignCenter)
        self.lblStartCol.setText("Col")

        # Maze Finish Cell (x and y)
        self.lblFinish = QtWidgets.QLabel(self)
        self.lblFinish.setGeometry(QtCore.QRect(10, 160, 50, 20))
        self.lblFinish.setText("Finish Cell")
        self.sbxFinishRow = QtWidgets.QSpinBox(self)
        self.sbxFinishRow.setGeometry(QtCore.QRect(10, 180, 40, 20))
        self.sbxFinishRow.setAlignment(QtCore.Qt.AlignCenter)
        self.sbxFinishRow.setMinimum(0)
        self.sbxFinishRow.setMaximum(0)
        self.sbxFinishRow.setProperty("value", 0)
        self.lblFinishRow = QtWidgets.QLabel(self)
        self.lblFinishRow.setGeometry(QtCore.QRect(10, 200, 40, 20))
        self.lblFinishRow.setAlignment(QtCore.Qt.AlignCenter)
        self.lblFinishRow.setText("Row")
        self.sbxFinishCol = QtWidgets.QSpinBox(self)
        self.sbxFinishCol.setGeometry(QtCore.QRect(70, 180, 40, 20))
        self.sbxFinishCol.setAlignment(QtCore.Qt.AlignCenter)
        self.sbxFinishCol.setMinimum(0)
        self.sbxFinishCol.setMaximum(0)
        self.sbxFinishCol.setProperty("value", 0)
        self.lblFinishCol = QtWidgets.QLabel(self)
        self.lblFinishCol.setGeometry(QtCore.QRect(70, 200, 40, 20))
        self.lblFinishCol.setAlignment(QtCore.Qt.AlignCenter)
        self.lblFinishCol.setText("Col")

    def maze_width(self):
        """ Get Maze Width Value Method

            Returns the value the user set as the maze width.

            Input:
            ------
            None.

            Output:
            -------
            Value of the maze width.
        """

        return self.sbxWidth.value()

    def maze_height(self):
        """ Get Maze Height Value Method

            Returns the value the user set as the maze height.

            Input:
            ------
            None.

            Output:
            -------
            Value of the maze height.
        """

        return self.sbxHeight.value()

    def start_cell(self):
        """ Get Maze Start Cell Value Method

            Returns the x and y values the user set as the maze
            start_cell. This is returned as a csv string and not a
            tuple as the value will be sent to the command line
            processor to be placed into a CLProcessor instance. This
            allows the same call to be used whether it comes from the
            GUI or from the command line.

            Input:
            ------
            None.

            Output:
            -------
            String containing the value of the maze start cell as row,
            col.
        """

        return str(self.sbxStartRow.value()) + "," + \
               str(self.sbxStartCol.value())

    def finish_cell(self):
        """ Get Maze Finish Cell Value Method

            Returns the x and y values the user set as the
            maze finish_cell. This is returned as a csv string and
            not a tuple as the value will be sent to the command line
            processor to be placed into a CLProcessor instance. This
            allows the same call to be used whether it comes from the
            GUI or from the command line.

            Input:
            ------
            None.

            Output:
            -------
            String containg the value of the maze finish cell as row,
            col.
        """

        return str(self.sbxFinishRow.value()) + "," + \
               str(self.sbxFinishCol.value())

    def set_startx_focus(self):
        self.sbxStartRow.setFocus()

    def __updateMaxWidth(self):
        """ Update Maximum Width Method (private)
            Called when the user changes the value of the maze width to
            ensure that the x-value (col) of start_cell and finish_cell
            cannot be set to a value outside the bounds of the maze.
        """


        maxWidth = self.sbxWidth.value()-1
        self.sbxStartRow.setMaximum(maxWidth)
        self.sbxFinishRow.setMaximum(maxWidth)

    def __updateMaxHeight(self):
        """ Update Maximim Height Method (private)
            Called when the user changes the value of the maze height to
            ensure that the y-value (row) of start_cell and finish_cell
            cannot be set to a value outside the bounds of the maze.
        """

        maxHeight = self.sbxHeight.value()-1
        self.sbxStartCol.setMaximum(maxHeight)
        self.sbxFinishCol.setMaximum(maxHeight)


    def __sendSignal(self):
        """ Send Signal method
        Called when the user is done updating the maze height or width
        spinbox values. It emits the sizeChanged signal, which will be
        picked up by the main GUI and used to re-process the maze.
        """

        self.sizeChanged.emit(self.sbxWidth.value(), self.sbxHeight.value())

class MainWindow(QtWidgets.QMainWindow):

    """ Main Window Class

        This class defines a the main display window for the Maze Reader
        program. It brings together the various pieces of the display as
        defined previously (i.e. the tabbed display for the maze images,
        the groupbox that collects details on the maze and the set of
        buttons (defined below) the user presses to tell the program
        what to do).

        For further details on these items, refer to help on:
            - QCommandButton class
            - QTabbedImage class
            - QMazeDetails class

        The window consists of three nested layouts, a QHBoxLayout that
        houses the tabbed image display with a QVBoxLayout to its right.
        This QVBoxLayout in turn contains the detail groupbox at the
        top, and a second QVBoxLayout containing the command buttons at
        the bottom.

        Input:
        ------
        None.

        Output:
        -------
        PyQt5 QMainWindow that acts as the main interface to the Maze
        Walker program.
    """

    def __init__(self):
        super().__init__()

        # Initialize the attribute to hold the maze array
        Maze = None

        # Set the title to the program name
        self.setWindowTitle("Maze Reader")

        # Add the menu bar

        menu = self.menuBar()
        self.mnuFileOpen = QAction("&Open", self)
        self.mnuFileOpen.setStatusTip("Open file containing an image of the " +
                                      "maze to be navigated.")
        self.mnuFileOpen.triggered.connect(self.__choose_file)

        self.mnuFileSaveScanned = QAction("Save S&canned Image", self)
        self.mnuFileSaveScanned.setStatusTip("Save the currently displayed " +
                                             "Scanned Image.")
        self.mnuFileSaveScanned.triggered.connect(self.__save_scanned)
        self.mnuFileSaveScanned.setEnabled(False)

        self.mnuFileSaveSolved = QAction("Save Sol&ved Image", self)
        self.mnuFileSaveSolved.setStatusTip("Save the currently displayed " +
                                            "Solved Image.")
        self.mnuFileSaveSolved.triggered.connect(self.__save_solved)
        self.mnuFileSaveSolved.setEnabled(False)

        self.mnuFileExit = QAction("E&xit", self)
        self.mnuFileExit.setStatusTip("Exit program.")
        self.mnuFileExit.triggered.connect(self.__exit_GUI)

        self.mnuFile = menu.addMenu("&File")

        self.mnuFile.addAction(self.mnuFileOpen)
        self.mnuFile.addSeparator()
        self.mnuFile.addAction(self.mnuFileSaveScanned)
        self.mnuFile.addAction(self.mnuFileSaveSolved)
        self.mnuFile.addSeparator()
        self.mnuFile.addAction(self.mnuFileExit)

        self.mnuProcess = menu.addMenu("&Process")
        self.mnuProcessSolve = QAction("&Solve Maze",self)
        self.mnuProcessSolve.triggered.connect(self.__solve_maze)
        self.mnuProcessSolve.setEnabled(False)

        self.mnuProcessCmdFile = QAction("Process &Command File", self)
        self.mnuProcessCmdFile.setStatusTip("Batch Process Mazes.")
        self.mnuProcessCmdFile.triggered.connect(self.__process_command_file)

        self.mnuProcess.addAction(self.mnuProcessSolve)
        self.mnuProcess.addAction(self.mnuProcessCmdFile)

        # Define the overall widget that will contain the window's
        #contents
        contents = QtWidgets.QWidget()

        # Define the three layouts that will hold the widgets (as
        # described above)
        mainLayout = QtWidgets.QHBoxLayout()
        controls = QVBoxLayout()
        button_panel = QtWidgets.QVBoxLayout()

        dataLayout = QtWidgets.QVBoxLayout()

        # Set the initial instructions in the window's status bar.
        self.__set_text("Use the Choose File button to select a maze image " +
                      "to be processed.")

        # Create the tabbed image panel and add it to the main (horizontal)
        # layout first
        self.image_panel = QTabbedImages()
        self.image_panel.tabMessage.connect(self.__set_text)
        dataLayout.addWidget(self.image_panel)

        mainLayout.addLayout(dataLayout)

        # Define a label as a "spacer" to add to the outer vertical layout.
        # This ensures that the detail groupbox appears at the top of the
        # layout and the command buttons appear at the bottom.
        spacer = QtWidgets.QLabel(self)
        spacer.setGeometry(QtCore.QRect(0, 0, 5, 5))

        # Create the detail groupbox and add it to the outer vertical layout
        self.detail_panel = QMazeDetails()
        # Define the slot to detect when the width or height spinboxes'
        # values change so new coordinates can be drawn on the file
        # image and scanned image.
        self.detail_panel.sizeChanged.connect(self.__reprocess_maze)
        controls.addWidget(self.detail_panel)
        controls.addWidget(spacer)
        contents.setLayout(mainLayout)

        # Define the command buttons and add them to their vertical
        # layout.
        # NOTE: The test button is placed here for testing purposes only
        # otherwise, the user should never see it so comment it out for
        # distribution.

        # self.btnTest = QCommandButton("&Test")
        # self.btnTest.pressed.connect(self.__test)
        # button_panel.addWidget(self.btnTest)

        #Define the Show Coordinates  button, which display the row and
        # column number of each cell on the file image and scanned
        # image.
        self.btnShowCoords = QCommandButton("Show &Coordinates", checkable=True)
        self.btnShowCoords.pressed.connect(self.__show_coordinates)
        # Make this button a "toggle" so the user can decide whether or
        # not they want to see the cell coordinates.
        button_panel.addWidget(self.btnShowCoords)

        # Define the Next Maze button, which will be used to iterate
        # through mazes being processed from a command line file.
        self.btnNext = QCommandButton("&Next Maze", visible=False)
        self.btnNext.pressed.connect(self.__next_maze)
        # This button is set to be invisible unless the user
        # specifically chooses to process a command file from the menu.
        button_panel.addWidget(self.btnNext)

        # Define a variable to pause processing of the batch processor
        #until the Next Maze button is pressed.
        self.pause_processing = True

        # The Choose File button will be one of the first things the
        # user clicks to open an image file for processing (this can
        # also be done from the File->Open menu).
        self.btnChooseFile = QCommandButton("&Choose File")
        self.btnChooseFile.pressed.connect(self.__choose_file)
        button_panel.addWidget(self.btnChooseFile)

        # This button is set to "disabled" so the user cannot click it
        # until the initial image file is read in and processed.
        self.btnSolve = QCommandButton("&Solve", enabled=False)
        self.btnSolve.pressed.connect(self.__solve_maze)
        button_panel.addWidget(self.btnSolve)

        # This button is set to "disabled" so the user cannot click it
        # until the maze is processed and there is something to save.
        self.btnSaveScanned = QCommandButton("Sa&ve Scanned", enabled=False)
        self.btnSaveScanned.pressed.connect(self.__save_scanned)
        button_panel.addWidget(self.btnSaveScanned)

        # This button is set to "disabled" so the user cannot click it
        # until the maze is processed and there is something to save.
        self.btnSaveSolved = QCommandButton("Save S&olution", enabled=False)
        self.btnSaveSolved.pressed.connect(self.__save_solved)
        button_panel.addWidget(self.btnSaveSolved)

        # Define an Exit button to end the program (this can also be
        # called through the File->Exit menu)
        self.btnExit = QCommandButton("E&xit")
        self.btnExit.pressed.connect(self.__exit_GUI)
        button_panel.addWidget(self.btnExit)

        # Add the created button panel to the controls layout
        controls.addLayout(button_panel)

        # Add thecontrols layout to the main layout
        mainLayout.addLayout(controls)

        # Set the overall contents to the main layout
        contents.setLayout(mainLayout)

        # Set all of this as the central widget of the window
        self.setCentralWidget(contents)

    def __is_loading(self, loading):
        """ Set Loading Flag Method (private)

            Used to set the flag telling the program that a new image
            file is being loaded. There are certain items, such as
            drawing the image with the coordinates on it that require
            the read-in image to be processed before they are called.
            In the case of the image with coordinates, for instance, the
            program needs to know the dimensions of the maze in order to
            correctly populate the cell indices. Since the
            draw_dimensions method is called when the width and height
            detail spinboxes are changes, and the program changes these
            while it reads in the image file, you want to wait until the
            image read and processing is done before calling
            draw_dimensions().

            This method abstracts the deeper Booleans. That is, a call
            to __is_loading() on the main window sets the Booleans
            within the display structure (on the image_panel for
            instance, making the call mainwindow.__is_loading() instead
            of mainwindow.display_panel.file_loading())

            Input:
            ------
            loading := Boolean indicating if a new image is being loaded
                       or not.

            Output:
            -------
            file_loading on the image_panel is set to the value of
            loading.
        """
        self.image_panel.file_loading = loading

    def __set_text(self, text):
        """ Set Main Window Text Method (private)

            This method is provided for cleaner code and simply takes
            the provided string and displays it in the status bar at the
            bottom of the main window.

            Input:
            ------
            text   := String to be displayed on the main window.

            Output:
            -------
            Main window status bar is updated with text.

        """
        self.statusBar().showMessage(text)

    def __test(self):
        """ Test Button Method (private)

            This method is provided for debugging and will be called
            when the Test button is pressed so is defined as a
            private method. Similarly, the test button code above is
            commented out so the button does not display on code
            intended for distribution.

            Input:
            ------
            None

            Output:
            -------
            Determined by the debugging code included.

        """
        pass

    def __reprocess_maze(self):
        """ Redraw Coordinates Method (private)

            Called when either the maze width or the maze height
            spinbox value changes. This will force a redraw of the cell
            coordinates on the file image and scanned image. This is
            important because this will ensure the coordinate values are
            being drawn onto clean copies of the images, otherwise we
            could end up with multiple copies of coordinates in
            different places on the image depending on what changes to
            width and height were made.

            Input:
            ------
            None

            Output:
            -------
            Updated file image and scanned image with new cell
            coordinates.

        """

        self.Maze = processMaze(self.image_panel.maze_image,
                                self.detail_panel.maze_width(),
                                self.detail_panel.maze_height())

        self.reset_scanned_images()

    def __show_coordinates(self):
        """ Show Coordinates Method (private)

            Called when the user clicks the Show Coordinates button.
            Depending on whether the button is checked or not, the
            images displayed will contain the coordinates or not.

            Input:
            ------
            Show Coordinates button click.

            Output:
            -------
            File image and scanned image displayed in the appropriate
            tabs with or without coordinates displayed (depending on
            the checked state of the button).

        """

        # Check the status of the Show Coordinates button and display
        # the appropriate images. Note that, if the button is NOT
        # checked then we are checking it so show the coordinate image.
        # This is somewhat opposite to the GUI experience where the
        # coordinate image is visible when the button IS checked.
        if not self.btnShowCoords.isChecked():
            self.image_panel.show_scanned_image(self.image_panel.scanned_pixmap_coords,
                                                self.image_panel.scanned_image_name)
            # Show the Scanned Image tab
            self.image_panel.setCurrentIndex(1)
        else:
            self.image_panel.show_scanned_image(self.image_panel.scanned_pixmap,
                                                self.image_panel.scanned_image_name)

    def __next_maze(self):
        """ Next Maze Method (private)

            This is used by the Next Maze button when processing files
            through the command line processor. When multiple files are
            being processed, the program will pause between each file
            so that the user can see the output, save images, etc. This
            is controlled using a Boolean called pause_processing, which
            is set to True when a file is processed. The program loops
            until pause_processing is set to false before processing the
            next maze.  This method sets the pause_processing flag to
            False.

        """

        self.pause_processing = False

    def __choose_file(self):
        """ Choose Image File Method

            Invoked when the Choose File command button is pressed.
            Opens a file dialog so the user can select the initial Image
            File. Once the file is loaded, the detail panel and the
            Solve command button are set to enabled.

            Input:
            ------
            Choose File button press.

            Output:
            -------
            File name for the Image File is set as the image file name
            and the imported image is displayed in the Image File tab
            and the initial calculations of the maze width and height
            are displayed in the spinboxes (see note below).

            This calls the set_file_image method of the tabbed display
            so will also invoke the creation of the file image with
            coordinates.

            NOTE: When the file is first read in, a limited number of
            row and columns in the file are scanned to help the program
            determine the width and height of a single cell. This is
            done to save time while loading the file and has a high
            hit rate for success but sometimes miscalculates the size.
            This was done to provide the convenience of having the
            width and height of the maze loaded with the file while not
            scanning the entire file twice (since it is fully scanned to
            populate the Maze_Cell structure).
        """

        # Set the __is_loading flag to true to prevent the
        # draw_coordinates method from executing when the program first
        # populates the width and height spinboxes.
        self.__is_loading(True)

        # Populate a File Open dialog with the image file types that
        # cv2 and PyQt5 are both capable of handling and get the file
        # name for the image file.
        get_file = QFileDialog.getOpenFileName(self, "Choose Maze Image to Process",
                                               "C:\"","Image files (*.bmp *.jpg "
                                               "*.jpeg *png *.pbm *.pgm *.ppm )"
                                               ";;All Files(*.*)")
        file_name = get_file[0]
        if file_name != '':
            # If the user has provided a file name, set the cursor to
            # show the program is processing the maze and populate the
            # initial image and estimated width and height values.
            QApplication.setOverrideCursor(Qt.WaitCursor)

            # Open the image as a grayscale image to make it easier to see the
            # walls.
            img = cv.imread(file_name, 0)

            # Clear "noise" by setting everything to either black or white.
            for x in np.nditer(img, op_flags=['readwrite']):
                if abs(x) > 125:
                    x[...] = 255
                else:
                    x[...] = 0

            self.image_panel.maze_image = img

            maze_width, maze_height = self.__calc_dimensions()#(file_name)
            self.detail_panel.sbxWidth.setValue(maze_width)
            self.detail_panel.sbxHeight.setValue(maze_height)
            self.detail_panel.sbxStartRow.setValue(0)
            self.detail_panel.sbxStartCol.setValue(0)
            self.detail_panel.sbxFinishRow.setValue(0)
            self.detail_panel.sbxFinishCol.setValue(0)

            # Turn off loading flag so the coordinate map gets produced
            self.__is_loading(False)

            self.Maze = processMaze(img, maze_width, maze_height)
            self.image_panel.set_file_image(file_name,
                                            maze_width,
                                            maze_height,
                                            self.btnShowCoords.isChecked())

            self.reset_scanned_images()

            # Set the disabled controls to enabled now that an image
            # file is loaded.
            self.detail_panel.setEnabled(True)
            self.btnSolve.setEnabled(True)
            self.mnuProcessSolve.setEnabled(True)
            self.__set_text(file_name)
            self.__is_loading(False)

            # Set the cursor back to normal once processing completes.
            QApplication.restoreOverrideCursor()
            self.image_panel.setCurrentIndex(0)

    def __solve_maze(self, cmdentry=None):
        """ Solve Maze Method (private)

            Invoked when the Solve Maze command button is pressed or
            via the command file processing routines. When a command
            file is being processed, the CLProcessor instance (cmdentry)
            will have been built already so it is passed. If called from
            the GUI, None will be passed, causing this method to gather
            the maze parameters set in the maze details groupbox and
            build the cmdentry to be passed to process_maze to invoke
            the maze scan and navigation.

            It then displays the Scan Image and, if a solution was found,
            the Solved Image in the appropriate tabs.

            This will also enable the save buttons.

            Input:
            ------
            cmdentry      := An instance of the CLProcessor class. This
                             will be passed if batch processing is being
                             performed. If called from the GUI, None will
                             be passed.

            Output:
            -------
            solved        := Boolean indicating whether or not a path
                             was found through the maze.
            Scanned_Image := Image generated from the Maze_Cells
                             populated when the File Image was scanned.
            Solved_Image  := Image of the maze with the solution path
                             displayed (if one was found). If no
                             solution was found, this will display a
                             second copy of the Scanned Image.
        """

        # Load the values from the GUI into local variables
        maze_name = '"' + self.image_panel.file_image_name + '"'
        maze_width = self.detail_panel.maze_width()
        maze_height = self.detail_panel.maze_height()
        start_cell = self.detail_panel.start_cell()
        finish_cell = self.detail_panel.finish_cell()
        # Set the save buttons to enabled
        self.btnSaveScanned.setEnabled(True)
        self.btnSaveSolved.setEnabled(True)
        self.mnuFileSaveScanned.setEnabled(True)
        self.mnuFileSaveSolved.setEnabled(True)

        if cmdentry is None:
        # This will be the case if __solve_maze is called from
        # the GUI so we build the command line from the GUI
        # entries and create a cmdentry for process_maze. If
        # solve-Maze is called by the batch processor, it will
        # pass the filled in cmdentry to the method.
            cmdline = maze_name + \
                  " -w " + str(maze_width) + \
                  " -h " + str(maze_height) + \
                  " -s " + start_cell +  \
                  " -f " + finish_cell

            cmdentry = clp(cmdline)

        # This next block of code checks if the start and finish cells
        # have been set by ensuring they are not the same cell (as they
        # would be when the program first loads an image for example).
        # If they are the same, a message box will be displayed saying
        # this and asking the user if they still want to proceed with
        # solving the maze. Since the response to proceed is "Yes",
        # set the return code to this by default so the program will
        # proceed even if the message box is not displayed (i.e. the
        # user specified a different start and finish cell).
        retcd = QMessageBox.Yes

        if start_cell == finish_cell:
            buttons = QMessageBox.Yes | QMessageBox.No
            retcd = self.msgBox("Possible Detail Issue",
                                "Start Cell = Finish Cell",
                                "Start Cell and Finish Cell are the same. " + \
                                "Do you still want to solve this maze?",
                                QMessageBox.Question,
                                buttons)

        # Whether or not the message box was displayed, check the
        # "return code" to see if we should proceed with looking for a
        # solution.
        if retcd == QMessageBox.Yes:
            QApplication.setOverrideCursor(Qt.WaitCursor)

            Scanned_Image, Coord_Image, Solved_Image, solved = solveMaze(self.Maze, cmdentry)

            # Set the returned images to the scanned and solved image
            # attributes.
            self.image_panel.set_scanned_image(self.toQImage(Scanned_Image),
                                               self.toQImage(Coord_Image),
                                               self.btnShowCoords.isChecked())

            # Check the status of the Show Coordinates button to
            # determine which images should be shown.
            if self.btnShowCoords.isChecked():
                self.image_panel.show_scanned_image(self.image_panel.scanned_pixmap_coords,
                                                    self.image_panel.scanned_image_name)
            if solved:
                self.image_panel.set_solved_image(self.toQImage(Solved_Image))
            else:
                self.image_panel.set_solved_image(self.toQImage(Solved_Image),
                                                  maze_name + " has no solution. "
                                                  "Removing any of the indicated "
                                                  "walls will make it solvable.")
            QApplication.restoreOverrideCursor()
            self.image_panel.setCurrentIndex(2)

    def __save_scanned(self):
        """ Save Scanned Image Method (private)

            Invoked when the Save Scanned command button is pressed.
            Opens a QFileDialog to get the name the user wishes to save
            the Scanned Image as. The filename will be initially set to
            the name the QTabbedImages instance generated when the File
            Image file was opened.

            Input:
            ------
            filename := Name of the file the Scanned Image will be saved
                        to.

            Output:
            -------
            File containing the Scanned Image.
        """
        # Open a Save File dialog populated with the types of image
        # files PyQt5 is capable of handling.
        get_file = QFileDialog.getSaveFileName(self, "Save Scanned Maze",
                                                     self.image_panel.scanned_image_name,
                                                     "Image files (*.bmp *.jpg "
                                                     "*.jpeg *png *.pbm *.pgm "
                                                     "*.ppm );;All FIles(*.*)")
        file_name = get_file[0]
        # Make sure the user has chosen a file name and save the file
        # using this name. This will pass the stored name through as
        # the default and will only return with a blank if the user
        # clicks cancel. Otherwise, it will return the same name or
        # the new filename specified by the user. In this case, store
        # the returned name (in case the user changed it) and save the
        # file using this name.
        if file_name != '':
            self.image_panel.scanned_image_name = \
            self.image_panel.scanned_image_message = file_name
            self.image_panel.tabMessage.emit(file_name)
            # Save the image based on the checked state of the
            # __show_coordinates button.
            self.image_panel.save_scanned_image(file_name, self.btnShowCoords.isChecked())

    def __save_solved(self):
        """ Save Solved Image Method (private)

            Invoked when the Save Solved command button is pressed.
            Opens a QFileDialog to get the name the user wishes to save
            the Solved Image as. The filename will be initially set to
            the name the QTabbedImages instance generated when the File
            Image file was opened.

            Input:
            ------
            filename := Name of the file the Solved Image will be saved
            to.

            Output:
            -------
            File containing the Solved Image.
        """

        get_file = QFileDialog.getSaveFileName(self, "Save Solved Maze",
                                                     self.image_panel.solved_image_name,
                                                     "Image files (*.bmp *.jpg "
                                                     "*.jpeg *png *.pbm *.pgm *"
                                                     ".ppm );;All Files(*.*)")
        file_name = get_file[0]
        # Make sure the user has chosen a file name and save the file
        # using this name. This will pass the stored name through as
        # the default and will only return with a blank if the user
        # clicks cancel. Otherwise, it will return the same name or
        # the new filename specified by the user. In this case, store
        # the returned name (in case the user changed it) and save the
        # file using this name.
        if file_name != '':
            self.image_panel.solved_image_name = \
            self.image_panel.solved_image_message = file_name
            self.image_panel.tabMessage.emit(file_name)
            self.image_panel.save_solved_image(file_name)


    def __process_command_file(self):
        """ Process Command File Method (private)

            Called when the user selects Process Command File from the
            Process menu. This method prompts the user for a filename,
            opens the file and calls CLProcessor to generate a set of
            instructions for the program to porcess.

            It then steps through each of the sets of instructions,
            processing each file in sequence and displaying the results.

        """
        get_file = QFileDialog.getOpenFileName(self, "Choose Command Line File to Process",
                                               "C:\"","Text files (*.txt);;All Files(*.*)")
        file_name = get_file[0]
        if file_name != '':
            self.btnNext.setVisible(True)
            try:
                instructions = self.__parse_command_file(file_name)
            except Exception as e:
                QApplication.restoreOverrideCursor()
                MainWindow.msgbox("Command File Parser Error",
                                  "Issue Encountered",
                                  str(e),
                                  QMessageBox.Critical)
            # Once the input file has been processed, run through
            # each list entry.
            for cmd_entry in instructions:
                QApplication.setOverrideCursor(Qt.WaitCursor)
                self.image_panel.set_file_image(cmd_entry.filename,
                                                cmd_entry.width,
                                                cmd_entry.height,
                                                self.btnShowCoords.isChecked())

                # Open the image as a grayscale image to make it easier to see the
                # walls.
                img = cv.imread(cmd_entry.filename, 0)

                # Clear "noise" by setting everything to either black or white.
                for x in np.nditer(img, op_flags=['readwrite']):
                    if abs(x) > 125:
                        x[...] = 255
                    else:
                        x[...] = 0

                self.image_panel.maze_image = img
                self.Maze = processMaze(img, cmd_entry.width, cmd_entry.height)

                # Set the loading flag so that the coordinate image will
                # not be drawn multiple times while the GUI is being
                # updated (width and height being set etc.)
                self.__is_loading(True)
                self.image_panel.file_image_name = cmd_entry.filename
                self.detail_panel.sbxWidth.setValue(cmd_entry.width)
                self.detail_panel.sbxHeight.setValue(cmd_entry.height)
                self.detail_panel.sbxStartRow.setValue(cmd_entry.start_cell[0])
                self.detail_panel.sbxStartCol.setValue(cmd_entry.start_cell[1])
                self.detail_panel.sbxFinishRow.setValue(cmd_entry.finish_cell[0])
                self.detail_panel.sbxFinishCol.setValue(cmd_entry.finish_cell[1])
                if cmd_entry.save_scanned:
                    self.image_panel.scanned_image_name = cmd_entry.scanned_name
                if cmd_entry.save_solution:
                    self.image_panel.solution_name = cmd_entry.solution_name

                self.detail_panel.setEnabled(True)
                self.btnSolve.setEnabled(True)
                self.mnuProcessSolve.setEnabled(True)
                # Turn off loading flag so coordinate updates will resume.
                self.__is_loading(False)
                self.__solve_maze(cmd_entry)
                self.__reprocess_maze()
                self.btnSaveScanned.setEnabled(True)
                self.btnSaveSolved.setEnabled(True)
                self.mnuFileSaveScanned.setEnabled(True)
                self.mnuFileSaveSolved.setEnabled(True)
                self.image_panel.setCurrentIndex(0)
                QApplication.restoreOverrideCursor()

                # If the user requested a save of either the scanned or
                # solved images (or both), do that here.
                if cmd_entry.save_scanned:
                    self.image_panel.save_scanned_image(cmd_entry.scanned_name)

                if cmd_entry.save_solution:
                    self.image_panel.save_solved_image(cmd_entry.solution_name)

                # If we are processing the last entry in the
                # instructions list, hide the Next Maze button.
                if cmd_entry == instructions[-1]:
                    self.btnNext.setVisible(False)
                else:
                # Otherwise, when the solved maze is displayed, wait for
                # the user to press the Next Maze button before
                # processing the next entry in the instructions list.
                # This gives the user the opportunity to look at the
                # solution, save the maze, etc. before moving on to the
                # next one.
                    while self.pause_processing:
                        QApplication.processEvents()
                        time.sleep(0.05)
                    self.pause_processing = True

    def __parse_command_file(self, filename):
        """ Command File Parser Method (private)

            This method processes the provided text file and
            interprets each command line contained in the file, creating
            a CLProcessor instance for each line read. This allows for a
            "batch" processor for multiple mazes.

            Input:
            ------
            filename   := the name of the file containing the command
                          line entries (see below for details)

            Output:
            -------
            A list of CLProcessor instances containing the details of
            the commands read in from each line in the provided file.


            Command Line Format:
            --------------------
            The format of the command lines is:

            filename      := the first parameter is taken as the input
                             file name (this is the only positional
                             parameter and MUST be the first thing on
                             the line).
            -f (row,col)  := tuple representing the finish cell in the
                             maze (0,0) is the upper-left corner.
            -h int        := integer representing the height of the maze
                             in cells.
            -s (row,col)  := tuple representing the start cell in the
                             maze (0,0) is the upper-left corner.
            -v [filename] := save solution into filename. If no filename
                             is provided, the name will be created by
                             taking the input filename and appending
                             " Solved" to the name.
            -w int        := integer representing the width of the maze
                             in cells
            -x [filename] := save scanned maze (before solution) into
                             filename. If no filename is provided, the
                             name will be created by taking the input
                             filename and appending " Scanned" to the
                             name.

            Note that filename, -h, -w, -s, -f are ALL MANDATORY

            Raises:
            -------
            IOError       := Raised if the passed filename cannot be
                                 accessed.
        """

        # Create an empty list to hold the values read
        instructions = []

        # Try open the file name provided and raise errors if required.
        try:
            cmd_file = open(filename, "r")
            cmdlines = cmd_file.readlines()
            # If the file can be read, feed each line, one at a time
            # through the command line processor class and append the
            # returned values to the list.
            for cmdline in cmdlines:
                if cmdline != "" and cmdline !="\n" and cmdline[0] != "#":
                    # Ignore blank lines and comment lines
                    instructions.append(clp(cmdline))
        except IOError:
            raise IOError("Maze Walker <I/O error>: Unable to access file "
                          + filename)
        except Exception as e:
            msgBox("CLProcessor Error",
                        "Issue Encountered",
                        str(e),
                        QMessageBox.Critical)
        finally:
            cmd_file.close()

        return instructions

    def __calc_dimensions(self): # , filename):
        """ Calculate the Maze Dimensions Method (private)

            Reads through the numpy array created from the image the
            program read in to try and determine the width and height of
            the maze in cells. It divides the array into "slices" of a
            specified size (set by num_slices), and scans these from top
            to bottom and left to right looking for walls. Using this
            data, it keeps track of the narrowest "corridor" it finds
            and assumes this to be the width/height of a single cell. It
            then uses this value to divide the image width and height so
            as to determine the dimensions in cells.

            Input:
            ------
            filename   := name of the image file containing the maze.

            Output:
            -------
            width      := width of the maze in cells.
            height     := height of the maze in cells.
        """

        # Define a lambda function to return the average of the values
        # in a list (rounded up).
        listAvg = lambda lst: int(sum(lst)/len(lst) + 0.5)

        # Set the size of each slice to 17 pixels so that approximately
        # 6 slices per 100 pixels will be scanned.
        slice_size = 17

        img = self.image_panel.maze_image

        # Determine how many rows and columns of pixels there are to be
        # processed.
        num_rows = img.shape[0]
        num_cols = img.shape[1]

         # Determine how many row and column slices there will be
        row_slices = num_rows//slice_size - 1
        col_slices = num_cols//slice_size - 1

        # Initialize the scanning indices.
        scan_indices = []

        # Set the initial cell width and height to an arbitrarily large
        # number that is bigger than a cell is likely to be. And set the
        # wall width and height to zero.
        cell_width = 99
        cell_height = 99
        horiz_wall_width = 0
        vert_wall_width = 0
        # Set up empty lists to contain the widths of the walls found.
        vert_walls = []
        horiz_walls = []

        for row_slice in range(1,row_slices):
            # Scan across each row slice looking for vertical walls.
            row = row_slice * slice_size
            # Ensure the row is not beyond the end of the maze
            row = min(row, img.shape[0]-1)
            # Set the wall indices to arbitrarily large numbers to
            # indicate they have not been set by the scanner yet.
            w1 = 99
            w2 = 99
            for scan in range(num_cols-1):
                # If a black pixel is encountered, keep track of how
                # many in a row are seen along with their cumulative
                # indices. This is then used to calculate the average,
                # which will give (approximately) the pixel in the
                # "middle" of the wall's width.
                if img.item(row, scan) == 0:
                    scan_indices.append(scan)
                else:
                    # The pixel is white so, check to see if scan_index
                    # is set to anything (i.e. the program was in the
                    # process of scanning a wall).
                    if scan_indices:
                        # If a wall was being scanned, check to see if
                        # been set yet and, if so , take the average of
                        # the pixels' indices and round up to determine
                        # which column this wall is part of and set it
                        # as wall 1.
                        if w1 == 99:
                            w1 = listAvg(scan_indices)
                        else:
                            # We already found one wall so determine the
                            # wall index as above and assign it to wall
                            # 2 then calculate the distance between
                            # them.
                            w2 = listAvg(scan_indices)
                            # Assign the smaller of the current cell
                            # width and the distance between the two
                            # walls to cell_width. This ensures the
                            # 'narrowest' width greater than 10 is
                            # recorded. We ignore values less than 10,
                            # assuming that this is more likely a
                            # spurious set of pixels as it is too narrow
                            # to represent a reasonably wide corridor.
                            if w2-w1-1 > 10:
                                cell_width = min(cell_width, w2-w1-1)
                            # Set wall 2 as the new wall 1 and continue
                            # scanning across the row.
                            w1 = w2
                        if len(scan_indices) < 10:
                            # If the index count is greater than 10,
                            # assume the program was scanning along a
                            # horizontal wall so ignore this entry.
                            # Otherwise, add this index to the
                            # vert_walls list.
                            vert_walls.append(len(scan_indices))
                        # Reset the indices for the next scan.
                        scan_indices = []

            if scan_indices:
                # This is the same code as in the else: section of the
                # above for loop and is used to ensure the last wall in
                # a row is seen if the row being scanned ends with a
                # black pixel (the "else" code above would not be
                # executed in that case).
                if w1 == 99:
                # If the first wall index is 99, assume it has not
                # been set yet do , take the average of the pixels'
                # indices and round up to determine which column
                #this wall is part of and set it as wall 1.
                    w1 = listAvg(scan_indices)
                else:
                    # We already found one wall so calculate the
                    # distance between them.
                    w2 = listAvg(scan_indices)
                    # Assign the smaller of the current cell width
                    # and the distance between the two walls to
                    # cell_width. This ensures the 'narrowest'
                    # width greater than 10 is
                    # recorded. We ignore values less than 10,
                    # assuming that this is more likely a spurious set
                    # of pixels as it is too narrow to represent a
                    # reasonably wide corridor.
                    if w2-w1-1 > 10:
                        cell_width = min(cell_width, w2-w1-1)
                if len(scan_indices) < 10 :
                    # If the index count is greater than 10,
                    # assume the program was scanning along a
                    # horizontal wall so ignore this entry.
                    # Otherwise, add this index to the vert_walls
                    # list.
                    vert_walls.append(len(scan_indices))
                # Reset the indices for the next scan.
                scan_indices = []
            vert_wall_width = listAvg(vert_walls)

        for col_slice in range(1,col_slices):
            # Scan down each column looking for horizontal walls..
            col = col_slice * slice_size
            col = min(col, img.shape[1]-1)
            # Set the wall indices to arbitrarily large numbers to
            # indicate they have not been set by the scanner yet.
            w1 = 99
            w2 = 99
            for scan in range(num_rows-1):
                # If a black pixel is encountered, keep track of how
                # many in a column are seen along with their cumulative
                # indices. This is then used to calculate the average,
                # which will give (approximately) the pixel in the
                # "middle" of the wall's width.
                if img.item(scan, col) == 0:
                    scan_indices.append(scan)
                else:
                    # The pixel is white so, check to see if scan_index
                    # is set to anything (i.e. the program was in the
                    # process of scanning a wall).
                    if scan_indices:
                        # If a wall was being scanned, check to see if
                        # been set yet and, if so, take the average of
                        # the pixels' indices and round up to determine
                        # which column this wall is part of and set it
                        # as wall 1.
                        if w1 == 99:
                            w1 = listAvg(scan_indices)
                        else:
                            # We already found one wall so calculate the
                            # distance between them.
                            w2 = listAvg(scan_indices)
                            # Assign the smaller of the current cell
                            # height and the distance between the two
                            # walls to cell_height. This ensures the
                            # 'narrowest' height greater than 10 is
                            # recorded. We ignore values less than 10,
                            # assuming that this is more likely a
                            # spurious set of pixels as it is too
                            # narrow to represent a reasonably wide
                            # corridor.
                            if w2-w1-1 > 10:
                                cell_height = min(cell_height, w2-w1-1)
                            # Set wall 2 as the new wall 1 and continue
                            # scanning across the row.
                            w1 = w2
                        if len(scan_indices) < 10:
                            # If the index count is greater than 10,
                            # assume the program was scanning along a
                            # vertical wall so ignore this entry.
                            # Otherwise, add this index to the
                            # vert_walls list.
                            horiz_walls.append(len(scan_indices))
                        # Reset the indices for the next scan.
                        scan_indices = []

            if scan_indices:
                # This is the same code as in the else: section of the
                # above for loop and is used to ensure the last wall in
                # a col is seen if the col being scanned ends with a
                # black pixel (the "else" code above would not be
                # executed in that case).
                if w1 == 99:
                # If the first wall index is 99, assume it has not
                # been set yet so, take the average of the pixels'
                # indices and round up to determine which column
                # this wall is part of and set it as wall 1.
                    w1 = listAvg(scan_indices)
                else:
                    # We already found one wall so calculate the distance
                    #  between them.
                    w2 = listAvg(scan_indices)
                    # Assign the smaller of the current cell height
                    # and the distance between the two walls to
                    # cell_height. This ensures the 'narrowest'
                    # height greater than 10 is recorded. We ignore
                    # values less than 10, assuming that this is more
                    # likely a spurious set of pixels as it is too narrow
                    # to represent a reasonably wide corridor.
                    if w2-w1-1 > 10:
                        cell_height = min(cell_height, w2-w1-1)

                if len(scan_indices) < 10:
                    # If the index count is greater than 10,
                    # assume the program was scanning along a
                    # vertical wall so ignore this entry.
                    # Otherwise, add this index to the vert_walls
                    # list.
                    horiz_walls.append(len(scan_indices))
                # Reset the indices for the next scan.
                scan_indices = []

            horiz_wall_width = listAvg(horiz_walls)
        # Return the width and height plus the average wall thicknesses.

        return img.shape[1]//(cell_width + vert_wall_width), \
               img.shape[0]//(cell_height + horiz_wall_width)

    def toQImage(self, im):
        """ Convert numpy Array to QImage Function (internal to the
            __solve_maze method)

        This function is used to convert the numpy array the Maze
        Walker module created into a PyQt5-compatible image so the GUI
        can correctly display it.

        Input:
        ------
        im     := The numpy array to be converted.

        Output:
        -------
        qim    := A copy of im formatted as a PyQt5 QImage.

        Attribution:
        ------------
        This code is a modified version of the function from:
        <https://gist.github.com/smex/5287589>

        """
        gray_color_table = [qRgb(i, i, i) for i in range(256)]
        if im is None:
            return QImage()

        qim = QImage(im.data, im.shape[1], im.shape[0],
                     im.strides[0], QImage.Format_Indexed8)
        qim.setColorTable(gray_color_table)
        return qim


    def reset_scanned_images(self):
        """ Draw Maze Function

            This method uses the data stored in the MazeCell array
            passed to it to create an image of the maze, which it
            returns to the calling process.

            Input:
            ------
            maze       := 2x2 numpy Array of MazeCell instances
                          describing the maze.

            Output:
            -------
            image      := generated image of the maze.

            Attribution:
            ------------
            Templte matching code (to fill in "missing corners") thanks
            to:
            <https://opencv-python-tutroals.readthedocs.io/en/latest/
            py_tutorials/py_imgproc/py_template_matching/py_template_matching.html>
        """

        # This function will build the image one row at a time by
        # reading each cell in the MazeCell array row-by-row. The
        # generated images for the cells in each row are stacked
        # horizontally into an image of the row. Once all the rows are
        # drawn, these images are all stacked vertically to produce the
        # full image.

        strip_list = list()
        coord_strip_list = list()

        for row in range(self.Maze.shape[0]):
            row_list = list()
            coord_row_list = list()
            for col in range(self.Maze.shape[1]):
                row_list.append(self.Maze[row][col].image())
                coord_row_list.append(self.Maze[row][col].image(row,col))

            strip_list.append(np.hstack(row_list))
            coord_strip_list.append(np.hstack(coord_row_list))

        scanned_image = np.vstack(strip_list)
        coord_image = np.vstack(coord_strip_list)

        # Because of the way the image tiles are put together
        # horizontally, there will be some corners that do not align
        # exactly.  This happens when one tile has a right wall set but
        # no top wall and the tile to the right has its top wall set.
        # The corner is cut off and the resulting area is 6x6 square of
        # pixels that looks like a checkerboard. To solve this, search
        # for the checkerboard pattern and fill the upper left 16 pixels
        # with a black rectangle.

        # Start by creating an all black 6x6 square then fill the upper
        # left and lower right 3x3 squares with white.

        template = np.zeros(shape=[6, 6], dtype=np.uint8)

        for row in range(3):
            for col in range(3):
                template[row][col] = 255
                template[row + 3][col + 3] = 255

        # Find all instances of the pattern in the generated image and
        # replace the upper 3x3 square of each found location with black
        # pixels.

        scanRes = cv.matchTemplate(scanned_image, template, cv.TM_CCOEFF_NORMED)
        coordRes = cv.matchTemplate(coord_image, template, cv.TM_CCOEFF_NORMED)
        threshold = 0.8
        loc = np.where(scanRes >= threshold)
        for pt in zip(*loc[::-1]):
            cv.rectangle(scanned_image, pt,
                         (pt[0] + 2, pt[1] + 2), (0, 0, 255), -1)
            cv.rectangle(coord_image, pt,
                         (pt[0] + 2, pt[1] + 2), (0, 0, 255), -1)

        # Set the generated images to the scanned image attributes.
        self.image_panel.set_scanned_image(self.toQImage(scanned_image),
                                           self.toQImage(coord_image),
                                           self.btnShowCoords.isChecked())




    def msgBox(self,
               title="",
               text="",
               informative_text = "",
               icon= QMessageBox.Information,
               buttons=QMessageBox.Ok):

        """ Message Box Method

            Displays a pop-up message box with information for the user
            and returns the button the user clicked on the message box.
            This is used to display warnings.

            Input:
            ------
            title  := String of text to display as the title of the
                      message box.
            text   := The short text to display in the message box.
            informative_text := A longer description of the warning or
                                error being reported.
            icon   := The icon to display on the message box (such as a
                      question mark, an exclamation point, etc.)
                      Default is the information icon ("i")
            buttons:= Which buttons to display on the message box. These
                      are standard PyQt5 button definitions. To pass
                      multiple buttons, they must be 'or'ed together.
                      Default is the OK button only.

            Output:
            -------

            Returns the value of the button the user pressed to close
            the message box.

        """
        msg = QMessageBox()
        msg.setIcon(icon)
        msg.setText(text)
        msg.setInformativeText(informative_text)
        msg.setWindowTitle(title)
        msg.setStandardButtons(buttons) #(QMessageBox.Ok | QMessageBox.Cancel)
        return msg.exec_()

    def centre (self):
        """ Centre Form on Screen Method

            Centres the main window on the screen using the detected
            size of the screen and the size of the main window. It
            splits the difference between the screen width and height
            and the window width and height.

            Input:
            ------
            None

            Output:
            -------
            Main window is centred on the display.

            NOTE: It is important that this method is called after
            the window is shown on the screen to ensure the correct
            width and height of the main window are calculated.
        """
        screenSize = QDesktopWidget().availableGeometry()
        self.move((screenSize.width() - self.width()) // 2,
                  (screenSize.height() - self.height()) // 2)


    def __exit_GUI(self):
        """ Exit Program Method (private)

            Invoked when the Exit command button is pressed. Destroys
            this instance of the main window and exits the program. This
            call is used in this particular instance since calling
            sys.exit() kills the Jupyter kernel as well.

            Input:
            ------
            None.

            Output:
            -------
            None.
        """

        self.destroy()
#         sys.exit()

def launch_GUI():
    """ Launch GUI Function
    Called by the program to launch the GUI.

    """
    # Check to see if app has already been initialized (if it has,
    # calling it again will cause a kernel error in the Jupyter
    # notebook), then initialize the mainWindow and display it.
    try:
        if app is None:
            app = QtWidgets.QApplication(sys.argv)
    except NameError:
            app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()

    window.setWindowState(QtCore.Qt.WindowActive)
    window.show()
    window.centre()
    app.exec_()

# launch_GUI()
