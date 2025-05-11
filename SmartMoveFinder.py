"""
This file is responsible for operating an AI to play against the player
"""

import random

pieceScore = {"K" : 0, "Q" : 9, "R" : 5, "B" : 3, "N" : 3, "p" : 1}
CHECKMATE = 10000
DRAW = 0
DEPTH = 2

transpositionTable = {}

def findRandomMove(validMoves):
    """
    Find a random valid moves
    Parameter:
    validMoves: List of valid moves
    """
    return random.choice(validMoves)

def quiescence(gs, alpha, beta, turnMultiplier):
    """
    Improved quiescence search to handle unstable positions.
    """
    stand_pat = turnMultiplier * scoreBoard(gs)
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    for move in gs.getValidMoves():
        # Check if the move is a capture, promotion, or results in a check
        gs.makeMove(move)
        isCheck = gs.inCheck()
        gs.undoMove()

        if move.pieceCaptured != "--" or isCheck or move.pawnPromotion:
            gs.makeMove(move)
            score = -quiescence(gs, -beta, -alpha, -turnMultiplier)
            gs.undoMove()
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
    return alpha

def findBestMovePVS(gs, validMoves, depth, alpha, beta, turnMultiplier):
    """
    Principal Variation Search (PVS) with alpha-beta pruning.
    """
    if depth == 0:
        return turnMultiplier * scoreBoard(gs), None

    bestMove = None
    maxScore = -CHECKMATE
    firstMove = True
    for move in orderMoves(gs, validMoves):
        gs.makeMove(move)
        nextMoves = gs.getValidMoves()
        if firstMove:
            score, _ = findBestMovePVS(gs, nextMoves, depth - 1, -beta, -alpha, -turnMultiplier)
            firstMove = False
        else:
            score, _ = findBestMovePVS(gs, nextMoves, depth - 1, -alpha - 1, -alpha, -turnMultiplier)
            if alpha < score < beta:
                score, _ = findBestMovePVS(gs, nextMoves, depth - 1, -beta, -alpha, -turnMultiplier)
        score = -score
        gs.undoMove()

        if score > maxScore:
            maxScore = score
            bestMove = move

        alpha = max(alpha, maxScore)
        if alpha >= beta:
            break

    return maxScore, bestMove

def getMove(gs, validMoves, depth):
    """
    Get AI's next move using Principal Variation Search (PVS).
    """
    _, bestMove = findBestMovePVS(gs, validMoves, depth, -CHECKMATE, CHECKMATE, 1 if gs.whiteToMove else -1)
    return bestMove if bestMove else findRandomMove(validMoves)

def orderMoves(gs, moves):
    """Sort moves to improve pruning: prioritize captures, checks, promotions, and castling."""
    def moveScore(move):
        score = 0
        if move.pieceCaptured != "--":
            # MVV-LVA heuristic: prioritize capturing high-value pieces with low-value pieces
            score += 10 * pieceScore[move.pieceCaptured[1]] - pieceScore[move.pieceMoved[1]]
        
        # Simulate the move to check if it results in a check
        #gs.makeMove(move)
        #isCheck = gs.inCheck()
        #gs.undoMove()
        #if isCheck:
        #    score += 50  # Prioritize moves that put the opponent in check
        
        if move.pawnPromotion:
            score += 100  # Prioritize pawn promotions
        
        # Prioritize castling moves
        if move.isCastleMove:
            score += 75  # Encourage castling for king safety and rook activation
        
        return score

    return sorted(moves, key=moveScore, reverse=True)

def scoreBoard(gs):
    """
    Score the board based on material, mobility, king safety, pawn structure, 
    pieces threatened, pieces protected, and castling capability.
    Return: score, the greater the better for white, the lower the better for black.
    """
    if gs.checkMate:
        if gs.whiteToMove:
            return -CHECKMATE  # Black wins
        else:
            return CHECKMATE  # White wins
    if gs.draw:
        return DRAW

    score = 0

    # Material score
    for row in gs.board:
        for square in row:
            if square[0] == 'w':
                score += pieceScore[square[1]]
            elif square[0] == 'b':
                score -= pieceScore[square[1]]

    # Mobility (number of valid moves)
    whiteMoves = len(gs.getAllPossibleMoves()) if gs.whiteToMove else 0
    gs.whiteToMove = not gs.whiteToMove
    blackMoves = len(gs.getAllPossibleMoves()) if not gs.whiteToMove else 0
    gs.whiteToMove = not gs.whiteToMove
    score += 0.1 * whiteMoves - 0.1 * blackMoves

    # King safety
    score += evaluateKingSafety(gs)

    # Pawn structure
    score += evaluatePawnStructure(gs)

    # Control of the center
    score += evaluateCenterControl(gs)

    # Pieces threatened and protected
    score += evaluateThreatsAndProtections(gs)

    # Castling capability
    score += evaluateCastling(gs)

    return score

