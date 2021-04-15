from collections import deque
import json
import random

INT_MIN, INT_MAX = -10 ** 3, 10 ** 3


class Preprocessing:
    def __init__(self, board, me):  # board = data["board"], me = data["me"]
        self.me = me
        self.height = board["height"]
        self.width = board["width"]
        self.food = board["food"]
        self.snakes = filter(lambda x: (x["id"] != self.me["id"]), board["snakes"])
        # self.hazards = board["hazards"]
        self.board = self.init_board()

        self.distance = [[-1] * self.width for _ in range(self.height)]
        """
        Distance[y][x] is the distance between "my head" to the grid (x, y)
        Distance[y][x] = -1 means unreachable
        Call get_distance() to fill self.distance with information
        """
        self.direction = [[None] * self.width for _ in range(self.height)]  # "up" or "down" or "left" or "right"
        # Updated along with self.distance

        self.weights = [[0] * self.width for _ in range(self.height)]
        """
        self.weights can be modified by avoid_corners(), attack_rivals() and detect_food()
        """

    def init_board(self):
        """
        We use number to denote different items on the board.
        0 for empty, 1 for (mine and rival snakes') body, 2 for rivals' head, 3 for my head, 4 for food, 5 for larger rivals' head neighbours

        The Y-Axis is positive in the up direction, and X-Axis is positive to the right
        """
        board = [[0] * self.width for _ in range(self.height)]

        for food in self.food:
            board[food["y"]][food["x"]] = 4

        for snake in self.snakes:
            # Don't count tail as it'll move in next step
            for body in snake["body"][:-1]:
                board[body["y"]][body["x"]] = 1
            head = snake["head"]
            board[head["y"]][head["x"]] = 2

            if snake["length"] >= self.me["length"]:
                head_neighbours = self.neighbors(head["y"], head["x"])
                for h_n in head_neighbours:
                    if 0 <= head["x"] < self.width and 0 <= head["y"] < self.height:
                        board[h_n[1]][h_n[2]] = 5

        # Don't count tail as it'll move in next step
        for body in self.me["body"][:-1]:
            board[body["y"]][body["x"]] = 1
        head = self.me["head"]
        board[head["y"]][head["x"]] = 3

        return board

    def neighbors(self, y, x, ordered_directions=None):
        if ordered_directions is None:
            ordered_directions = ['up', 'down', 'left', 'right']
        coordinates = {
            'up': {'x': 0, 'y': 1},
            'down': {'x': 0, 'y': -1},
            'left': {'x': -1, 'y': 0},
            'right': {'x': 1, 'y': 0},
        }
        neighbors = []
        for direction in ordered_directions:
            Y = y + coordinates[direction]['y']
            X = x + coordinates[direction]['x']
            if 0 <= Y < self.height and 0 <= X < self.width:
                neighbors.append((direction, Y, X))
        return neighbors

    def get_distance(self, ordered_directions=None):
        # Strategy: BFS, FloodFill
        y, x = self.me["head"]["y"], self.me["head"]["x"]
        if ordered_directions is None:
            ordered_directions = ['up', 'down', 'left', 'right']
        self.distance[y][x] = 0
        queue = deque()
        for direction, ny, nx in self.neighbors(y, x, ordered_directions):
            self.distance[ny][nx] = 1
            self.direction[ny][nx] = direction
            if self.board[ny][nx] == 0:
                queue.append((ny, nx))
        while queue:
            y, x = queue.popleft()
            for _, ny, nx in self.neighbors(y, x, ordered_directions):
                if self.distance[ny][nx] == -1:
                    self.distance[ny][nx] = self.distance[y][x] + 1
                    self.direction[ny][nx] = self.direction[y][x]
                    if self.board[ny][nx] == 0:
                        queue.append((ny, nx))

    def closest_food(self, allowed_direction):
        distance = 122
        y, x = None, None
        for food in self.food:
            if -1 < self.distance[food['y']][food['x']] <= distance and \
                    self.direction[food['y']][food['x']] in allowed_direction:
                distance = self.distance[food['y']][food['x']]
                print("closest_food:", (y, x), self.distance[y][x])
                if self.distance[food['y']][food['x']] == distance:
                    y, x = list(y) + [food['y']], list(x) + [food['x']]
                else:
                    y, x = food['y'], food['x']
        return list(zip(y, x)) if type(y) is list else [(y, x)]

    def movement_check(self):
        """
        Recommends a list of possible moves by eliminating 
        illegal moves
        """
        y, x = self.me["head"]["y"], self.me["head"]["x"]
        path_suggest = []

        for i in [1, -1]:
            if self.coordinate_check(y + i, x) not in [-1, 1, 2, 5]:
                # 2 should be included because the corresponding position will be occupied by the rival snake's body in the next move
                path_suggest.append("up" if (i == 1) else "down")
            if self.coordinate_check(y, x + i) not in [-1, 1, 2, 5]:
                path_suggest.append("right" if (i == 1) else "left")

        # If all four directions illegal, allow head neighbours
        if not path_suggest:
            for i in [1, -1]:
                if self.coordinate_check(y + i, x) not in [-1, 1, 2]:
                    # 2 should be included because the corresponding position will be occupied by the rival snake's body in the next move
                    path_suggest.append("up" if (i == 1) else "down")
                if self.coordinate_check(y, x + i) not in [-1, 1, 2]:
                    path_suggest.append("right" if (i == 1) else "left")

        return path_suggest

    def coordinate_check(self, y, x):
        """
        Checks the given co-ordinate and returns -1 for out of bounds
        and regular self.board output for the rest.
        """
        return self.board[y][x] if (0 <= x < self.width and 0 <= y < self.height) else -1

    def enclosed_space(self, y, x, turn):
        queue = deque()
        board = [[0] * self.width for _ in range(self.height)]
        size = 1
        for k, ny, nx in self.neighbors(y, x):
            if (self.board[ny][nx] in [0, 4]) and (board[ny][nx] != 69):
                board[ny][nx] = 69
                queue.append((ny, nx))
                size += 1
        while queue:
            my, mx = queue.popleft()
            for k, ny, nx in self.neighbors(my, mx):
                if (self.board[ny][nx] in [0, 4]) and (board[ny][nx] != 69):
                    board[ny][nx] = 69
                    queue.append((ny, nx))
                    size += 1
        print(f"X: {x}, Y: {y}, SIZE: {size}, TURN: {turn}")
        return size

    def pick_direction(self, directions, turn):
        coordinates = {
            'up': {'x': 0, 'y': 1},
            'down': {'x': 0, 'y': -1},
            'left': {'x': -1, 'y': 0},
            'right': {'x': 1, 'y': 0},
        }
        best_direction = [directions[0]]
        greatest_space = 0

        for direction in directions:
            Y = self.me["head"]["y"] + coordinates[direction]['y']
            X = self.me["head"]["x"] + coordinates[direction]['x']
            cur_space = self.enclosed_space(Y, X, turn)
            if cur_space > greatest_space:
                greatest_space = cur_space
                best_direction = [direction]
            elif cur_space == greatest_space:
                best_direction.append(direction)

        print(f"BEST MOVES: {best_direction}")
        return self.hungry_direction(best_direction)

    def hungry_direction(self, directions):
        ordered_directions = directions + [i for i in ['up', 'down', 'left', 'right'] if i not in directions]
        self.get_distance(ordered_directions)
        closest_foods = self.closest_food(directions)
        food_selected = random.choice(closest_foods)
        if food_selected[0] is None:  # No
            return random.choice(directions)
        return self.direction[food_selected[0]][food_selected[1]]

    # def avoid_corners(self):
    #     # Add weights to area around walls. Assign heavy weight to corners
    #     corner_weights = [[8, 6, 5, 4], [6, 5, 4, 2], [5, 4, 2, 1]]
    #     for i in range(3):
    #         for j in range(self.width):
    #             self.weights[i][j] = max(self.weights[i][j], corner_weights[i][min(3, j)])
    #             self.weights[i][self.width - 1 - j] = max(self.weights[i][self.width - 1 - j], corner_weights[i][min(3, j)])
    #             self.weights[self.height - 1 - i][j] = max(self.weights[self.height - 1 - i][j], corner_weights[i][min(3, j)])
    #             self.weights[self.height - 1 - i][self.width - 1 - j] = max(self.weights[self.height - 1 - i][self.width - 1 - j],
    #                                                                         corner_weights[i][min(3, j)])
    #     for i in range(3):
    #         for j in range(self.height):
    #             self.weights[j][i] = max(self.weights[j][i], corner_weights[i][min(3, j)])
    #             self.weights[j][self.width - 1 - i] = max(self.weights[j][self.width - 1 - i], corner_weights[i][min(3, j)])
    #             self.weights[self.height - 1 - j][i] = max(self.weights[self.height - 1 - j][i], corner_weights[i][min(3, j)])
    #             self.weights[self.height - 1 - j][self.width - 1 - i] = max(self.weights[self.height - 1 - j][self.width - 1 - i],
    #                                                          corner_weights[i][min(3, j)])

    # def avoid_snakes(self):
    #     pass

    # def detect_food(self, coef):
    #     pass

    # def attack_rivals(self):  # attack and defend
    #     pass

    # def get_weights(self, legal_directions):
    #     """
    #     Passive/Defensive Strategy:
    #         1. Must call avoid_corners() first
    #         2. Call avoid_snakes()
    #         3. Call detect_food()
    #         4. Call attack_rivals()

    #     """
    #     self.avoid_corners()
    #     self.avoid_snakes()
    #     food_coef = 1 #+ 2 *
    #     self.detect_food(food_coef)
    #     self.attack_rivals()
