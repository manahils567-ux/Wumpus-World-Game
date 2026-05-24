import tkinter as tk
import random
from PIL import Image, ImageTk, ImageDraw, ImageColor


#  CONFIGURATION 
SIZE = 8
TILE_SIZE = 80
NUM_PITS = 2
NUM_ARROWS = 2
NUM_GOLDS = 1
INITIAL_PIT_PROB = 0.2 / (SIZE * SIZE) * 16
INITIAL_WUMPUS_PROB = 1 / (SIZE * SIZE)
LOSS_DEATH = 10000


#  A* AGENT 
class AStarAgent:
    MOVE_COST = 1

    def __init__(self, world):
        self.world = world
        self.kb = {}
        self.visited = set()
        self.safe_tiles = set([(0, 0)])
        self.gold_location = None
        self.wumpus_location = None
        self.arrows = 0
        self.current_path = []
        self.prob_pit = {}
        self.prob_wumpus = {}
        self.prob_pit[(0, 0)] = 0.0
        self.prob_wumpus[(0, 0)] = 0.0

    #  AGENT PERCEPTS 
    def get_percepts(self):
        px, py = self.world.player_pos
        percepts = set()
        is_breeze = self.world.is_adjacent_item(px, py, "pit")
        is_stench = self.world.is_adjacent_item(px, py, "wumpus") and self.world.wumpus_alive
        if is_breeze:
            percepts.add("breeze")
        if is_stench:
            percepts.add("stench")
        tile = self.world.grid[px][py]
        if "gold" in tile:
            percepts.add("glitter")
        if "arrow" in tile:
            percepts.add("item")
        return percepts

    #  AGENT KNOWLEDGE UPDATE 
    def update_kb(self, px, py, percepts):
        self.kb[(px, py)] = percepts
        self.visited.add((px, py))
        if "breeze" not in percepts and "stench" not in percepts:
            for nx, ny in self.world.get_adjacent_tiles((px, py)):
                if (nx, ny) not in self.visited:
                    self.safe_tiles.add((nx, ny))
                    self.prob_pit[(nx, ny)] = 0.0
                    self.prob_wumpus[(nx, ny)] = 0.0
        unvisited_neighbors = [
            (nx, ny)
            for nx, ny in self.world.get_adjacent_tiles((px, py))
            if (nx, ny) not in self.visited and 0 <= nx < SIZE and 0 <= ny < SIZE
        ]
        neighbor_count = len(unvisited_neighbors)
        if "breeze" in percepts and neighbor_count > 0:
            initial_breeze_prob = min(1.0, 0.9 / neighbor_count)
            for nx, ny in unvisited_neighbors:
                if (nx, ny) not in self.safe_tiles:
                    self.prob_pit[(nx, ny)] = max(
                        self.prob_pit.get((nx, ny), INITIAL_PIT_PROB),
                        initial_breeze_prob,
                    )
        if "stench" in percepts and neighbor_count > 0:
            initial_stench_prob = min(1.0, 0.95 / neighbor_count)
            for nx, ny in unvisited_neighbors:
                if (nx, ny) not in self.safe_tiles:
                    self.prob_wumpus[(nx, ny)] = max(
                        self.prob_wumpus.get((nx, ny), INITIAL_WUMPUS_PROB),
                        initial_stench_prob,
                    )
        if "glitter" in percepts and self.gold_location is None:
            self.gold_location = (px, py)
        if not self.world.wumpus_alive:
            for r in range(SIZE):
                for c in range(SIZE):
                    self.prob_wumpus[(r, c)] = 0.0

    #  AGENT UTILS 
    def get_move_direction(self, start_pos, end_pos):
        px, py = start_pos
        nx, ny = end_pos
        if nx < px:
            return "Up"
        if nx > px:
            return "Down"
        if ny < py:
            return "Left"
        if ny > py:
            return "Right"
        return "S"

    def determine_shoot_direction(self, px, py):
        best_neighbor = None
        max_prob = 0.0
        for nx, ny in self.world.get_adjacent_tiles((px, py)):
            prob = self.prob_wumpus.get((nx, ny), INITIAL_WUMPUS_PROB)
            if prob > max_prob:
                max_prob = prob
                best_neighbor = (nx, ny)
            elif (
                prob == max_prob
                and (nx, ny) not in self.visited
                and best_neighbor not in self.visited
            ):
                best_neighbor = (nx, ny)
        if best_neighbor and max_prob > 0.1:
            return self.get_move_direction((px, py), best_neighbor)
        unvisited_neighbors = [
            (nx, ny)
            for nx, ny in self.world.get_adjacent_tiles((px, py))
            if (nx, ny) not in self.visited
        ]
        if unvisited_neighbors:
            target_pos = unvisited_neighbors[0]
            return self.get_move_direction((px, py), target_pos)
        return None

    #  AGENT DECISIONS 
    def determine_action(self):
        px, py = self.world.player_pos
        percepts = self.get_percepts()
        self.update_kb(px, py, percepts)
        self.arrows = self.world.arrows
        if "glitter" in percepts or "item" in percepts:
            return "G"
        if self.world.has_gold and (px, py) == (0, 0):
            return "V"
        # Prioritize shooting Wumpus when stench is detected (before moving)
        if "stench" in percepts and self.arrows > 0 and self.world.wumpus_alive:
            shoot_direction = self.determine_shoot_direction(px, py)
            if shoot_direction:
                return "Shoot_" + shoot_direction
        if self.current_path:
            next_pos = self.current_path.pop(0)
            # Check if next position has Wumpus - if so, shoot first or avoid
            if self.world.wumpus_alive and "wumpus" in self.world.grid[next_pos[0]][next_pos[1]]:
                # Try to shoot in that direction first
                if self.arrows > 0:
                    shoot_dir = self.get_move_direction((px, py), next_pos)
                    return "Shoot_" + shoot_dir
                # If no arrows, remove this path and find alternative
                self.current_path = []
                return self.determine_action()
            return self.get_move_direction((px, py), next_pos)
        if not self.world.has_gold and self.gold_location:
            path = self.A_star_search(px, py, self.gold_location[0], self.gold_location[1])
            if path:
                self.current_path = path[1:]
                return self.determine_action()
        if self.world.has_gold:
            path = self.A_star_search(px, py, 0, 0)
            if path:
                self.current_path = path[1:]
                return self.determine_action()
        unvisited_tiles = [
            (r, c) for r in range(SIZE) for c in range(SIZE) if (r, c) not in self.visited
        ]
        if unvisited_tiles:
            def calculate_risk_score(pos):
                p_pit = self.prob_pit.get(pos, INITIAL_PIT_PROB)
                p_wumpus = self.prob_wumpus.get(pos, INITIAL_WUMPUS_PROB)
                distance = abs(pos[0] - px) + abs(pos[1] - py)
                return (p_pit + p_wumpus) * LOSS_DEATH + distance
            unvisited_tiles.sort(key=calculate_risk_score)
            for tx, ty in unvisited_tiles:
                path = self.A_star_search(px, py, tx, ty)
                if path:
                    self.current_path = path[1:]
                    return self.determine_action()
        return "S"

    #  A* SEARCH 
    def A_star_search(self, start_x, start_y, target_x, target_y):
        start = (start_x, start_y)
        target = (target_x, target_y)
        open_set = [(0, 0, start)]
        g_scores = {start: 0}
        came_from = {}

        def heuristic(pos):
            return abs(pos[0] - target[0]) + abs(pos[1] - target[1])

        while open_set:
            min_f_score = float("inf")
            min_index = -1
            for i, (f, g, pos) in enumerate(open_set):
                if f < min_f_score or (f == min_f_score and g < open_set[min_index][1]):
                    min_f_score = f
                    min_index = i
            if min_index == -1:
                break
            f_score, g_score, current = open_set.pop(min_index)
            if current == target:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]
            for neighbor in self.world.get_adjacent_tiles(current):
                nx, ny = neighbor
                neighbor_pos = (nx, ny)
                p_pit = self.prob_pit.get(neighbor_pos, INITIAL_PIT_PROB)
                p_wumpus = 0.0
                if self.world.wumpus_alive:
                    p_wumpus = self.prob_wumpus.get(neighbor_pos, INITIAL_WUMPUS_PROB)
                if neighbor_pos in self.safe_tiles:
                    p_pit = 0.0
                    p_wumpus = 0.0
                # Avoid moving into tiles with high Wumpus probability (>0.3) or known Wumpus location
                if self.world.wumpus_alive and p_wumpus > 0.3:
                    continue
                # Check if this tile actually contains a Wumpus
                if self.world.wumpus_alive and "wumpus" in self.world.grid[nx][ny]:
                    continue
                # CRITICAL: Avoid moving into tiles that actually contain a pit
                if "pit" in self.world.grid[nx][ny]:
                    continue
                # Also avoid tiles with high pit probability (>0.3) to be safer
                if p_pit > 0.3:
                    continue
                p_death = p_pit + p_wumpus
                expected_loss = p_death * LOSS_DEATH + (1 - p_death) * self.MOVE_COST
                cost = expected_loss
                tentative_g_score = g_score + cost
                if tentative_g_score < g_scores.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_scores[neighbor] = tentative_g_score
                    f_score_neighbor = tentative_g_score + heuristic(neighbor)
                    open_set.append((f_score_neighbor, tentative_g_score, neighbor))
        return None


