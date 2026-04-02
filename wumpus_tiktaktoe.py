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
    
    def is_pit(self, cell):
        return cell in self.pits
    
class WumpusKBAgent:
    def __init__(self, world):
        self.world = world
        self.sp = world.start
        self.alive = True
        self.goal_reached = False
        self.visited = set()
        self.safe = set([self.sp])
        self.no_pit = set([self.sp])
        self.no_wumpus = set([self.sp])
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
                self.no_pit.add(n)
                self.safe.add(n)
                self.possible_pit.discard(n)
        else:
            for n in adjacent:
                if n not in self.no_pit:
                    self.possible_pit.add(n)
        
        if not stench:
            for n in adjacent:
                self.no_wumpus.add(n)
                self.safe.add(n)
                self.possible_wumpus.discard(n)
        else:
            for n in adjacent:
                if n not in self.no_wumpus:
                    self.possible_wumpus.add(n)

        for n in adjacent:
            if n in self.no_pit and n in self.no_wumpus:
                self.safe.add(n)

    def choose_move(self):
        self.states_expanded += 1
        neighbors = list(self.world.neighbors(self.sp))

        safe_unvisited = [c for c in neighbors if c in self.safe and c not in self.visited]
        if safe_unvisited:
            return safe_unvisited[0]

        safe_visited = [c for c in neighbors if c in self.safe]
        if safe_visited:
            return safe_visited[0]

        unknown = [
            c for c in neighbors
            if c not in self.safe
            and c not in self.possible_pit
            and c not in self.possible_wumpus
        ]
        if unknown:
            return unknown[0]

        risky = [
            c for c in neighbors
            if c not in self.possible_pit and c not in self.possible_wumpus
        ]
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
            self.goal_reached = True
            return False
        move = self.choose_move()
        if move is None:
            return False
        self.sp = move
        if self.world.is_pit(self.sp) or self.world.is_wumpus(self.sp):
            self.alive = False
            self.trace.append({"sp" : self.sp, "event" : "death"})
            return False
        return True
    
    def run(self, max_steps = 100):
        steps = 0
        while steps < max_steps and self.alive and not self.goal_reached:
            cont = self.step()
            if not cont:
                break
            steps += 1

        return {
            "success" : self.alive and self.goal_reached,
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
        for a, b1, c in lines:
            if b[a] != " " and b[a] == b[b1] == b[c]:
                return b[a]
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
                if val < best_val:
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
    
    def scripted_opponent_move(self):
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
                    move = self.scripted_opponent_move()
                self.board[move] = "O" if ai == "X" else "X"
                self.trace.append({"player" : "O" if ai == "X" else "X", "move": move, "board": self.board[:]})
            current = "O" if current == "X" else "X"
    
        util = self.utility(self.board, ai)
        if util == 1:
            result = "win"
        elif util == 0:
            result = "draw"
        else:
            result = "loss"
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

def test_percept_rules():
    layout = {
        "size" : 4,
        "start" : [0, 0],
        "goal" : [3, 3],
        "pits" : [[1, 0]],
        "wumpus" : [0, 1],
    }
    world = WumpusWorld(layout)

    p = world.percept((0,0))
    assert p["breeze"] is True
    assert p["stench"] is True

    p2 = world.percept((2,2))
    assert p2["breeze"] is False
    assert p2["stench"] is False

def test_kb_updates():
    layout = WUMPUS_LAYOUTS["easy1"]
    world = WumpusWorld(layout)
    agent = WumpusKBAgent(world)

    percept = world.percept(agent.sp)
    agent.update_kb(agent.sp, percept)

    assert agent.sp in agent.safe
    assert agent.sp in agent.no_pit
    assert agent.sp in agent.no_wumpus

    if not percept["breeze"]:
        for n in world.neighbors(agent.sp):
            assert n in agent.no_pit
    if not percept["stench"]:
        for n in world.neighbors(agent.sp):
            assert n in agent.no_wumpus

def test_agent_avoids_known_unsafe():
    layout = WUMPUS_LAYOUTS["easy1"]
    world = WumpusWorld(layout)
    agent = WumpusKBAgent(world)

    neighbors = list(world.neighbors(agent.sp))
    bad = neighbors[0]
    agent.possible_pit.add(bad)

    move = agent.choose_move()
    assert move != bad, "AI should not move into a known unsafe space"

def test_legal_moves():
    game = TicTacToe()
    game.board = [
        "X","O","X",
        " ","O"," ",
        " "," ","X"
    ]
    assert game.available_moves() == [3,5,6,7]

def test_terminal_states():
    game = TicTacToe()

    game.board = ["X","X","X"," "," "," "," "," "," "]
    assert game.terminal() is True
    assert game.winner() == "X"

    game.board = [
        "X","O","X",
        "X","O","O",
        "O","X","X"
    ]
    assert game.terminal() is True
    assert game.winner() is None

    game.board = [
        "X","O","X",
        " ","O"," ",
        " "," ","X"
    ]
    assert game.terminal() is False

def test_minimax_optimal_move():
    game = TicTacToe()
    game.board = [
        "X","X"," ",
        "O","O"," ",
        " "," "," "
    ]
    _, move = game.minimax(game.board[:], "X", "X")
    assert move == 2, f"Minimax should choose winning move 2, got {move}"

def run_all_tests():
    print("\nRunning Wumpus tests.")
    test_percept_rules()
    test_kb_updates()
    test_agent_avoids_known_unsafe()
    print("Wumpus tests passed.")

    print("\nRunning Tic-Tac-Toe tests.")
    test_legal_moves()
    test_terminal_states()
    test_minimax_optimal_move()
    print("Tic-Tac-Toe tests passed.")

    print("\nAll tests passed successfully.\n")

def json_path(base_name, out_dir = "results"):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--problem", choices = ["wumpus", "tictactoe"])
    parser.add_argument("--instance")
    parser.add_argument("--config")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--run-tests", action = "store_true")
    args = parser.parse_args()

    if args.run_tests:
        run_all_tests()
        return

    if args.problem is None or args.instance is None or args.config is None:
        raise ValueError("Must specify --problem, --instance, and --config unless using --run-tests")

    if args.seed is not None:
        random.seed(args.seed)

    if args.problem == "wumpus":
        if args.config != "kb":
            raise ValueError("Wumpus only supports config 'kb'")
        if args.instance not in WUMPUS_LAYOUTS:
            raise ValueError(f"Unknown Wumpus instance {args.instance}")
        result = run_wumpus(args.instance, args.config)
    else:
        if args.config not in ["minimax", "alphabeta"]:
            raise ValueError("Tic-Tac-Toe config must be 'minimax' or 'alphabeta'")
        if args.instance not in ["random", "scripted"]:
            raise ValueError("Tic-Tac-Toe instance must be 'random' or 'scripted'")
        result = run_tictactoe(args.instance, args.config)

    print(json.dumps(result, indent=2))
    path = save_json(result)
    print(f"Saved to {path}")

if __name__ == "__main__":
    main()
