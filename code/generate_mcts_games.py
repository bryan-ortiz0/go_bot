import argparse
import numpy as np

from dlgo.encoders import get_encoder_by_name
from dlgo import goboard_fast as goboard
from dlgo import mcts
from dlgo.utils import print_board, print_move




def generate_game(board_size, rounds, max_moves, temperature):
    # In 'boards' the encoded board state is stored, 'moves' is for 
    # encoded moves
    boards, moves = [], []

    # Initialize a OnePlaneEncoder by name with given board size
    encoder = get_encoder_by_name('oneplane', board_size)

    # New game of size 'board_size' is instantiated
    game = goboard.GameState.new_game(board_size)

    # MCTS agent with specified number of rounds and temp will serve as bot
    bot = mcts.MCTSAgent(rounds, temperature)

    num_moves = 0
    while not game.is_over():
        print_board(game.board)
        # Next move is selected by bot
        move = bot.select_move(game)
        if move.is_play:
            # Encoded board situation is appended to 'board'
            boards.append(encoder.encode(game))

            move_one_hot = np.zeros(encoder.num_points())
            move_one_hot[encoder.encode_point(move.point)] = 1
            # OHE next move is appended to 'board'
            moves.append(move_one_hot)

        print_move(game.next_player, move)
        # Bot move is applied to the board
        game = game.apply_move(move)
        num_moves += 1
        # Continue with next move, unless max number of moves has been reached
        if num_moves > max_moves:
            break

    return np.array(boards), np.array(moves)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--board-size', '-b', type=int, default=9)
    parser.add_argument('--rounds', '-r', type=int, default=1000)
    parser.add_argument('--temperature', '-t', type=float, default=0.8)
    parser.add_argument('--max-moves', '-m', type=int, default=60,
                        help='Max moves per game.')
    parser.add_argument('--num-games', '-n', type=int, default=10)
    parser.add_argument('--board-out')
    parser.add_argument('--move-out')

    # Application allows some customiazation via CLI
    args = parser.parse_args()
    xs = []
    ys = []

    for i in range(args.num_games):
        print('Generating game %d/%d...' % (i + 1, args.num_games))
        # Specified number of games we generate game data
        x, y = generate_game(args.board_size, args.rounds, args.max_moves, args.temperature)
        xs.append(x)
        ys.append(y)

    # After all games have been generated, concatenate features and labels
    x = np.concatenate(xs)
    y = np.concatenate(ys)

    # Store features and label data to separate files, as specified by CLI
    np.save(args.board_out, x)
    np.save(args.move_out, y)


if __name__ == '__main__':
    main()