import numpy as np
import cv2 as cv
import random
import ctypes
from CLProcessor import CLProcessor as clp
from MazeCell import Cell as mzCell

def read_maze_file(img, width, height):
    """ Maze File Reader Function

        Opens the image file containing the maze and, using the width
        and height dimensions, reads through the image detecting
        vertical and horizontal walls. Detected walls are stored in a
        numpy array and will be loaded into MazeCell instances later.

        This scan is done by rows then by columns and detects the right
        and bottom walls of each maze cell.

        Input:
        ------
        filename   := name of the file containing the image of the maze
                      to be processed.
        width      := width of the maze in cells. Note that this is NOT
                      the width of the image in pixels but how many
                      "columns" the maze has.
        height     := height of the maze in cells. Note that this is NOT
                      the height of the image in pixels but how many
                      "rows" the maze has.

        Output:
        -------
        Grid       := 2x2 numpy array containing wall_index values for
                      each cell found in the image.
    """

    # Define a lambda function to return the average of the values in
    # a list (rounded up).
    listAvg = lambda lst: int(sum(lst)/len(lst)) # + 0.5)

    # Create the numpy array to hold wall_index values and initialize to
    # all zeroes
    Grid = np.zeros((height,width), dtype=int)

    # Get the size of the scanned-in image in pixels.
    num_rows = img.shape[0]
    num_cols = img.shape[1]

    # Divide the image width and height by the maze width and height to
    # get the size of each cell in pixels.
    cell_width = num_cols // width
    cell_height = num_rows // height

    # Set the midpoint of a cell. This is used to look for walls along
    # the middle of each row and column of cells so as to avoid picking
    # up the edge of a vertical wall as a horizontal wall or vice-versa.
    horiz_midpoint = cell_height // 2
    vert_midpoint = cell_width // 2

    # scan_index will be set when walls are encountered. When a black
    # pixel is encountered while scanning either a row or column, the
    # index of the pixel will be added to scan_index and index count
    # will be incremented by 1. When a white pixel is then encountered
    # (or the end of the row/column being scanned is reached), the
    # average will be calculated (scan_index/index_count) to
    # approximate the "centre" of the wall found so that the maze cell
    # it belongs to can be calculated.
    scan_index = []

    for rows in range(height):
        # Scan across each row (at the centre) looking for vertical
        # walls.
        row_centre = horiz_midpoint + cell_height * rows
        for scan in range(num_cols):
            # If a black pixel is encountered, keep track of how many
            # in a row are seen along with their cumulative indices.
            # This is then used to calculate the average, which will
            # give (approximately) the pixel in the "middle" of the
            # wall's width.
            if img.item(row_centre, scan) == 0:
                scan_index.append(scan)
            else:
                # The pixel is white so, check to see if scan_index is
                # set to anything (i.e. the program was in the process
                # of scanning a wall).
                if scan_index:
                    # If the list is not empty, take the average of the
                    # pixels' indices to determine which column this
                    # wall (centre) is part of. If it is the first row
                    # then place the left (outside) wall, otherwise
                    # place the right wall of the previous column.
                    cindex = int(listAvg(scan_index) / cell_width + 0.5)
                    if cindex == 0:
                        Grid[rows][0] = 1
                    else:
                        Grid[rows][cindex - 1] += 4
                    # Reset the scan_index for the next iteration.
                    scan_index = []

        if scan_index:
            # This is the same code as in the else: section of the
            # above for loop and is used to ensure the last wall in
            # a row is seen if the row being scanned ends with a black
            # pixel (the "else" code above would not be executed in
            # that case).
            cindex = int(listAvg(scan_index) / cell_width)
            if cindex == 0:
                Grid[rows][0] = 1
            else:
                Grid[rows][cindex - 1] += 4
            scan_index = []

    for cols in range(width):
        # Scan down each column (at the centre) looking for horizontal
        # walls.
        col_centre = vert_midpoint + cell_width * cols
        scan_index = []

        for scan in range(num_rows):
            # If a black pixel is encountered, keep track of how many
            # in a row are seen along with their cumulative indices.
            # This is then used to calculate the average, which will
            # give (approximately) the pixel in the "middle" of the
            # wall's thickness.
            if img.item(scan, col_centre) == 0:
                scan_index.append(scan)
            else:
                # The pixel is white so, check to see if scan_index is
                # set to anything (i.e. the program was scanning a
                # wall).
                if scan_index:
                    # If the list is not empty, take the average of the
                    # pixels' indices to determine which column this
                    # wall (centre) is part of. If it is the first row
                    # then place the left (outside) wall, otherwise
                    # place the right wall of the previous column.
                    cindex = int(listAvg(scan_index) / cell_height + 0.5)
                    if cindex == 0:
                        Grid[0][cols] += 2
                    else:
                        Grid[cindex - 1][cols] += 8
                    scan_index = []
        if scan_index:
            # This is the same code as in the else: section of the
            # above for loop and is used to ensure the last wall in
            # a row is seen if the row being scanned ends with a black
            # pixel (the "else" code above would not be executed in
            # that case).
            cindex = int(listAvg(scan_index) / cell_height)
            if cindex == 0:
                Grid[0][cols] += 2
            else:
                if (cols == 0) and (cindex < height - 1):
                    cindex += 1
                Grid[cindex - 1][cols] += 8
            scan_index = []

    return Grid

def create_maze(grid):
    """ Create Maze Function

        After the image file has been scanned by read_maze_file, we will
        have a 2x2 numpy array of integers that represents the right and
        bottom walls of each maze cell as well as the outside walls of
        the maze.

        This function takes this data and creates the MazeCell
        instances corresponding to each cell scanned from the image
        and stores the MazeCell instances in a new 2x2 array.

        To ensure the traversal routine has the correct wall value for
        whatever cell it is in, we need to update the scanned
        wall_index values make sure cells with left and top walls are
        correctly registered. For instance, if the cell at position 1,1
        has a right wall, this would also be the left wall of cell 1,2.
        The initial scan however would only pick up the right wall of
        cell 1,1 so we need to add the index for the left wall (1) to
        the wall_index of cell 1,2 (likewise for top walls).

        The tile_index would not be modified so that the wall is not
        drawn for both cells, as this would create a double-thick wall.

        Input:
        ------
        grid       := 2x2 numpy Array representing the wall_index
                      values for each cell in the maze.

        Output:
        -------
        np Array   := 2x2 array containing MazeCell instances
                      representing each cell in the maze.
    """

    maze_height = grid.shape[0]
    maze_width = grid.shape[1]

    # Initialize the 2x2 array of MazeCell instances.
    Maze = np.empty(shape=(grid.shape[0],
                           grid.shape[1]),
                           dtype=mzCell)

    # Load the values from the grid array into the matrix that holds
    # the MazeCell instances.
    for row in range(maze_height):
        for col in range(maze_width):
            Maze[row][col] = mzCell(grid[row][col])

    # Because of the way the wall indices are calculated, we can use
    # bitwise operations to determine whether or not a given wall is
    # present.

    for row in range(maze_height):
        for col in range(maze_width):
            if row > 0:
                if Maze[row - 1][col].wall_index() & mzCell.wi_bottom:
                    # previous cell has a bottom wall so set this cell
                    # to have a top wall
                    Maze[row][col].add_wall(mzCell.wi_top)

            if col > 0:
                if Maze[row][col - 1].wall_index() & mzCell.wi_right:
                    # previous cell has a right wall so set this cell to
                    # have a left wall
                    Maze[row][col].add_wall(mzCell.wi_left)

    # Next, examine the outside edges of the maze and place "virtual
    # walls" across any openings. This ensures the traversal routine
    # does not try to leave the maze while it is running.

    for col in range(maze_width):
        if not Maze[0][col].wall_index() & mzCell.wi_top:
            Maze[0][col].add_wall(mzCell.wi_top)
        if not Maze[maze_height - 1][col].wall_index() & mzCell.wi_bottom:
            Maze[maze_height - 1][col].add_wall(mzCell.wi_bottom)

    for row in range(maze_height):
        if not Maze[row][0].wall_index() & mzCell.wi_left:
            Maze[row][0].add_wall(mzCell.wi_left)
        if not Maze[row][maze_width - 1].wall_index() & mzCell.wi_right:
            Maze[row][maze_width - 1].add_wall(mzCell.wi_right)

    return Maze

