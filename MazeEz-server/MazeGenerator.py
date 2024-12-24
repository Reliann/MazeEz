from random import choice, randrange, shuffle
import numpy as np


SCREEN_WIDTH = 840
SCREEN_HEIGHT = 620
ROOM_HEIGHT = 30
ROOM_WIDTH = 30


class Maze(object):
    """
    1. Randomly choose a starting cell.
    2. Perform a random walk from the current cel, carving passages to unvisited neighbors,
        until the current cell has no unvisited neighbors.
    3. Select a new grid cell; if it has been visited, walk from it.
    4. Repeat steps 2 and 3 a sufficient number of times that there the probability of a cell
        not being visited is extremely small.
    In this implementation of Hunt-and-kill there are two different ways to select a new grid
        cell in step 2.  The first is serpentine through the grid (the classic solution), the
        second is to randomly select a new cell enough times that the probability of an
        unexplored cell is very, very low. The second option includes a small amount of risk,
        but it creates a more interesting, harder maze.
    """

    def __init__(self, width, height):
        self.H = height
        self.W = width
        self.maze = self.generate()

    def random_location(self):

        """get a random cell in the meaze"""
        x = randrange(self.W)
        y = randrange(self.H)

        while self.maze[y, x] != 0:
            x = randrange(self.W)
            y = randrange(self.H)
        return x, y

    def make_rooms(self):
        rooms = np.zeros(((self.H*self.W)//(ROOM_HEIGHT*ROOM_WIDTH), ROOM_HEIGHT,ROOM_WIDTH), dtype=np.int8)
        ypos = 0
        xpos = 0
        for num in range((self.H*self.W)//(ROOM_HEIGHT*ROOM_WIDTH)):
            for y in range(ROOM_HEIGHT):
                for x in range(ROOM_WIDTH):
                    rooms[num, y, x] = self.maze[ypos + y, xpos + x]

            if xpos + ROOM_WIDTH < self.W:
                xpos += ROOM_WIDTH
            else:
                xpos = 0
                if ypos + ROOM_HEIGHT < self.H:
                    ypos += ROOM_HEIGHT


        return rooms

    def generate(self):
        # create empty grid
        grid = np.empty((self.H, self.W), dtype=np.int8)
        grid.fill(1)

        # find an arbitrary starting position
        current_row, current_col = (randrange(1, self.H, 2), randrange(1, self.W, 2))
        grid[current_row][current_col] = 0

        # perform many random walks, to fill the maze
        num_trials = 0
        while (current_row, current_col) != (-1, -1):
            self.walk(grid, current_row, current_col)
            current_row, current_col = self.hunt(num_trials)
            num_trials += 1

        return grid

    def walk(self, grid, row, col):
        """
        This is a standard random walk. It must start from a visited cell.
        And it completes when the current cell has no unvisited neighbors.
        """
        if grid[row][col] == 0:
            this_row = row
            this_col = col
            unvisited_neighbors = self.find_neighbors(this_row, this_col, grid, True)

            while len(unvisited_neighbors) > 0:
                neighbor = choice(unvisited_neighbors)
                grid[neighbor[0]][neighbor[1]] = 0
                grid[(neighbor[0] + this_row) // 2][(neighbor[1] + this_col) // 2] = 0
                this_row, this_col = neighbor
                unvisited_neighbors = self.find_neighbors(this_row, this_col, grid, True)

    def hunt(self, count):
        """ Select the next cell to walk from, randomly. """
        if count >= (self.H * self.W):
            return (-1, -1)
        return (randrange(1, self.H, 2), randrange(1, self.W, 2))

    def find_neighbors(self, r, c, grid, is_wall=False):
        """ Find all the grid neighbors of the current position;
            visited, or not.
        """
        ns = []

        if r > 1 and grid[r - 2][c] == is_wall:
            ns.append((r - 2, c))
        if r < self.H - 2 and grid[r + 2][c] == is_wall:
            ns.append((r + 2, c))
        if c > 1 and grid[r][c - 2] == is_wall:
            ns.append((r, c - 2))
        if c < self.W - 2 and grid[r][c + 2] == is_wall:
            ns.append((r, c + 2))

        shuffle(ns)

        return ns

    def change_value(self, x, y, value):
        self.maze[y][x] = value

    def clear_cell(self, x, y):
        self.maze[y][x] = 0

    def get_cell(self, x, y):
        return self.maze[y][x]