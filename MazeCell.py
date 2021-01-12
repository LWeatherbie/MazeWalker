import numpy as np
import cv2 as cv
class Cell:
    """ Maze Cell Class

        This class represents a single cell in the maze, including all
        of its attributes such as its size, which walls the cell has and
        whether or not it is on the correct path through the maze. It
        also handles the drawing of the cells for the maze.

        Inputs:
        ------
        wall_index := one of 17 values (see below) representing which
                      walls are present in the cell.
                      (default for wall_index = wi_none).
        scale      := positive integer representing the scaling factor
                      for maze cells (by default, cells are 36 x 36
                      pixels and walls are 4 pixels thick).
                      (default for scale = 1).

        Methods:
        --------
        wall_index()
                   := returns the value of the wall_index attribute.

        add_wall(wall_index)
                   := adds the specified wall(s) depending on the
                      wall_index passed (see below).

        set_direction(direction)
                   := sets an arrow indicating the direction of travel
                      on the correct path through the maze. See below
                      for valid values for direction. Note that each
                      call to this method will clear any previously set
                      direction.

        set_as_start()
                   := Specifies the cell as the start cell. START will
                      be printed at the top of the cell in the returned
                      image (removes FINISH if it has been set).

        set_as_finish()
                   := Specifies the cell as the finish cell. FINISH will
                      be printed at the top of the cell in the returned
                      image (removes START if it has been set).

        Output:
        -------
        image() := Returns an np array image of the cell with any
                   "decorations" such as walls, directional arrows, etc.

        Indices and Masks:
        --------
        The following indices are used by this class:

        Wall Indices:               Directional Indices:

        wi_none                     go_nodir (prints a dot in the cell)
        wi_left                     go_left
        wi_top                      go_up
        wi_lefttop                  go_right
        wi_right                    go_down
        wi_leftright                go_none (clears any direction)
        wi_topright
        wi_lefttopright
        wi_bottom
        wi_leftbottom
        wi_topbottom
        wi_lefttopbottom
        wi_rightbottom
        wi_leftrightbottom
        wi_toprightbottom
        wi_all (draws all 4 walls with an open centre)
        wi_filled (draws a completely filled cell)
        wi_start (prints START at the top of the cell)
        wi_finish (prints FINISH at the top of the cell)

        Directional Masks:

        Four masks (np arrays containing the vertices of polygons) are
        also used to tell the program which directional arrow to draw in
        any given cell, depending upon whether or not a Directional
        Index is set in the cell.

        left_arrow
        up_arrow
        right_arrow
        down_arrow

    """

    # Each wall is assigned a specific index, starting with the left
    # wall and moving clockwise around the cell so that Left=1, Top=2,
    # Right=4, and Bottom=8. This numbering is used so that any
    # combination of walls can be represented in a "bitwise" notation
    # (since 1=0001, 2=0010, 4=0100, and 8=1000, any combination of
    # walls can be uniquely represented with the binary numbers 0000
    # through 1111).
    #
    # Similarly, the directional instructions used to indicate the path
    # through the maze are numbered in ascending powers of 2 starting
    # with 32 and the flags for START and FINISH get the next two after
    # that.  All of this allows a single attribute (display_index) to
    # contain all of this information in a single integer value that is
    # then interpreted by the image method when drawing the cell.

    import numpy as np
    import cv2 as cv

    # Set the base features of the cell. Note that the user can change
    # the scale when creating an instance of this class and all of the
    # features (cell size, walls, arrows, etc.) will be scaled
    # accordingly.
    cell_width = 36
    cell_height = 36
    wall_thickness = 4
    wall_colour = 0
    background_colour = 255
    scale = 1

    # Wall index values
    wi_none = 0
    wi_left = 1
    wi_top = 2
    wi_lefttop = 3
    wi_right = 4
    wi_leftright = 5
    wi_topright = 6
    wi_lefttopright = 7
    wi_bottom = 8
    wi_leftbottom = 9
    wi_topbottom = 10
    wi_lefttopbottom = 11
    wi_rightbottom = 12
    wi_leftrightbottom = 13
    wi_toprightbottom = 14
    wi_all = 15
    wi_filled = 16

    # Set directional attributes
    # go_nodir is used if the path is on the solution and the direction
    # is "None" (generally the Finish)
    # go_none is used to clear a direction previously set.
    go_nodir = 32
    go_left = 64
    go_up = 128
    go_right = 256
    go_down = 512
    go_none = 0

    # Set the Start and Finish "flags"
    wi_start = 1024
    wi_finish = 2048

    # Define the vertices of the polygons (masks) for each directional
    # arrow. Since they are defined as sets of vertices, they are easily
    # scaled.
    left_arrow = np.array([[4, 0], [4, 3], [9, 3], [9, 3], [9, 7],
                           [4, 7], [4, 10], [0, 5]])
    up_arrow = np.array([[5, 0], [10, 4], [7, 4], [7, 9], [3, 9],
                         [3, 4], [0, 4], [5, 0]])
    down_arrow = np.array([[3, 0], [7, 0], [7, 5], [10, 5], [5, 9],
                           [0, 5], [3, 5], [3, 0]])
    right_arrow = np.array([[5, 0], [9, 5], [5, 10], [5, 7], [0, 7],
                            [0, 3], [5, 3], [5, 0]])

    # The instance of the maze cell is initialized with "default" values
    # (a cell is 36x36 pixels and walls are 4 pixels thick by default).
    # If the user specifies a scale here, the cell will be resized
    # accordingly along with the walls, arrows and START/FINISH strings.

    # The MazeCell instances contain both a wall_index and a
    # display_index as they are used for different purposes. Initially
    # set to the same value, the wall_index will be used to navigate
    # the maze while the display_index will be used to produce the
    # image of the cell. For these reasons, wall_index will be updated
    # to contain all walls while display_index will not. It will,
    # however, be updated to contain values for directions and the
    # START/FINISH flags.

    # The reason these need to be different has to do with the way the
    # maze file is read. The program reads across "rows" of the maze
    # and down "columns" so it will detect the right and bottom walls
    # of each cell. This is also what we will want to print out. The
    # navigation, on the other hand, needs to know whether a particular
    # cell has any of the four walls so, the program will update the
    # wall_index with this information. We would not want left and top
    # walls displayed on the output as they would show up beside the
    # right and bottom walls respectively and the image would show a
    # "double-thick" wall. This is why display_index is not updated
    # with the "extra" walls.

    def __init__(self, wall_index=wi_none, scale=1):
        # Creates a new instance of a maze cell with the specified
        # scaling.
        self.__cell_width = self.cell_width * scale
        self.__cell_height = self.cell_height * scale
        self.__wall_thickness = self.wall_thickness
        if not isinstance(scale, int):
            raise TypeError("MazeCell scale must be an integer")
        self.__scale = scale
        if wall_index > 4095:
            raise ValueError("MazeCell wall_index must be between "
                             "0 and 4095")
            wall_index = self.wi_none
        self.__wall_index = wall_index
        self.__display_index = wall_index
        self.visited = False
        self.direction = self.go_none

    def __add_caption(self, cell_image, caption):
        """ Add Caption Method (private)

            Writes the caption at the top of the cell (offset enough
            so that the text prints inside the walls).

            Inputs:
            -------
            cell_image   := The image of a specific maze cell.
            caption      := The text to be printed at the top of the
                            cell_image.

            Output:
            -------
            Copy of cell_image with caption added at the top.
        """

        x = self.__wall_thickness * self.__scale
        y = self.__wall_thickness * 3 * self.__scale
        size = 0.3 * self.__scale
        return cv.putText(cell_image, caption, (x, y), cv.FONT_HERSHEY_SIMPLEX,
                          size, self.wall_colour, 1, cv.LINE_AA)

    def __draw_direction(self, cell_image, mask):
        """ Draw Directional Arrow Method (private)

            Draws the appropriate arrow in the centre of the cell passed
            as cell_image.

            Inputs:
            -------
            cell_image   := The image of a specific maze cell.
            mask         := One of the four pre-defined masks indicating
                            a directional arrow (see the docstrings from
                            the Maze Cell class for a description).

            Output:
            -------
            Copy of cell_image with the specified directional arrow
            drawn in the centre.
        """

        # Make a copy of the array containing the vertices so any
        # scaling does not affect the original.
        scaled = np.copy(mask)

        # Multiply all vertex values by the scaling factor
        for i in range(scaled.shape[0]):
            scaled[i][0] = scaled[i][0] * self.__scale + \
                           self.__cell_width // 2 - 5 * self.__scale
            scaled[i][1] = scaled[i][1] * self.__scale + \
                           self.__cell_height // 2 - 5 * self.__scale

        # Draw the filled polygon on the image and retrun it
        return cv.fillPoly(cell_image, [scaled], color=(0, 0, 0))

    def __draw_dot(self, cell_image):
        """ Draw Dot Method (private)
            Called if the direction is go_nodir. Draws a dot in the
            centre of the image.

            Input:
            ------
            cell_image   := The image of a specific maze cell.

            Output:
            -------
            Copy of cell_image with a dot drawn in the centre.


        """

        return cv.circle(cell_image, (self.__cell_width // 2,
                                      self.__cell_height // 2),
                                      5 * self.__scale, (0, 0, 0), -1)

    def wall_index(self):
        """ wall_index Value Method.

            Returns the current value of the wall_index attribute for
            this maze cell.

            The wall_index itself is a private attribute since we need
            to ensure it gets set only to the specified values (i.e.
            specific powers of 2). We do need to expose its value to the
            program, however, since it is required when adding in the
            "additional" walls.  This method simply returns the value,
            effectively making wall_index read-only.

            Input:
            ------
            none

            Output:
            -------
            Integer := Value representing the value of the current
            wall_index.
        """

        return self.__wall_index

    def add_wall(self, wall_index):
        """ Add Maze Wall Method.

            Used to set the wall_index for the maze cell so the program
            can correctly navigate the maze. This method updates the
            wall_index and not the display_index (the others - except
            for remove_wall below - update the display_index so the
            image is accurate).

            Since we need to ensure the wall_index gets set only to the
            specified values, this method will confirm that a valid
            value has been passed and raise an error if not. It also
            confirms that the passed wall_index has not already been set
            before setting it.

            Input:
            ------
            wall_index := one of 17 values (see help(MazeCell) for a
                          full listing)) representing valid walls which
                          is to be set.

            Output:
            -------
            none

            Raises:
            -------
            ValueError is raised if the wall index passed is not valid.
        """

        if wall_index > 16:
            raise ValueError(
                "MazeCell add_wall wall_index must be between 0 and 16."
                " Value passed was {}.".format(wall_index))
        else:
            # Add the passed index by or-ing it with the current
            # wall_index. This assures only walls not already set are
            # added. For example, if wall_index is already set to
            # lefttop (3) and topright(6) is passed, we only want to add
            # the right wall (4) and not the value of 6 or the
            # wall_index will actually be incorrect.
            self.__wall_index |= wall_index

    def remove_wall(self, wall_index):
        """ Remove Maze Wall Method.

            Used to set the wall_index for the maze cell so the program
            can correctly navigate the maze. This method updates the
            wall_index and not the display_index (the others - except
            for add_wall() above - update the display_index so the image
            is accurate).

            Since we need to ensure the wall_index gets set only to the
            specified values, this method will confirm that a valid
            value has been passed and raise an error if not. It also
            confirms that the passed wall_index has not already been set
            before setting it.

            Input:
            ------
            wall_index := one of 17 values (see help(MazeCell for a full
                          listing)) representing valid walls which is to
                          be set.

            Output:
            -------
            none

            Raises:
            -------
            ValueError is raised if the wall index passed is not valid.
        """

        if wall_index > 16:
            raise ValueError(
                "MazeCell remove_wall wall_index must be between 0 and " +
                "16. Value passed was {}.".format(wall_index))
        else:
            # Remove the passed index by and-ing it with the current
            # wall_index then deleting that value from the current
            # wall_index. This assures only walls already set are
            # removed. For example, if wall_index is set to lefttop (3)
            # and topright(6) is passed, we only want to remove the top
            # wall (2) and not the value of 6 (since the right wall is
            # not set) or the wall_index will actually be incorrect.
            remove_index = self.__wall_index & wall_index
            self.__wall_index -= remove_index

    def set_direction(self, direction):
        """ Direction Setting Method.

            Used to set the display_index for the maze cell  so that the
            correct arrow is added to the image.

            Since we need to ensure the display_index gets set only to
            the specific values associated with navigation directions,
            this method will confirm that a valid value has been passed
            and raise an error if not. It then clears all values for
            directions before adding the passed value. This confirms
            that only one direction indicator is displayed.

            Input:
            ------
            direction := one of 6 values (see help(MazeCell) for a full
                         listing)) representing valid directional
                         indicators which is to be set.

            Output:
            -------
            none.
        """

        if not direction in [self.go_none, self.go_nodir, self.go_left,
                             self.go_up, self.go_right, self.go_down]:
            return ValueError("MazeCell add_direction direction " +
                              "received invalid value {}"
                              .format(direction))
        else:
            # Clear out any previously set direction then add the new
            # direction.
            if self.__display_index & self.go_nodir:
                self.__display_index -= self.go_nodir
            if self.__display_index & self.go_left:
                self.__display_index -= self.go_left
            if self.__display_index & self.go_up:
                self.__display_index -= self.go_up
            if self.__display_index & self.go_right:
                self.__display_index -= self.go_right
            if self.__display_index & self.go_down:
                self.__display_index -= self.go_down
            self.__display_index += direction

    def clear_navigation(self):
        """ Clear Navigation Method.

            Clears out any values set by a previous navigation of the
            maze. This will reset the direction value to none and the
            visited flag to False. This needs to be done if a maze
            is has no solution and the program runs through the maze
            collecting all viable paths so it can make suggestions for
            changes to make the maze solvable.

            Input:
            ------
            none

            Output:
            -------
            Previously set navigation indicators (direction and visited
            flags) are cleared.
        """

        self.set_direction(self.go.none)
        self.visited = False

    def set_as_start(self):
        """ Set Start Cell Method.

            Updates the display_index for the maze cell, making it the
            start cell so that "START" is printed at the top of the cell
            in the display.

            Calling this method will clear the value set by
            set_as_finish() if it has been previously called on this
            cell.

            Input:
            ------
            none

            Output:
            -------
            none.
        """

        # Check to be sure the "start flag" is not already set then,
        # remove the "finish flag" if it is set then set the "start
        # flag".
        if not self.__display_index & self.wi_start:
            if self.__display_index & self.wi_finish:
                self.__display_index -= self.wi_finish
            self.__display_index += self.wi_start

    def set_as_finish(self, show_dot=False):
        """ Set Finish Cell Method.

            Updates the display_index for the maze cell, making it the
            finish cell so that "FINISH" is printed at the top of the
            cell in the display.

            Calling this method will clear the value set by
            set_as_start() if it has been previously called on this
            cell.

            Input:
            ------
            none

            Output:
            -------
            none.
        """

        # Check to be sure the "finish flag" is not already set then,
        # remove the "start flag" if it is set then set the 'finish
        # flag' and set the dot as the direction.
        if not self.__display_index & self.wi_finish:
            if self.__display_index & self.wi_start:
                self.__display_index -= self.wi_start
            self.__display_index += self.wi_finish
        if (show_dot):
            self.set_direction(self.go_nodir)
        else:
            self.set_direction(self.go_none)

    def image(self, row=-1, col=-1):
        """ Draw Image Method.

            Uses the display_index attribute to determine what items
            ("decorations") should be displayed for this cell. This
            includes walls, arrows and START/FINISH. It will then
            draw the appropriate image and return it.

            If row AND col are passed to this call, it will return
            an image of the cell with the row and column number
            printed on it. This is used to produce the "show
            coordinates" image.

            Input:
            ------
            [row]       := Optional integer indicating which row this
                           maze cell is in. If both row and col are
                           passed, they will be printed as row,col in
                           the centre of the returned image in place of
                           any other decorations.
            [col]       := Optional integer indicating which column this
                           maze cell is in. If both row and col are
                           passed, they will be printed as row,col in
                           the centre of the returned image in place of
                           any other decorations.

            Output:
            -------
            numpy array := Image stored as an np Array (used by cv2)
        """

        # Start with a black image with the correct dimensions
        cell_image = np.zeros(shape=[self.__cell_width,
                                     self.__cell_height],
                                     dtype=np.uint8)

        start_x = 0
        end_x = self.__cell_width
        start_y = 0
        end_y = self.__cell_height

        # Draw the walls by setting the x and y coordinates "inside"
        # the walls and then filling this area with a rectangle in the
        # background colour (white by default).
        if self.__display_index & self.wi_left:
            start_x += self.__wall_thickness
        if self.__display_index & self.wi_top:
            start_y += self.__wall_thickness
        if self.__display_index & self.wi_right:
            end_x -= self.__wall_thickness
        if self.__display_index & self.wi_bottom:
            end_y -= self.__wall_thickness

        cell_image = cv.rectangle(cell_image,
                                  (start_x, start_y),
                                  (end_x, end_y),
                                  self.background_colour, -1)

        # Check the other attributes stored in the self.__display_index
        # and set the cell decorations accordingly.

        if row != -1 and col != -1:
            strCoord = str(row) + "," + str(col)
            cell_image = self.__add_caption(cell_image, strCoord)
        else:
            # Add directional arrows to the cells on the path:
            if self.__display_index & self.go_nodir:
                cell_image = self.__draw_dot(cell_image)
            if self.__display_index & self.go_left:
                cell_image = self.__draw_direction(cell_image,
                                                   self.left_arrow)
            if self.__display_index & self.go_up:
                cell_image = self.__draw_direction(cell_image,
                                                   self.up_arrow)
            if self.__display_index & self.go_right:
                cell_image = self.__draw_direction(cell_image,
                                                   self.right_arrow)
            if self.__display_index & self.go_down:
                cell_image = self.__draw_direction(cell_image,
                                                   self.down_arrow)

            # Set the START and FINISH cells.
            if self.__display_index & self.wi_start:
                cell_image = self.__add_caption(cell_image, "START")
            if self.__display_index & self.wi_finish:
                cell_image = self.__add_caption(cell_image, "FINISH")

        return cell_image
