from collections import deque
import heapq

class SearchAgent:
    def __init__(self):
        # Step 1.3: Empty plan and active algorithm config
        self.plan = []
        # Change this to 'DFS', 'BFS', or 'UCS' to test different algorithms
        self.active_algo = 'BFS'

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
        heapq.heappush(frontier, (0, start, [])) # Priority Queue
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

    def sense_and_act(self, percept):
        # Generate plan if empty
        if not self.plan:
            all_food = percept['all_food']
            if not all_food:
                return "Stay"

            start_state = percept['agent_pos']
            walls = set(percept['walls'])
            grid_size = percept['grid_size']

            # Find closest food
            closest_food = min(
                all_food,
                key=lambda f: abs(f[0] - start_state[0]) + abs(f[1] - start_state[1])
            )

            if self.active_algo == 'BFS':
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
