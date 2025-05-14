"""
This file is responsible for operating an AI to play against the player
with Numba optimization for improved performance
"""

import numpy as np
import random
from multiprocessing import Queue, Pool
from numba import njit, int32, float64, prange, types
from numba.typed import Dict, List
import pickle
import hashlib

# Define piece scores as constants for Numba functions
PAWN_SCORE = 1
KNIGHT_SCORE = 3
BISHOP_SCORE = 3
ROOK_SCORE = 5
QUEEN_SCORE = 9
KING_SCORE = 0

# Convert piece scores to a Numba-compatible dictionary
pieceScoreDict = Dict.empty(
    key_type=types.int32,
    value_type=types.float64,
)
pieceScoreDict[1] = 1.0  # White pawn
pieceScoreDict[2] = 3.0  # White knight
pieceScoreDict[3] = 3.0  # White bishop
pieceScoreDict[4] = 5.0  # White rook
pieceScoreDict[5] = 9.0  # White queen
pieceScoreDict[6] = 0.0  # White king

# Create piece position score arrays with Numba-compatible types
kightScore = np.array([
    [1, 1, 1, 1, 1, 1, 1, 1],
    [1, 2, 2, 2, 2, 2, 2, 1],
    [1, 2, 3, 3, 3, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 3, 3, 3, 2, 1],
    [1, 2, 2, 2, 2, 2, 2, 1],
    [1, 1, 1, 1, 1, 1, 1, 1]
], dtype=np.float64)

bishopScore = np.array([
    [4, 3, 2, 1, 1, 2, 3, 4],
    [3, 4, 3, 2, 2, 3, 4, 3],
    [2, 3, 4, 3, 3, 4, 3, 2],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [2, 3, 4, 3, 3, 4, 3, 2],
    [3, 4, 3, 2, 2, 3, 4, 3],
    [4, 3, 2, 1, 1, 2, 3, 4]
], dtype=np.float64)

queenScore = np.array([
    [1, 1, 1, 3, 1, 1, 1, 1],
    [1, 2, 3, 3, 3, 1, 1, 1],
    [1, 4, 3, 3, 3, 4, 2, 1],
    [1, 2, 3, 3, 3, 2, 2, 1],
    [1, 2, 3, 3, 3, 2, 2, 1],
    [1, 4, 3, 3, 3, 4, 2, 1],
    [1, 2, 3, 3, 3, 1, 1, 1],
    [1, 1, 1, 3, 1, 1, 1, 1]
], dtype=np.float64)

rookScore = np.array([
    [4, 3, 4, 4, 4, 4, 3, 4],
    [4, 4, 4, 4, 4, 4, 4, 4],
    [1, 1, 2, 3, 3, 2, 1, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 1, 2, 3, 3, 2, 1, 1],
    [4, 4, 4, 4, 4, 4, 4, 4],
    [4, 3, 4, 4, 4, 4, 3, 4]
], dtype=np.float64)

whitePawnScore = np.array([
    [8, 8, 8, 8, 8, 8, 8, 8],
    [8, 8, 8, 8, 8, 8, 8, 8],
    [5, 6, 6, 7, 7, 6, 6, 5],
    [2, 3, 3, 5, 5, 3, 3, 2],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 1, 2, 3, 3, 2, 1, 1],
    [1, 1, 1, 0, 0, 1, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0]
], dtype=np.float64)

blackPawnScore = np.array([
    [0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 0, 0, 1, 1, 1],
    [1, 1, 2, 3, 3, 2, 1, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [2, 3, 3, 5, 5, 3, 3, 2],
    [5, 6, 6, 7, 7, 6, 6, 5],
    [8, 8, 8, 8, 8, 8, 8, 8],
    [8, 8, 8, 8, 8, 8, 8, 8]
], dtype=np.float64)

# Global constants
CHECKMATE = 1000000
DRAW = 0
DEPTH = 4

# Numba doesn't support dictionary of numpy arrays, so we'll use functions instead
@njit(float64(int32, int32, int32), cache=True)
def getPiecePositionScore(pieceType, row, col):
    """Get the position score for a specific piece type at a given position"""
    if pieceType == 2:  # Knight
        return kightScore[row][col]
    elif pieceType == 3:  # Bishop
        return bishopScore[row][col]
    elif pieceType == 4:  # Rook
        return rookScore[row][col]
    elif pieceType == 5:  # Queen
        return queenScore[row][col]
    elif pieceType == 11:  # White pawn
        return whitePawnScore[row][col]
    elif pieceType == 21:  # Black pawn
        return blackPawnScore[row][col]
    return 0.0

# Global transposition table (can't use Numba for this, will use pickle for hashing)
transpositionTable = {}

def hash_board(board):
    """Create a hash of the board for transposition table"""
    board_bytes = pickle.dumps(board)
    return hashlib.md5(board_bytes).hexdigest()

def findRandomMove(validMoves):
    """
    Returns a random move from the list of valid moves.
    If no valid moves are available, returns None.
    """
    if not validMoves:  # Check if the list is empty
        return None
    return validMoves[random.randint(0, len(validMoves) - 1)]

def parallelEvaluateMove(args):
    gs, move, depth, alpha, beta, turnMultiplier = args
    gs.makeMove(move)
    nextMoves = gs.getValidMoves()
    score = -findMoveNegaMaxAlphaBeta(gs, nextMoves, depth - 1, -beta, -alpha, -turnMultiplier)
    gs.undoMove()
    return score, move

def findBestMove(gs, validMoves, returnQueue):
    """
    Helper method to make first recursive call with parallel processing
    """
    with Pool() as pool:
        results = pool.map(parallelEvaluateMove, [(gs, move, DEPTH, -CHECKMATE, CHECKMATE, 1 if gs.whiteToMove else -1) for move in validMoves])
    global nextMove
    nextMove = max(results, key=lambda x: x[0])[1]
    returnQueue.put(nextMove)

@njit(float64(float64[:, :], types.boolean, types.UniTuple(int32, 2), types.UniTuple(int32, 2)), cache=True)
def evaluate_king_safety(board, isWhite, whiteKingLocation, blackKingLocation):
    """
    Evaluate the safety of the king.
    A king in the center or exposed to attacks is penalized.
    """
    king_row, king_col = whiteKingLocation if isWhite else blackKingLocation
    safety_score = 0.0

    # Penalize if the king is in the center
    if 2 <= king_row <= 5 and 2 <= king_col <= 5:
        safety_score -= 2.0  # King is in the center

    # Penalize if the king is exposed (no pawns nearby)
    pawn_row = king_row - 1 if isWhite else king_row + 1
    if 0 <= pawn_row < 8:
        if king_col - 1 >= 0 and board[pawn_row][king_col - 1] % 10 == 1:
            safety_score += 1.0  # Pawn on the left
        if king_col + 1 < 8 and board[pawn_row][king_col + 1] % 10 == 1:
            safety_score += 1.0  # Pawn on the right

    return safety_score

@njit(float64(float64[:, :]), cache=True)
def evaluate_pawn_structure(board):
    """
    Evaluate the pawn structure.
    Reward connected pawns and penalize isolated or doubled pawns.
    """
    score = 0.0

    # Penalize doubled pawns
    for col in range(8):
        white_pawns_in_col = 0
        black_pawns_in_col = 0
        for row in range(8):
            if board[row][col] == 11:  # White pawn
                white_pawns_in_col += 1
            elif board[row][col] == 21:  # Black pawn
                black_pawns_in_col += 1
        
        if white_pawns_in_col > 1:
            score -= 0.2 * (white_pawns_in_col - 1)  # Penalize doubled white pawns
        if black_pawns_in_col > 1:
            score += 0.2 * (black_pawns_in_col - 1)  # Penalize doubled black pawns

    # Reward connected pawns
    for row in range(8):
        for col in range(8):
            if board[row][col] == 11:  # White pawn
                if col - 1 >= 0 and board[row][col - 1] == 11:
                    score += 0.1  # Connected white pawn
                if col + 1 < 8 and board[row][col + 1] == 11:
                    score += 0.1  # Connected white pawn
            elif board[row][col] == 21:  # Black pawn
                if col - 1 >= 0 and board[row][col - 1] == 21:
                    score -= 0.1  # Connected black pawn
                if col + 1 < 8 and board[row][col + 1] == 21:
                    score -= 0.1  # Connected black pawn

    return score

@njit(
    float64(
        float64[:, :],  # board
        types.boolean,  # checkmate
        types.boolean,  # draw
        types.UniTuple(int32, 2),  # whiteKingLocation
        types.UniTuple(int32, 2),  # blackKingLocation
        int32,  # valid_moves_count
        types.DictType(int32, float64)  # pieceScoreDict
    ),
    cache=True
)
def score_board_numba(board, checkmate, draw, whiteKingLocation, blackKingLocation, valid_moves_count, pieceScoreDict):
    """
    Score the board. A positive score is good for white, a negative score is good for black.
    Numba optimized version.
    """
    if checkmate:
        if board[0][0] == -1:  # White's turn
            return -CHECKMATE  # Black wins
        else:
            return CHECKMATE  # White wins
    elif draw:
        return DRAW

    score = 0.0

    # Material and positional scoring
    for row in range(len(board)):
        for col in range(len(board[0])):
            square = board[row][col]
            if square != 0 and square != -1:  # Skip empty squares and turn marker
                piece_position_score = 0.0
                if square % 10 != 6:  # No position table for king
                    piece_position_score = getPiecePositionScore(int(square % 10), row, col)

                if square // 10 == 1:  # White piece
                    piece_value = pieceScoreDict[int(square % 10)]
                    score += piece_value + piece_position_score * 0.1
                elif square // 10 == 2:  # Black piece
                    piece_value = pieceScoreDict[int(square % 10)]
                    score -= piece_value + piece_position_score * 0.1

    # Additional scoring conditions
    white_to_move = (board[0][0] == -1)
    if white_to_move:
        score += evaluate_king_safety(board, True, whiteKingLocation, blackKingLocation)
        score -= evaluate_king_safety(board, False, whiteKingLocation, blackKingLocation)
    else:
        score += evaluate_king_safety(board, False, whiteKingLocation, blackKingLocation)
        score -= evaluate_king_safety(board, True, whiteKingLocation, blackKingLocation)

    # Control of the center
    center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
    for r, c in center_squares:
        piece = board[r][c]
        if piece != 0 and piece != -1:
            if piece // 10 == 1:  # White controls center
                score += 2.0
            elif piece // 10 == 2:  # Black controls center
                score -= 2.0

    # Pawn structure
    score += evaluate_pawn_structure(board)

    # Mobility
    score += 0.1 * valid_moves_count if white_to_move else -0.1 * valid_moves_count

    return score

def scoreBoard(gs):
    """
    Wrapper function for the Numba-optimized score_board_numba function.
    Prepares the board and calls the JIT-compiled function.
    """
    # Create a copy of the board as a float array for Numba
    board_array = np.array(gs.board, dtype=np.float64)
    
    # Add a marker for turn in an unused part of the board (top-left corner)
    board_array[0][0] = -1.0 if gs.whiteToMove else 0.0
    
    # Convert king locations to tuples for Numba
    whiteKingLocation = (gs.whiteKingLocation[0], gs.whiteKingLocation[1])
    blackKingLocation = (gs.blackKingLocation[0], gs.blackKingLocation[1])
    
    # Count valid moves for mobility score
    valid_moves_count = len(gs.getValidMoves())
    
    # Call the Numba-optimized function
    return score_board_numba(
        board_array, 
        gs.checkMate, 
        gs.draw, 
        whiteKingLocation, 
        blackKingLocation, 
        valid_moves_count,
        pieceScoreDict  # Pass the dictionary as an argument
    )

def findMoveNegaMaxAlphaBeta(gs, validMoves, depth, alpha, beta, turnMultiplier):
    """
    Find the best move using NegaMax algorithm with Alpha-Beta pruning
    """
    global nextMove
    
    # Use transposition table for caching
    board_hash = hash_board(gs.board)
    if board_hash in transpositionTable and transpositionTable[board_hash][0] >= depth:
        return transpositionTable[board_hash][1]

    if depth == 0:
        return turnMultiplier * scoreBoard(gs)
    
    maxScore = -CHECKMATE
    validMoves = orderMoves(gs, validMoves)
    for move in validMoves:
        gs.makeMove(move)
        nextMoves = gs.getValidMoves()
        score = -findMoveNegaMaxAlphaBeta(gs, nextMoves, depth - 1, -beta, -alpha, -turnMultiplier)
        if score > maxScore:
            maxScore = score
            if depth == DEPTH:
                nextMove = move
        gs.undoMove()
        
        # Alpha-beta pruning
        if maxScore > alpha:
            alpha = maxScore
        if alpha >= beta:
            break

    # Store result in transposition table
    transpositionTable[board_hash] = (depth, maxScore)
    return maxScore

def findBestMoveMinMax(gs, validMoves, returnQueue):
    """
    Helper method to make first recursive call
    """
    global nextMove
    nextMove = None
    random.shuffle(validMoves)
    findMoveMinMax(gs, validMoves, DEPTH, gs.whiteToMove)
    returnQueue.put(nextMove)

def findMoveMinMax(gs, validMoves, depth, whiteToMove):
    """
    Find the best move using MinMax algorithm
    """
    global nextMove
    if depth == 0:
        return scoreBoard(gs)
    
    if whiteToMove:
        maxScore = -CHECKMATE
        for move in validMoves:
            gs.makeMove(move)
            nextMoves = gs.getValidMoves()
            score = findMoveMinMax(gs, nextMoves, depth - 1, False)
            if score > maxScore:
                maxScore = score
                if depth == DEPTH:
                    nextMove = move
            gs.undoMove()
        return maxScore
    
    else:
        minScore = CHECKMATE
        for move in validMoves:
            gs.makeMove(move)
            nextMoves = gs.getValidMoves()
            score = findMoveMinMax(gs, nextMoves, depth - 1, True)
            if score < minScore:
                minScore = score
                if depth == DEPTH:
                    nextMove = move
            gs.undoMove()
        return minScore

def getMove(gs, validMoves):
    """
    Get the best move for the current game state.
    Returns None if no valid moves are available.
    """
    if not validMoves:  # Check if there are no valid moves
        return None
        
    returnQueue = Queue()
    findBestMove(gs, validMoves, returnQueue)
    return returnQueue.get()

@njit(float64(int32, int32, float64[:, :], types.DictType(int32, float64)), cache=True)
def calculate_move_score(start_piece, end_piece, board, pieceScoreDict):
    """Calculate the score for a move for move ordering"""
    # Skip empty squares
    start_score = pieceScoreDict[int(start_piece % 10)] if start_piece != 0 else 0
    end_score = pieceScoreDict[int(end_piece % 10)] if end_piece != 0 else 0
    return end_score - start_score

def orderMoves(gs, validMoves):
    """Order moves to improve alpha-beta pruning efficiency"""
    move_scores = []
    
    for move in validMoves:
        start_piece = gs.board[move.startRow][move.startCol]
        end_piece = gs.board[move.endRow][move.endCol]
        
        # Convert board to Numba-compatible array
        board_array = np.array(gs.board, dtype=np.float64)
        
        # Calculate move score
        score = 0
        if end_piece != 0:  # Capture move
            score = 10 * calculate_move_score(start_piece, end_piece, board_array, pieceScoreDict)
        
        # Prioritize promotions
        if move.isPawnPromotion:
            score += 9  # Queen value
            
        # Prioritize checking moves
        gs.makeMove(move)
        if gs.inCheck():
            score += 5
        gs.undoMove()
        
        move_scores.append((move, score))
    
    # Sort moves by score in descending order
    sorted_moves = [x[0] for x in sorted(move_scores, key=lambda x: x[1], reverse=True)]
    return sorted_moves

# Initialize the nextMove variable for global access
nextMove = None

# Clear the transposition table at the start of each search
def clear_transposition_table():
    global transpositionTable
    transpositionTable = {}