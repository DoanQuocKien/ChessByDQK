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
    def makeMove(self, move):
        """
        Make a chess move.
        input:
        - move: the Move() object, to take the position, notation, etc.
        """
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.moveLog.append(move) #log the move so we can undo it later
        self.whiteToMove = not self.whiteToMove #switch players
class Move():
    """
    This is get the information to move the pieces, with the init takes in:
    - startSquare: the initial square
    - endSquare: the goal square
    - board: the current board
    """


    """
    Dictionaries from ranks to rows and from files to columns and vice versa
    """
    ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4,
                   "5": 3, "6": 2, "7": 1, "8": 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}
    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3,
                   "e": 4, "f": 5, "g": 6, "h": 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}
    def __init__(self, startSquare, endSquare, board):
        self.startRow = startSquare[0]
        self.startCol = startSquare[1]
        self.endRow = endSquare[0]
        self.endCol = endSquare[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
    
    def getChessNotation(self):
        # note: the order of coding and chess notation is reversed (row, col) -> (file, rank)
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)
    def getRankFile(self, r, c):
        """
        transcribe from row, column to rank, file (from code language to proper chess notation)
        input:
        - self
        - r: row
        - c: column
        output:
        - respective rank and file
        """
        return self.colsToFiles[c], self.rowsToRanks[r]
    
