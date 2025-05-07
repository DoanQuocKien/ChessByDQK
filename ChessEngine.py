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
        self.moveFunctions = {'p': self.getPawnMoves, 'R': self.getRookMoves, 'N': self.getKnightMoves,
                              'B': self.getBishopMoves, 'Q': self.getQueenMoves, 'K': self.getKingMoves}
        self.whiteKingLocation = (7, 4) # for checking if the king is in check
        self.blackKingLocation = (0, 4) # for checking if the king is in check
        self.checkMate = False # checkmate or not
        self.staleMate = False # stalemate or not

    def makeMove(self, move):
        """
        Make a chess move.
        parameter:
        - move: the Move() object, to take the position, notation, etc.
        """
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.moveLog.append(move) #log the move so we can undo it later
        if move.pieceMoved == 'wK':
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == 'bK':
            self.blackKingLocation = (move.endRow, move.endCol)
        self.whiteToMove = not self.whiteToMove #switch players

    def undoMove(self):
        """
        Undo the last move made
        """
        if len(self.moveLog) != 0:
            move = self.moveLog.pop()
            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            if move.pieceMoved == 'wK':
                self.whiteKingLocation = (move.startRow, move.startCol)
            elif move.pieceMoved == 'bK':
                self.blackKingLocation = (move.startRow, move.startCol)
            self.whiteToMove = not self.whiteToMove #switch players

    def squareUnderAttack(self, r, c):
        """
        Check if the square is under attack by the opponent
        Parameters:
        r, c: row and column of the square to check
        """
        self.whiteToMove = not self.whiteToMove #switch players
        # check if the square is under attack by the opponent
        oppMoves = self.getAllPossibleMoves()
        self.whiteToMove = not self.whiteToMove #switch players back
        for move in oppMoves:
            if move.endRow == r and move.endCol == c:
                return True
        return False

    def getValidMoves(self):
        """
        Moves considering checks
        """
        moves = self.getAllPossibleMoves()
        for i in range(len(moves) - 1, -1, -1):
            self.makeMove(moves[i])
            self.whiteToMove = not self.whiteToMove
            if self.inCheck():
                moves.remove(moves[i])
            self.whiteToMove = not self.whiteToMove
            self.undoMove()
        if len(moves) == 0: #either checkmate or stalemate
            if self.inCheck():
                self.checkMate = True
            else:
                self.staleMate = True
        else:
            self.checkMate = False
            self.staleMate = False
        
        return moves
    
    def inCheck(self):
        """
        Check if the current player is in check
        """
        if self.whiteToMove:
            return self.squareUnderAttack(self.whiteKingLocation[0], self.whiteKingLocation[1])
        else:
            return self.squareUnderAttack(self.blackKingLocation[0], self.blackKingLocation[1])

    def getAllPossibleMoves(self):
        """
        Moves not considering checks
        """
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == 'w' and self.whiteToMove) or (turn == 'b' and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    self.moveFunctions[piece](r, c, moves)
        return moves

    def getPawnMoves(self, r, c, moves):
        """
        Generate all possible moves for pawn.
        Parameters:
        r, c:  row and column as positions
        moves: list of moves
        """
        if self.whiteToMove: # white pawns
            if self.board[r - 1][c] == "--": # one-square advance
                moves.append(Move((r, c), (r - 1, c), self.board))
                if r == 6 and self.board[r - 2][c] == "--": #two-square advance
                    moves.append(Move((r, c), (r - 2, c), self.board))
            # enemy capture pieces
            if c - 1 >= 0:
                if self.board[r - 1][c - 1][0] == 'b': 
                    moves.append(Move((r, c), (r - 1, c - 1), self.board))
            if c + 1 < len(self.board):
                if self.board[r - 1][c + 1][0] == 'b':
                    moves.append(Move((r, c), (r - 1, c + 1), self.board))
        else: #black pawns
            if self.board[r + 1][c] == "--": # one-square advance
                moves.append(Move((r, c), (r + 1, c), self.board))
                if r == 1 and self.board[r + 2][c] == "--": #two-square advance
                    moves.append(Move((r, c), (r + 2, c), self.board))
            # enemy capture pieces
            if c - 1 >= 0:
                if self.board[r + 1][c - 1][0] == 'w': 
                    moves.append(Move((r, c), (r + 1, c - 1), self.board))
            if c + 1 < len(self.board):
                if self.board[r + 1][c + 1][0] == 'w':
                    moves.append(Move((r, c), (r + 1, c + 1), self.board))

    def getRookMoves(self, r, c, moves):
        """
        Generate all possible moves for rook.
        Parameters:
        r, c:  row and column as positions
        moves: list of moves
        """
        curr_turn = 'b'
        op_turn = 'w'
        if self.whiteToMove:
            curr_turn = 'w'
            op_turn = 'b'
        for cur_c in range(c + 1, 8): # move to the right
            if self.board[r][cur_c][0] == curr_turn:
                break
            moves.append(Move((r, c), (r, cur_c), self.board))
            if self.board[r][cur_c][0] == op_turn:
                break
        for cur_c in range(c - 1, -1, -1): # move to the left
            if self.board[r][cur_c][0] == curr_turn:
                break
            moves.append(Move((r, c), (r, cur_c), self.board))
            if self.board[r][cur_c][0] == op_turn:
                break
        for cur_r in range(r + 1, 8): # move down
            if self.board[cur_r][c][0] == curr_turn:
                break
            moves.append(Move((r, c), (cur_r, c), self.board))
            if self.board[cur_r][c][0] == op_turn:
                break
        for cur_r in range(r - 1, -1, -1): # move up
            if self.board[cur_r][c][0] == curr_turn:
                break
            moves.append(Move((r, c), (cur_r, c), self.board))
            if self.board[cur_r][c][0] == op_turn:
                break

    def insideBoard(self, r, c):
        """
        return if a square is inside the board
        Parameters:
        r, c: row and column need checking
        """
        if r < 0 or c < 0 or r >= len(self.board) or c >= len(self.board):
            return False
        return True
    
    def getKnightMoves(self, r, c, moves):
        """
        Generate all possible moves for knight.
        Parameters:
        r, c:  row and column as positions
        moves: list of moves
        """
        curr_turn = 'b'
        if self.whiteToMove:
            curr_turn = 'w'
        directions = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)] #L-shaped moves
        for i in directions:
            if self.insideBoard(r + i[0], c + i[1]):
                if self.board[r + i[0]][c + i[1]][0] != curr_turn:
                    moves.append(Move((r, c), (r + i[0], c + i[1]), self.board))

    def getBishopMoves(self, r, c, moves):
        """
        Generate all possible moves for knight.
        Parameters:
        r, c:  row and column as positions
        moves: list of moves
        """
        curr_turn = 'b'
        op_turn = 'w'
        if self.whiteToMove:
            curr_turn = 'w'
            op_turn = 'b'
        # Move down-right
        currRow = r + 1
        currColumn = c + 1
        while self.insideBoard(currRow, currColumn):
            if self.board[currRow][currColumn][0] == curr_turn:
                break
            moves.append(Move((r, c), (currRow, currColumn), self.board))
            if self.board[currRow][currColumn][0] == op_turn:
                break
            currRow += 1
            currColumn += 1
        
        #Move down-left
        currRow = r + 1
        currColumn = c - 1
        while self.insideBoard(currRow, currColumn):
            if self.board[currRow][currColumn][0] == curr_turn:
                break
            moves.append(Move((r, c), (currRow, currColumn), self.board))
            if self.board[currRow][currColumn][0] == op_turn:
                break
            currRow += 1
            currColumn -= 1

        #Move up-right
        currRow = r - 1
        currColumn = c + 1
        while self.insideBoard(currRow, currColumn):
            if self.board[currRow][currColumn][0] == curr_turn:
                break
            moves.append(Move((r, c), (currRow, currColumn), self.board))
            if self.board[currRow][currColumn][0] == op_turn:
                break
            currRow -= 1
            currColumn += 1
        
        #Move up-left
        currRow = r - 1
        currColumn = c - 1
        while self.insideBoard(currRow, currColumn):
            if self.board[currRow][currColumn][0] == curr_turn:
                break
            moves.append(Move((r, c), (currRow, currColumn), self.board))
            if self.board[currRow][currColumn][0] == op_turn:
                break
            currRow -= 1
            currColumn -= 1
    def getQueenMoves(self, r, c, moves):
        """
        Generate all possible moves for queen. Since queen are basically rook and bishop combine, we could just get the rook and bishop moves at this piece
        Parameters:
        r, c:  row and column as positions
        moves: list of moves
        """
        self.getRookMoves(r, c, moves)
        self.getBishopMoves(r, c, moves)

    def getKingMoves(self, r, c, moves):
        """
        Generate all possible moves for king.
        Parameters:
        r, c:  row and column as positions
        moves: list of moves
        """
        curr_turn = 'b'
        if self.whiteToMove:
            curr_turn = 'w'
        directions = [(0, 1), (0, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (1, 1), (1, -1)] #one-space moves
        for i in directions:
            if self.insideBoard(r + i[0], c + i[1]):
                if self.board[r + i[0]][c + i[1]][0] != curr_turn:
                    moves.append(Move((r, c), (r + i[0], c + i[1]), self.board))
        
class Move():
    """
    This is get the information to move the pieces, init takes in parameters:
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
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def getChessNotation(self):
        # note: the order of coding and chess notation is reversed (row, col) -> (file, rank)
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)
    
    
    def getRankFile(self, r, c):
        """
        transcribe from row, column to rank, file (from code language to proper chess notation)
        parameters:
        - self
        - r: row
        - c: column
        function return:
        - respective rank and file
        """
        return self.colsToFiles[c], self.rowsToRanks[r]
    
