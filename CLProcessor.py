import shlex

class CLProcessor:
    """ Command Line Processor Class

        This class takes a line of text in the format of a standard
        command line and parses out the arguments, storing them as
        attributes. It also performs error checking on the parameters.

        Input:
        ------
        commands := string containing the command line

        Output:
        -------
        Class attributes containing the individual components and
        switches from the passed command line will be set to the
        appropriate values

        Raises:
        -------
        ValueError if an unknown flag or other entry is encountered in
        the command line being processed.

        Notes:
        ------
        While this class is convenient to use as a parser for a single
        command line, one of its real strengths is to read multiple
        command-line-like strings from a file and storing the resulting
        class instances in a list. This provides an ability for batch
        processing.

        This Implementation:
        --------------------
        This particular implementation processes the following
        parameters and switches:

        filename      := the first parameter is taken as the input file
                        name (this is the only positional parameter and
                        MUST be the first thing on the line).
        -f (row,col)  := tuple representing the finish cell in the maze
                         (0,0) is the upper-left corner.
        -h int        := integer representing the height of the maze in
                        cells.
        -s (row,col)  := tuple representing the start cell in the maze
                         (0,0) is the upper-left corner.
        -v [filename] := save solution into filename. If no filename is
                         provided, the name will be created by taking
                         the input filename and appending " Solution"
                         to the name.
        -w int        := integer representing the width of the maze in
                         cells.
        -x [filename] := save scanned maze (before solution) into
                         filename. If no filename is provided, the name
                         will be created by taking the input filename
                         and appending " Scanned" to the name.

        Note that filename, -h, -w, -s, -f are ALL MANDATORY
    """

    def __init__(self, commands):
        # Initialize the appropriate attributes then call the __parse
        # method to populate the attributes.
        self.filename = ""
        self.width = 0
        self.height = 0
        self.start_cell = (0, 0)
        self.finish_cell = (0, 0)
        self.save_scanned = False
        self.scanned_name = ""
        self.save_solution = False
        self.solution_name = ""
        self.__parse(commands)

    def __get_numbers(self, num_string, separator=" ", as_float=False):
        """ Get Numbers Method (private)

        Takes a string of arbitrary characters and extracts digits
        only, passing back a list of the numbers found. If a separator
        is provided a list of the number on either side of the
        separator character will be returned, otherwise a single
        number is returned. The as_float parameter indicates whether
        float or int values are returned.

        (NOTE when returining a single number, a negative sign will
        only be returned if the first number found is negative.)

        Inputs:
        -------
        num_string := The string containing digits and arbitrary
                      characters.
        separator  := The character denoting where the passed string
                      should be split. Default is a blank.
        as_float   := Boolean indicating whether or not the returned
                      values are floats (True) of integers (False).
                      Default is False.

        Output:
        -------
        num_list   := List of the numbers extracted from num_string.

        Examples:
        ---------

            >>>__get_numbers("14,20")
            [1420]
            >>>__get_numbers("14,-20.3")
            [1420]
            >>>__get_numbers("-14,-20.3")
            [-1420]
            >>>__get_numbers("-14,-20.3",",")
            [-14, -20]

            >>>__get_numbers("numbers 14,20",self.as_float=True)
            [1420.0]
            >>>__get_numbers("numbers 14,-20.3",self.as_float=True)
            [1420.3]
            >>>__get_numbers("numbers -14,-20.3",self.as_float=True)
            [-1420.3]
            >>>__get_numbers("numbers -14,-20.3",",",True)
            [-14.0, -20.3]
        """
        str_list = num_string.split(separator)
        num_list = []
        for entries in str_list:
            num_chars = [str(i) for i in entries if i.isdigit()
                         or i == "-" or i == "."]
            num_string = "".join(num_chars)
            if len(num_string):
                num_string = num_string[0] + num_string[1:].replace("-", "")
                last_decimal = num_string.rfind(".")
                num_string = num_string[:last_decimal].replace(".", "") + \
                             num_string[last_decimal:]
                if as_float:
                    num_list.append(float(num_string))
                else:
                    num_list.append(int(float(num_string)))
        return num_list

    def __make_tuple(self, tstring, separator="", as_float=False):
        """ Make Tuple Method (private)

        Invokes the __get_numbers method on the string following a
        command line switch that takes a tuple. This is used so that
        the user can pass either a tuple or simply a string of numbers
        separated with commas and a proper tuple will still be
        returned.

        Inputs:
        -------

        tstring       := String containing the numbers to be placed in
                         the tuple (may also contain non-numeric
                         characters).
        separator     := The character denoting where the passed string
                         should be split. Default is a the empty string.
        as_float      := Boolean indicating whether or not the returned
                         values are floats (True) of integers (False).
                         Default is False.

        Output:
        -------
        A tuple containing the numbers read form tstring.

        Examples:
        ---------
            >>> __make_tuple("(0,0)")
            (0,0)
            >>> __make_tuple("3,9")
            (3,9)
        """

        return tuple(self.__get_numbers(tstring, separator))

    def __make_new_filename(self, filename, add_string):
        """ Make New Filename Method (private)

        Splits the passed filename at the last period, appends the
        add_string to the leading string then re-applies the trailing
        piece (assumed to be the extension). If no extension is found
        (i.e. no period in the filename), add_string is added along
        with the ".jpg" extension.


        Inputs:
        -------
        filename      := The filename to be modified.
        add_string    := The text to add to filename before the
                         extension.

        Output:
        -------
        Passed filename with the contents of add_string inserted before
        the extension.

        Examples:
        --------
            >>> __make_new_filename("TestMaze.png", " Solved")
            "TestMaze Solved.png"
        """
        # Look for the last period in the string passed in.
        dotpos = filename.rfind(".")

        # If no period, append the add string and .jpg extension.
        if dotpos == -1:
            return filename + add_string + ".jpg"
        else:
        # If the filename passed in has an extension, insert the
        # add_string value between the filename and extension.
            return filename[:dotpos - len(filename)] + add_string + \
                   filename[dotpos:]

    def __parse(self, cmdline):
        """ Parse Method (private)

        This is the module that does all of the work. It loops through
        the various parts of the split command line and sets the
        appropriate attribute values. The syntax used is the
        "standard" argv (array to hold command line entries) and argc
        (the count of the arguments found).

        Once all values are read in, they are run through the
        __check_inputs() method to ensure they are all valid.

        Input:
        ------
        cmdline    := The command line to be interpreted.

        Outputs:
        --------
        Updated class attributes reflecting the values passed in the
        cmdline.

        Raises:
        -------
        ValueError := Raised if an unknown flag or other entry is
                      encountered in cmdline.
        """

        # Use shlex.split to preserve strings in double-quotes. This
        # accommodates items like filenames with spaces in the name
        # that need to be enclosed in quotes.

        argv = shlex.split(cmdline)  # cmdline.split()

        argc = len(argv)

        # Assume the first argument is the filename then loop through
        # the rest using a number of if/elif statements to interpret
        # each one.
        cmd_count = 1
        self.filename = argv[0]

        while cmd_count < argc:
            if argv[cmd_count].lower() == "-f":
                cmd_count += 1
                self.finish_cell = self.__make_tuple(argv[cmd_count], ",")
            elif argv[cmd_count].lower() == "-h":
                cmd_count += 1
                self.height = self.__get_numbers(argv[cmd_count])[0]
            elif argv[cmd_count].lower() == "-s":
                cmd_count += 1
                self.start_cell = self.__make_tuple(argv[cmd_count], ",")
            elif argv[cmd_count].lower() == "-v":
                self.save_solution = True
                # Check to see if a filename was provided. First, look
                # to see if there is anything then make sure it does not
                # start with a '-' indicating a new flag. If there is
                # something that does not start with a '-', assume it is
                # a filename.
                if cmd_count + 1 < argc:
                    if argv[cmd_count + 1][0] != "-":
                        cmd_count += 1
                        self.solution_name = argv[cmd_count]
                    else:
                        self.solution_name = self.__make_new_filename(
                                                    self.filename, " Solution")
                else:
                    self.solution_name = self.__make_new_filename(
                                                self.filename, " Solution")
            elif argv[cmd_count].lower() == "-w":
                cmd_count += 1
                self.width = self.__get_numbers(argv[cmd_count])[0]
            elif argv[cmd_count].lower() == "-x":
                self.save_scanned = True
                # Check to see if a filename was provided. First, look
                # to see if there is anything then make sure it does not
                # start with a '-' indicating a new flag. If there is
                # something that does not start with a '-', assume it is
                # a filename.
                if cmd_count + 1 < argc:
                    if argv[cmd_count + 1][0] != "-":
                        cmd_count += 1
                        self.scanned_name = argv[cmd_count]
                    else:
                        self.scanned_name = self.__make_new_filename(
                                            self.filename, " Scanned")
                else:
                    self.scanned_name = self.__make_new_filename(
                                        self.filename, " Scanned")
            else:
                raise ValueError("Unknown entry " + argv[cmd_count] +
                                 " encountered in command line: " + cmdline)
            cmd_count += 1

        self.__check_inputs()

    def __check_inputs(self):
        """ Check Inputs Method (private)

        This method is called once the command line has been interpreted
        and the class attributes are set. It checks each of the
        attributes to confirm they are valid (e.g. height and width are
        positive integers, start cell and finish cell are within the
        bounds of the maze).

        Raises:
        ValueError   := If any of the attributes are not valid.

        """

        # Check to ensure the file exists before proceeding
        try:
            f = open(self.filename)
        except IOError:
            raise IOError("File " + self.filename + " not found")
        finally:
            f.close()

        # Check that the width and height are both positive integers
        if self.width < 1 or not isinstance(self.width, int):
            raise ValueError("Maze Walker <parameter error>: width must be a "
                             "positive integer (>0).")
        if self.height < 1 or not isinstance(self.height, int):
            raise ValueError("Maze Walker <parameter error>: height must be a "
                             "positive integer (>0).")

        # Confirm that the start_cell and finish_cell parameters are
        # within the bounds of the maze. If not raise a ValueError
        # and terminate any further processing.
        if not self.start_cell[0] in range(self.width):
            raise ValueError("Maze Walker <parameter error>: start_cell x "
                             "value = {}. Must be between 0 and {}"
                             .format(self.start_cell[0], self.width - 1))
        if not self.finish_cell[0] in range(self.width):
            raise ValueError("Maze Walker <parameter error>: finish_cell x "
                             "value = {}. Must be between 0 and {}"
                             .format(self.finish_cell[0], self.width - 1))
        if not self.start_cell[1] in range(self.height):
            raise ValueError("Maze Walker <parameter error>: start_cell y "
                             "value = {}. Must be between 0 and {}"
                             .format(self.start_cell[1], self.height - 1))
        if not self.finish_cell[1] in range(self.height):
            raise ValueError("Maze Walker <parameter error>: finish_cell y "
                             "value = {}. Must be between 0 and {}"
                             .format(self.finish_cell[1], self.width - 1))
