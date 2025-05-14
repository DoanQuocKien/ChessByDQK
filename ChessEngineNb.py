"""
This file is an optimized version of ChessEngine.py using Numba for acceleration
"""
import numpy as np
from numba import njit, jit, int32, boolean, types
from numba.experimental import jitclass
from numba.typed import Dict, List
import copy

# Define specs for jitclasses
castle_right_spec = [
    ('wks', boolean),
    ('bks', boolean),
    ('wqs', boolean),
    ('bqs', boolean)
]

move_spec = [
    ('startRow', int32),
    ('startCol', int32),
    ('endRow', int32),
    ('endCol', int32),
    ('pieceMoved', int32),
    ('pieceCaptured', int32),
    ('moveID', int32),
    ('pawnPromotion', boolean),
    ('promotionChoice', types.optional(int32)),
    ('isEnPassantMove', boolean),
    ('isCastleMove', boolean)
]

# Numba-optimized implementation of CastleRight
@jitclass(castle_right_spec)
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

# Numba-optimized implementation of Move
@jitclass(move_spec)
class Move:
    """
    This class handles chess moves information
    """
    def __init__(self, startSquare, endSquare, board, isEnPassantMove=False, isCastleMove=False, promotionChoice=None):
        self.startRow = startSquare[0]
        self.startCol = startSquare[1]
        self.endRow = endSquare[0]
        self.endCol = endSquare[1]
        self.pieceMoved = board[self.startRow, self.startCol]
        self.pieceCaptured = board[self.endRow, self.endCol]
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol
        
        # pawn promotion
        self.pawnPromotion = (self.pieceMoved == 11 and self.endRow == 0) or (self.pieceMoved == 21 and self.endRow == 7)
        self.promotionChoice = promotionChoice if promotionChoice is not None else 0
        
        # en passant
        self.isEnPassantMove = isEnPassantMove
        if self.isEnPassantMove:
            self.pieceCaptured = 11 if self.pieceMoved == 21 else 21
        
        # castling
        self.isCastleMove = isCastleMove

# Helper functions that need to be outside classes for Numba compatibility
@njit
def insideBoard(r, c):
    """Check if a position is inside the board"""
    return 0 <= r < 8 and 0 <= c < 8

@njit
def getPawnMoves(board, r, c, moves, white_to_move, en_passant_possible):
    """Generate all possible pawn moves"""
    if white_to_move:  # white pawns
        if board[r - 1, c] == 0:  # one-square advance
            moves.append(Move((r, c), (r - 1, c), board))
            if r == 6 and board[r - 2, c] == 0:  # two-square advance
                moves.append(Move((r, c), (r - 2, c), board))
        # enemy capture pieces
        if c - 1 >= 0:
            if board[r - 1, c - 1] // 10 == 2:
                moves.append(Move((r, c), (r - 1, c - 1), board))
            elif en_passant_possible[0] == r - 1 and en_passant_possible[1] == c - 1:
                moves.append(Move((r, c), (r - 1, c - 1), board, isEnPassantMove=True))
        if c + 1 < 8:
            if board[r - 1, c + 1] // 10 == 2:
                moves.append(Move((r, c), (r - 1, c + 1), board))
            elif en_passant_possible[0] == r - 1 and en_passant_possible[1] == c + 1:
                moves.append(Move((r, c), (r - 1, c + 1), board, isEnPassantMove=True))
    else:  # black pawns
        if board[r + 1, c] == 0:  # one-square advance
            moves.append(Move((r, c), (r + 1, c), board))
            if r == 1 and board[r + 2, c] == 0:  # two-square advance
                moves.append(Move((r, c), (r + 2, c), board))
        # enemy capture pieces
        if c - 1 >= 0:
            if board[r + 1, c - 1] // 10 == 1:
                moves.append(Move((r, c), (r + 1, c - 1), board))
            elif en_passant_possible[0] == r + 1 and en_passant_possible[1] == c - 1:
                moves.append(Move((r, c), (r + 1, c - 1), board, isEnPassantMove=True))
        if c + 1 < 8:
            if board[r + 1, c + 1] // 10 == 1:
                moves.append(Move((r, c), (r + 1, c + 1), board))
            elif en_passant_possible[0] == r + 1 and en_passant_possible[1] == c + 1:
                moves.append(Move((r, c), (r + 1, c + 1), board, isEnPassantMove=True))

