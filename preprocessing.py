from collections import deque


class Preprocessing:
    def __init__(self, board, me):  # board = data["board"], me = data["me"]
        self.board = board
        self.me = me
        self.height = board["height"]
        self.width = board["width"]
        self.food = board["food"]
        self.snakes = board["snakes"]
        # self.hazards = board["hazards"]
        self.map = self.init_map()

        self.distance = [[-1] * self.width for _ in range(self.height)]
        """
        Distance[y][x] is the distance between "my head" to the grid (x, y)
        Distance[y][x] = -1 means unchecked, Distance[y][x] = -2 means unreachable
        Call get_distance() to fill self.distance with information
        """
        self.direction = [[None] * self.width for _ in range(self.height)]  # "up" or "down" or "left" or "right"
        # Updated along with self.distance

    def init_map(self):
        """
        We use number to denote different items on the board.
        0 for empty, 1 for (mine and rival snakes') body, 2 for rivals' head, 3 for my head, 4 for food

        The Y-Axis is positive in the up direction, and X-Axis is positive to the right
        """
        board = [[0] * self.width for _ in range(self.height)]
        for snake in self.snakes:
            for body in snake["body"]:
                board[body["y"]][body["x"]] = 1
            head = snake["head"]
            board[head["y"]][head["x"]] = 2
        for body in self.me["body"]:
            board[body["y"]][body["x"]] = 1
        head = self.me["head"]
        board[head["y"]][head["x"]] = 3
        for food in self.food:
            board[food["y"]][food["x"]] = 4

        return board

    def neighbors(self, y, x):
        coordinates = {
            'up': {'x': 0, 'y': -1},
            'down': {'x': 0, 'y': 1},
            'left': {'x': -1, 'y': 0},
            'right': {'x': 1, 'y': 0},
        }
        neighbors = []
        for direction in ['up', 'down', 'left', 'right']:
            Y = y + coordinates[direction]['y']
            X = x + coordinates[direction]['x']
            if 0 <= Y < self.height and 0 <= X < self.width:
                neighbors.append((direction, Y, X))
        return neighbors

    def get_distance(self):
        # Strategy: BFS, FloodFill
        y, x = self.me["head"]["y"], self.me["head"]["x"]
        self.distance[y][x] = 0
        queue = deque()
        for direction, ny, nx in self.neighbors(y, x):
            self.distance[ny][nx] = 1
            self.direction[ny][nx] = direction
            if self.board[ny][nx] == 0:
                queue.append((ny, nx))
        while queue:
            y, x = queue.popleft()
            for direction, ny, nx in self.neighbors(y, x):
                if self.distance[ny][nx] == -1:
                    self.distance[ny][nx] = self.distance[y][x] + 1
                    self.direction[ny][nx] = direction
                    if self.board[ny][nx] == 0:
                        queue.append((ny, nx))
        for i in range(self.height):
            for j in range(self.width):
                if self.distance[i][j] == -1:
                    self.distance[i][j] = -2  # unreachable

    def closest_food(self):
        distance = 122
        y, x = None, None
        for food in self.food:
            if self.distance[food['y']][food['x']] == -1:
                self.get_distance()
            if -1 < self.distance[food['y']][food['x']] < distance:
                distance = self.distance[food['y']][food['x']]
                y, x = food['y'], food['x']
        return y, x
