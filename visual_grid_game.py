import random
import tkinter as tk


# ============================================================
# IT3012 - Intelligent Agents
# Practical 02 - Agent Architectures
#
# Demonstrates:
#   1. Partial observability
#   2. Simple Reflex Agent
#   3. Model-Based Agent with internal memory
# ============================================================


class VisualGridHuntGame:
    """Grid environment used by both agents."""

    def __init__(
        self,
        width=10,
        height=10,
        num_food=10,
        num_opponents=0,
        num_traps=0,
        custom_walls=None,
        seed=None,
    ):
        if seed is not None:
            random.seed(seed)

        self.width = width
        self.height = height
        self.agent_pos = [0, 0]

        # The agent has an orientation because the practical
        # requires local percepts such as wall_ahead.
        self.facing = "Right"

        if custom_walls is not None:
            self.walls = set(custom_walls)
        else:
            self.walls = {
                (2, 2),
                (2, 3),
                (5, 5),
                (6, 5),
                (3, 7),
            }

        # These containers must exist before placing objects.
        self.food_positions = set()
        self.toxic_traps = set()
        self.opponents = []

        self._place_food(num_food)
        self._place_traps(num_traps)
        self._place_opponents(num_opponents)

        self.score = 0
        self.steps = 0
        self.collision = False

    # -------------------- Environment setup --------------------

    def _random_free_position(self):
        """Return a random position that is not occupied."""
        free_positions = [
            (x, y)
            for x in range(self.width)
            for y in range(self.height)
            if (
                (x, y) != (0, 0)
                and (x, y) not in self.walls
                and (x, y) not in self.food_positions
                and (x, y) not in self.toxic_traps
                and [x, y] not in self.opponents
            )
        ]

        if not free_positions:
            return None

        return random.choice(free_positions)

    def _place_food(self, num_food):
        for _ in range(num_food):
            pos = self._random_free_position()
            if pos is None:
                break
            self.food_positions.add(pos)

    def _place_traps(self, num_traps):
        for _ in range(num_traps):
            pos = self._random_free_position()
            if pos is None:
                break
            self.toxic_traps.add(pos)

    def _place_opponents(self, num_opponents):
        for _ in range(num_opponents):
            pos = self._random_free_position()
            if pos is None:
                break
            self.opponents.append(list(pos))

    # -------------------- Local perception --------------------

    def _next_position(self, direction=None):
        """Return the cell directly in the requested direction."""
        direction = direction or self.facing
        x, y = self.agent_pos

        if direction == "Up":
            y += 1
        elif direction == "Down":
            y -= 1
        elif direction == "Left":
            x -= 1
        elif direction == "Right":
            x += 1

        return x, y

    def _is_blocked(self, position):
        x, y = position
        return (
            x < 0
            or x >= self.width
            or y < 0
            or y >= self.height
            or position in self.walls
        )

    def get_percept(self):
        """
        PARTIAL OBSERVABILITY

        The agent is NOT given global coordinates or the global map.
        It receives only local sensor information.
        """
        ahead = self._next_position(self.facing)

        return {
            "wall_ahead": self._is_blocked(ahead),
            "food_here": tuple(self.agent_pos) in self.food_positions,
            "collision": self.collision,
            "remaining_food": len(self.food_positions),
        }

    # -------------------- Actions --------------------

    def execute_action(self, action):
        self.steps += 1

        if action == "TurnLeft":
            self.facing = self._turn_left(self.facing)

        elif action == "TurnRight":
            self.facing = self._turn_right(self.facing)

        elif action == "MoveForward":
            new_pos = list(self._next_position())

            if self._is_blocked(tuple(new_pos)):
                self.score -= 5
            else:
                self.agent_pos = new_pos

        elif action == "Suck":
            current = tuple(self.agent_pos)
            if current in self.food_positions:
                self.food_positions.remove(current)
                self.score += 20

        # Keep the toxic-trap feature from Lab 01.
        if tuple(self.agent_pos) in self.toxic_traps:
            self.score -= 15

        # Move opponents after the agent acts.
        for opponent in self.opponents:
            move = random.choice(
                ["Up", "Down", "Left", "Right", "Stay"]
            )

            x, y = opponent

            if move == "Up":
                y = min(self.height - 1, y + 1)
            elif move == "Down":
                y = max(0, y - 1)
            elif move == "Left":
                x = max(0, x - 1)
            elif move == "Right":
                x = min(self.width - 1, x + 1)

            if not self._is_blocked((x, y)):
                opponent[0] = x
                opponent[1] = y

            if opponent == self.agent_pos:
                self.score -= 50
                self.collision = True

    @staticmethod
    def _turn_left(direction):
        order = ["Up", "Left", "Down", "Right"]
        return order[(order.index(direction) + 1) % 4]

    @staticmethod
    def _turn_right(direction):
        order = ["Up", "Right", "Down", "Left"]
        return order[(order.index(direction) + 1) % 4]

    def is_done(self):
        return (
            len(self.food_positions) == 0
            or self.steps >= 150
            or self.collision
        )


# ============================================================
# STEP 1.2 - SIMPLE REFLEX AGENT
# ============================================================

class SimpleReflexAgent:
    """
    Pure condition-action agent.

    There is intentionally NO __init__ method and NO memory.
    """

    def sense_and_act(self, percept):
        # IF food_here THEN suck
        if percept["food_here"]:
            return "Suck"

        # IF wall_ahead THEN turn_left
        if percept["wall_ahead"]:
            return "TurnLeft"

        # ELSE move_forward
        return "MoveForward"


# ============================================================
# STEP 1.3 - MODEL-BASED AGENT
# ============================================================

class ModelBasedAgent:
    """
    Model-based agent with internal memory.

    The environment still does not give global coordinates.
    The agent reconstructs a relative position from its own
    actions and stores visited/blocked cells internally.
    """

    def __init__(self):
        # Internal state / memory
        self.internal_pos = (0, 0)
        self.facing = "Right"

        self.visited_cells = set()
        self.known_blocked = set()

        self.last_action = None

    # -------------------- Transition Model --------------------

    def _update_state_from_last_action(self):
        """
        Transition Model:
        predict how the world changes after the previous action.
        """
        if self.last_action == "TurnLeft":
            self.facing = self._turn_left(self.facing)

        elif self.last_action == "TurnRight":
            self.facing = self._turn_right(self.facing)

        elif self.last_action == "MoveForward":
            self.internal_pos = self._next_position(
                self.internal_pos,
                self.facing,
            )

    # -------------------- Sensor Model --------------------

    def _update_sensor_model(self, percept):
        """
        Sensor Model:
        use the current local percept to update internal memory.
        """
        ahead = self._next_position(
            self.internal_pos,
            self.facing,
        )

        if percept["wall_ahead"]:
            self.known_blocked.add(ahead)

        self.visited_cells.add(self.internal_pos)

    # -------------------- Decision rules --------------------

    def sense_and_act(self, percept):
        # First update internal state using the previous action.
        if self.last_action is not None:
            self._update_state_from_last_action()

        # Then update memory from the current percept.
        self._update_sensor_model(percept)

        # IF food_here THEN suck
        if percept["food_here"]:
            action = "Suck"
            self.last_action = action
            return action

        front = self._next_position(
            self.internal_pos,
            self.facing,
        )

        left_direction = self._turn_left(self.facing)
        right_direction = self._turn_right(self.facing)

        left = self._next_position(
            self.internal_pos,
            left_direction,
        )
        right = self._next_position(
            self.internal_pos,
            right_direction,
        )

        front_visited = front in self.visited_cells
        left_visited = left in self.visited_cells
        right_visited = right in self.visited_cells

        # Model-based rules:
        #
        # IF wall_ahead AND left_is_visited THEN turn_right
        # IF wall_ahead THEN turn_left
        # IF front_is_visited THEN choose another direction
        # ELSE move_forward

        if percept["wall_ahead"]:
            if left_visited and not right_visited:
                action = "TurnRight"
            else:
                action = "TurnLeft"

        elif front_visited:
            if not left_visited:
                action = "TurnLeft"
            elif not right_visited:
                action = "TurnRight"
            else:
                action = "TurnRight"

        else:
            action = "MoveForward"

        self.last_action = action
        return action

    @staticmethod
    def _next_position(position, direction):
        x, y = position

        if direction == "Up":
            y += 1
        elif direction == "Down":
            y -= 1
        elif direction == "Left":
            x -= 1
        elif direction == "Right":
            x += 1

        return x, y

    @staticmethod
    def _turn_left(direction):
        order = ["Up", "Left", "Down", "Right"]
        return order[(order.index(direction) + 1) % 4]

    @staticmethod
    def _turn_right(direction):
        order = ["Up", "Right", "Down", "Left"]
        return order[(order.index(direction) + 1) % 4]


# ============================================================
# GUI
# ============================================================

class GridGameGUI:
    """Tkinter GUI for comparing both agent architectures."""

    def __init__(
        self,
        root,
        width=12,
        height=12,
        num_food=15,
        num_opponents=0,
        num_traps=0,
        walls=None,
    ):
        self.root = root
        self.root.title("IT3012 - Practical 02: Agent Architectures")

        self.width = width
        self.height = height
        self.num_food = num_food
        self.num_opponents = num_opponents
        self.num_traps = num_traps
        self.custom_walls = walls

        max_canvas = 600
        self.cell_size = max(
            20,
            min(
                max_canvas // self.width,
                max_canvas // self.height,
            ),
        )

        canvas_w = self.width * self.cell_size
        canvas_h = self.height * self.cell_size

        self.canvas = tk.Canvas(
            root,
            width=canvas_w,
            height=canvas_h,
            bg="white",
        )
        self.canvas.pack()

        self.label = tk.Label(
            root,
            text="Choose an agent and start the simulation.",
            font=("Arial", 13),
        )
        self.label.pack(pady=8)

        button_frame = tk.Frame(root)
        button_frame.pack(pady=5)

        self.simple_btn = tk.Button(
            button_frame,
            text="Run Simple Reflex Agent",
            command=self.start_simple,
            font=("Arial", 11),
        )
        self.simple_btn.grid(row=0, column=0, padx=5)

        self.model_btn = tk.Button(
            button_frame,
            text="Run Model-Based Agent",
            command=self.start_model,
            font=("Arial", 11),
        )
        self.model_btn.grid(row=0, column=1, padx=5)

        self.reset_btn = tk.Button(
            button_frame,
            text="Reset",
            command=self.reset_game,
            font=("Arial", 11),
        )
        self.reset_btn.grid(row=0, column=2, padx=5)

        self.env = None
        self.agent = None
        self.agent_name = ""
        self.running = False

        self.reset_game()

    # -------------------- Game control --------------------

    def create_environment(self):
        return VisualGridHuntGame(
            width=self.width,
            height=self.height,
            num_food=self.num_food,
            num_opponents=self.num_opponents,
            num_traps=self.num_traps,
            custom_walls=self.custom_walls,
        )

    def reset_game(self):
        self.running = False
        self.env = self.create_environment()
        self.agent = None
        self.agent_name = ""

        self.simple_btn.config(state="normal")
        self.model_btn.config(state="normal")

        self.label.config(
            text="Choose an agent and start the simulation."
        )
        self.draw_grid()

    def start_simple(self):
        self.start_agent(
            SimpleReflexAgent(),
            "Simple Reflex Agent",
        )

    def start_model(self):
        self.start_agent(
            ModelBasedAgent(),
            "Model-Based Agent",
        )

    def start_agent(self, agent, agent_name):
        if self.running:
            return

        self.env = self.create_environment()
        self.agent = agent
        self.agent_name = agent_name
        self.running = True

        self.simple_btn.config(state="disabled")
        self.model_btn.config(state="disabled")

        self.draw_grid()
        self.step()

    def step(self):
        if not self.running:
            return

        if self.env.is_done():
            self.finish_game()
            return

        percept = self.env.get_percept()
        action = self.agent.sense_and_act(percept)

        self.env.execute_action(action)

        self.draw_grid()

        self.label.config(
            text=(
                f"{self.agent_name} | "
                f"Score: {self.env.score} | "
                f"Steps: {self.env.steps} | "
                f"Facing: {self.env.facing} | "
                f"Action: {action} | "
                f"Food left: {len(self.env.food_positions)}"
            )
        )

        self.root.after(250, self.step)

    def finish_game(self):
        self.running = False

        if self.env.collision:
            message = "Collision! Game Over!"
        elif len(self.env.food_positions) == 0:
            message = "Finished! All food collected!"
        else:
            message = "Stopped: step limit reached."

        self.label.config(
            text=(
                f"{self.agent_name} | {message} | "
                f"Final Score: {self.env.score} | "
                f"Steps: {self.env.steps}"
            )
        )

        self.simple_btn.config(state="normal")
        self.model_btn.config(state="normal")

    # -------------------- Drawing --------------------

    def draw_grid(self):
        self.canvas.delete("all")

        if self.env is None:
            return

        # Grid and walls
        for x in range(self.env.width):
            for y in range(self.env.height):
                x1 = x * self.cell_size
                y1 = (
                    self.env.height - 1 - y
                ) * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                fill = (
                    "#64748b"
                    if (x, y) in self.env.walls
                    else "#f1f5f9"
                )

                self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=fill,
                    outline="#cbd5e1",
                )

        # Toxic traps
        for tx, ty in self.env.toxic_traps:
            offset = self.cell_size * 0.25
            x1 = tx * self.cell_size + offset
            y1 = (
                self.env.height - 1 - ty
            ) * self.cell_size + offset

            self.canvas.create_rectangle(
                x1,
                y1,
                x1 + self.cell_size * 0.5,
                y1 + self.cell_size * 0.5,
                fill="#8b5cf6",
                outline="#6d28d9",
            )

        # Food
        for fx, fy in self.env.food_positions:
            offset = self.cell_size * 0.25
            x1 = fx * self.cell_size + offset
            y1 = (
                self.env.height - 1 - fy
            ) * self.cell_size + offset

            self.canvas.create_oval(
                x1,
                y1,
                x1 + self.cell_size * 0.5,
                y1 + self.cell_size * 0.5,
                fill="#f59e0b",
                outline="#d97706",
            )

        # Opponents
        for ox, oy in self.env.opponents:
            offset = self.cell_size * 0.2
            x1 = ox * self.cell_size + offset
            y1 = (
                self.env.height - 1 - oy
            ) * self.cell_size + offset

            self.canvas.create_rectangle(
                x1,
                y1,
                x1 + self.cell_size * 0.6,
                y1 + self.cell_size * 0.6,
                fill="#990000",
                outline="#7a0000",
            )

        # Agent
        ax, ay = self.env.agent_pos
        offset = self.cell_size * 0.15
        x1 = ax * self.cell_size + offset
        y1 = (
            self.env.height - 1 - ay
        ) * self.cell_size + offset

        self.canvas.create_oval(
            x1,
            y1,
            x1 + self.cell_size * 0.7,
            y1 + self.cell_size * 0.7,
            fill="#000066",
            outline="#1e3a8a",
        )

        # Direction indicator
        cx = x1 + self.cell_size * 0.35
        cy = y1 + self.cell_size * 0.35

        self.canvas.create_text(
            cx,
            cy,
            text=self._direction_symbol(self.env.facing),
            fill="white",
            font=(
                "Arial",
                max(8, self.cell_size // 4),
                "bold",
            ),
        )

    @staticmethod
    def _direction_symbol(direction):
        return {
            "Up": "^",
            "Down": "v",
            "Left": "<",
            "Right": ">",
        }.get(direction, "?")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()

    app = GridGameGUI(
        root,
        width=12,
        height=12,
        num_food=15,
        num_opponents=0,
        num_traps=0,
    )

    root.mainloop()
