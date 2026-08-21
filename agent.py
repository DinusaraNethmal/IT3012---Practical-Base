from collections import deque
import heapq
import math

class SearchAgent:
    def __init__(self):
        # Step 1.3: Empty plan and active algorithm config
        self.plan = []
        # Options: 'DFS', 'BFS', 'UCS', 'AStar'
        self.active_algo = 'AStar'

    # Step 1.1: Heuristic Functions
    def manhattan_distance(self, pos, goal):
        """Calculates Manhattan distance h(n) = |x1 - x2| + |y1 - y2|"""
        return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

    def euclidean_distance(self, pos, goal):
        """Calculates Euclidean distance h(n) = sqrt((x1 - x2)^2 + (y1 - y2)^2)"""
        return math.sqrt((pos[0] - goal[0]) ** 2 + (pos[1] - goal[1]) ** 2)

    def get_neighbors(self, state, grid_size, walls):
        """Helper function to get valid adjacent cells and movement actions."""
        x, y = state
        w, h = grid_size
        neighbors = []
       
        # Mapping actions to coordinate changes
        directions = {
            "Up": (x, y + 1),
            "Down": (x, y - 1),
            "Left": (x - 1, y),
            "Right": (x + 1, y)
        }
       
        for action, (nx, ny) in directions.items():
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in walls:
                # Returns (Action, Next State, Step Cost)
                neighbors.append((action, (nx, ny), 1))
               
        return neighbors

    # 1. Breadth-First Search (BFS)
    def bfs_search(self, start, goal, grid_size, walls):
        frontier = deque([(start, [])])  # Queue
        reached = {start}

        while frontier:
            current_state, path = frontier.popleft()

            if current_state == goal:
                return path

            for action, next_state, _ in self.get_neighbors(current_state, grid_size, walls):
                if next_state not in reached:
                    reached.add(next_state)
                    frontier.append((next_state, path + [action]))
        return []

    # 2. Depth-First Search (DFS)
    def dfs_search(self, start, goal, grid_size, walls):
        frontier = [(start, [])]  # Stack
        reached = set()

        while frontier:
            current_state, path = frontier.pop()

            if current_state == goal:
                return path

            if current_state not in reached:
                reached.add(current_state)
                for action, next_state, _ in self.get_neighbors(current_state, grid_size, walls):
                    if next_state not in reached:
                        frontier.append((next_state, path + [action]))
        return []

    # 3. Uniform Cost Search (UCS)
    def ucs_search(self, start, goal, grid_size, walls):
        frontier = []
        heapq.heappush(frontier, (0, start, []))  # Priority Queue
        reached = {}

        while frontier:
            cost, current_state, path = heapq.heappop(frontier)

            if current_state == goal:
                return path

            if current_state not in reached or cost < reached[current_state]:
                reached[current_state] = cost
               
                for action, next_state, action_cost in self.get_neighbors(current_state, grid_size, walls):
                    new_cost = cost + action_cost
                    if next_state not in reached or new_cost < reached.get(next_state, float('inf')):
                        heapq.heappush(frontier, (new_cost, next_state, path + [action]))
        return []

    # Step 1.2: A* Search
    def astar_search(self, start_pos, goal_pos, walls, grid_size, heuristic_type='manhattan'):
        frontier = []
        
        # Calculate initial h(n)
        if heuristic_type == 'manhattan':
            h_start = self.manhattan_distance(start_pos, goal_pos)
        else:
            h_start = self.euclidean_distance(start_pos, goal_pos)
            
        # Push start node formatted as: (f_cost, g_cost, current_pos, path_taken)
        heapq.heappush(frontier, (0 + h_start, 0, start_pos, []))
        reached_states = set()

        while frontier:
            f_cost, g_cost, current_pos, path = heapq.heappop(frontier)

            if current_pos == goal_pos:
                return path

            if current_pos not in reached_states:
                reached_states.add(current_pos)
                
                for action, next_state, step_cost in self.get_neighbors(current_pos, grid_size, walls):
                    if next_state not in reached_states:
                        g_new = g_cost + step_cost
                        
                        if heuristic_type == 'manhattan':
                            h_new = self.manhattan_distance(next_state, goal_pos)
                        else:
                            h_new = self.euclidean_distance(next_state, goal_pos)
                            
                        f_new = g_new + h_new
                        heapq.heappush(frontier, (f_new, g_new, next_state, path + [action]))
        return []

    # Step 1.3: Decision Loop Integration
    def sense_and_act(self, percept):
        # Generate plan if empty
        if not self.plan:
            all_food = percept['all_food']
            if not all_food:
                return "Stay"

            start_state = percept['agent_pos']
            walls = set(percept['walls'])
            grid_size = percept['grid_size']

            # Find closest food using Manhattan distance
            closest_food = min(
                all_food,
                key=lambda f: self.manhattan_distance(start_state, f)
            )

            # Route algorithm based on active selection
            if self.active_algo == 'AStar':
                self.plan = self.astar_search(start_state, closest_food, walls, grid_size, heuristic_type='manhattan')
            elif self.active_algo == 'BFS':
                self.plan = self.bfs_search(start_state, closest_food, grid_size, walls)
            elif self.active_algo == 'DFS':
                self.plan = self.dfs_search(start_state, closest_food, grid_size, walls)
            elif self.active_algo == 'UCS':
                self.plan = self.ucs_search(start_state, closest_food, grid_size, walls)

        # Execute plan
        if self.plan:
            return self.plan.pop(0)
        else:
            return "Stay"
