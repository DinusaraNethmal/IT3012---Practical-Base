import random
import tkinter as tk
from agent import SearchAgent

class VisualGridHuntGame:
    def __init__(self, width=10, height=10, num_food=10, num_opponents=2, custom_walls=None):
        self.width = width
        self.height = height
        self.agent_pos = [0, 0]
        self.agent_direction = "Up"

        if custom_walls is not None:
            self.walls = set(custom_walls)
        else:
            self.walls = {(2, 2), (2, 3), (5, 5), (6, 5), (3, 7)}

        self.food_positions = set()
        while len(self.food_positions) < num_food:
            fx = random.randint(0, self.width - 1)
            fy = random.randint(0, self.height - 1)
            food_pos = (fx, fy)
            if food_pos != (0, 0) and food_pos not in self.walls:
                self.food_positions.add(food_pos)

        self.toxic_traps = set()
        while len(self.toxic_traps) < 3:
            tx = random.randint(0, self.width - 1)
            ty = random.randint(0, self.height - 1)
            trap_pos = (tx, ty)
            if trap_pos != (0, 0) and trap_pos not in self.walls and trap_pos not in self.food_positions:
                self.toxic_traps.add(trap_pos)

        self.opponents = []
        while len(self.opponents) < num_opponents:
            ox = random.randint(0, self.width - 1)
            oy = random.randint(0, self.height - 1)
            op_pos = [ox, oy]
            op_tuple = tuple(op_pos)
            if op_tuple != (0, 0) and op_tuple not in self.walls and op_tuple not in self.food_positions and op_tuple not in self.toxic_traps:
                self.opponents.append(op_pos)

        self.score = 0
        self.steps = 0
        self.collision = False

    def get_ahead_position(self):
        x, y = self.agent_pos
        if self.agent_direction == "Up":
            return (x, y + 1)
        elif self.agent_direction == "Down":
            return (x, y - 1)
        elif self.agent_direction == "Left":
            return (x - 1, y)
        elif self.agent_direction == "Right":
            return (x + 1, y)
        return (x, y)

    def get_percept(self) -> dict:
        ahead_x, ahead_y = self.get_ahead_position()

        outside_grid = (
            ahead_x < 0 or ahead_x >= self.width or
            ahead_y < 0 or ahead_y >= self.height
        )

        wall_ahead = outside_grid or (ahead_x, ahead_y) in self.walls
        food_here = tuple(self.agent_pos) in self.food_positions
        smells_toxin = tuple(self.agent_pos) in self.toxic_traps

        return {
            "wall_ahead": wall_ahead,
            "food_here": food_here,
            "smells_toxin": smells_toxin,
            "agent_pos": tuple(self.agent_pos),
            "grid_size": (self.width, self.height),
            "walls": list(self.walls),
            "all_food": list(self.food_positions)
        }

    def turn_left(self):
        directions = ["Up", "Left", "Down", "Right"]
        current_index = directions.index(self.agent_direction)
        self.agent_direction = directions[(current_index + 1) % 4]

    def turn_right(self):
        directions = ["Up", "Right", "Down", "Left"]
        current_index = directions.index(self.agent_direction)
        self.agent_direction = directions[(current_index + 1) % 4]

    def execute_action(self, action: str):
        self.steps += 1
        old_pos = list(self.agent_pos)

        if action == "TurnLeft":
            self.turn_left()
        elif action == "TurnRight":
            self.turn_right()
        elif action == "MoveForward":
            next_x, next_y = self.get_ahead_position()
            outside_grid = (next_x < 0 or next_x >= self.width or next_y < 0 or next_y >= self.height)
            if outside_grid or (next_x, next_y) in self.walls:
                self.score -= 5
            else:
                self.agent_pos = [next_x, next_y]
        elif action in ["Up", "Down", "Left", "Right"]:
            self.agent_direction = action
            next_x, next_y = self.get_ahead_position()
            outside_grid = (next_x < 0 or next_x >= self.width or next_y < 0 or next_y >= self.height)
            if outside_grid or (next_x, next_y) in self.walls:
                self.score -= 5
            else:
                self.agent_pos = [next_x, next_y]

        current_pos = tuple(self.agent_pos)

        if current_pos in self.food_positions:
            self.food_positions.remove(current_pos)
            self.score += 20

        moved = old_pos != self.agent_pos
        if moved and current_pos in self.toxic_traps:
            self.score -= 15

        for op in self.opponents:
            move = random.choice(["Up", "Down", "Left", "Right", "Stay"])
            old_op = list(op)
            if move == "Up": op[1] += 1
            elif move == "Down": op[1] -= 1
            elif move == "Left": op[0] -= 1
            elif move == "Right": op[0] += 1

            if (op[0] < 0 or op[0] >= self.width or op[1] < 0 or op[1] >= self.height):
                op[:] = old_op
            elif tuple(op) in self.walls:
                op[:] = old_op

            if op == self.agent_pos:
                self.score -= 50
                self.collision = True

    def is_done(self) -> bool:
        return len(self.food_positions) == 0 or self.steps >= 150 or self.collision