def process_maze(img, width, height):
    """ Central Maze Processing Function

        This function brings together the various functions that process
        the image of the maze. It takes an instance of CLProcessor and
        processes the image file provided, generating the digital
        version of the maze for the program to process (MazeCell
        instances), walking through the maze looking for solutions and
        producing images of the scanned file as well as any solution or
        suggested edits found.


        Input:
        ------
        cmd_entry       := A CLProcessor instance with the details of
                           the maze to be navigated.

        Output:
        -------
        Scanned_Image   := numpy array containing an image of the
                           scanned-in file produced from the MazeCell
                           entries the program produced.
        Solution_Image  := numpy array. If a solution was found, this
                           will be an image of the maze with directional
                           arrows in each cell on the path through the
                           maze showing the direction to take. If the
                           maze has no solution but the program found
                           suggested edits to make the maze solvable,
                           this will be an image of the maze with the
                           candidate walls for removal circled. If there
                           is neither a solution nor suggested edits,
                           this will simply be an image of the maze
                           (same as Scanned_Image).
        solved          := Boolean indicating whether the maze was
                           solved or not.
    """

    # Create the array of MazeCell entries representing the maze image
    return create_maze(read_maze_file(img, width, height))

def solve_maze(Maze, cmd_entry):
    # Set start and finish cells
    Maze[cmd_entry.start_cell].set_as_start()
    Maze[cmd_entry.finish_cell].set_as_finish()

    # Produce an image of what the program sees
    Scanned_Image = draw_maze(Maze)
    Coord_Image = draw_maze(Maze, True)

#     return Scanned_Image, Scanned_Image, False

    # Navigate the maze to see if there is a path through it. If there
    # is, it will be returned as from_start and from_finish will be
    # empty. If there is no path from start to finish, the two returned
    # lists will contain all attempted paths from either end of the
    # maze. These can then be used to suggest edits to the maze to make
    # it solvable.
    from_start, from_finish = find_paths(Maze,
                                         cmd_entry.start_cell,
                                         cmd_entry.finish_cell)

    if from_start[0] == (-1, -1):
        # This is the flag that navigate_maze() sets when it finds a
        # successful path so, the maze has a solution, which is
        # contained in from_start. Remove the flag and process the
        # remaining entries to show the solution.
        from_start.pop(0)

        for path_cells in range(len(from_start)):
            row = from_start[path_cells][0]
            col = from_start[path_cells][1]
            Maze[row, col].set_direction(Maze[row, col].direction)

        # Set the finish cell so it shows a dot.
        Maze[cmd_entry.finish_cell].set_as_finish(True)

        # Draw the solution
        Solution_Image = draw_maze(Maze)

        # Return the results, indicating a solution was found.
        return Scanned_Image, Coord_Image, Solution_Image, True
    else:
        # Maze has no solution so we can use the returned lists to see
        # if removing a single wall would make it solvable.
        suggestions, coordinates = find_suggestions(from_start,
                                                    from_finish)

        # Since there is no solution, the Solution_Image will be the
        # same as Scanned_Image so simply copy that.
        Solution_Image = Scanned_Image.copy()

        # Draw an indicator around the walls whose removal would make
        # the maze solvable (if there are any).
        for coords in coordinates:
            Solution_Image = circle_wall(Solution_Image,
                                         coords[0],
                                         coords[1],
                                         coords[2], 2)

        return Scanned_Image, Coord_Image, Solution_Image, False