@njit
def getRookMoves(board, r, c, moves, white_to_move):
    """Generate all possible rook moves"""
    curr_turn = 1 if white_to_move else 2
    op_turn = 2 if white_to_move else 1
    
    # Move right
    for cur_c in range(c + 1, 8):
        if board[r, cur_c] // 10 == curr_turn:
            break
        moves.append(Move((r, c), (r, cur_c), board))
        if board[r, cur_c] // 10 == op_turn:
            break
    
    # Move left
    for cur_c in range(c - 1, -1, -1):
        if board[r, cur_c] // 10 == curr_turn:
            break
        moves.append(Move((r, c), (r, cur_c), board))
        if board[r, cur_c] // 10 == op_turn:
            break
    
    # Move down
    for cur_r in range(r + 1, 8):
        if board[cur_r, c] // 10 == curr_turn:
            break
        moves.append(Move((r, c), (cur_r, c), board))
        if board[cur_r, c] // 10 == op_turn:
            break
    
    # Move up
    for cur_r in range(r - 1, -1, -1):
        if board[cur_r, c] // 10 == curr_turn:
            break
        moves.append(Move((r, c), (cur_r, c), board))
        if board[cur_r, c] // 10 == op_turn:
            break

@njit
def getKnightMoves(board, r, c, moves, white_to_move):
    """Generate all possible knight moves"""
    curr_turn = 1 if white_to_move else 2
    directions = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
    
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if insideBoard(nr, nc) and board[nr, nc] // 10 != curr_turn:
            moves.append(Move((r, c), (nr, nc), board))

@njit
def getBishopMoves(board, r, c, moves, white_to_move):
    """Generate all possible bishop moves"""
    curr_turn = 1 if white_to_move else 2
    op_turn = 2 if white_to_move else 1
    directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    
    for dr, dc in directions:
        curr_r, curr_c = r + dr, c + dc
        while insideBoard(curr_r, curr_c):
            if board[curr_r, curr_c] // 10 == curr_turn:
                break
            moves.append(Move((r, c), (curr_r, curr_c), board))
            if board[curr_r, curr_c] // 10 == op_turn:
                break
            curr_r += dr
            curr_c += dc

@njit
def getQueenMoves(board, r, c, moves, white_to_move):
    """Generate all possible queen moves"""
    getRookMoves(board, r, c, moves, white_to_move)
    getBishopMoves(board, r, c, moves, white_to_move)

