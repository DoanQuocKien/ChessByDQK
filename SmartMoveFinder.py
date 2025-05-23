"""
SmartMoveFinder.py

Provides AI move selection and board evaluation for the chess game.
Implements NegaMax and MinMax algorithms, board scoring, and helper functions for computer play.

Author: Doan Quoc Kien
"""
import numpy as np
import random
from multiprocessing import Queue, Pool

pieceScore = {
    1: 1.5,  # White pawn
    2: 4.5,  # White knight
    3: 4.5,  # White bishop
    4: 7.5,  # White rook
    5: 13.5,  # White queen
    6: 0,  # White king
}

kightScore = np.array([[1, 1, 1, 1, 1, 1, 1, 1],
                      [1, 2, 2, 2, 2, 2, 2, 1],
                      [1, 2, 3, 3, 3, 3, 2, 1],
                      [1, 2, 3, 4, 4, 3, 2, 1],
                      [1, 2, 3, 4, 4, 3, 2, 1],
                      [1, 2, 3, 3, 3, 3, 2, 1],
                      [1, 2, 2, 2, 2, 2, 2, 1],
                      [1, 1, 1, 1, 1, 1, 1, 1]])

bishopScore = np.array([[4, 3, 2, 1, 1, 2, 3, 4],
                       [3, 4, 3, 2, 2, 3, 4, 3],
                       [2, 3, 4, 3, 3, 4, 3, 2],
                       [1, 2, 3, 4, 4, 3, 2, 1],
                       [1, 2, 3, 4, 4, 3, 2, 1],
                       [2, 3, 4, 3, 3, 4, 3, 2],
                       [3, 4, 3, 2, 2, 3, 4, 3],
                       [4, 3, 2, 1, 1, 2, 3, 4]])

queenScore = np.array([[1, 1, 1, 3, 1, 1, 1, 1],
                      [1, 2, 3, 3, 3, 1, 1, 1],
                      [1, 4, 3, 3, 3, 4, 2, 1],
                      [1, 2, 3, 3, 3, 2, 2, 1],
                      [1, 2, 3, 3, 3, 2, 2, 1],
                      [1, 4, 3, 3, 3, 4, 2, 1],
                      [1, 2, 3, 3, 3, 1, 1, 1],
                      [1, 1, 1, 3, 1, 1, 1, 1]])

rookScore = np.array([[4, 3, 4, 4, 4, 4, 3, 4],
                     [4, 4, 4, 4, 4, 4, 4, 4],
                     [1, 1, 2, 3, 3, 2, 1, 1],
                     [1, 2, 3, 4, 4, 3, 2, 1],
                     [1, 2, 3, 4, 4, 3, 2, 1],
                     [1, 1, 2, 3, 3, 2, 1, 1],
                     [4, 4, 4, 4, 4, 4, 4, 4],
                     [4, 3, 4, 4, 4, 4, 3, 4]])

whitePawnScore = np.array([[8, 8, 8, 8, 8, 8, 8, 8],
                          [8, 8, 8, 8, 8, 8, 8, 8],
                          [5, 6, 6, 7, 7, 6, 6, 5],
                          [2, 3, 3, 5, 5, 3, 3, 2],
                          [1, 2, 3, 4, 4, 3, 2, 1],
                          [1, 1, 2, 3, 3, 2, 1, 1],
                          [1, 1, 1, 0, 0, 1, 1, 1],
                          [0, 0, 0, 0, 0, 0, 0, 0]])

blackPawnScore = np.array([[0, 0, 0, 0, 0, 0, 0, 0],
                          [1, 1, 1, 0, 0, 1, 1, 1],
                          [1, 1, 2, 3, 3, 2, 1, 1],
                          [1, 2, 3, 4, 4, 3, 2, 1],
                          [2, 3, 3, 5, 5, 3, 3, 2],
                          [5, 6, 6, 7, 7, 6, 6, 5],
                          [8, 8, 8, 8, 8, 8, 8, 8],
                          [8, 8, 8, 8, 8, 8, 8, 8]])

piecePositionScores = {2: kightScore, 
                       3: bishopScore,
                       5: queenScore,
                       4: rookScore,
                       11: whitePawnScore,
                       21: blackPawnScore}

CHECKMATE = 1000000
DRAW = 0
DEPTH = 2

transpositionTable = {}

def findRandomMove(validMoves):
    """
    Selects and returns a random move from the list of valid moves.

    Parameters:
        validMoves (list): List of valid moves.

    Returns:
        Move or None: A randomly selected move, or None if no valid moves are available.
    """
    if not validMoves:  # Check if the list is empty
        return None
    return validMoves[random.randint(0, len(validMoves) - 1)]