def navigate_maze(maze, from_cell, to_cell, maze_path, all_paths=[]):
    """ Maze Navigation Function

        The main engine that navigates through the maze looking for a
        path from start to finish. It starts at the specified start cell
        and uses simple recursion to walk through the maze. As it moves
        from one cell to the next, it keeps track of which cells it has
        visited and the direction it went when  moving from one cell to
        the next (by setting the attributes in the appropriate maze cell
        instances).  If it hits a dead end, it backs up, one cell at a
        time, trying different paths as it goes.

        It will also return all paths traversed in the all_paths list
        since the parameter is called by ref. This can be used if there
        is no solution found to see if there are edits that would make
        the maze solvable.

        Input:
        ------
        maze       := 2x2 array of maze cells containing the details of
                      the maze to be navigated (created by
                      create_maze()).
        from_cell  := tuple specifying the x,y coordinates of the maze
                      cell the navigation starts from. Cell 0,0 is the
                      cell at the upper-left corner of the maze.
        to_cell    := tuple specifying the x,y coordinates of the maze
                      cell the navigation is going to. Cell 0,0 is the
                      cell at the upper-left corner of the maze.
        maze_path  := list of tuples representing the Maze Cells
                      already visited on this run through the
                      navigation recursion.
        all_paths  := list of any paths the program was able to
                      navigate along during this recursive series. This
                      will be used to find suggested edits if the maze
                      turns out not to be solvable as is.

        Output:
        -------
        maze_path  := list of tuples containing the cells on the path
                      found through the maze. If a successful path was
                      found, the first tuple will be set to (-1,-1) to
                      serve as a flag to the program that a solution
                      was found (this is also used to terminate
                      recursion). If no solution was found, this list
                      will contain only the start cell of the maze.
        [all_paths]:= A list of all of the "viable" paths the program
                      found while navigating the maze. They do not lead
                      to the finish cell but may if certain walls are
                      removed. This is what find_suggestions() will use.
    """

    # Because parameters are passed by reference, we need to work with a
    # copy of the maze_path so that the final returned list is complete.
    _maze_path = maze_path.copy()
    row = from_cell[0]
    col = from_cell[1]
    # The first thing the recursive function does is to see if the cell
    # it is in is the finish cell. If so, add a special "flag" tuple to
    # the beginning of the Maze Path (-1,-1), the cell you are in to the
    # end of Maze Path and return the result.
    if from_cell == to_cell:
        _maze_path.append(from_cell)
        _maze_path.insert(0, (-1, -1))
        return _maze_path

    # Next, check to ensure this cell was not previously visited (since
    # we know any previously visited cell is either on a dead end we
    # already abandoned or is on a loop on the current path). Each of
    # these checks also looks at the first tuple to see if the "solved"
    # flag has been set.

    if not maze[row][col].visited and _maze_path[0] != (-1, -1):
        _maze_path.append(from_cell)
        maze[row][col].visited = True

        # If this a valid cell for the path (i.e. not previously
        # visited), add it to the Maze Path and try to move forward.

        # Movement is based on the same concept of seeing walls
        # (starting at the left and moving clockwise around the cell).

        # Note here that all directions are tried since we may return
        # to this recursive instance multiple times as the program
        # walks the maze.

        # Try to move left
        if not maze[row][col].wall_index() & mzCell.wi_left \
                and _maze_path[0] != (-1, -1):
            maze[row][col].direction = (mzCell.go_left)
            _maze_path = navigate_maze(maze, (row, col - 1),
                                       to_cell, _maze_path, all_paths)
        # Try to move up
        if not maze[row][col].wall_index() & mzCell.wi_top \
                and _maze_path[0] != (-1, -1):
            maze[row][col].direction = (mzCell.go_up)
            _maze_path = navigate_maze(maze, (row - 1, col),
                                       to_cell, _maze_path, all_paths)
        # Try to move right
        if not maze[row][col].wall_index() & mzCell.wi_right \
                and _maze_path[0] != (-1, -1):
            maze[row][col].direction = (mzCell.go_right)
            _maze_path = navigate_maze(maze, (row, col + 1),
                                       to_cell, _maze_path, all_paths)
        # Try to move down
        if not maze[row][col].wall_index() & mzCell.wi_bottom \
                and _maze_path[0] != (-1, -1):
            maze[row][col].direction = (mzCell.go_down)
            _maze_path = navigate_maze(maze, (row + 1, col),
                                       to_cell, _maze_path, all_paths)

        # If we have tried all available directions from this cell and
        # the maze is not solved then this cell is not on the successful
        # path so, remove it from the Maze Path list.
        if (_maze_path[0] != (-1, -1)):
            # Add this path to all_paths before popping the last cell
            # visited (again, appending a copy to avoid the "by ref
            # issue".
            all_paths.append(_maze_path.copy())
            _maze_path.pop()

    return _maze_path

