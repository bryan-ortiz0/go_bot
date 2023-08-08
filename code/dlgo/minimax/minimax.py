import enum
import random

from dlgo.agent import Agent

__all__ = [
    'MinimaxAgent',
]

# Create Game Result Class

# This class represents the outcome of a game
class GameResult(enum.Enum):
    loss = 1
    draw = 2
    win = 3
    
def best_result(game_state):
    if game_state.is_over():
        if game_state.winner() == game_state.next_player:
            # We Won
            return GameResult.win 
        elif game_state.winner() is None:
            # A Draw
            return GameResult.draw 
        else:
            # We Lost
            return GameResult.loss 
    
    best_result_so_far = GameResult.loss
    for candidate_move in game_state.legal_moves():
        # See what the board would look like if you play this move
        next_state = game_state.apply_move(candidate_move) 
        # Find out your opponents best move
        opponent_best_result = best_result(next_state) 
        # Whatever your opponent wants, you want the opposite
        our_result = reverse_game_result(opponent_best_result) 
        # See if this result is better than the best you've seen so far
        if our_result.value > best_result_so_far.value: 
            best_result_so_far = our_result
    return best_result_so_far

# Create Minimax Agent Class

# This class represents a game-playing agent that implements Minimax Search
class MinimaxAgent(Agent):
    def select_move(self, game_state):
        winning_moves = []
        draw_moves = []
        losing_moves = []
        # Loops over all legal moves
        for possible_move in game_state.legal_moves(): 
            # Calculates the game state if you select this move
            next_state = game_state.apply_move(possible_move) 
            opponent_best_outcome = best_result(next_state)
            our_best_outcome = reverse_game_result(opponent_best_outcome)
            if our_best_outcome == GameResult.win:
                winning_moves.append(possible_move)
            elif our_best_outcome == GameResult.draw:
                draw_moves.append(possible_move)
            else:
                losing_moves.append(possible_move)
        if winning_moves:
            return random.choice(winning_moves)
        if draw_moves:
            return random.choice(draw_moves)
        return random.choice(losing_moves)