def parallelEvaluateMove(args):
    """
    Evaluates a move in parallel for multiprocessing.

    Parameters:
        args (tuple): (gs, move, depth, alpha, beta, turnMultiplier)

    Returns:
        tuple: (score (float), move)
    """
    gs, move, depth, alpha, beta, turnMultiplier = args
    gs.makeMove(move)
    nextMoves = gs.getValidMoves()
    score = -findMoveNegaMaxAlphaBeta(gs, nextMoves, depth - 1, -beta, -alpha, -turnMultiplier)
    gs.undoMove()
    return score, move

def findBestMove(gs, validMoves, returnQueue):
    """
    Finds the best move using NegaMax with alpha-beta pruning and multiprocessing.

    Parameters:
        gs (GameState): Current game state.
        validMoves (list): List of valid moves.
        returnQueue (multiprocessing.Queue): Queue to return the best move.

    Returns:
        None: The best move is put into returnQueue.
    """
    with Pool() as pool:
        results = pool.map(parallelEvaluateMove, [(gs, move, DEPTH, -CHECKMATE, CHECKMATE, 1 if gs.whiteToMove else -1) for move in validMoves])
    global nextMove
    nextMove = max(results, key=lambda x: x[0])[1]
    returnQueue.put(nextMove)

def findMoveNegaMaxAlphaBeta(gs, validMoves, depth, alpha, beta, turnMultiplier):
    """
    Recursively searches for the best move using NegaMax with alpha-beta pruning.

    Parameters:
        gs (GameState): Current game state.
        validMoves (list): List of valid moves.
        depth (int): Search depth.
        alpha (float): Alpha value for pruning.
        beta (float): Beta value for pruning.
        turnMultiplier (int): 1 for white, -1 for black.

    Returns:
        float: Evaluation score of the position.
    """
    global nextMove
    boardHash = hash(str(gs.board))
    if boardHash in transpositionTable and transpositionTable[boardHash][0] >= depth:
        return transpositionTable[boardHash][1]

    if depth == 0:
        return turnMultiplier * scoreBoard(gs)
    
    maxScore = -CHECKMATE
    validMoves = orderMoves(gs, validMoves)
    validMoves = validMoves[:10]
    for move in validMoves:
        gs.makeMove(move)
        nextMoves = gs.getValidMoves()
        score = -findMoveNegaMaxAlphaBeta(gs, nextMoves, depth - 1, -beta, -alpha, -turnMultiplier)
        if score > maxScore:
            maxScore = score
            if depth == DEPTH:
                nextMove = move
        gs.undoMove()
        if maxScore > alpha:  # pruning happens
            alpha = maxScore
        if alpha >= beta:
            break

    transpositionTable[boardHash] = (depth, maxScore)
    return maxScore

def scoreBoard(gs):
    """
    Evaluates and scores the board position.

    Parameters:
        gs (GameState): Current game state.

    Returns:
        float: Positive for white advantage, negative for black.
    """
    if gs.checkMate:
        if gs.whiteToMove:
            return -CHECKMATE  # Black wins
        else:
            return CHECKMATE  # White wins
    elif gs.draw:
        return DRAW

    score = 0

    # Material and positional scoring
    for row in range(len(gs.board)):
        for col in range(len(gs.board[row])):
            square = gs.board[row][col]
            if square != 0:
                # Score it positionally
                piecePositionScore = 0
                if square % 10 != 6:  # No position table for king, yet
                    if square % 10 == 1:  # For pawns
                        piecePositionScore = piecePositionScores[int(square)][row][col]
                    else:  # For other pieces
                        piecePositionScore = piecePositionScores[int(square % 10)][row][col]

                if square // 10 == 1:  # White piece
                    score += pieceScore[int(square % 10)] + piecePositionScore * 0.05
                elif square // 10 == 2:  # Black piece
                    score -= pieceScore[int(square % 10)] + piecePositionScore * 0.05


    # Additional scoring conditions

    # 1. King safety
    score += evaluateKingSafety(gs, True)
    score -= evaluateKingSafety(gs, False)

    # 2. Control of the center
    centerSquares = [(3, 3), (3, 4), (4, 3), (4, 4)]
    for r, c in centerSquares:
        piece = gs.board[r][c]
        if piece != 0:
            if piece // 10 == 1:  # White controls center
                score += 1
            elif piece // 10 == 2:  # Black controls center
                score -= 1

    # 3. Pawn structure
    score += evaluatePawnStructure(gs)

    # 4. Mobility (number of valid moves)
    whiteMoves = len(gs.getValidMoves()) if gs.whiteToMove else 0
    blackMoves = len(gs.getValidMoves()) if not gs.whiteToMove else 0
    score += 0.05 * whiteMoves
    score -= 0.05 * blackMoves

    return score

