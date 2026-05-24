# Hidden Wumpus World Game

A Python-based implementation of the classic Wumpus World AI problem, featuring a fully interactive graphical interface, a built-in AI agent, and strategic grid-based gameplay.

**Course:** Artificial Intelligence
**Student:** Menahil Suleman 

---

## Table of Contents

- [Overview](#overview)
- [Game Entities](#game-entities)
- [Interface](#interface)
- [Algorithms Used](#algorithms-used)
- [Modules](#modules)
- [Scoring System](#scoring-system)
- [Limitations](#limitations)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)

---

## Overview

The Hidden Wumpus World Game is a grid-based adventure inspired by the classic AI problem of the same name. The player navigates an 8x8 grid filled with hidden hazards including pits and a Wumpus, while collecting valuable items such as gold and arrows.

Players rely on perceptual clues from adjacent tiles to make safe decisions. A breeze signals a nearby pit; a stench signals the Wumpus. The game supports both manual keyboard-driven play and automated AI agent gameplay using A* pathfinding.

Key features:

- Navigate safely across an 8x8 grid to collect gold and avoid hazards
- Use arrows strategically to kill the Wumpus
- Receive perceptual hints (breeze, stench) from adjacent tiles
- Activate the built-in AI agent to explore the grid automatically
- Score is based on items collected, Wumpus kills, and penalties avoided

---

## Game Entities

Each tile in the grid can contain one or more of the following entities:

<img width="834" height="551" alt="game_entities" src="https://github.com/user-attachments/assets/dbcb5cb6-735c-4876-9845-a2bde503a30c" />

| Entity | Role |
|--------|------|
| Player | Starts at (0,0). Moves using arrow keys. |
| Gold | Collectible item. Increases score by +1000. |
| Arrow | Collectible ammo. Increases ammo count by +10. |
| Wumpus | Monster. Killing it gives +500 score. Walking into it causes death. |
| Pit | Hidden hazard. Walking into one causes instant death. |
| Breeze | Percept. Appears on tiles adjacent to a pit. |
| Stench | Percept. Appears on tiles adjacent to the Wumpus. |

---

## Interface

### Main Menu

The game opens with a simple menu offering three options: start a new game, read the About screen, or exit.

<img width="344" height="347" alt="main_menu" src="https://github.com/user-attachments/assets/b1360a7d-a886-4890-9013-d5f38fdc7e1a" />

### In-Game HUD

During gameplay a top control bar shows real-time information and action buttons.

<img width="672" height="171" alt="hud" src="https://github.com/user-attachments/assets/6c5fca31-4804-486e-85b9-ee1d1e7b8f60" />

| HUD Element | Purpose |
|-------------|---------|
| Score | Running total of points earned or lost |
| Arrows Counter | Remaining arrows available to fire |
| Area is clear / Percept | Current percept status for the active tile |
| Agent (A) | Activates the AI agent |
| Restart | Generates a fresh world and restarts instantly |
| Inventory | Opens the inventory panel |
| Quit to Menu | Returns to the main menu |

### Grid Environment

The 8x8 game world is rendered on a Tkinter canvas. Items, hazards, percepts, safe tile highlights, and the AI path are all displayed visually and update after every action.

<img width="482" height="473" alt="grid_environment" src="https://github.com/user-attachments/assets/e7343961-019e-4150-ba15-c1c4d7d3a15a" />

### Inventory

The inventory panel shows whether the player is currently holding gold and how many arrows remain.

**Before collecting items:**

<img width="397" height="382" alt="inventory_before" src="https://github.com/user-attachments/assets/5c231b98-8ef0-4ba9-a6a2-08e33fbb0b5d" />

**After collecting items:**

<img width="400" height="382" alt="inventory_after" src="https://github.com/user-attachments/assets/37a05a4f-fe66-4daf-b98e-f9b0319acd95" />

### AI Agent in Action

When the AI agent is activated it highlights safe tiles in green and traces its A* path across the grid toward gold and back to the start.

<img width="1057" height="689" alt="ai_agent" src="https://github.com/user-attachments/assets/ad890844-6d71-4ce9-97de-603cd5b75d24" />

---

## Algorithms Used

| Algorithm | Description |
|-----------|-------------|
| Local-Based Constraint Reasoning | Uses percepts (breeze / stench) to infer safe or dangerous neighboring tiles |
| Probabilistic Inference | Updates probabilities for pits and Wumpus to handle uncertainty and risk |
| Knowledge-Based Reasoning | Maintains a knowledge base of visited tiles and percepts to support informed decisions |
| Heuristic Decision Making | Chooses actions based on expected risk, Manhattan distance, and probabilities |
| A* Search Algorithm | Finds optimal paths from the current position to targets (gold, safe tiles, or home) |
| Risk-Based Path Selection | Computes expected loss for each tile and selects the safest exploration path |
| Rule-Based Action Selection | Uses IF-ELSE logic to decide whether to move, shoot, grab, or retreat |

---

## Modules

| Module | Description |
|--------|-------------|
| World Generation | Initializes the grid and places the Wumpus, pits, gold, and arrows at valid positions |
| Player Actions | Handles movement, item grabbing, arrow shooting, and score updates |
| Arrow and Wumpus Interaction | Implements arrow shooting mechanics and Wumpus death logic |
| Percept System | Provides stench and breeze feedback based on hazards in adjacent tiles |
| AI Agent | Implements A* pathfinding, safe tile detection, and AI-driven decision-making |
| GUI Rendering | Uses Tkinter to display the grid, player, items, agent path, and game state |
| HUD and Scoring | Updates score, arrows, and status messages in real-time |
| Game Logic and Events | Maintains game state and checks for collisions, hazards, victory, or defeat |

---

## Scoring System

| Action | Score Change |
|--------|-------------|
| Each movement step | -1 |
| Hitting a wall | -5 |
| Collecting gold | +1000 |
| Collecting an arrow | +10 |
| Killing the Wumpus | +500 |
| Falling into a pit | Game over |
| Walking into the Wumpus | Game over |

---

## On-Screen Indicators

| Indicator | Meaning |
|-----------|---------|
| Breeze | A pit is adjacent to this tile |
| Stench | The Wumpus is adjacent to this tile |
| Safe Tile Highlight (green) | Tile confirmed safe by the AI agent |
| Agent Path Lines | Route calculated by A* pathfinding |

---

## Limitations

| Limitation | Detail |
|------------|--------|
| Fixed Grid Size | Only 8x8; limits environment complexity |
| Random Placement | Some worlds may be easier or harder than others |
| Basic AI Logic | AI uses structured reasoning, not advanced inference or learning |
| Different Win Conditions | Manual mode: kill Wumpus. AI mode: grab gold and return to start |
| Simple Graphics | Tkinter limits animation quality and visual fidelity |
| No Dynamic World | Environment does not change after initial generation |
| Fixed Scoring | Users cannot modify scoring rules |
| No Sound | No audio feedback due to library limitations |

---

## Project Structure

```
HiddenWumpusWorld/
|
|-- World.py                  # Main game file (grid, player, AI, GUI)
|-- README.md
|
|-- images/
|   |-- main_menu.png         # Main menu screenshot
|   |-- hud.png               # In-game HUD screenshot
|   |-- grid_environment.png  # Game world screenshot
|   |-- game_entities.png     # All entity sprites labeled
|   |-- inventory_before.png  # Inventory panel empty
|   |-- inventory_after.png   # Inventory panel with items
|   |-- ai_agent.png          # AI agent exploring the grid
```

---

## Getting Started

### Requirements

- Python 3.8 or higher
- Tkinter (included with standard Python installations)
- Pillow (for image rendering)

### Install Dependencies

```bash
pip install pillow
```

### Run the Game

```bash
python World.py
```

### Controls

| Key | Action |
|-----|--------|
| Arrow Keys | Move player (Up, Down, Left, Right) |
| Shift + Arrow Key | Shoot arrow in that direction |
| G | Grab item on current tile |
| A (button) | Activate AI agent |

---
