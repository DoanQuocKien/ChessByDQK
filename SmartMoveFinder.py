"""
This file is responsible for operating an AI to play against the player
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
    Helper method to make first recursive call
    """
    with Pool() as pool:
        results = pool.map(parallelEvaluateMove, [(gs, move, DEPTH, -CHECKMATE, CHECKMATE, 1 if gs.whiteToMove else -1) for move in validMoves])
    global nextMove
    nextMove = max(results, key=lambda x: x[0])[1]
    returnQueue.put(nextMove)

def findMoveNegaMaxAlphaBeta(gs, validMoves, depth, alpha, beta, turnMultiplier):
    """
    Find the best move using NegaMax algorithm with Alpha-Beta pruning
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
    Score the board. A positive score is good for white, a negative score is good for black.
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
    if gs.whiteToMove:
        score += evaluateKingSafety(gs, True)
        score -= evaluateKingSafety(gs, False)
    else:
        score += evaluateKingSafety(gs, False)
        score -= evaluateKingSafety(gs, True)

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
    Evaluate the safety of the king.
    A king in the center or exposed to attacks is penalized.
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
    Evaluate the pawn structure.
    Reward connected pawns and penalize isolated or doubled pawns.
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

def orderMoves(gs, validMoves):
    def moveHeuristic(move):
        startScore = scoreBoard(gs)
        gs.makeMove(move)
        endScore = scoreBoard(gs)
        gs.undoMove()
        return (endScore - startScore) * (1 if gs.whiteToMove else -1)
    return sorted(validMoves, key=moveHeuristic, reverse=True)