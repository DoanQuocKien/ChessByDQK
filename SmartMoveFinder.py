"""
This file is responsible for operating an AI to play against the player
"""

import random

pieceScore = {"K" : 0, "Q" : 9, "R" : 5, "B" : 3, "N" : 3, "p" : 1}
CHECKMATE = 10000
DRAW = 0
DEPTH = 3

def findRandomMove(validMoves):
    """
    Find a random valid moves
    Parameter:
    validMoves: List of valid moves
    """
    return random.choice(validMoves)

def quiescence(gs, alpha, beta, turnMultiplier):
    """
    Implement quiescence search - extend the search past leaf nodes if the position is "unstable"
    """
    stand_pat = turnMultiplier * scoreBoard(gs)
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    # Only consider capture moves
    for move in gs.getValidMoves():
        if move.pieceCaptured != "--":
            gs.makeMove(move)
            score = -quiescence(gs, -beta, -alpha, -turnMultiplier)
            gs.undoMove()
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
    return alpha

def findBestMove(gs, validMoves, depth, alpha, beta, turnMultiplier):
    """
    Find the best move by min-maxing the next move with the number of move think-ahead = depth
    Or, negamax search + alpha-beta pruning
    Parameter:
    gs: Game State
    validMoves: list of possible move
    alpha, beta: for alpha-beta pruning
    depth: How many move ahead
    It returns the score and the best move
    """
    if depth == 0:
        return turnMultiplier * scoreBoard(gs), None
    
    bestMove = None
    
    # move ordering
    maxScore = -CHECKMATE
    for move in orderMoves(validMoves):
        gs.makeMove(move)

        nextMoves = gs.getValidMoves()
        score, _ = findBestMove(gs, nextMoves, depth - 1, -beta, -alpha, -turnMultiplier)
        score = -score
        if score > maxScore:
            maxScore = score
            bestMove = move
            
        gs.undoMove()

        alpha = max(alpha, maxScore) # prunning happens
        if alpha >= beta:
            break

    return maxScore, bestMove

def getMove(gs, validMoves, depth):
    """
    Get AI next move
    """
    _, bestMove = findBestMove(gs, validMoves, depth, -CHECKMATE, CHECKMATE, 1 if gs.whiteToMove else -1)
    return bestMove if bestMove else findRandomMove(validMoves)

def orderMoves(moves):
    """Sort moves to improve pruning: prioritize captures."""
    return sorted(moves, key=lambda m: pieceScore.get(m.pieceCaptured[1], 0) if m.pieceCaptured != "--" else 0, reverse=True)

def scoreBoard(gs):
    """
    Score of the board based on material
    Return: score, the greater the better for white, the lower the better for black
    """
    if gs.checkMate:
        if gs.whiteToMove:
            return -CHECKMATE #black win
        else:
            return CHECKMATE #white win
    if gs.draw:
        return DRAW
    score = 0
    for row in gs.board:
        for square in row:
            if square[0] == 'w':
                score += pieceScore[square[1]]
            elif square[0] == 'b':
                score -= pieceScore[square[1]]
    return score