def find_paths(maze, start_cell, finish_cell):
    """ Find Viable Paths Function

        This function calls upon the recursive navigate_maze() function
        to, see if there is a solution to the maze. If there is, this
        path will be returned. If no solution is found, the function
        keeps track of all of the viable paths found from the start cell
        then calls the navigate_maze() function a second time, this time
        going from the finish cell toward the start cell, keeping track
        of all of the viable paths found in this direction and returning
        the two lists to the calling function.

        These lists can then be used to look for possible edits to make
        the maze solvable (e.g. removing the wall between a cell on a
        path from the start cell that is adjacent to a cell on a path
        from the finish cell).

        Input:
        ------
        maze       := 2x2 array containing the MazeCell instances
                      representing the maze.
        start_cell := tuple containing the x,y coordinates of the start
                      cell.
        finish_cell:= tuple containing the x,y coordinates of the finish
                      cell.

        Output:
        -------
        from_start := list of paths - themselves lists of tuples
                      representing maze cells - of all viable paths from
                      the start cell.
        from_finish:= list of paths - themselves lists of tuples
                      representing maze cells - of all viable paths from
                      the finish cell.

        NOTE: If a solution is found, from_start will be returned as the
              successful path and from_finish will be empty.
    """

    # Clear any previous navigation through the maze. This ensures a
    # "clean slate" if this happens to be the second call to this
    # function during this run (i.e. we are navigating from the
    # finish cell).
    for row in maze:
        for cell in row:
            cell.clear_navigation

    # Set from_start as an empty list.
    from_start = []

    # Notice here that navigate_maze returns the path it found to the
    # variable called maze_path and NOT to the from_start list. This is
    # so that when navigate_maze completes, from_start - which is passed
    # as the 'all_paths' parameter will contain all viable paths from
    # the start cell of the maze_name.
    maze_path = navigate_maze(maze,
                              start_cell, finish_cell,
                              [start_cell], from_start)
    # if the returned path has more than one entry, it is a successful
    # navigation so, return it as the from_start and an empty list as
    # from_finish.
    if len(maze_path) > 1:
        return maze_path, []

    # If the maze was not solved, we navigate the maze backwards so,
    # clear out the previous navigation.
    for row in maze:
        for cell in row:
            cell.clear_navigation
    # Navigate the maze from finish to start, collecting all viable
    # paths.
    from_finish = []
    # Notice here that navigate_maze returns the path it found to the
    # variable called maze_path and NOT to the from_finish list. This is
    # so that when navigate_maze completes, from_finish - which is
    # passed as the 'all_paths' parameter will contain all viable paths
    # from the finish cell of the maze.
    maze_path = navigate_maze(maze,
                              finish_cell, start_cell,
                              [finish_cell], from_finish)

    # Now, we return from_start and from_finish, NOT maze_path. Since
    # we know the maze is not solvable at this point, maze_path will
    # contain the finish_cell only.
    return from_start, from_finish