def evaluateKingSafety(gs, isWhite):
    """
    Evaluates the safety of the king for a given side.

    Parameters:
        gs (GameState): Current game state.
        isWhite (bool): True for white king, False for black king.

    Returns:
        float: King safety score (positive is safer).
    """
    kingPosition = gs.whiteKingLocation if isWhite else gs.blackKingLocation
    kingRow, kingCol = kingPosition
    safetyScore = 0

    # Penalize if the king is in the center
    if 2 <= kingRow <= 5 and 2 <= kingCol <= 5:
        safetyScore -= 2  # King is in the center

    # Penalize if the king is exposed (no pawns nearby)
    pawnRow = kingRow - 1 if isWhite else kingRow + 1
    if 0 <= pawnRow < 8:
        if kingCol - 1 >= 0 and gs.board[pawnRow][kingCol - 1] % 10 == 1:
            safetyScore += 2  # Pawn on the left
        if kingCol + 1 < 8 and gs.board[pawnRow][kingCol + 1] % 10 == 1:
            safetyScore += 2  # Pawn on the right

    return safetyScore

def evaluatePawnStructure(gs):
    """
    Evaluates the pawn structure for both sides.

    Parameters:
        gs (GameState): Current game state.

    Returns:
        float: Pawn structure score (positive for white, negative for black).
    """
    score = 0
    whitePawns = [col for row in gs.board for col in row if col == 11]
    blackPawns = [col for row in gs.board for col in row if col == 21]

    # Penalize doubled pawns
    for col in range(8):
        whitePawnsInCol = sum(1 for row in range(8) if gs.board[row][col] == 11)
        blackPawnsInCol = sum(1 for row in range(8) if gs.board[row][col] == 21)
        if whitePawnsInCol > 1:
            score -= 0.2 * (whitePawnsInCol - 1)  # Penalize doubled white pawns
        if blackPawnsInCol > 1:
            score += 0.2 * (blackPawnsInCol - 1)  # Penalize doubled black pawns

    # Reward connected pawns
    for row in range(8):
        for col in range(8):
            if gs.board[row][col] == 11:  # White pawn
                if col - 1 >= 0 and gs.board[row][col - 1] == 11:
                    score += 0.1  # Connected white pawn
                if col + 1 < 8 and gs.board[row][col + 1] == 11:
                    score += 0.1  # Connected white pawn
            elif gs.board[row][col] == 21:  # Black pawn
                if col - 1 >= 0 and gs.board[row][col - 1] == 21:
                    score -= 0.1  # Connected black pawn
                if col + 1 < 8 and gs.board[row][col + 1] == 21:
                    score -= 0.1  # Connected black pawn

    return score

def findBestMoveMinMax(gs, validMoves, returnQueue):
    """
    Finds the best move using the MinMax algorithm.

    Parameters:
        gs (GameState): Current game state.
        validMoves (list): List of valid moves.
        returnQueue (multiprocessing.Queue): Queue to return the best move.

    Returns:
        None: The best move is put into returnQueue.
    """
    global nextMove
    nextMove = None
    random.shuffle(validMoves)
    findMoveMinMax(gs, validMoves, DEPTH, gs.whiteToMove)
    returnQueue.put(nextMove)

def findMoveMinMax(gs, validMoves, depth, whiteToMove):
    """
    Recursively searches for the best move using MinMax.

    Parameters:
        gs (GameState): Current game state.
        validMoves (list): List of valid moves.
        depth (int): Search depth.
        whiteToMove (bool): True if white's turn, False otherwise.

    Returns:
        float: Evaluation score of the position.
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
    Gets the best move for the current game state using multiprocessing.

    Parameters:
        gs (GameState): Current game state.
        validMoves (list): List of valid moves.

    Returns:
        Move or None: The best move, or None if no valid moves are available.
    """
    if not validMoves:  # Check if there are no valid moves
        return None
        
    returnQueue = Queue()
    findBestMove(gs, validMoves, returnQueue)
    return returnQueue.get()

def orderMoves(gs, validMoves):
    """
    Orders moves based on a simple heuristic to improve search efficiency.

    Parameters:
        gs (GameState): Current game state.
        validMoves (list): List of valid moves.

    Returns:
        list: Sorted list of moves (best first).
    """
    def moveHeuristic(move):
        startScore = scoreBoard(gs)
        gs.makeMove(move)
        endScore = scoreBoard(gs)
        gs.undoMove()
        return (endScore - startScore) * (1 if gs.whiteToMove else -1)
    return sorted(validMoves, key=moveHeuristic, reverse=True)