def evaluateKingSafety(gs):
    """
    Evaluate king safety based on pawn protection and exposure to attacks.
    """
    score = 0
    kingPositions = {"wK": gs.whiteKingLocation, "bK": gs.blackKingLocation}
    for color, kingPos in kingPositions.items():
        r, c = kingPos
        pawnDirection = -1 if color == "wK" else 1
        pawnProtection = [
            (r + pawnDirection, c - 1),
            (r + pawnDirection, c + 1),
        ]
        for pr, pc in pawnProtection:
            if gs.insideBoard(pr, pc) and gs.board[pr][pc] == color[0] + "p":
                score += 0.5 if color == "wK" else -0.5

        # Penalize exposed kings (e.g., no pawns nearby)
        if r < 2 or r > 5:  # Kings near the edges are more exposed
            score -= 1 if color == "wK" else -1

    return score

def evaluatePawnStructure(gs):
    """
    Evaluate pawn structure, penalizing doubled, isolated, and backward pawns.
    """
    score = 0
    whitePawns = [c for r in range(8) for c in range(8) if gs.board[r][c] == "wp"]
    blackPawns = [c for r in range(8) for c in range(8) if gs.board[r][c] == "bp"]

    # Penalize doubled pawns
    for col in range(8):
        whiteCount = sum(1 for r in range(8) if gs.board[r][col] == "wp")
        blackCount = sum(1 for r in range(8) if gs.board[r][col] == "bp")
        if whiteCount > 1:
            score -= 0.5 * (whiteCount - 1)
        if blackCount > 1:
            score += 0.5 * (blackCount - 1)

    # Penalize isolated pawns
    for col in range(8):
        if col > 0 and col < 7:
            whiteIsolated = all(gs.board[r][col - 1] != "wp" and gs.board[r][col + 1] != "wp" for r in range(8))
            blackIsolated = all(gs.board[r][col - 1] != "bp" and gs.board[r][col + 1] != "bp" for r in range(8))
        elif col == 0:
            whiteIsolated = all(gs.board[r][col + 1] != "wp" for r in range(8))
            blackIsolated = all(gs.board[r][col + 1] != "bp" for r in range(8))
        elif col == 7:
            whiteIsolated = all(gs.board[r][col - 1] != "wp" for r in range(8))
            blackIsolated = all(gs.board[r][col - 1] != "bp" for r in range(8))
        if whiteIsolated:
            score -= 0.5
        if blackIsolated:
            score += 0.5

    return score

def evaluateCenterControl(gs):
    """
    Evaluate control of the center squares (e4, d4, e5, d5).
    """
    centerSquares = [(3, 3), (3, 4), (4, 3), (4, 4)]
    score = 0
    for r, c in centerSquares:
        if gs.board[r][c][0] == "w":
            score += 5
        elif gs.board[r][c][0] == "b":
            score -= 5
    return score

def evaluateThreatsAndProtections(gs):
    """
    Evaluate pieces that are threatened or protected.
    """
    score = 0
    tempWhiteToMove = gs.whiteToMove
    for r in range(8):
        for c in range(8):
            piece = gs.board[r][c]
            if piece == "--":
                continue
            color = piece[0]
            pieceValue = pieceScore[piece[1]]

            # Check if the piece is threatened
            if gs.squareUnderAttack(r, c):
                score -= 0.5 * pieceValue if color == "w" else -0.5 * pieceValue

            # Check if the piece is protected
            gs.whiteToMove = (color == "w")
            if any(gs.squareUnderAttack(r + dr, c + dc) for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]):
                score += 0.3 * pieceValue if color == "w" else -0.3 * pieceValue
    gs.whiteToMove = tempWhiteToMove

    return score

def evaluateCastling(gs):
    """
    Evaluate castling capability and reward completed castling moves.
    """
    score = 0

    # Reward the ability to castle if it hasn't been done yet
    if gs.currentCastlingRight.wks or gs.currentCastlingRight.wqs:
        score += 4  # White can still castle
    if gs.currentCastlingRight.bks or gs.currentCastlingRight.bqs:
        score -= 4  # Black can still castle

    # Reward completed castling moves
    if gs.whiteKingLocation == (7, 6) or gs.whiteKingLocation == (7, 2):  # White has castled
        score += 5  # Reward for castling
    if gs.blackKingLocation == (0, 6) or gs.blackKingLocation == (0, 2):  # Black has castled
        score -= 5  # Reward for castling

    return score