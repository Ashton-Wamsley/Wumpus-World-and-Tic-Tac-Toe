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
        "wumpus" : [2, 1]
    },
    "easy2": {
        "size" : 4,
        "start" : [0, 0],
        "goal" : [3, 0],
        "pits" : [[1, 1]],
        "wumpus" : [2, 2]
    },
    "hard1": {
        "size" : 4,
        "start" : [0, 0],
        "goal" : [3, 3],
        "pits" : [[1, 2], [2, 3]],
        "wumpus" : [2, 1]
    },
    "hard2": {
        "size" : 4,
        "start" : [0, 0],
        "goal" : [3, 3],
        "pits" : [[1, 0], [2, 2]],
        "wumpus" : [1, 3]
    }
}

class TicTacToe:
    def __init__(self):
        self.board = [" "] * 9
        self.trace = []
        self.nodes_evaluated = 0

    def available_moves(self, board = None):
        b = board or self.board
        return [i for i, v in enumerate(b) if v == " "]
    
    def winner(self, board = None):
        b = board or self.board
        lines = [
            (0,1,2),(3,4,5),(6,7,8),
            (0,3,6),(1,4,7),(2,5,8),
            (0,4,8),(2,4,6)
        ]
        for a,b1,c in lines:
            if board[a] != " " and board[a] == board[b1] == board[c]:
                return board[a]
        return None

    def terminal(self, board = None):
        b = board or self.board
        return self.winner(b) is not None or all(v != " " for v in b)
    
    def utility(self, board, ai):
        w = self.winner(board)
        if w == ai:
            return 1
        elif w is None and all(v != " " for v in board):
            return 0
        elif w is None:
            return None
        else:
            return -1
        
    def minimax(self, board, player, ai):
        self.nodes_evaluated += 1
        util = self.utility(board, ai)
        if util is not None:
            return util, None
        moves = self.available_moves(board)
        if player == ai:
            best_val = -float("inf")
            best_move = None
            for m in moves:
                new_board = board[:]
                new_board[m] = player
                val, _ = self.minimax(new_board, "O" if player == "X" else "X", ai)
                if val > best_val:
                    best_val, best_move = val, m
            return best_val, best_move
        else:
            best_val = float("inf")
            best_move = None
            for m in moves:
                new_board = board[:]
                new_board[m] = player
                val, _ = self.minimax(new_board, "O" if player == "X" else "X", ai)
                if val > best_val:
                    best_val, best_move = val, m
            return best_val, best_move
    
    def alphabeta(self, board, player, ai, alpha = -float("inf"), beta = float("inf")):
        self.nodes_evaluated += 1
        util = self.utility(board, ai)
        if util is not None:
            return util, None
        moves = self.available_moves(board)
        if player == ai:
            best_val = -float("inf")
            best_move = None
            for m in moves:
                new_board = board[:]
                new_board[m] = player
                val, _ = self.alphabeta(new_board, "O" if player == "X" else "X", ai, alpha, beta)
                if val > best_val:
                    best_val, best_move = val, m
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return best_val, best_move
        else:
            best_val = float("inf")
            best_move = None
            for m in moves:
                new_board = board[:]
                new_board[m] = player
                val, _ = self.alphabeta(new_board, "O" if player == "X" else "X", ai, alpha, beta)
                if val < best_val:
                    best_val, best_move = val, m
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return best_val, best_move
        
    def rand_opponent_move(self):
        return random.choice(self.available_moves())
    
    def scripted_opponent_moves(self):
        prefs = [4, 0, 2, 6, 8, 1, 3, 5, 7]
        moves = self.available_moves()
        for p in prefs:
            if p in moves:
                return p
        return moves[0]
    
    def play_game(self, config = "minimax", opponent = "random", ai = "X"):
        current = "X"
        self.trace = []
        self.nodes_evaluated = 0

        while not self.terminal():
            if current == ai:
                board_copy = self.board[:]
                if config == "alphabeta":
                    _, move = self.alphabeta(board_copy, ai, ai)
                else:
                    _, move = self.minimax(board_copy, ai, ai)
                self.board[move] = ai
                self.trace.append({"player" : ai, "move" : move, "board" : self.board[:]})
            else:
                if opponent == "random":
                    move = self.rand_opponent_move()
                else:
                    move = self.scripted_opponent_moves()
                self.board[move] = "O" if ai == "X" else "X"
                self.trace.append({"player" : "O" if ai == "X" else "X", "move": move, "board": self.board[:]})
            current = "O" if current == "X" else "X"
    
        util = self.utility(self.board, ai)
        if util == 1:
            result = "Win"
        elif util == 0:
            result = "Draw"
        else:
            result = "Loss"
        return {
            "result" : result,
            "moves_taken" : len([t for t in self.trace if "move" in t]),
            "nodes_evaluated" : self.nodes_evaluated,
            "trace" : self.trace,
        }


def run_wumpus(instance_id, config):
    layout = WUMPUS_LAYOUTS[instance_id]
    world = WumpusWorld(layout)
    agent = WumpusKBAgent(world)
    start = time.perf_counter()
    res = agent.run()
    end = time.perf_counter()
    output = {
        "problem" : "wumpus",
        "instance" : instance_id,
        "config" : config,
        "success" : res["success"],
        "runtime_ms" : (end - start) * 1000.0,
        "states_expanded" : res["states_expanded"],
        "moves_taken" : res["moves_taken"],
        "trace" : res["trace"]
    }
    return output

def run_tictactoe(instance_id, config):
    game = TicTacToe()
    start = time.perf_counter()
    res = game.play_game(config = config, opponent = instance_id)
    end = time.perf_counter()
    output = {
        "problem" : "tictactoe",
        "instance" : instance_id,
        "config" : config,
        "result" : res["result"],
        "runtime_ms" : (end - start) * 1000.0,
        "nodes_evaluated" : res["nodes_evaluated"],
        "moves_taken" : res["moves_taken"],
        "trace" : res["trace"],
    }
    return output

def json_path(base_name, out_dir = "results"):
    Path(out_dir).mkdir(parents = True, exist_yes = True)
    i = 1
    while True:
        candidate = Path(out_dir) / f"{base_name}_{i}.json"
        if not candidate.exists():
            return candidate
        i += 1

def save_json(result, out_dir = "results"):
    base = f"{result['problem']}_{result['instance']}_{result['config']}"
    path = json_path(base, out_dir)
    with open(path, "w") as f:
        json.dump(result, f, indent=2)
    return path



