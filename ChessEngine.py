"""
ChessEngine.py

Contains the GameState class and logic for chess rules, move generation, and validation.

Author: Doan Quoc Kien
"""

import numpy as np
import copy

class GameState:
    """
    Represents the current state of a chess game.

    Attributes:
        board (list): 2D list representing the board.
        whiteToMove (bool): True if it's white's turn.
        moveLog (list): List of moves made and .
        whiteKingLocation (tuple): (row, col) of the white king.
        blackKingLocation (tuple): (row, col) of the black king.
        checkMate (bool): True if the game is in checkmate.
        draw (bool): True if the game is a draw.
        enPassantPossible (tuple): If it's not None type, there is an en passant move available at (row, col)
        currentCastlingRight (class): Handling castle right of White king side, Black king side, White queen side, and Blak queen side
        enPassantPossibleLog (list): List of history of possible en passant for each move
        positionCounts (dict): Count the number of repeating move, mostly for checking three-fold-repetition
        fiftyMoveCounter (int): Count the number of move for checking draw by fifty-mive rule
    """

    def __init__(self):
        """
        Initializes the game state.
        """
        self.board = np.array([
            [24, 22, 23, 25, 26, 23, 22, 24],
            [21, 21, 21, 21, 21, 21, 21, 21],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [11, 11, 11, 11, 11, 11, 11, 11],
            [14, 12, 13, 15, 16, 13, 12, 14],
        ])
        self.whiteToMove = True
        self.moveLog = []
        self.moveFunctions = {1: self.getPawnMoves, 4: self.getRookMoves, 2: self.getKnightMoves,
                              3: self.getBishopMoves, 5: self.getQueenMoves, 6: self.getKingMoves}
        self.whiteKingLocation = (7, 4)  # for checking if the king is in check
        self.blackKingLocation = (0, 4)  # for checking if the king is in check
        self.checkMate = False  # checkmate or not
        self.draw = False  # draw or not
        self.enPassantPossible = ()  # store the square of the pawn that can be captured by en passant
        self.currentCastlingRight = CastleRight(True, True, True, True)
        self.castleRightsLog = [CastleRight(
            self.currentCastlingRight.wks,
            self.currentCastlingRight.bks,
            self.currentCastlingRight.wqs,
            self.currentCastlingRight.bqs
        )]
        self.enPassantPossibleLog = [()]
        self.positionCounts = {self.getBoardHash(): 1}
        self.fiftyMoveCounter = 0

    def makeMove(self, move):
        """
        Executes a move on the board.

        Parameters:
            move (Move): The move to make.

        Returns:
            None
        """
        self.board[move.startRow][move.startCol] = 0
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.whiteToMove = not self.whiteToMove  # switch players
        if move.pieceMoved == 16:
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == 26:
            self.blackKingLocation = (move.endRow, move.endCol)

        if move.pawnPromotion:
            promotionPiece = move.promotionChoice if move.promotionChoice else 5  # Default to Queen
            self.board[move.endRow][move.endCol] = (10 if move.pieceMoved == 11 else 20) + promotionPiece

        # en passant
        if move.isEnPassantMove:
            self.board[move.startRow][move.endCol] = 0  # capturing the pawn

        # update enPassantPossible
        if move.pieceMoved % 10 == 1 and abs(move.startRow - move.endRow) == 2:
            self.enPassantPossible = ((move.startRow + move.endRow) // 2, move.startCol)
            self.enPassantPossibleLog.append((self.enPassantPossible[0], self.enPassantPossible[1]))
        else:
            self.enPassantPossible = ()
            self.enPassantPossibleLog.append(())

        # update castling rights - whenever it is a rook or a king move
        self.updateCastleRights(move)
        self.castleRightsLog.append(CastleRight(
            self.currentCastlingRight.wks,
            self.currentCastlingRight.bks,
            self.currentCastlingRight.wqs,
            self.currentCastlingRight.bqs
        ))

        # castle
        if move.isCastleMove:
            if move.endCol - move.startCol == 2:  # Kingside castle move
                self.board[move.endRow][move.endCol - 1] = self.board[move.endRow][move.endCol + 1]  # moves the rook
                self.board[move.endRow][move.endCol + 1] = 0
            else:
                self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 2]  # moves the rook
                self.board[move.endRow][move.endCol - 2] = 0

        # Update position counts for threefold repetition
        boardString = self.getBoardHash()
        if boardString in self.positionCounts:
            self.positionCounts[boardString] += 1
        else:
            self.positionCounts[boardString] = 1

        # Update fifty-move counter
        if move.pieceMoved % 10 == 1 or move.pieceCaptured != 0:
            self.fiftyMoveCounter = 0  # Reset counter on pawn move or capture
        else:
            self.fiftyMoveCounter += 1
        self.moveLog.append((move, self.fiftyMoveCounter))  # log the move so we can undo it later

    def undoMove(self):
        """
        Undoes the last move made.

        Returns:
            None
        """
        if len(self.moveLog) != 0:
            move = self.moveLog.pop()[0]

            # Decrement position count for threefold repetition
            boardString = self.getBoardHash()
            if boardString in self.positionCounts:
                self.positionCounts[boardString] -= 1
                if self.positionCounts[boardString] == 0:
                    del self.positionCounts[boardString]

            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            if move.pieceMoved == 16:
                self.whiteKingLocation = (move.startRow, move.startCol)
            elif move.pieceMoved == 26:
                self.blackKingLocation = (move.startRow, move.startCol)
            self.whiteToMove = not self.whiteToMove  # switch players

            # undo en passant
            if move.isEnPassantMove:
                self.board[move.endRow][move.endCol] = 0
                self.board[move.startRow][move.endCol] = move.pieceCaptured
            self.enPassantPossibleLog.pop()
            if self.enPassantPossibleLog[-1] != ():
                self.enPassantPossible = (self.enPassantPossibleLog[-1][0], self.enPassantPossibleLog[-1][1])
            else:
                self.enPassantPossible = ()

            # undo castling right
            self.castleRightsLog.pop()
            self.currentCastlingRight = CastleRight(self.castleRightsLog[-1].wks,
                                                    self.castleRightsLog[-1].bks,
                                                    self.castleRightsLog[-1].wqs,
                                                    self.castleRightsLog[-1].bqs)

            # undo castle move
            if len(self.moveLog) != 0:
                self.fiftyMoveCounter = self.moveLog[-1][1]
            else:
                self.fiftyMoveCounter = 0
            if move.isCastleMove:
                if move.endCol - move.startCol == 2:  # kingside
                    self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 1]
                    self.board[move.endRow][move.endCol - 1] = 0
                else:
                    self.board[move.endRow][move.endCol - 2] = self.board[move.endRow][move.endCol + 1]
                    self.board[move.endRow][move.endCol + 1] = 0

            # undo checkmate and draw state
            self.checkMate = False
            self.draw = False

    def getValidMoves(self):
        """
        Generates all valid moves for the current player.

        Returns:
            list: List of valid Move objects.
        """
        before = dict(self.positionCounts)
        moves = self.getAllPossibleMoves()

        # Add castling moves
        if self.whiteToMove:
            self.getCastleMoves(self.whiteKingLocation[0], self.whiteKingLocation[1], moves)
        else:
            self.getCastleMoves(self.blackKingLocation[0], self.blackKingLocation[1], moves)

        # Filter out moves that leave the king in check
        validMoves = []
        for move in moves:
            self.makeMove(move)
            self.whiteToMove = not self.whiteToMove
            if not self.inCheck():
                validMoves.append(move)
            self.whiteToMove = not self.whiteToMove
            self.undoMove()

        after = self.positionCounts
        if before != after:
            print("=== positionCounts mutated during getValidMoves! ===")
            for k in set(before) | set(after):
                b = before.get(k, 0)
                a = after.get(k, 0)
                if a != b:
                    print(f"  hash {k}: before={b}, after={a}")
        # Handle draw conditions
        if not validMoves:
            if self.inCheck():
                self.checkMate = True
            else:
                self.draw = True
        elif self.fiftyMoveCounter >= 50:
            self.draw = True
            print("Draw by 50-move rule")
        elif any(count >= 3 for count in list(self.positionCounts.values())):
            self.draw = True
            print("Draw by threefold repetition")
        elif self.insufficientMaterial():
            self.draw = True
            print("Draw by insufficient material")
        else:
            self.checkMate = False
            self.draw = False

        return validMoves

    def squareUnderAttack(self, row, col):
        """
        Determines if a square is under attack.

        Parameters:
            row (int): Row index of the square.
            col (int): Column index of the square.

        Returns:
            bool: True if the square is under attack, False otherwise.
        """
        attackingColor = 10 if not self.whiteToMove else 20  # Determine the attacking color based on whiteToMove
        directions = {
            'knight': [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)],
            'king': [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)],
            'rook': [(0, 1), (0, -1), (1, 0), (-1, 0)],
            'bishop': [(1, 1), (1, -1), (-1, 1), (-1, -1)],
        }

        # Check for pawn attacks
        pawnDirection = -1 if attackingColor == 20 else 1
        if self.insideBoard(row + pawnDirection, col - 1) and self.board[row + pawnDirection][col - 1] == attackingColor + 1:
            return True
        if self.insideBoard(row + pawnDirection, col + 1) and self.board[row + pawnDirection][col + 1] == attackingColor + 1:
            return True

        # Check for knight attacks
        for dr, dc in directions['knight']:
            if self.insideBoard(row + dr, col + dc) and self.board[row + dr][col + dc] == attackingColor + 2:
                return True

        # Check for rook and queen attacks (horizontal and vertical)
        for dr, dc in directions['rook']:
            for i in range(1, 8):
                nr, nc = row + dr * i, col + dc * i
                if not self.insideBoard(nr, nc):
                    break
                piece = self.board[nr][nc]
                if piece != 0:
                    if piece == attackingColor + 4 or piece == attackingColor + 5:
                        return True
                    break

        # Check for bishop and queen attacks (diagonals)
        for dr, dc in directions['bishop']:
            for i in range(1, 8):
                nr, nc = row + dr * i, col + dc * i
                if not self.insideBoard(nr, nc):
                    break
                piece = self.board[nr][nc]
                if piece != 0:
                    if piece == attackingColor + 3 or piece == attackingColor + 5:
                        return True
                    break

        # Check for king attacks
        for dr, dc in directions['king']:
            if self.insideBoard(row + dr, col + dc) and self.board[row + dr][col + dc] == attackingColor + 6:
                return True

        return False

class Move:
    """
    Represents a chess move.

    Attributes:
        startRow (int): Starting row.
        startCol (int): Starting column.
        endRow (int): Ending row.
        endCol (int): Ending column.
        pieceMoved (int): The piece being moved.
        pieceCaptured (int): The piece being captured, if any.
        ... (other attributes as needed)
    """

    def __init__(self, startSq, endSq, board):
        """
        Initializes a Move object.

        Parameters:
            startSq (tuple): (row, col) of the start square.
            endSq (tuple): (row, col) of the end square.
            board (list): The current board state.
        """
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol

    def getChessNotation(self):
        """
        Returns the move in standard chess notation.

        Returns:
            str: The move in chess notation.
        """
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)

    def getRankFile(self, r, c):
        """
        transcribe from row, column to rank, file (from code language to proper chess notation)
        parameters:
        - r: row
        - c: column
        function return:
        - respective rank and file
        """
        return self.colsToFiles[c] + self.rowsToRanks[r]

class CastleRight:
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
