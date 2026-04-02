This project implements two AI problems:
- Wumpus World using a Knowledge Based Agent
- Tic‑Tac‑Toe using Minimax and Alpha‑Beta Pruning
##The program supports running individual problem instances, saving results as JSON, and running a built in tests.
#How to run:
###All commands are executed from the terminal: ex. python wumpus_tictactoe.py [options]
#Wumpus:
###Wumpus only supports the kb config and has 4 available wumpus instances, easy1, easy2, hard1, and hard2.
##Wumpus Example:
###python wumpus_tictactoe.py --problem wumpus --instance easy1 --config kb
#Tic-Tac-Toe:
###Tic-Tac-Toe supports 2 configs (minimax and alphabeta) and has 2 available instances/opponent types, random and scripted.
##Tic-Tac-Toe Example:
###python wumpus_tictactoe.py --problem tictactoe --instance random --config minimax
##Run Tests Example:
###python wumpus_tictactoe.py --run-tests
