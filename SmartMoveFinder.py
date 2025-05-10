"""
This file is responsible for operating an AI to play against the player
"""

import random


def findRandomMove(validMoves):
    """
    Find a random valid moves
    Parameter:
    validMoves: List of valid moves
    """
    return random.choice(validMoves)