@njit
def getKingMoves(board, r, c, moves, white_to_move):
    """Generate all possible king moves"""
    curr_turn = 1 if white_to_move else 2
    directions = [(0, 1), (0, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (1, 1), (1, -1)]
    
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if insideBoard(nr, nc) and board[nr, nc] // 10 != curr_turn:
            moves.append(Move((r, c), (nr, nc), board))

@njit
def squareUnderAttack(board, r, c, white_to_move):
    """Check if a square is under attack"""
    attacking_color = 20 if white_to_move else 10  # Opposite of current player
    
    # Check for pawn attacks
    pawn_dir = 1 if attacking_color == 20 else -1
    for dc in [-1, 1]:
        nr, nc = r + pawn_dir, c + dc
        if insideBoard(nr, nc) and board[nr, nc] == attacking_color + 1:
            return True
    
    # Check for knight attacks
    knight_dirs = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
    for dr, dc in knight_dirs:
        nr, nc = r + dr, c + dc
        if insideBoard(nr, nc) and board[nr, nc] == attacking_color + 2:
            return True
    
    # Check for bishop/queen diagonal attacks
    diag_dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    for dr, dc in diag_dirs:
        nr, nc = r + dr, c + dc
        while insideBoard(nr, nc):
            piece = board[nr, nc]
            if piece != 0:
                if piece == attacking_color + 3 or piece == attacking_color + 5:  # Bishop or Queen
                    return True
                break
            nr += dr
            nc += dc
    
    # Check for rook/queen straight attacks
    straight_dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    for dr, dc in straight_dirs:
        nr, nc = r + dr, c + dc
        while insideBoard(nr, nc):
            piece = board[nr, nc]
            if piece != 0:
                if piece == attacking_color + 4 or piece == attacking_color + 5:  # Rook or Queen
                    return True
                break
            nr += dr
            nc += dc
    
    # Check for king attacks
    king_dirs = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    for dr, dc in king_dirs:
        nr, nc = r + dr, c + dc
        if insideBoard(nr, nc) and board[nr, nc] == attacking_color + 6:
            return True
    
    return False

@njit
def getCastleMoves(board, r, c, moves, white_to_move, castle_rights, king_location):
    """Generate all valid castle moves"""
    # Can't castle while in check
    if squareUnderAttack(board, king_location[0], king_location[1], not white_to_move):
        return
    
    # Kingside Castle
    if (white_to_move and castle_rights.wks) or (not white_to_move and castle_rights.bks):
        if board[r, c+1] == 0 and board[r, c+2] == 0:
            if not squareUnderAttack(board, r, c+1, not white_to_move) and not squareUnderAttack(board, r, c+2, not white_to_move):
                moves.append(Move((r, c), (r, c+2), board, isCastleMove=True))
    
    # Queenside Castle
    if (white_to_move and castle_rights.wqs) or (not white_to_move and castle_rights.bqs):
        if board[r, c-1] == 0 and board[r, c-2] == 0 and board[r, c-3] == 0:
            if not squareUnderAttack(board, r, c-1, not white_to_move) and not squareUnderAttack(board, r, c-2, not white_to_move):
                moves.append(Move((r, c), (r, c-2), board, isCastleMove=True))

@njit
def insufficientMaterial(board):
    """Check if there is insufficient material to continue the game"""
    pieces = []
    for r in range(8):
        for c in range(8):
            piece = board[r, c]
            if piece != 0:
                pieces.append(piece)
    
    # King vs. King
    if len(pieces) == 2 and 16 in pieces and 26 in pieces:
        return True
    
    # King and Bishop/Knight vs. King
    if len(pieces) == 3 and 16 in pieces and 26 in pieces:
        for piece in pieces:
            if piece in [12, 13, 22, 23]:  # Knight or Bishop
                return True
    
    # King and Bishop vs. King and Bishop (same-colored bishops)
    if len(pieces) == 4 and 16 in pieces and 26 in pieces:
        bishop_count = 0
        bishop_positions = []
        for r in range(8):
            for c in range(8):
                if board[r, c] == 13 or board[r, c] == 23:
                    bishop_count += 1
                    bishop_positions.append((r, c))
        
        if bishop_count == 2:
            # Same color bishops check
            return (bishop_positions[0][0] + bishop_positions[0][1]) % 2 == (bishop_positions[1][0] + bishop_positions[1][1]) % 2
    
    return False

# Main GameState class (cannot be fully jitted due to complexity)
class GameState:
    """
    This class tracks the current state of the game
    """
    def __init__(self):
        # Initial board setup
        self.board = np.array([
            [24, 22, 23, 25, 26, 23, 22, 24],
            [21, 21, 21, 21, 21, 21, 21, 21],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [11, 11, 11, 11, 11, 11, 11, 11],
            [14, 12, 13, 15, 16, 13, 12, 14],
        ], dtype=np.int32)
        
        self.whiteToMove = True
        self.moveLog = []
        self.whiteKingLocation = (7, 4)
        self.blackKingLocation = (0, 4)
        self.checkMate = False
        self.draw = False
        self.enPassantPossible = (-1, -1)  # Using -1,-1 to represent empty
        self.enPassantPossibleLog = [(-1, -1)]
        self.currentCastlingRight = CastleRight(True, True, True, True)
        self.castleRightsLog = [CastleRight(True, True, True, True)]
        self.fiftyMoveCounter = 0
        self.positionCounts = {}  # Will use string representation as keys
        
    def makeMove(self, move):
        """Make a chess move"""
        # Update board
        self.board[move.startRow, move.startCol] = 0
        self.board[move.endRow, move.endCol] = move.pieceMoved
        
        # Switch players
        self.whiteToMove = not self.whiteToMove
        
        # Update king location
        if move.pieceMoved == 16:
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == 26:
            self.blackKingLocation = (move.endRow, move.endCol)
        
        # Handle pawn promotion
        if move.pawnPromotion:
            promotion_piece = move.promotionChoice if move.promotionChoice != 0 else 5  # Default to Queen
            self.board[move.endRow, move.endCol] = (10 if move.pieceMoved == 11 else 20) + promotion_piece
        
        # Handle en passant
        if move.isEnPassantMove:
            self.board[move.startRow, move.endCol] = 0
        
        # Update en passant possibility
        if move.pieceMoved % 10 == 1 and abs(move.startRow - move.endRow) == 2:
            self.enPassantPossible = ((move.startRow + move.endRow) // 2, move.startCol)
            self.enPassantPossibleLog.append(self.enPassantPossible)
        else:
            self.enPassantPossible = (-1, -1)
            self.enPassantPossibleLog.append((-1, -1))
        
        # Update castling rights
        self.updateCastleRight(move)
        self.castleRightsLog.append(CastleRight(
            self.currentCastlingRight.wks,
            self.currentCastlingRight.bks,
            self.currentCastlingRight.wqs,
            self.currentCastlingRight.bqs
        ))
        
        # Handle castling move
        if move.isCastleMove:
            if move.endCol - move.startCol == 2:  # Kingside
                self.board[move.endRow, move.endCol - 1] = self.board[move.endRow, move.endCol + 1]
                self.board[move.endRow, move.endCol + 1] = 0
            else:  # Queenside
                self.board[move.endRow, move.endCol + 1] = self.board[move.endRow, move.endCol - 2]
                self.board[move.endRow, move.endCol - 2] = 0
        
        # Update position count for threefold repetition
        board_hash = self.getBoardHash()
        if board_hash in self.positionCounts:
            self.positionCounts[board_hash] += 1
        else:
            self.positionCounts[board_hash] = 1
        
        # Update fifty-move counter
        if move.pieceMoved % 10 == 1 or move.pieceCaptured != 0:
            self.fiftyMoveCounter = 0
        else:
            self.fiftyMoveCounter += 1
        
        self.moveLog.append((move, self.fiftyMoveCounter))
    
    def getBoardHash(self):
        """Generate a hash for the current board state"""
        # Convert board to string representation for hashing
        return str(self.board.tobytes()) + str(int(self.whiteToMove))
    
    def updateCastleRight(self, move):
        """Update castling rights based on the move"""
        if move.pieceMoved == 16:  # White king moved
            self.currentCastlingRight.wks = False
            self.currentCastlingRight.wqs = False
        elif move.pieceMoved == 26:  # Black king moved
            self.currentCastlingRight.bks = False
            self.currentCastlingRight.bqs = False
        elif move.pieceMoved == 14:  # White rook moved
            if move.startRow == 7:
                if move.startCol == 0:  # Queen's rook
                    self.currentCastlingRight.wqs = False
                elif move.startCol == 7:  # King's rook
                    self.currentCastlingRight.wks = False
        elif move.pieceMoved == 24:  # Black rook moved
            if move.startRow == 0:
                if move.startCol == 0:  # Queen's rook
                    self.currentCastlingRight.bqs = False
                elif move.startCol == 7:  # King's rook
                    self.currentCastlingRight.bks = False
        
        # If a rook is captured
        if move.pieceCaptured == 14:
            if move.endRow == 7:
                if move.endCol == 0:
                    self.currentCastlingRight.wqs = False
                elif move.endCol == 7:
                    self.currentCastlingRight.wks = False
        elif move.pieceCaptured == 24:
            if move.endRow == 0:
                if move.endCol == 0:
                    self.currentCastlingRight.bqs = False
                elif move.endCol == 7:
                    self.currentCastlingRight.bks = False
    
    def undoMove(self):
        """Undo the last move made"""
        if len(self.moveLog) == 0:
            return
        
        move, _ = self.moveLog.pop()
        
        # Decrement position count
        board_hash = self.getBoardHash()
        if board_hash in self.positionCounts:
            self.positionCounts[board_hash] -= 1
            if self.positionCounts[board_hash] == 0:
                del self.positionCounts[board_hash]
        
        # Restore board
        self.board[move.startRow, move.startCol] = move.pieceMoved
        self.board[move.endRow, move.endCol] = move.pieceCaptured
        
        # Update king position if needed
        if move.pieceMoved == 16:
            self.whiteKingLocation = (move.startRow, move.startCol)
        elif move.pieceMoved == 26:
            self.blackKingLocation = (move.startRow, move.startCol)
        
        # Switch back turn
        self.whiteToMove = not self.whiteToMove
        
        # Handle en passant
        if move.isEnPassantMove:
            self.board[move.endRow, move.endCol] = 0
            self.board[move.startRow, move.endCol] = move.pieceCaptured
        
        # Update en passant possibility
        self.enPassantPossibleLog.pop()
        if len(self.enPassantPossibleLog) > 0:
            self.enPassantPossible = self.enPassantPossibleLog[-1]
        
        # Update castling rights
        self.castleRightsLog.pop()
        if len(self.castleRightsLog) > 0:
            self.currentCastlingRight = self.castleRightsLog[-1]
        
        # Handle castle move
        if move.isCastleMove:
            if move.endCol - move.startCol == 2:  # Kingside
                self.board[move.endRow, move.endCol + 1] = self.board[move.endRow, move.endCol - 1]
                self.board[move.endRow, move.endCol - 1] = 0
            else:  # Queenside
                self.board[move.endRow, move.endCol - 2] = self.board[move.endRow, move.endCol + 1]
                self.board[move.endRow, move.endCol + 1] = 0
        
        # Update fifty move counter
        if len(self.moveLog) > 0:
            self.fiftyMoveCounter = self.moveLog[-1][1]
        else:
            self.fiftyMoveCounter = 0
        
        # Reset checkmate and draw flags
        self.checkMate = False
        self.draw = False
    
    def in_check(self):
        """Check if current player is in check"""
        if self.whiteToMove:
            return squareUnderAttack(self.board, self.whiteKingLocation[0], self.whiteKingLocation[1], False)
        else:
            return squareUnderAttack(self.board, self.blackKingLocation[0], self.blackKingLocation[1], True)
    
    def getAllPossibleMoves(self):
        """Get all possible moves without checking for checks"""
        moves = List.empty_list(Move.class_type.instance_type)  # Initialize typed list
        for r in range(8):
            for c in range(8):
                piece = self.board[r, c]
                if piece == 0:
                    continue
                    
                piece_color = piece // 10
                piece_type = piece % 10
                
                if (piece_color == 1 and self.whiteToMove) or (piece_color == 2 and not self.whiteToMove):
                    if piece_type == 1:  # Pawn
                        getPawnMoves(self.board, r, c, moves, self.whiteToMove, self.enPassantPossible)
                    elif piece_type == 2:  # Knight
                        getKnightMoves(self.board, r, c, moves, self.whiteToMove)
                    elif piece_type == 3:  # Bishop
                        getBishopMoves(self.board, r, c, moves, self.whiteToMove)
                    elif piece_type == 4:  # Rook
                        getRookMoves(self.board, r, c, moves, self.whiteToMove)
                    elif piece_type == 5:  # Queen
                        getQueenMoves(self.board, r, c, moves, self.whiteToMove)
                    elif piece_type == 6:  # King
                        getKingMoves(self.board, r, c, moves, self.whiteToMove)
        
        return moves
    
    def getValidMoves(self):
        """Get all valid moves considering checks"""
        moves = self.getAllPossibleMoves()
        
        # Add castling moves
        valid_moves = List.empty_list(Move.class_type.instance_type)  # Initialize typed list
        if self.whiteToMove:
            getCastleMoves(self.board, self.whiteKingLocation[0], self.whiteKingLocation[1], moves, 
                         self.whiteToMove, self.currentCastlingRight, self.whiteKingLocation)
        else:
            getCastleMoves(self.board, self.blackKingLocation[0], self.blackKingLocation[1], moves, 
                         self.whiteToMove, self.currentCastlingRight, self.blackKingLocation)
        
        # Filter moves that leave king in check
        for move in moves:
            # Make the move
            original_piece = self.board[move.endRow, move.endCol]
            self.board[move.endRow, move.endCol] = move.pieceMoved
            self.board[move.startRow, move.startCol] = 0
            
            # Update king position temporarily if king moved
            original_king_pos = None
            if move.pieceMoved == 16:  # White king
                original_king_pos = self.whiteKingLocation
                self.whiteKingLocation = (move.endRow, move.endCol)
            elif move.pieceMoved == 26:  # Black king
                original_king_pos = self.blackKingLocation
                self.blackKingLocation = (move.endRow, move.endCol)
            
            # Check if king is in check after move
            in_check = False
            if self.whiteToMove:
                in_check = squareUnderAttack(self.board, self.whiteKingLocation[0], self.whiteKingLocation[1], False)
            else:
                in_check = squareUnderAttack(self.board, self.blackKingLocation[0], self.blackKingLocation[1], True)
            
            if not in_check:
                valid_moves.append(move)
            
            # Undo the move
            self.board[move.startRow, move.startCol] = move.pieceMoved
            self.board[move.endRow, move.endCol] = original_piece
            
            # Restore king position if it was moved
            if move.pieceMoved == 16 and original_king_pos:
                self.whiteKingLocation = original_king_pos
            elif move.pieceMoved == 26 and original_king_pos:
                self.blackKingLocation = original_king_pos
        
        return valid_moves