#  GAME CLASS 
class HiddenWumpusWorld:
    def __init__(self, root):
        self.root = root
        self.root.title("Wumpus World")
        self.score = 0
        self.arrows = 0
        self.wumpus_alive = True
        self.revealed_tiles = []
        self.game_over = False
        self.player_pos = (0, 0)
        self.image_refs = []
        self.button_image_refs = []
        self.has_gold = False
        self.game_end_cause = None
        self.agent = AStarAgent(self)
        self.agent_running = False
        self.agent_delay_ms = 500
        self.auto_shoot_direction = "Up"
        self.load_images()
        self.build_ui()
        self.create_world()
        self.draw_world()
        self.root.bind("<Key>", self._all_keys)

    #  KEY BINDINGS 
    def _all_keys(self, event):
        if self.agent_running and event.keysym != "a":
            return
        if event.char in ["g", "G"]:
            self.grab()
        elif event.char in ["a", "A"]:
            self.toggle_agent()
        else:
            self.key_pressed(event)

    #  AGENT CONTROL 
    def toggle_agent(self):
        self.agent_running = not self.agent_running
        if self.agent_running:
            self.status_btn.config(text="Agent ON!")
            self.agent.current_path = []
            self.run_agent_step()
        else:
            self.status_btn.config(text="Agent OFF.")
            self.update_hud()

    def run_agent_step(self):
        if not self.agent_running or self.game_over:
            self.agent_running = False
            return
        action = self.agent.determine_action()
        if action == "V":
            self.game_end_cause = "victory"
            self.game_over = True
            self.show_game_over_popup("A* Agent won, VICTORY")
            self.agent_running = False
            return
        if action == "S":
            self.status_btn.config(text="Agent STALLED. Stopping.")
            self.agent_running = False
            return
        if action.startswith("Shoot_"):
            direction = action.split("_")[1]
            self.shoot(direction)
            self.root.after(100, self.run_agent_step)
            return
        if action in ["Up", "Down", "Left", "Right"]:
            mock_event = type("Event", (object,), {"keysym": action, "char": ""})()
            self.key_pressed(mock_event)
        elif action == "G":
            self.grab()
            if self.agent_running and self.agent.current_path:
                self.agent.current_path = []
            self.root.after(100, self.run_agent_step)
            return
        if self.game_over:
            self.agent_running = False
            return
        self.root.after(self.agent_delay_ms, self.run_agent_step)

    #  IMAGE HELPERS 
    def _create_rounded_image(self, w, h, r, color, alpha=255):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        if isinstance(color, str):
            try:
                color = ImageColor.getrgb(color)
            except ValueError:
                color_map = {
                    "lightgreen": (144, 238, 144),
                    "lightblue": (173, 216, 230),
                    "lightyellow": (255, 255, 224),
                    "lightcoral": (240, 128, 128),
                }
                color = color_map.get(color.lower(), (200, 200, 200))
        if isinstance(color, tuple) and len(color) == 3:
            color = (*color, alpha)
        draw.rounded_rectangle((0, 0, w, h), radius=r, fill=color)
        return ImageTk.PhotoImage(img)

    def load_images(self):
        try:
            folder = r"C:\Users\lenovo\Desktop\SEM 3\Ai\Ai lab\Ai project"
            self.bg_image_tk = ImageTk.PhotoImage(
                Image.open(folder + r"\grid1.png").resize((SIZE * TILE_SIZE, SIZE * TILE_SIZE))
            )
            self.player_img = ImageTk.PhotoImage(
                Image.open(folder + r"\player.png").resize((TILE_SIZE, TILE_SIZE))
            )
            self.gold_img = ImageTk.PhotoImage(
                Image.open(folder + r"\gold.png").resize((TILE_SIZE, TILE_SIZE))
            )
            self.arrow_img = ImageTk.PhotoImage(
                Image.open(folder + r"\arrow.png").resize((TILE_SIZE, TILE_SIZE))
            )
            self.wumpus_img = ImageTk.PhotoImage(
                Image.open(folder + r"\wumpus.png").resize((TILE_SIZE, TILE_SIZE))
            )
            self.pit_img = ImageTk.PhotoImage(
                Image.open(folder + r"\pit.png").resize((TILE_SIZE, TILE_SIZE))
            )
            print("INFO: Attempting to load images from user's local path.")
        except Exception as e:
            print(
                f"CRITICAL: Image load failed from local path. Ensure files exist at {folder}. Error: {e}"
            )
            self.bg_image_tk = None
            self.player_img = None
            self.arrow_img = None
            self.gold_img = None
            self.wumpus_img = None
            self.pit_img = None
        size = TILE_SIZE
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.line((size * 0.1, size * 0.1, size * 0.9, size * 0.9), fill=(255, 0, 0, 255), width=8)
        draw.line((size * 0.9, size * 0.1, size * 0.1, size * 0.9), fill=(255, 0, 0, 255), width=8)
        self.dead_wumpus_img = ImageTk.PhotoImage(img)
        print("X as for Dead Wumpus image.")

    #  UI BUILD 
    def make_btn(self, parent, text, img, cmd=None, fg="white", disabled=False):
        state = "disabled" if disabled else "normal"
        btn = tk.Button(
            parent,
            text=text,
            image=img,
            compound="center",
            font=("Arial", 10, "bold"),
            fg=fg,
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
            disabledforeground="white",
            command=cmd,
            state=state,
        )
        return btn

    def build_ui(self):
        self.game_frame = tk.Frame(self.root)
        self.game_frame.pack()
        self.hud_frame = tk.Frame(self.game_frame)
        self.hud_frame.pack(pady=8)
        btn_h = 42
        r = 22
        widths = {
            "score": 110,
            "arrow": 110,
            "status": 280,
            "restart": 110,
            "inv": 110,
            "quit": 110,
            "agent": 110,
        }
        imgs = {
            "score": self._create_rounded_image(widths["score"], btn_h, r, (76, 175, 80)),
            "arrow": self._create_rounded_image(widths["arrow"], btn_h, r, (33, 150, 243)),
            "status": self._create_rounded_image(widths["status"], btn_h, r, (156, 39, 176)),
            "restart": self._create_rounded_image(widths["restart"], btn_h, r, (255, 152, 0)),
            "inv": self._create_rounded_image(widths["inv"], btn_h, r, (255, 193, 7)),
            "quit": self._create_rounded_image(widths["quit"], btn_h, r, (244, 67, 54)),
            "agent": self._create_rounded_image(widths["agent"], btn_h, r, (96, 125, 139)),
        }
        self.button_image_refs.extend(imgs.values())
        self.score_btn = self.make_btn(self.hud_frame, f"Score: {self.score}", imgs["score"])
        self.score_btn.grid(row=0, column=0, padx=5)
        self.arrow_btn = self.make_btn(self.hud_frame, f"Arrows: {self.arrows}", imgs["arrow"])
        self.arrow_btn.grid(row=0, column=1, padx=5)
        self.status_btn = self.make_btn(self.hud_frame, "Area is clear", imgs["status"])
        self.status_btn.grid(row=0, column=2, padx=5)
        self.agent_btn = self.make_btn(
            self.hud_frame,
            "Agent (A)",
            imgs["agent"],
            cmd=self.toggle_agent,
        )
        self.agent_btn.grid(row=0, column=3, padx=5)
        self.restart_btn = self.make_btn(
            self.hud_frame,
            "Restart",
            imgs["restart"],
            cmd=self.restart_game,
        )
        self.restart_btn.grid(row=0, column=4, padx=5)
        self.inventory_btn = self.make_btn(
            self.hud_frame,
            "Inventory",
            imgs["inv"],
            cmd=self.show_inventory,
            fg="black",
        )
        self.inventory_btn.grid(row=0, column=5, padx=5)
        self.quit_to_menu_btn = self.make_btn(
            self.hud_frame,
            "Quit to Menu",
            imgs["quit"],
            cmd=self.quit_to_menu,
        )
        self.quit_to_menu_btn.grid(row=0, column=6, padx=5)
        self.canvas = tk.Canvas(self.game_frame, width=SIZE * TILE_SIZE, height=SIZE * TILE_SIZE)
        self.canvas.pack(pady=10)
        self.menu_frame = tk.Frame(self.root)
        self.menu_frame.pack(fill="both", expand=True)
        self.menu_canvas = tk.Canvas(self.menu_frame, highlightthickness=0)
        self.menu_canvas.pack(fill="both", expand=True)
        self.center_frame = tk.Frame(self.menu_canvas)
        self.center_window_id = None

        def create_center_window():
            w = self.menu_canvas.winfo_width()
            h = self.menu_canvas.winfo_height()
            if w < 10:
                w = 1200
                h = 800
            self.center_window_id = self.menu_canvas.create_window(
                w // 2,
                h // 2,
                window=self.center_frame,
                anchor="center",
            )

        self.root.after(100, create_center_window)
        new_game_img = self._create_rounded_image(300, 75, 37, (152, 251, 152), 255)
        about_img = self._create_rounded_image(300, 75, 37, (173, 216, 230), 255)
        exit_img = self._create_rounded_image(300, 75, 37, (255, 182, 193), 255)
        self.button_image_refs.append(new_game_img)
        self.button_image_refs.append(about_img)
        self.button_image_refs.append(exit_img)
        self.new_game_btn = tk.Button(
            self.center_frame,
            text="New Game",
            image=new_game_img,
            compound="center",
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
            fg="black",
            font=("Arial", 20, "bold"),
            command=self.start_new_game,
        )
        self.new_game_btn.pack(pady=20)
        self.about_btn = tk.Button(
            self.center_frame,
            text="About",
            image=about_img,
            compound="center",
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
            fg="black",
            font=("Arial", 20, "bold"),
            command=self.show_about,
        )
        self.about_btn.pack(pady=20)
        self.exit_btn = tk.Button(
            self.center_frame,
            text="Exit",
            image=exit_img,
            compound="center",
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
            fg="black",
            font=("Arial", 20, "bold"),
            command=self.root.quit,
        )
        self.exit_btn.pack(pady=20)

        def update_menu_canvas(event=None):
            self.menu_canvas.config(width=event.width, height=event.height)
            if self.center_window_id:
                self.menu_canvas.coords(self.center_window_id, event.width // 2, event.height // 2)

        self.menu_frame.bind("<Configure>", update_menu_canvas)
        self.root.geometry("1200x800")
        self.root.update_idletasks()
        self.game_frame.pack_forget()

    # MENU ACTIONS
    def start_new_game(self):
        self.menu_frame.pack_forget()
        self.game_frame.pack()
        self.restart_game()

    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("About")
        about_window.geometry("700x600")
        about_label = tk.Label(
            about_window,
            text="Wumpus World Game\n\nA classic AI game where you explore\na cave, avoid pits and the Wumpus,\nand collect gold!",
            justify=tk.LEFT,
            padx=40,
            pady=40,
            wraplength=600,
            font=("Arial", 11),
        )
        about_label.pack(fill="both", expand=True, padx=20, pady=20)
        close_btn = tk.Button(about_window, text="Close", command=about_window.destroy)
        close_btn.pack(pady=10)

    def show_inventory(self):
        inventory_window = tk.Toplevel(self.root)
        inventory_window.title("Inventory")
        inventory_window.geometry("400x350")
        inventory_window.configure(bg="#f0f0f0")
        bubble_frame = tk.Frame(inventory_window, bg="#ffffff", relief="flat")
        bubble_frame.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.85)
        title_label = tk.Label(
            bubble_frame,
            text="INVENTORY",
            font=("Arial", 24, "bold"),
            bg="#ffffff",
            fg="#333333",
        )
        title_label.pack(pady=(30, 20))
        gold_frame = tk.Frame(bubble_frame, bg="#ffffff")
        gold_frame.pack(pady=15, padx=30, fill="x")
        gold_icon = "✨" if self.has_gold else "❌"
        gold_text = "Yes" if self.has_gold else "No"
        gold_color = "#4CAF50" if self.has_gold else "#757575"
        gold_label_icon = tk.Label(gold_frame, text=gold_icon, font=("Arial", 32), bg="#ffffff")
        gold_label_icon.pack(side="left", padx=10)
        gold_label_text = tk.Label(
            gold_frame,
            text=f"Gold: {gold_text}",
            font=("Arial", 20, "bold"),
            bg="#ffffff",
            fg=gold_color,
        )
        gold_label_text.pack(side="left", padx=10)
        arrow_frame = tk.Frame(bubble_frame, bg="#ffffff")
        arrow_frame.pack(pady=15, padx=30, fill="x")
        arrow_label_icon = tk.Label(arrow_frame, text="🏹", font=("Arial", 32), bg="#ffffff")
        arrow_label_icon.pack(side="left", padx=10)
        arrow_label_text = tk.Label(
            arrow_frame,
            text=f"Arrows: {self.arrows}",
            font=("Arial", 20, "bold"),
            bg="#ffffff",
            fg="#2196F3",
        )
        arrow_label_text.pack(side="left", padx=10)
        close_btn = tk.Button(
            bubble_frame,
            text="Close",
            command=inventory_window.destroy,
            font=("Arial", 14, "bold"),
            bg="#2196F3",
            fg="white",
            relief="flat",
            padx=30,
            pady=10,
            cursor="hand2",
        )
        close_btn.pack(pady=25)

    def quit_to_menu(self):
        self.game_frame.pack_forget()
        self.menu_frame.pack()
        self.agent_running = False

    def show_game_over_popup(self, message):
        popup = tk.Toplevel(self.root)
        popup.title("Game Over")
        popup.geometry("400x150")
        popup.grab_set()
        message_label = tk.Label(popup, text=message, font=("Arial", 14, "bold"), padx=20, pady=20)
        message_label.pack()
        button_frame = tk.Frame(popup)
        button_frame.pack(pady=10)
        restart_btn = tk.Button(
            button_frame,
            text="Restart Game",
            command=lambda: [popup.destroy(), self.restart_game()],
        )
        restart_btn.pack(side=tk.LEFT, padx=10)
        menu_btn = tk.Button(
            button_frame,
            text="Back to Menu",
            command=lambda: [popup.destroy(), self.quit_to_menu()],
        )
        menu_btn.pack(side=tk.LEFT, padx=10)
        self.agent_running = False

    #  WORLD CREATION
    def create_world(self):
        self.player_pos = (0, 0)
        self.score = 0
        self.arrows = 0
        self.wumpus_alive = True
        self.revealed_tiles = []
        self.game_over = False
        self.has_gold = False
        self.game_end_cause = None
        self.agent_running = False
        self.agent = AStarAgent(self)
        self.agent.wumpus_location = None
        self.auto_shoot_direction = "Up"
        self.grid = [[set() for _ in range(SIZE)] for _ in range(SIZE)]
        self.grid[0][0] = set()

        def is_start_or_adjacent(x, y):
            sx, sy = 0, 0
            if (x, y) == (sx, sy):
                return True
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = sx + dx, sy + dy
                if 0 <= nx < SIZE and 0 <= ny < SIZE and (nx, ny) == (x, y):
                    return True
            return False

        def pick_tile(avoid_adjacent_start=False, ensure_empty=True):
            while True:
                x = random.randint(0, SIZE - 1)
                y = random.randint(0, SIZE - 1)
                if (x, y) == (0, 0):
                    continue
                if avoid_adjacent_start and is_start_or_adjacent(x, y):
                    continue
                if self.grid[x][y]:
                    continue
                return x, y

        wx, wy = pick_tile(avoid_adjacent_start=True, ensure_empty=True)
        self.grid[wx][wy].add("wumpus")
        self.agent.wumpus_location = (wx, wy)
        pits_placed = 0
        while pits_placed < NUM_PITS:
            x, y = pick_tile(avoid_adjacent_start=True, ensure_empty=True)
            self.grid[x][y].add("pit")
            pits_placed += 1
        golds_placed = 0
        while golds_placed < NUM_GOLDS:
            x, y = pick_tile(avoid_adjacent_start=True, ensure_empty=True)
            self.grid[x][y].add("gold")
            golds_placed += 1
        arrows_placed = 0
        while arrows_placed < NUM_ARROWS:
            x, y = pick_tile(avoid_adjacent_start=True, ensure_empty=True)
            self.grid[x][y].add("arrow")
            arrows_placed += 1

    def restart_game(self):
        self.create_world()
        self.draw_world()
        self.agent_running = False
        self.status_btn.config(text="Agent OFF.")
        self.update_hud()

    #  INPUT HANDLING 
    def key_pressed(self, event):
        if self.game_over:
            return
        char_lower = (event.char or "").lower()
        is_agent_event = getattr(event, "from_agent", False)

        #  HUMAN PLAYER CONTROLS 
        if not is_agent_event:
            # Shoot only with 'f' and only if standing in a stench tile (adjacent to live Wumpus)
            if char_lower == "f":
                px, py = self.player_pos
                if self.is_adjacent_item(px, py, "wumpus") and self.wumpus_alive:
                    # Find the direction to the Wumpus
                    shoot_direction = None
                    for nx, ny in self.get_adjacent_tiles((px, py)):
                        if "wumpus" in self.grid[nx][ny] and self.wumpus_alive:
                            # Calculate direction from player to Wumpus
                            if nx < px:
                                shoot_direction = "Up"
                            elif nx > px:
                                shoot_direction = "Down"
                            elif ny < py:
                                shoot_direction = "Left"
                            elif ny > py:
                                shoot_direction = "Right"
                            break
                    if shoot_direction:
                        self.shoot(shoot_direction)
                return
            # Normal movement with arrow keys (no Shift-shoot for human)
            key = event.keysym
            if key in ["Up", "Down", "Left", "Right"]:
                self.move(key)
            return

        #  AGENT CONTROLS (MOVEMENT ONLY VIA key_pressed) 
        key = event.keysym
        if key in ["Up", "Down", "Left", "Right"]:
            self.move(key)

    #  GAME ACTIONS 
    def grab(self):
        px, py = self.player_pos
        tile = self.grid[px][py]
        if "gold" in tile:
            self.has_gold = True
            tile.remove("gold")
            self.score += 1000
            self.update_hud()
            self.draw_world()
        elif "arrow" in tile:
            self.arrows += 1
            tile.remove("arrow")
            self.score += 10
            self.update_hud()
            self.draw_world()

    def move(self, direction):
        if self.game_over:
            return
        px, py = self.player_pos
        nx, ny = px, py
        if direction == "Up":
            nx -= 1
        elif direction == "Down":
            nx += 1
        elif direction == "Left":
            ny -= 1
        elif direction == "Right":
            ny += 1
        if 0 <= nx < SIZE and 0 <= ny < SIZE:
            self.player_pos = (nx, ny)
            self.auto_shoot_direction = direction
            self.score -= 1
            tile = self.grid[nx][ny]
            if "pit" in tile:
                self.game_end_cause = "pit"
                self.game_over = True
                self.show_game_over_popup(f"You fell into Pit,Score: {self.score}")
            elif "wumpus" in tile and self.wumpus_alive:
                self.game_end_cause = "wumpus"
                self.game_over = True
                self.show_game_over_popup(f"Wumpus ate you,Score: {self.score}")
            self.draw_world()
        else:
            self.score -= 5
            self.update_hud()

    def shoot(self, direction):
        if self.game_over:
            return
        if self.arrows <= 0:
            self.update_hud()
            return
        self.arrows -= 1
        self.score -= 10
        px, py = self.player_pos
        tx, ty = px, py
        if direction == "Up":
            tx -= 1
        elif direction == "Down":
            tx += 1
        elif direction == "Left":
            ty -= 1
        elif direction == "Right":
            ty += 1
        if 0 <= tx < SIZE and 0 <= ty < SIZE:
            target_tile = self.grid[tx][ty]
            if "wumpus" in target_tile and self.wumpus_alive:
                self.wumpus_alive = False
                self.score += 500
                self.agent.wumpus_location = (tx, ty)

                if not self.agent_running:
                    self.game_end_cause = "killed_wumpus"
                    self.game_over = True
                    self.show_game_over_popup("You Won! You killed the Wumpus!")
                self.update_hud()
                self.draw_world()
                return
        self.update_hud()
        self.draw_world()


    def draw_world(self):
        self.canvas.delete("all")
        self.image_refs.clear()
        if self.bg_image_tk:
            self.canvas.create_image(
                SIZE * TILE_SIZE // 2,
                SIZE * TILE_SIZE // 2,
                image=self.bg_image_tk,
            )
            self.image_refs.append(self.bg_image_tk)
        for i in range(SIZE):
            for j in range(SIZE):
                x = j * TILE_SIZE
                y = i * TILE_SIZE
                center_x = x + TILE_SIZE // 2
                center_y = y + TILE_SIZE // 2
                tile_pos = (i, j)
                tile = self.grid[i][j]
                if self.agent_running:
                    if tile_pos in self.agent.safe_tiles:
                        safe_img = self._create_rounded_image(TILE_SIZE, TILE_SIZE, 0, (144, 238, 144), 50)
                        self.canvas.create_image(center_x, center_y, image=safe_img)
                        self.image_refs.append(safe_img)
                    if tile_pos in self.agent.current_path:
                        path_img = self._create_rounded_image(TILE_SIZE, TILE_SIZE, 0, (255, 255, 0), 80)
                        self.canvas.create_image(center_x, center_y, image=path_img)
                        self.image_refs.append(path_img)
                if "gold" in tile and self.gold_img:
                    self.canvas.create_image(center_x, center_y, image=self.gold_img)
                    self.image_refs.append(self.gold_img)
                if "arrow" in tile and self.arrow_img:
                    self.canvas.create_image(center_x, center_y, image=self.arrow_img)
                    self.image_refs.append(self.arrow_img)
        if self.game_over:
            px, py = self.player_pos
            if self.game_end_cause == "pit" and self.pit_img:
                self.canvas.create_image(
                    py * TILE_SIZE + TILE_SIZE // 2,
                    px * TILE_SIZE + TILE_SIZE // 2,
                    image=self.pit_img,
                )
                self.image_refs.append(self.pit_img)
            elif self.game_end_cause == "wumpus" and self.wumpus_img:
                self.canvas.create_image(
                    py * TILE_SIZE + TILE_SIZE // 2,
                    px * TILE_SIZE + TILE_SIZE // 2,
                    image=self.wumpus_img,
                )
                self.image_refs.append(self.wumpus_img)
            elif (
                self.game_end_cause == "killed_wumpus"
                and self.dead_wumpus_img
                and self.agent.wumpus_location
            ):
                wx, wy = self.agent.wumpus_location
                self.canvas.create_image(
                    wy * TILE_SIZE + TILE_SIZE // 2,
                    wx * TILE_SIZE + TILE_SIZE // 2,
                    image=self.dead_wumpus_img,
                )
                self.image_refs.append(self.dead_wumpus_img)
        px, py = self.player_pos
        draw_player_at_current_pos = True
        if self.game_over and self.game_end_cause in ["pit", "wumpus"]:
            draw_player_at_current_pos = False
        if draw_player_at_current_pos and self.player_img:
            px_x = py * TILE_SIZE
            px_y = px * TILE_SIZE
            self.canvas.create_image(px_x + TILE_SIZE // 2, px_y + TILE_SIZE // 2, image=self.player_img)
            self.image_refs.append(self.player_img)
        self.update_hud()

    #  HUD 
    def update_hud(self):
        self.score_btn.config(text=f"Score: {self.score}")
        self.arrow_btn.config(text=f"Arrows: {self.arrows}")
        if self.agent_running:
            self.status_btn.config(text="Agent is exploring")
            return
        px, py = self.player_pos
        messages = []
        if self.game_over:
            if self.game_end_cause in ["killed_wumpus", "victory"]:
                messages.append("VICTORY!")
            else:
                messages.append("GAME OVER!")
        else:
            if self.is_adjacent_item(px, py, "wumpus") and self.wumpus_alive:
                messages.append("Stench!")
            if self.is_adjacent_item(px, py, "pit"):
                messages.append("Breeze!")
            tile = self.grid[px][py]
            if "gold" in tile:
                messages.append("Gold visible! Press G to grab")
            if "arrow" in tile:
                messages.append("Arrow visible! Press G to grab")
            if not messages:
                messages.append("Area is clear")
        self.status_btn.config(text=" | ".join(messages))

    #  ADJACENT HELPERS 
    def get_adjacent_tiles(self, pos):
        x, y = pos
        tiles = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < SIZE and 0 <= ny < SIZE:
                tiles.append((nx, ny))
        return tiles

    def is_adjacent_item(self, x, y, item):
        for nx, ny in self.get_adjacent_tiles((x, y)):
            if item in self.grid[nx][ny]:
                return True
        return False


#  ENTRY POINT 
if __name__ == "__main__":
    root = tk.Tk()
    game = HiddenWumpusWorld(root)
    root.mainloop()

