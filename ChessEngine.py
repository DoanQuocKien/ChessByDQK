"""
This class is responsible for starting all the information
And determining the valid moves at the current state
Basically all of the background things
"""
class GameState():
    """
    This class tracks the current state of the game
    """
    def __init__(self):
        """
        The chess board is and 8x8 2D list, each elements have two characters
        The first character represents the color of the pieces
        The second character represents the type of the pieces
        "--" is an empty space
        """
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"],
        ]
        self.whiteToMove = True
        self.moveLog = []
        