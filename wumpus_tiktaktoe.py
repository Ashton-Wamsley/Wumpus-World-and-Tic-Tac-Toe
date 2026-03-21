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
    