def find_suggestions(from_start, from_finish):
    """ Find Possible Solutions Function

        This function will be called if the initial call to
        find_paths() does not find a solution to the maze. In this
        case, find_paths() will have returned two lists, one containing
        all viable paths through the maze from the start cell and the
        other containing all viable paths from the finish cell.

        This function takes these two list and looks for entries that
        are next to each other, meaning that the removal of the wall
        between them would, in essence, join the two paths and provide a
        path through the maze.

        Input:
        ------
        from_start := list of paths - themselves lists of tuples
                      representing maze cells - of all viable paths from
                      the start cell.
        from_finish:= list of paths - themselves lists of tuples
                      representing maze cells - of all viable paths from
                      the finish cell.

        Output:
        -------
        suggestions:= A list of strings describing which walls to remove
                      to make the maze solvable.
        coordinates:= A list of tuples, each with three elements. The
                      first two are the row and column of the cell whose
                      wall should be removed and the third is the
                      wall_index of the wall to be removed.

        NOTE: The reason both suggestions and coordinates are returned
        is so that there is both a human-readable and a machine-readable
        version of the suggestions available. This particular
        implementation of the program uses the coordinates only.

        Raises:
        -------
        ValueError  := Only raised if a processing error returns a pair
                       of cells whose distance apart is > 1.

        Attribution:
        ------------
        Removal of duplicates by converting to a set and back thanks
        to:
        <https://www.geeksforgeeks.org/python-remove-duplicates-list/>
    """

    def calc_distance(t1, t2):
        """ Calculate Distances between Cells Function (internal to
            find_suggestions())

        This function is local to find_suggestions() as this is the only
        place it will be used.

        Since the maze is laid out as a grid, we can easily find
        adjacent cells by looking for cells that are 1 unit apart. This
        follows the formula for the distance between two vertices
        v1=(x1,y1) and v2=(x2,y2):

                    𝑑(𝑣1,𝑣2)=sqrt((𝑥1−𝑥2)**2+(𝑦1−𝑦2)**2)

        Input:
        ------
        t1         := tuple containing the row and column of the cell in
                      the first list (generally from_start).
        t2         := tuple containing the row and column of the cell in
                      the second list (generally from_finish).

        Output:
        -------
        distance   := float representing the distance between the two
                      cells.

    """
        return ((t1[0] - t2[0]) ** 2 + (t1[1] - t2[1]) ** 2) ** 0.5

    # Set up two empty lists, one to hold the textual descriptions of
    # which walls to remove and one for the tuples containing the row,
    # column and wall_index information.
    suggestions = []
    coordinates = []

    # Loop through each list in the from_start list and each list in
    # the from_finish list.
    for fStart in from_start:
        for fFinish in from_finish:
            # Iterate over every combination of tuples in the two lists,
            # creating a list of tuple-pairs and a list of the distances
            # between the two tuples in the pair.
            pairs = [[i, j] for i in fStart for j in fFinish]
            distances = [calc_distance(i, j) for i in fStart
                                             for j in fFinish]

            # Create a list of tuple-pairs whose distance apart is 1.
            candidates = [pairs[i] for i in range(len(distances))
                          if distances[i] == 1.0]

            # For each tuple-pair whose distance apart is 1, determine
            # which coordinates differ by 1 to determine which direction
            # you would go from tuple 1 to tuple 2 and set the correct
            # wall to be removed. Set two variables to show both the
            # index and the name of the wall to be removed.
            for c in candidates:
                row_shift = c[0][0] - c[1][0]
                col_shift = c[0][1] - c[1][1]

                if row_shift == -1:
                    wall_name = "bottom wall"
                    wall_index = mzCell.wi_bottom
                elif row_shift == 1:
                    wall_name = "top wall"
                    wall_index = mzCell.wi_top
                elif col_shift == -1:
                    wall_name = "right wall"
                    wall_index = mzCell.wi_right
                elif col_shift == 1:
                    wall_name = "left wall"
                    wall_index = mzCell.wi_left
                else:
                    # If it turns out that none of the appropriate
                    # coordinates are 1 unit apart, raise an error.
                    raise ValueError("Maze Walker <find_suggestions()>: "
                                     "Internal error processing non-adjacent"
                                     " cells.")

                # Build both the human-readable and machine-readable
                # entries and append them to the appropriate lists.
                suggestions.append("Remove the " + wall_name + " from cell {}"
                                   .format(c[0]))
                coord = (c[0][0], c[0][1], wall_index)
                coordinates.append(coord)

    # Convert the lists to sets and back to remove duplicates then sort
    # the lists and return them.
    suggestions = list(set(suggestions))
    suggestions.sort()
    coordinates = list(set(coordinates))
    coordinates.sort
    return suggestions, coordinates

def draw_maze(maze, show_coords = False):
    """ Draw Maze Function

        This function uses the data stored in the MazeCell array passed
        to it to create an image of the maze, which it returns to the
        calling process.

        Input:
        ------
        maze       := 2x2 numpy Array of MazeCell instances describing
                      the maze.

        Output:
        -------
        image      := generated image of the maze.

        Attribution:
        ------------
        Template matching code (to fill in "missing corners") thanks to:

        <https://opencv-python-tutroals.readthedocs.io/en/latest/
        py_tutorials/py_imgproc/py_template_matching/py_template_matching.html>
    """

    # This function will build the image one row at a time by reading
    # each cell in the MazeCell array row-by-row. The generated images
    # for the cells in each row are stacked horizontally into an image
    # of the row. Once all the rows are drawn, these images are all
    # stacked vertically to produce the full image.
    row_list = list()
    strip_list = list()

    for row in range(maze.shape[0]):
        row_list = list()
        for col in range(maze.shape[1]):
            if show_coords:
                row_list.append(maze[row][col].image(row,col))
            else:
                row_list.append(maze[row][col].image())

        strip_list.append(np.hstack(row_list))

    full_image = np.vstack(strip_list)

    # Because of the way the image tiles are put together horizontally,
    # there will be some corners that do not align exactly.  This
    # happens when one tile has a right wall set but no top wall and
    # the tile to the right has its top wall set. The corner is cut off
    # and the resulting area is 6x6 square of pixels that looks like a
    # checkerboard. To solve this, search for the checkerboard pattern
    # and fill the upper left 16 pixels with a black rectangle.

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

    res = cv.matchTemplate(full_image, template, cv.TM_CCOEFF_NORMED)
    threshold = 0.8
    loc = np.where(res >= threshold)
    for pt in zip(*loc[::-1]):
        cv.rectangle(full_image, pt,
                     (pt[0] + 2, pt[1] + 2), (0, 0, 255), -1)

    return full_image

def circle_wall(img, row, col, wall, thickness=2):
    """ Circle Walls for Removal Function

        This function uses the data returned from find_suggestions() to
        indicate candidate walls that could be removed to make the maze
        solvable.  Despite the name, it actually draws an ellipse around
        the wall.

        Input:
        ------
        img        := image containing the maze.
        row        := integer indicating the row of the cell the wall to
                      be circled is in.
        col        := integer indicating the column of the cell the wall
                      to be circled is in.
        wall       := integer indicating wall_index of the wall to be
                      circled.
        thickness  := integer indicating the thickness of the ellipse
                      to be drawn (default is 2).

        Output:
        -------
        image      := updated image of the input img with the
                      appropriate wall circled.
    """
    # Use the scaling factor to ensure you are drawing the ellipse in the
    # correct spot.
    cell_width = mzCell.cell_width * mzCell.scale
    cell_height = mzCell.cell_height * mzCell.scale

    # Using the passed data, calculate the position of and the
    # orientation of the ellipse.
    if wall == mzCell.wi_left:
        axes_len = (int(cell_width // 4), int(cell_height // 2))
        r = int((row + 1) * cell_height - (cell_height // 2))
        c = int((col) * cell_width) - thickness
    elif wall == mzCell.wi_top:
        axes_len = (int(cell_width // 2), int(cell_height // 4))
        r = int((row) * cell_height - thickness)
        c = int((col + 1) * cell_width - (cell_width // 2))
    elif wall == mzCell.wi_right:
        axes_len = (int(cell_width // 4), int(cell_height // 2))
        r = int((row + 1) * cell_height - (cell_height // 2))
        c = int((col + 1) * cell_width) - thickness
    elif wall == mzCell.wi_bottom:
        axes_len = (int(cell_width // 2), int(cell_height // 4))
        r = int((row + 1) * cell_height - thickness)
        c = int((col + 1) * cell_width - (cell_width // 2))

    # Set the centre coordinate of the ellipse and draw it on the image
    centre_coord = (c, r)

    return cv.ellipse(img, centre_coord, axes_len,
                      0, 0, 360, 0, thickness)
