"""
ChessEngine.py

Contains the GameState class and logic for chess rules, move generation, and validation.

Author: Doan Quoc Kien
"""
import numpy as np

class GameState():
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
        The chess board is an 8x8 2D list, each element is a numerical value:
        0: Empty square
        11-16: White pieces (pawn, knight, bishop, rook, queen, king)
        21-26: Black pieces (pawn, knight, bishop, rook, queen, king)
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
        self.simulation = False
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
        self.whiteToMove = not self.whiteToMove #switch players
        if move.pieceMoved == 16:
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == 26:
            self.blackKingLocation = (move.endRow, move.endCol)

        if move.isPawnPromotion:
            promotionPiece = move.promotionChoice if move.promotionChoice else 5  # Default to Queen
            self.board[move.endRow][move.endCol] = (10 if move.pieceMoved == 11 else 20) + promotionPiece
        
        #en passant
        if move.isEnPassantMove:
            self.board[move.startRow][move.endCol] = 0 #capturing the pawn

        #update enPassantPossible
        if move.pieceMoved % 10 == 1 and abs(move.startRow - move.endRow) == 2:
            self.enPassantPossible = ((move.startRow + move.endRow) // 2, move.startCol)
            self.enPassantPossibleLog.append((self.enPassantPossible[0], self.enPassantPossible[1]))
        else:
            self.enPassantPossible = ()
            self.enPassantPossibleLog.append(())
        
        #update castling rights - whenever it is a rook or a king move      
        self.updateCastleRights(move)
        self.castleRightsLog.append(CastleRight(
                                    self.currentCastlingRight.wks,
                                    self.currentCastlingRight.bks,
                                    self.currentCastlingRight.wqs,
                                    self.currentCastlingRight.bqs
                                    ))  
                    
        #castle
        if move.isCastleMove:
            if move.endCol - move.startCol == 2: #Kingside castle move
                self.board[move.endRow][move.endCol - 1] = self.board[move.endRow][move.endCol + 1] #moves the rook
                self.board[move.endRow][move.endCol + 1] = 0
            else:
                self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 2] #moves the rook
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
        self.moveLog.append((move, self.fiftyMoveCounter)) #log the move so we can undo it later

    def getBoardHash(self):
        """
        Generate a hash representation of the board for threefold repetition.
        
        Returns:
            int: The value of the hash
        """
        return hash((
            tuple(tuple(row) for row in self.board),  # Board layout
            self.whiteToMove,  # Current player's turn
        ))
    
    def updateCastleRights(self, move):
        """
        Update Castling right when a piece moved
        
        Parameters:
            move (Move): move just made
        """
        if move.pieceMoved == 16:
            self.currentCastlingRight.wks = False
            self.currentCastlingRight.wqs = False
        elif move.pieceMoved == 26:
            self.currentCastlingRight.bks = False
            self.currentCastlingRight.bqs = False
        elif move.pieceMoved == 14:
            if move.startRow == 7:
                if move.startCol == 0: # left rook
                    self.currentCastlingRight.wqs = False
                elif move.startCol == 7: #right took
                    self.currentCastlingRight.wks = False
        elif move.pieceMoved == 24:
            if move.startRow == 0:
                if move.startCol == 0: # left rook
                    self.currentCastlingRight.bqs = False
                elif move.startCol == 7: #right took
                    self.currentCastlingRight.bks = False
        if move.pieceCaptured == 14:
            if move.endRow == 7:
                if move.endCol == 0: # left rook
                    self.currentCastlingRight.wqs = False
                elif move.endCol == 7: #right took
                    self.currentCastlingRight.wks = False
        elif move.pieceCaptured == 24:
            if move.endRow == 0:
                if move.endCol == 0: # left rook
                    self.currentCastlingRight.bqs = False
                elif move.endCol == 7: #right took
                    self.currentCastlingRight.bks = False

    
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
            self.whiteToMove = not self.whiteToMove #switch players

            #undo en passant
            if move.isEnPassantMove:
                self.board[move.endRow][move.endCol] = 0
                self.board[move.startRow][move.endCol] = move.pieceCaptured
            self.enPassantPossibleLog.pop()
            if self.enPassantPossibleLog[-1] != ():
                self.enPassantPossible = (self.enPassantPossibleLog[-1][0], self.enPassantPossibleLog[-1][1])
            else: self.enPassantPossible = ()
            
            #undo castling right
            self.castleRightsLog.pop()
            self.currentCastlingRight = CastleRight(self.castleRightsLog[-1].wks,
                                                    self.castleRightsLog[-1].bks,
                                                    self.castleRightsLog[-1].wqs,
                                                    self.castleRightsLog[-1].bqs)

            #undo castle move
            if len(self.moveLog) != 0:
                self.fiftyMoveCounter = self.moveLog[-1][1]
            else:
                self.fiftyMoveCounter = 0
            if move.isCastleMove:
                if move.endCol - move.startCol == 2: #kingside
                    self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 1]
                    self.board[move.endRow][move.endCol - 1] = 0
                else:
                    self.board[move.endRow][move.endCol - 2] = self.board[move.endRow][move.endCol + 1]
                    self.board[move.endRow][move.endCol + 1] = 0
            
            #undo checkmate and draw state
            self.checkMate = False
            self.draw = False
            

    def insufficientMaterial(self):
        """
        Check if there is insufficient material to continue the game.
        
        Returns:
            True/False
        """
        pieces = [piece for row in self.board for piece in row if piece != 0]

        # King vs. King
        if pieces == [16, 26]:
            return True

        # King and Bishop/Knight vs. King
        if len(pieces) == 3 and 16 in pieces and 26 in pieces and (13 in pieces or 12 in pieces):
            return True

        # King and Bishop vs. King and Bishop (same-colored bishops)
        if len(pieces) == 4 and 16 in pieces and 26 in pieces and pieces.count(13) == 2:
            bishops = [(r, c) for r, row in enumerate(self.board) for c, piece in enumerate(row) if piece == 13]
            if (bishops[0][0] + bishops[0][1]) % 2 == (bishops[1][0] + bishops[1][1]) % 2:
                return True

        return False

    def squareUnderAttack(self, r, c):
        """
        Check if a square is attacked by the opponent.
        
        Parameters:
            r, c: Row and column of the square to check.
        Returns:
            True if the square is attacked, False otherwise.
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
        if self.insideBoard(r + pawnDirection, c - 1) and self.board[r + pawnDirection][c - 1] == attackingColor + 1:
            return True
        if self.insideBoard(r + pawnDirection, c + 1) and self.board[r + pawnDirection][c + 1] == attackingColor + 1:
            return True

        # Check for knight attacks
        for dr, dc in directions['knight']:
            if self.insideBoard(r + dr, c + dc) and self.board[r + dr][c + dc] == attackingColor + 2:
                return True

        # Check for rook and queen attacks (horizontal and vertical)
        for dr, dc in directions['rook']:
            for i in range(1, 8):
                nr, nc = r + dr * i, c + dc * i
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
                nr, nc = r + dr * i, c + dc * i
                if not self.insideBoard(nr, nc):
                    break
                piece = self.board[nr][nc]
                if piece != 0:
                    if piece == attackingColor + 3 or piece == attackingColor + 5:
                        return True
                    break

        # Check for king attacks
        for dr, dc in directions['king']:
            if self.insideBoard(r + dr, c + dc) and self.board[r + dr][c + dc] == attackingColor + 6:
                return True

        return False

    def getValidMoves(self):
        """
        Generate all valid moves considering checks, castling, and special rules.
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
        elif self.fiftyMoveCounter >= 100:
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
    
    def inCheck(self):
        """
        Check if the current player is in check
        
        Returns:
            True/False
        """
        if self.whiteToMove:
            return self.squareUnderAttack(self.whiteKingLocation[0], self.whiteKingLocation[1])
        else:
            return self.squareUnderAttack(self.blackKingLocation[0], self.blackKingLocation[1])

    def getAllPossibleMoves(self):
        """
        Generate all possible moves without considering checks.
        
        Returns:
            List of Move that satisfy the standard chess rules 
        """
        moves = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece != 0 and ((piece // 10 == 1 and self.whiteToMove) or (piece // 10 == 2 and not self.whiteToMove)):
                    self.moveFunctions[piece % 10](r, c, moves)
        return moves

    def getPawnMoves(self, r, c, moves):
        """
        Generate all possible moves for pawn.
        
        Parameters:
            r, c (int):  row and column as positions
            moves (list of Moves as reference): list of moves
        """
        if self.whiteToMove: # white pawns
            if self.board[r - 1][c] == 0: # one-square advance
                moves.append(Move((r, c), (r - 1, c), self.board))
                if r == 6 and self.board[r - 2][c] == 0: #two-square advance
                    moves.append(Move((r, c), (r - 2, c), self.board))
            # enemy capture pieces
            if c - 1 >= 0:
                if self.board[r - 1][c - 1] // 10 == 2: 
                    moves.append(Move((r, c), (r - 1, c - 1), self.board))
                elif (r - 1, c - 1) == self.enPassantPossible:
                    moves.append(Move((r, c), (r - 1, c - 1), self.board, isEnPassantMove=True))
            if c + 1 < len(self.board):
                if self.board[r - 1][c + 1] // 10 == 2:
                    moves.append(Move((r, c), (r - 1, c + 1), self.board))
                elif (r - 1, c + 1) == self.enPassantPossible:
                    moves.append(Move((r, c), (r - 1, c + 1), self.board, isEnPassantMove=True))
        else: #black pawns
            if self.board[r + 1][c] == 0: # one-square advance
                moves.append(Move((r, c), (r + 1, c), self.board))
                if r == 1 and self.board[r + 2][c] == 0: #two-square advance
                    moves.append(Move((r, c), (r + 2, c), self.board))
            # enemy capture pieces
            if c - 1 >= 0:
                if self.board[r + 1][c - 1] // 10 == 1: 
                    moves.append(Move((r, c), (r + 1, c - 1), self.board))
                elif (r + 1, c - 1) == self.enPassantPossible:
                    moves.append(Move((r, c), (r + 1, c - 1), self.board, isEnPassantMove=True))
            if c + 1 < len(self.board):
                if self.board[r + 1][c + 1] // 10 == 1:
                    moves.append(Move((r, c), (r + 1, c + 1), self.board))
                elif (r + 1, c + 1) == self.enPassantPossible:
                    moves.append(Move((r, c), (r + 1, c + 1), self.board, isEnPassantMove=True))

    def getRookMoves(self, r, c, moves):
        """
        Generate all possible moves for rook.
        
        Parameters:
            r, c (int):  row and column as positions
            moves (list of Moves as reference): list of moves
        """
        curr_turn = 2
        op_turn = 1
        if self.whiteToMove:
            curr_turn = 1
            op_turn = 2
        for cur_c in range(c + 1, 8): # move to the right
            if self.board[r][cur_c] // 10 == curr_turn:
                break
            moves.append(Move((r, c), (r, cur_c), self.board))
            if self.board[r][cur_c] // 10 == op_turn:
                break
        for cur_c in range(c - 1, -1, -1): # move to the left
            if self.board[r][cur_c] // 10 == curr_turn:
                break
            moves.append(Move((r, c), (r, cur_c), self.board))
            if self.board[r][cur_c] // 10 == op_turn:
                break
        for cur_r in range(r + 1, 8): # move down
            if self.board[cur_r][c] // 10 == curr_turn:
                break
            moves.append(Move((r, c), (cur_r, c), self.board))
            if self.board[cur_r][c] // 10 == op_turn:
                break
        for cur_r in range(r - 1, -1, -1): # move up
            if self.board[cur_r][c] // 10 == curr_turn:
                break
            moves.append(Move((r, c), (cur_r, c), self.board))
            if self.board[cur_r][c] // 10 == op_turn:
                break

    def insideBoard(self, r, c):
        """
        Return True if a square is inside the board
        
        Parameters:
            r, c (int): row and column need checking
        Returns:
            True/False
        """
        return 0 <= r < 8 and 0 <= c < 8
    
    def getKnightMoves(self, r, c, moves):
        """
        Generate all possible moves for knight.
        
        Parameters:
            r, c (int):  row and column as positions
            moves (list of Moves as reference): list of moves
        """
        curr_turn = 2
        if self.whiteToMove:
            curr_turn = 1
        directions = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)] #L-shaped moves
        for i in directions:
            if self.insideBoard(r + i[0], c + i[1]):
                if self.board[r + i[0]][c + i[1]] // 10 != curr_turn:
                    moves.append(Move((r, c), (r + i[0], c + i[1]), self.board))

    def getBishopMoves(self, r, c, moves):
        """
        Generate all possible moves for knight.
        
        Parameters:
            r, c (int):  row and column as positions
            moves (list of Moves as reference): list of moves
        """
        curr_turn = 2
        op_turn = 1
        if self.whiteToMove:
            curr_turn = 1
            op_turn = 2
        # Move down-right
        currRow = r + 1
        currColumn = c + 1
        while self.insideBoard(currRow, currColumn):
            if self.board[currRow][currColumn] // 10 == curr_turn:
                break
            moves.append(Move((r, c), (currRow, currColumn), self.board))
            if self.board[currRow][currColumn] // 10 == op_turn:
                break
            currRow += 1
            currColumn += 1
        
        #Move down-left
        currRow = r + 1
        currColumn = c - 1
        while self.insideBoard(currRow, currColumn):
            if self.board[currRow][currColumn] // 10 == curr_turn:
                break
            moves.append(Move((r, c), (currRow, currColumn), self.board))
            if self.board[currRow][currColumn] // 10 == op_turn:
                break
            currRow += 1
            currColumn -= 1

        #Move up-right
        currRow = r - 1
        currColumn = c + 1
        while self.insideBoard(currRow, currColumn):
            if self.board[currRow][currColumn] // 10 == curr_turn:
                break
            moves.append(Move((r, c), (currRow, currColumn), self.board))
            if self.board[currRow][currColumn] // 10 == op_turn:
                break
            currRow -= 1
            currColumn += 1
        
        #Move up-left
        currRow = r - 1
        currColumn = c - 1
        while self.insideBoard(currRow, currColumn):
            if self.board[currRow][currColumn] // 10 == curr_turn:
                break
            moves.append(Move((r, c), (currRow, currColumn), self.board))
            if self.board[currRow][currColumn] // 10 == op_turn:
                break
            currRow -= 1
            currColumn -= 1
    def getQueenMoves(self, r, c, moves):
        """
        Generate all possible moves for queen. Since queen are basically rook and bishop combine, we could just get the rook and bishop moves at this piece
        
        Parameters:
            r, c (int):  row and column as positions
            moves (list of Moves as reference): list of moves
        """
        self.getRookMoves(r, c, moves)
        self.getBishopMoves(r, c, moves)

    def getKingMoves(self, r, c, moves):
        """
        Generate all possible moves for king.
        
        Parameters:
            r, c (int):  row and column as positions
            moves (list of Moves as reference): list of moves
        """
        curr_turn = 2
        if self.whiteToMove:
            curr_turn = 1
        directions = [(0, 1), (0, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (1, 1), (1, -1)] #one-space moves
        for i in directions:
            if self.insideBoard(r + i[0], c + i[1]):
                if self.board[r + i[0]][c + i[1]] // 10 != curr_turn:
                    moves.append(Move((r, c), (r + i[0], c + i[1]), self.board))
    
    def getCastleMoves(self, r, c, moves):
        """
        Generate all valid castle moves at r, c for the current turn.
        
        Parameters:
            r, c (int):  row and column as positions
            moves (list of Moves as reference): list of moves
        """
        if self.inCheck():
            return  # Can't castle while in check

        # Kingside Castle Moves
        if (self.whiteToMove and self.currentCastlingRight.wks) or (not self.whiteToMove and self.currentCastlingRight.bks):
            if c + 2 < 8 and self.board[r][c + 1] == 0 and self.board[r][c + 2] == 0:
                if not self.squareUnderAttack(r, c + 1) and not self.squareUnderAttack(r, c + 2):
                    moves.append(Move((r, c), (r, c + 2), self.board, isCastleMove=True))

        # Queenside Castle Moves
        if (self.whiteToMove and self.currentCastlingRight.wqs) or (not self.whiteToMove and self.currentCastlingRight.bqs):
            if c - 3 >= 0 and self.board[r][c - 1] == 0 and self.board[r][c - 2] == 0 and self.board[r][c - 3] == 0:
                if not self.squareUnderAttack(r, c - 1) and not self.squareUnderAttack(r, c - 2):
                    moves.append(Move((r, c), (r, c - 2), self.board, isCastleMove=True))
class Move():
    """
    Represents a chess move.

    Attributes:
        startRow (int): Starting row.
        startCol (int): Starting column.
        endRow (int): Ending row.
        endCol (int): Ending column.
        pieceMoved (int): The piece being moved.
        pieceCaptured (int): The piece being captured, if any.
        moveID (int): ID of a move, including the hashed starting and ending positions
        isPawnPromotion (bool): Check if a move is a pawn promotion
        promotionChoice (int): The piece that the pawn promotes to
        isEnPassantMove (bool): Check if a move is en passant
        isCastleMove (bool): Check if a move is castling
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
    pieceToNotation = {1: "", 2: "N", 3: "B", 4: "R", 5: "Q", 6: "K"}


    def __init__(self, startSquare, endSquare, board, isEnPassantMove = False, isCastleMove = False, promotionChoice = None):
        self.startRow = startSquare[0]
        self.startCol = startSquare[1]
        self.endRow = endSquare[0]
        self.endCol = endSquare[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol

        #pawn promotion
        self.isPawnPromotion = (self.pieceMoved == 11 and self.endRow == 0) or (self.pieceMoved == 21 and self.endRow == 7)
        self.promotionChoice = promotionChoice

        #en passant
        self.isEnPassantMove = isEnPassantMove
        if self.isEnPassantMove:
            self.pieceCaptured = 11 if self.pieceMoved == 21 else 21

        #castling
        self.isCastleMove = isCastleMove

    def __eq__(self, other):
        """
        Two move is equal if they have the same moveID
        
        Parameters:
            other (Move): Move to compare
        Returns:
            True/False
        """
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def getChessNotation(self):
        """
        Returns the move in standard chess notation.

        Returns:
            str: The move in chess notation.
        """
        # note: the order of coding and chess notation is reversed (row, col) -> (file, rank)
        if self.isCastleMove:
            if self.startCol - self.endCol == 2:
                return "O - O - O"
            else:
                return "O - O"
        notation = self.pieceToNotation[self.pieceMoved % 10] + self.getRankFile(self.startRow, self.startCol) + ("x" if self.pieceCaptured != 0 else "→") + self.getRankFile(self.endRow, self.endCol)
        if self.isPawnPromotion:
            notation += "=" + self.pieceToNotation[self.promotionChoice if self.promotionChoice else 5]
        return notation
    
    def getRankFile(self, r, c):
        """
        Transcribe from row, column to rank, file (from code language to proper chess notation)

        Parameters:
            self
            r: row
            c: column
        Returns:
            respective rank and file
        """
        return self.colsToFiles[c] + self.rowsToRanks[r]



class CastleRight():
    """
    Checking castling availability including:

    Attributes:
        wks (bool): white king side
        wqs (bool): white queen side
        bks (bool): black king side
        bqs (bool): black queen side
    """
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs
