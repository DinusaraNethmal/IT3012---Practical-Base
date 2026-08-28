from collections import deque
import heapq
import math

from logic_engine import KnowledgeBase


class SearchAgent:

    def __init__(self):
        # Empty plan
        self.plan = []

        # Knowledge Base
        self.kb = KnowledgeBase()

        # Rule 1:
        # TargetVisible AND HasDust -> SafeToEngage
        self.kb.tell_rule(
            ['TargetVisible', 'HasDust'],
            'SafeToEngage'
        )

        # Rule 2:
        # SafeToEngage AND BloodseekerMissing -> Retreat
        self.kb.tell_rule(
            ['SafeToEngage', 'BloodseekerMissing'],
            'Retreat'
        )

        # Options: 'DFS', 'BFS', 'UCS', 'AStar'
        self.active_algo = 'AStar'

    # ---------------------------------------------------------
    # Heuristic Functions
    # ---------------------------------------------------------

    def manhattan_distance(self, pos, goal):
        """Manhattan distance."""
        return (
            abs(pos[0] - goal[0])
            + abs(pos[1] - goal[1])
        )

    def euclidean_distance(self, pos, goal):
        """Euclidean distance."""
        return math.sqrt(
            (pos[0] - goal[0]) ** 2
            + (pos[1] - goal[1]) ** 2
        )

    # ---------------------------------------------------------
    # Get Neighbors
    # ---------------------------------------------------------

    def get_neighbors(self, state, grid_size, walls):
        """Get valid adjacent cells."""

        x, y = state
        w, h = grid_size

        neighbors = []

        directions = {
            "Up": (x, y + 1),
            "Down": (x, y - 1),
            "Left": (x - 1, y),
            "Right": (x + 1, y)
        }

        for action, (nx, ny) in directions.items():

            if (
                0 <= nx < w
                and 0 <= ny < h
                and (nx, ny) not in walls
            ):
                neighbors.append(
                    (action, (nx, ny), 1)
                )

        return neighbors

    # ---------------------------------------------------------
    # BFS
    # ---------------------------------------------------------

    def bfs_search(self, start, goal, grid_size, walls):

        frontier = deque([
            (start, [])
        ])

        reached = {start}

        while frontier:

            current_state, path = frontier.popleft()

            if current_state == goal:
                return path

            for action, next_state, _ in self.get_neighbors(
                current_state,
                grid_size,
                walls
            ):

                if next_state not in reached:

                    reached.add(next_state)

                    frontier.append(
                        (
                            next_state,
                            path + [action]
                        )
                    )

        return []

    # ---------------------------------------------------------
    # DFS
    # ---------------------------------------------------------

    def dfs_search(self, start, goal, grid_size, walls):

        frontier = [
            (start, [])
        ]

        reached = set()

        while frontier:

            current_state, path = frontier.pop()

            if current_state == goal:
                return path

            if current_state not in reached:

                reached.add(current_state)

                for action, next_state, _ in self.get_neighbors(
                    current_state,
                    grid_size,
                    walls
                ):

                    if next_state not in reached:

                        frontier.append(
                            (
                                next_state,
                                path + [action]
                            )
                        )

        return []

    # ---------------------------------------------------------
    # UCS
    # ---------------------------------------------------------

    def ucs_search(self, start, goal, grid_size, walls):

        frontier = []

        heapq.heappush(
            frontier,
            (0, start, [])
        )

        reached = {}

        while frontier:

            cost, current_state, path = heapq.heappop(
                frontier
            )

            if current_state == goal:
                return path

            if (
                current_state not in reached
                or cost < reached[current_state]
            ):

                reached[current_state] = cost

                for action, next_state, action_cost in self.get_neighbors(
                    current_state,
                    grid_size,
                    walls
                ):

                    new_cost = cost + action_cost

                    if (
                        next_state not in reached
                        or new_cost < reached.get(
                            next_state,
                            float('inf')
                        )
                    ):

                        heapq.heappush(
                            frontier,
                            (
                                new_cost,
                                next_state,
                                path + [action]
                            )
                        )

        return []

    # ---------------------------------------------------------
    # A* Search + Knowledge Base
    # ---------------------------------------------------------

    def astar_search(
        self,
        start_pos,
        goal_pos,
        walls,
        grid_size,
        toxic_traps,
        opponents,
        heuristic_type='manhattan'
    ):

        frontier = []

        # Initial heuristic
        if heuristic_type == 'manhattan':

            h_start = self.manhattan_distance(
                start_pos,
                goal_pos
            )

        else:

            h_start = self.euclidean_distance(
                start_pos,
                goal_pos
            )

        # (f_cost, g_cost, position, path)
        heapq.heappush(
            frontier,
            (
                h_start,
                0,
                start_pos,
                []
            )
        )

        reached_states = set()

        # Convert to sets for easy checking
        toxic_traps = set(toxic_traps)
        opponent_positions = set(opponents)

        while frontier:

            f_cost, g_cost, current_pos, path = heapq.heappop(
                frontier
            )

            if current_pos == goal_pos:
                return path

            if current_pos not in reached_states:

                reached_states.add(current_pos)

                for action, next_state, step_cost in self.get_neighbors(
                    current_pos,
                    grid_size,
                    walls
                ):

                    if next_state in reached_states:
                        continue

                    # -------------------------------------------------
                    # Knowledge Base check
                    # -------------------------------------------------

                    # Clear facts from previous tile
                    self.kb.clear_facts()

                    # TargetVisible
                    if next_state in opponent_positions:
                        self.kb.tell_fact(
                            'TargetVisible'
                        )

                    # HasDust
                    if next_state in toxic_traps:
                        self.kb.tell_fact(
                            'HasDust'
                        )

                    # BloodseekerMissing
                    if next_state not in opponent_positions:
                        self.kb.tell_fact(
                            'BloodseekerMissing'
                        )

                    # Run Forward Chaining
                    self.kb.forward_chain()

                    # If Retreat is deduced,
                    # this tile is considered infeasible.
                    if 'Retreat' in self.kb.facts:
                        continue

                    # -------------------------------------------------
                    # Normal A* calculation
                    # -------------------------------------------------

                    g_new = g_cost + step_cost

                    if heuristic_type == 'manhattan':

                        h_new = self.manhattan_distance(
                            next_state,
                            goal_pos
                        )

                    else:

                        h_new = self.euclidean_distance(
                            next_state,
                            goal_pos
                        )

                    f_new = g_new + h_new

                    heapq.heappush(
                        frontier,
                        (
                            f_new,
                            g_new,
                            next_state,
                            path + [action]
                        )
                    )

        return []

    # ---------------------------------------------------------
    # Decision Loop
    # ---------------------------------------------------------

    def sense_and_act(self, percept):

        # Generate a new plan if there is no current plan
        if not self.plan:

            all_food = percept['all_food']

            if not all_food:
                return "Stay"

            start_state = percept['agent_pos']

            walls = set(
                percept['walls']
            )

            grid_size = percept['grid_size']

            # Information needed by Knowledge Base
            toxic_traps = set(
                percept['toxic_traps']
            )

            opponents = [
                tuple(op)
                for op in percept['opponents']
            ]

            # Find closest food
            closest_food = min(
                all_food,
                key=lambda f: self.manhattan_distance(
                    start_state,
                    f
                )
            )

            # -------------------------------------------------
            # Select Search Algorithm
            # -------------------------------------------------

            if self.active_algo == 'AStar':

                self.plan = self.astar_search(
                    start_state,
                    closest_food,
                    walls,
                    grid_size,
                    toxic_traps,
                    opponents,
                    heuristic_type='manhattan'
                )

            elif self.active_algo == 'BFS':

                self.plan = self.bfs_search(
                    start_state,
                    closest_food,
                    grid_size,
                    walls
                )

            elif self.active_algo == 'DFS':

                self.plan = self.dfs_search(
                    start_state,
                    closest_food,
                    grid_size,
                    walls
                )

            elif self.active_algo == 'UCS':

                self.plan = self.ucs_search(
                    start_state,
                    closest_food,
                    grid_size,
                    walls
                )

        # -------------------------------------------------
        # Execute plan
        # -------------------------------------------------

        if self.plan:

            return self.plan.pop(0)

        else:

            return "Stay"