class GridGameGUI:
    def __init__(self, root, width=10, height=10, num_food=12, num_opponents=2, walls=None):
        self.root = root
        self.root.title("IT3012 - Search Agents (Lab 04)")

        self.env = VisualGridHuntGame(
            width=width, height=height, num_food=num_food,
            num_opponents=num_opponents, custom_walls=walls
        )

        # Step 1.3: Inject SearchAgent
        self.agent = SearchAgent()

        max_canvas_dim = 600
        self.cell_size = max(20, min(max_canvas_dim // self.env.width, max_canvas_dim // self.env.height))

        canvas_w = self.env.width * self.cell_size
        canvas_h = self.env.height * self.cell_size

        self.canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="white")
        self.canvas.pack()

        self.label = tk.Label(root, text="Score: 0 | Steps: 0", font=("Arial", 14))
        self.label.pack(pady=10)

        self.btn = tk.Button(root, text="Start Simulation", command=self.run_loop, font=("Arial", 12), bg="#000066", fg="white")
        self.btn.pack(pady=5)

        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete("all")

        for x in range(self.env.width):
            for y in range(self.env.height):
                x1 = x * self.cell_size
                y1 = (self.env.height - 1 - y) * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                color = "#64748b" if (x, y) in self.env.walls else "#f1f5f9"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#cbd5e1")

                if self.cell_size >= 40 and (x, y) in self.env.walls:
                    self.canvas.create_text(x1 + self.cell_size / 2, y1 + self.cell_size / 2, text="W", fill="white", font=("Arial", 8, "bold"))

        for fx, fy in self.env.food_positions:
            offset = self.cell_size * 0.25
            x1 = fx * self.cell_size + offset
            y1 = (self.env.height - 1 - fy) * self.cell_size + offset
            self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.5, y1 + self.cell_size * 0.5, fill="#f59e0b", outline="#d97706")

        for tx, ty in self.env.toxic_traps:
            offset = self.cell_size * 0.25
            x1 = tx * self.cell_size + offset
            y1 = (self.env.height - 1 - ty) * self.cell_size + offset
            self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.5, y1 + self.cell_size * 0.5, fill="purple", outline="black")

        for ox, oy in self.env.opponents:
            offset = self.cell_size * 0.2
            x1 = ox * self.cell_size + offset
            y1 = (self.env.height - 1 - oy) * self.cell_size + offset
            self.canvas.create_rectangle(x1, y1, x1 + self.cell_size * 0.6, y1 + self.cell_size * 0.6, fill="#990000", outline="#7a0000")

        ax, ay = self.env.agent_pos
        offset = self.cell_size * 0.15
        x1 = ax * self.cell_size + offset
        y1 = (self.env.height - 1 - ay) * self.cell_size + offset
        self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.7, y1 + self.cell_size * 0.7, fill="#000066", outline="#1e3a8a")

    def run_loop(self):
        self.btn.config(state="disabled")

        def step():
            if not self.env.is_done():
                percept = self.env.get_percept()
                action = self.agent.sense_and_act(percept)
                self.env.execute_action(action)
                self.draw_grid()

                self.label.config(
                    text=f"Score: {self.env.score} | Steps: {self.env.steps} | Algo: {self.agent.active_algo}"
                )
                self.root.after(150, step)
            else:
                end_text = f"Collision! Final Score: {self.env.score}" if self.env.collision else f"Finished! Final Score: {self.env.score}"
                self.label.config(text=end_text)
                self.btn.config(state="normal")

        step()


if __name__ == "__main__":
    root = tk.Tk()
    app = GridGameGUI(root, width=12, height=12, num_food=5, num_opponents=0)
    root.mainloop()
