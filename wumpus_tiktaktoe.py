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
        