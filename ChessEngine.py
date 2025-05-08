"""
This class is responsible for starting all the information
And determining the valid moves at the current state
Basically all of the background things
"""
import copy
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
        self.enPassantPossible = () # store the square of the pawn that can be captured by en passant
        self.currentCastlingRight = CastleRight(True, True, True, True)
        self.castleRightsLog = [copy.deepcopy(self.currentCastlingRight)]
        self.enPassantPossiblelog = [()]
    
    def makeMove(self, move):
        """
        Make a chess move.
        parameter:
        - move: the Move() object, to take the position, notation, etc.
        """
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.moveLog.append(move) #log the move so we can undo it later
        self.whiteToMove = not self.whiteToMove #switch players
        if move.pieceMoved == 'wK':
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == 'bK':
            self.blackKingLocation = (move.endRow, move.endCol)

        if move.pawnPromotion:
            promotionPiece = move.promotionChoice if move.promotionChoice else 'Q'  # Default to Queen
            self.board[move.endRow][move.endCol] = ('w' if move.pieceMoved == 'wp' else 'b') + promotionPiece
        
        #en passant
        if move.isEnPassantMove:
            self.board[move.startRow][move.endCol] = '--' #capturing the pawn

        #update enPassantPossible
        if move.pieceMoved[1] == 'p' and abs(move.startRow - move.endRow) == 2:
            self.enPassantPossible = ((move.startRow + move.endRow) // 2, move.startCol)
            self.enPassantPossiblelog.append((self.enPassantPossible[0], self.enPassantPossible[1]))
        else:
            self.enPassantPossible = ()
            self.enPassantPossiblelog.append(())
        
        #update castling rights - whenever it is a rook or a king move
        print(self.currentCastlingRight.wks, self.currentCastlingRight.bks, self.currentCastlingRight.wqs, self.currentCastlingRight.bqs)
        print("moving")
        for log in self.castleRightsLog:
            print(str(log.wks) + " " + str(log.bks) + " " + str(log.wqs) + " " + str(log.bqs), end = ",")
        print()        
        self.updateCastleRights(move)
        self.castleRightsLog.append(copy.deepcopy(self.currentCastlingRight))
        print(self.currentCastlingRight.wks, self.currentCastlingRight.bks, self.currentCastlingRight.wqs, self.currentCastlingRight.bqs)
        print("switch to undoing")
        #castle
        if move.isCastleMove:
            if move.endCol - move.startCol == 2: #Kingside castle move
                self.board[move.endRow][move.endCol - 1] = self.board[move.endRow][move.endCol + 1] #moves the rook
                self.board[move.endRow][move.endCol + 1] = "--"
            else:
                self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 2] #moves the rook
                self.board[move.endRow][move.endCol - 2] = "--"

    def updateCastleRights(self, move):
        """
        Update Castling right when a piece moved
        Parameters:
        move: move just made
        """
        if move.pieceMoved == "wK":
            self.currentCastlingRight.wks = False
            self.currentCastlingRight.wqs = False
        elif move.pieceMoved == "bK":
            self.currentCastlingRight.bks = False
            self.currentCastlingRight.bqs = False
        elif move.pieceMoved == "wR":
            if move.startRow == 7:
                if move.startCol == 0: # left rook
                    self.currentCastlingRight.wqs = False
                elif move.startCol == 7: #right took
                    self.currentCastlingRight.wks = False
        elif move.pieceMoved == "bR":
            if move.startRow == 0:
                if move.startCol == 0: # left rook
                    self.currentCastlingRight.bqs = False
                elif move.startCol == 7: #right took
                    self.currentCastlingRight.bks = False
        if move.pieceCaptured == "wR":
            if move.endRow == 7:
                if move.endCol == 0: # left rook
                    self.currentCastlingRight.wqs = False
                elif move.endCol == 7: #right took
                    self.currentCastlingRight.wks = False
        elif move.pieceCaptured == "bR":
            if move.endRow == 0:
                if move.endCol == 0: # left rook
                    self.currentCastlingRight.bqs = False
                elif move.endCol == 7: #right took
                    self.currentCastlingRight.bks = False

    
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

            #undo en passant
            if move.isEnPassantMove:
                self.board[move.endRow][move.endCol] = "--"
                self.board[move.startRow][move.endCol] = move.pieceCaptured
            self.enPassantPossiblelog.pop()
            self.enPassantPossible = copy.deepcopy(self.enPassantPossiblelog[-1])
            
            #undo castling right
            print(self.currentCastlingRight.wks, self.currentCastlingRight.bks, self.currentCastlingRight.wqs, self.currentCastlingRight.bqs)
            print("undoing")
            for log in self.castleRightsLog:
                print(str(log.wks) + " " + str(log.bks) + " " + str(log.wqs) + " " + str(log.bqs), end = ",")
            print()
            self.castleRightsLog.pop()
            self.currentCastlingRight = copy.deepcopy(self.castleRightsLog[-1])
            print(self.currentCastlingRight.wks, self.currentCastlingRight.bks, self.currentCastlingRight.wqs, self.currentCastlingRight.bqs)
            print("debug")
            #undo castle move
            if move.isCastleMove:
                if move.endCol - move.startCol == 2: #kingside
                    self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 1]
                    self.board[move.endRow][move.endCol - 1] = "--"
                else:
                    self.board[move.endRow][move.endCol - 2] = self.board[move.endRow][move.endCol + 1]
                    self.board[move.endRow][move.endCol + 1] = "--"

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
        Moves considering checks + castling
        """
        tempEnpassantPossible = self.enPassantPossible
        tempCastleRight = CastleRight(self.currentCastlingRight.wks, self.currentCastlingRight.bks,
                                      self.currentCastlingRight.wqs, self.currentCastlingRight.bqs)
        moves = self.getAllPossibleMoves()
        if self.whiteToMove:
            self.getCastleMoves(self.whiteKingLocation[0], self.whiteKingLocation[1], moves)
        else:
            self.getCastleMoves(self.blackKingLocation[0], self.blackKingLocation[1], moves)
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
        self.enPassantPossible = tempEnpassantPossible
        self.currentCastlingRight = tempCastleRight
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
                elif (r - 1, c - 1) == self.enPassantPossible:
                    moves.append(Move((r, c), (r - 1, c - 1), self.board, isEnPassantMove=True))
            if c + 1 < len(self.board):
                if self.board[r - 1][c + 1][0] == 'b':
                    moves.append(Move((r, c), (r - 1, c + 1), self.board))
                elif (r - 1, c + 1) == self.enPassantPossible:
                    moves.append(Move((r, c), (r - 1, c + 1), self.board, isEnPassantMove=True))
        else: #black pawns
            if self.board[r + 1][c] == "--": # one-square advance
                moves.append(Move((r, c), (r + 1, c), self.board))
                if r == 1 and self.board[r + 2][c] == "--": #two-square advance
                    moves.append(Move((r, c), (r + 2, c), self.board))
            # enemy capture pieces
            if c - 1 >= 0:
                if self.board[r + 1][c - 1][0] == 'w': 
                    moves.append(Move((r, c), (r + 1, c - 1), self.board))
                elif (r + 1, c - 1) == self.enPassantPossible:
                    moves.append(Move((r, c), (r + 1, c - 1), self.board, isEnPassantMove=True))
            if c + 1 < len(self.board):
                if self.board[r + 1][c + 1][0] == 'w':
                    moves.append(Move((r, c), (r + 1, c + 1), self.board))
                elif (r + 1, c + 1) == self.enPassantPossible:
                    moves.append(Move((r, c), (r + 1, c + 1), self.board, isEnPassantMove=True))

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
    
    def getCastleMoves(self, r, c, moves):
        """
        Generate all valid castle move at r, c in curr_turn color
        Parameters:
        r: Row
        c: Column
        moves: move list
        curr_turn: current color this turn
        """
        if self.inCheck():
            return #can't castle while checked

        #Kingside Castle Moves
        if (self.whiteToMove and self.currentCastlingRight.wks) or (not self.whiteToMove and self.currentCastlingRight.bks):
            if self.board[r][c + 1] == "--" and self.board[r][c + 2] == "--":
                if not self.squareUnderAttack(r, c + 1) and not self.squareUnderAttack(r, c + 2):
                    moves.append(Move((r, c), (r, c + 2), self.board, isCastleMove=True))

        #Queenside Castle Moves           
        if (self.whiteToMove and self.currentCastlingRight.wqs) or (not self.whiteToMove and self.currentCastlingRight.bqs):
            if self.board[r][c - 1] == "--" and self.board[r][c - 2] == "--":
                if not self.squareUnderAttack(r, c - 1) and not self.squareUnderAttack(r, c - 2):
                    moves.append(Move((r, c), (r, c - 2), self.board, isCastleMove=True))
class Move():
    """
    This is get the information to move the pieces, init takes in parameters:
    - startSquare: the initial square
    - endSquare: the goal square
    - board: the current board
    - isEnPassantMove: check if en passant move is possible
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


    def __init__(self, startSquare, endSquare, board, isEnPassantMove = False, isCastleMove = False, promotionChoice = None):
        self.startRow = startSquare[0]
        self.startCol = startSquare[1]
        self.endRow = endSquare[0]
        self.endCol = endSquare[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol

        #pawn promotion
        self.pawnPromotion = (self.pieceMoved == 'wp' and self.endRow == 0) or (self.pieceMoved == 'bp' and self.endRow == 7)
        self.promotionChoice = promotionChoice

        #en passant
        self.isEnPassantMove = isEnPassantMove
        if self.isEnPassantMove:
            self.pieceCaptured = "wp" if self.pieceMoved == "bp" else "bp"

        #castling
        self.isCastleMove = isCastleMove

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



class CastleRight():
    """
    For castling moves
    constructor parameters:
    wks: white king side
    wqs: white queen side
    bks: black king side
    bqs: black queen side
    """
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs
