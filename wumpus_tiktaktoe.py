import argparse
import json
import random
import time
from pathlib import Path

class WumpusWorld:
    def __init__(self, layout):
        self.size = layout["size"]
        self.start = tuple(layout["start"])
        self.goal = tuple(layout["goal"])
        self.pits = {tuple(p) for p in layout["pits"]}
        self.wumpus = tuple(layout["wumpus"])

    def in_map(self, cell):
        x, y = cell
        return 0 <= x < self.size and 0 <= y < self.size
   
    def neighbors(self, cell):
        x, y = cell
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            n = (x + dx, y + dy)
            if self.in_map(n):
                yield n

    def percept(self, cell):
        breeze = any(n in self.pits for n in self.neighbors(cell))
        stench = any(n == self.wumpus for n in self.neighbors(cell))
        return {"breeze" : breeze, "stench" : stench}
    
    def is_wumpus(self, cell):
        return cell == self.wumpus
    
class WumpusKBAgent:
    def __init__(self, world):
        self.world = world
        self.sp = world.start
        self.alive = True
        self.goal_reached = False
        self.visited = set()
        self.safe = set([self.ps])
        self.no_pit = set([self.ps])
        self.no_wumpus = set([self.ps])
        self.possible_pit = set()
        self.possible_wumpus = set()
        self.trace = []
        self.states_expanded = 0

    def update_kb(self, cell, percept):
        self.visited.add(cell)
        breeze = percept["breeze"]
        stench = percept["stench"]
        adjacent = list(self.world.neighbors(cell))

        if not breeze:
            for n in adjacent:
                self.no_wumpus.add(n)
                self.safe.add(n)
                if n in self.possible_wumpus:
                    self.possible_wumpus.remove(n)
        else:
            for n in adjacent:
                if n not in self.no_wumpus and n not in self.safe:
                    self.possible_wumpus.add(n)

        for n in adjacent:
            if n in self.no_pit and n in self.no_wumpus:
                self.safe.add(n)

    def choose_move(self):
        self.states_expanded += 1

        possible_moves = list(self.world.neighbors(self.ps))
        safe_unvisited = [c for c in possible_moves if c in self.safe and c not in self.visited]
        if safe_unvisited:
            return safe_unvisited[0]
        
        safe_visited = [c for c in possible_moves if c in self.safe]
        if safe_visited:
            return safe_visited[0]
        
        unknown = [
            c for c in possible_moves
            if c not in self.safe
            and c not in self.possible_pit
            and c not in self.possible_wumpus
        ]
        if unknown:
            return unknown[0]
        
        risky = [
            c for c in possible_moves
            if c not in self.possible_pit and c not in self.possible_wumpus
        ]
        if risky:
            return risky[0] if risky else None

    def step(self):
        percept = self.world.percept(self.sp)
        self.update_kb(self.sp, percept)
        self.trace.append({
            "sp" : self.sp,
            "percept" : percept,
            "safe" : sorted(list(self.safe)),
            "visited" : sorted(list(self.visited))
        })
        if self.sp == self.world.goal:
            self.reached_goal = True
            return False
        move = self.choose_move()
        if move is None:
            return False
        self.sp = move
        if self.world.is_pit(self.sp) or self.world.is_wumpus(self.sp):
            self.alive = False
            self.trace.append({"sp"} : self.sp, "event" : "death")
            return False
        return True
    
    def run(self, max_steps = 100):
        steps = 0
        while steps < max_steps and self.alive and not self.reached_goal:
            cont = self.step()
            if not cont:
                break
            steps += 1

        return {
            "success" : self.alive and self.reached_goal,
            "moves_taken" : steps + 1,
            "states_expanded" : self.states_expanded,
            "trace" : self.trace
        }
    
WUMPUS_LAYOUTS = {
    "easy1": {
        "size" : 4,
        "start" : [0, 0],
        "goal" : [3, 3],
        "pits" : [[1, 2]],
        "wumpus" : [2, 1],
    },
    "easy2": {
        "size" : 4,
        "start" : [0, 0],
        "goal" : [3, 0],
        "pits" : [[1, 1]],
        "wumpus" : [2, 2],
    },
    "hard1": {
        "size" : 4,
        "start" : [0, 0],
        "goal" : [3, 3],
        "pits" : [[1, 2], [2, 3]],
        "wumpus" : [2, 1],
    },
    "hard2": {
        "size" : 4,
        "start" : [0, 0],
        "goal" : [3, 3],
        "pits" : [[1, 0], [2, 2]],
        "wumpus" : [1, 3],
    }
}

class TicTacToe:
