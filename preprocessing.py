from collections import deque
import json


class Preprocessing:
    def __init__(self, board, me):  # board = data["board"], me = data["me"]
        self.me = me
        self.height = board["height"]
        self.width = board["width"]
        self.food = board["food"]
        self.snakes = board["snakes"]
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
        self.get_distance()

    def init_board(self):
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
            'up': {'x': 0, 'y': 1},
            'down': {'x': 0, 'y': -1},
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
                    self.direction[ny][nx] = self.direction[y][x]
                    if self.board[ny][nx] == 0:
                        queue.append((ny, nx))

    def closest_food(self, allowed_direction=None):
        if allowed_direction is None:
            allowed_direction = []
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
        print(f"X: {x}, Y: {y}, SELF: {json.dumps(self.me)}")
        return self.board[y][x] if (0 <= x < self.width and 0 <= y < self.height) else -1

    def avoid_corners(self, legal_directions):
        corners = []
        # corners are grid of which two or more sides are wall or snake's body
        y, x = self.me["head"]["y"], self.me["head"]["x"]
        neighbors = list(filter(lambda nbr: nbr[0] in legal_directions, self.neighbors(y, x)))
        for direction, ny, nx in neighbors:
            safe_area = len(list(filter(lambda nbr: self.board[nbr[1]][nbr[2]] == 0 or self.board[nbr[1]][nbr[2]] == 4,
                                        self.neighbors(ny, nx))))
            if safe_area < 3:
                weight = 0.7
                if safe_area < 1:
                    weight = 2.7
                elif safe_area < 2:
                    weight = 1.5
                corners.append((direction, weight))

        return corners

    def attack_rivals(self, legal_directions):  # attack and defend
        y, x = self.me["head"]["y"], self.me["head"]["x"]
        neighbors = map(lambda nb: (nb[1], nb[2]), self.neighbors(y, x))
        rival_moves = {ld: 0 for ld in legal_directions}
        snakes = [(y + i, x + i) for i in [-1, 1]] + [(y + i, x - i) for i in [-1, 1]] + [(y + i) for i in [-2, 2]] \
                 + [(x + i) for i in [-2, 2]]
        snakes = list(filter(lambda pos: self.coordinate_check(pos[0], pos[1]) == 2, snakes))
        for snake in snakes:
            possible_moves = list(filter(lambda pos: self.board[pos[1]][pos[2]] == 0 or self.board[pos[1]][pos[2]] == 4,
                                         self.neighbors(snake[0], snake[1])))
            for _, move_y, move_x in possible_moves:
                if (move_y, move_x) in neighbors:
                    pass
                """
                if (move_y, move_x) has food and snake["health"] is low, then assign high prob to this position
                """
            for snake_info in self.snakes:
                if (snake_info["head"]["y"], snake_info["head"]["x"]) == snake:
                    if snake_info["length"] >= self.me["length"]:
                        pass  # positive prob_weight
                    else:
                        pass  # negative prob_weight

        return [(key, val) for key, val in rival_moves.items()]

    def check_sparsity(self):
        pass

    def get_weights(self, legal_directions):
        """
        Passive/Defensive Strategy:
            1. Only looking for food when health < 36 or #rivals less than 3
            2. Avoid Corners and being besieged
            3. Passive Strategy against rival snakes
                - Trade-off between attacking and going into a corner
                - Adjust Weight: Need to take care of the weights added from avoid_corners()

        """
        INT_MIN, INT_MAX = -10 ** 3, 10 ** 3
        weights = {ld: 0 for ld in legal_directions}

        if self.me["health"] < 36 or len(self.snakes) < 4:
            direction_of_food = self.closest_food(legal_directions)
            for y, x in direction_of_food:
                if self.me["health"] < 6:
                    weights[self.direction[y][x]] += INT_MIN * 3
                elif len(self.snakes) < 3:
                    weights[self.direction[y][x]] += INT_MIN
                elif self.me["health"] < 15:
                    weights[self.direction[y][x]] += INT_MIN
                elif len(self.snakes) == 4:
                    weights[self.direction[y][x]] += int(INT_MIN / 2)
                elif self.me["health"] < 28:
                    weights[self.direction[y][x]] += int(INT_MIN / 2)
                else:
                    weights[self.direction[y][x]] += int(INT_MIN / 10)

        corners = self.avoid_corners(legal_directions)
        for direction, corner_weight in corners:
            weights[direction] += corner_weight * INT_MAX

        rival_moves = self.attack_rivals(legal_directions)
        for direction, prob_weight in rival_moves:
            if prob_weight > 0:
                weights[direction] += prob_weight * INT_MAX * 2
            elif prob_weight < 0 and prob_weight == -1:  # no active attack there is uncertainty
                weights[direction] += prob_weight * int(INT_MAX / 2)
                """
                Goal of attack: 
                1. Eliminate Rival if prob_weight == -1
                2. Drive rival into a corner if -1 < prob_weight < 0
                    - Multiple Cases to check ....
                """

        # Place Holder for moving to a sparse area

        return [(key, val) for key, val in weights.items()]  # convert dict to tuple
