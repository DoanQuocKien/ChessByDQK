"""
ReplayViewer.py

Handles loading, listing, and managing replay (saved) games.

Author: Doan Quoc Kien
"""

import os
import pickle
import copy
import ChessEngine as CsE

SAVE_DIR = os.path.join(os.getenv('LOCALAPPDATA'), "ChessGame", "saved_games")

class ReplayGame:
    """
    Represents a replayable saved game.

    Attributes:
        moveLog (list): List of move notations.
        positions (list): List of board positions.
    """
    def __init__(self, filename):
        self.filename = filename
        self.moveLog = []
        self.positions = []
        self.load()

    def load(self):
        with open(self.filename, "rb") as f:
            data = pickle.load(f)
        self.moveLog = data["moveLog"]
        self.positions = data["positions"]

class ReplayManager:
    """
    Manages replay (saved) games for different users.
    """
    def __init__(self, savedDirectory):
        self.savedDirectory = savedDirectory

    def list_games(self):
        """
        Lists all saved game files in the given directory.

        Returns:
            list: List of file paths for saved games.
        """
        if not os.path.exists(self.savedDirectory):
            os.makedirs(self.savedDirectory)
        return [os.path.join(self.savedDirectory, f) for f in os.listdir(self.savedDirectory) if f.endswith(".pkl")]

    def load_game(self, filepath):
        """
        Loads a saved game from a file.

        Parameters:
            filepath (str): Path to the saved game file.

        Returns:
            ReplayGame: The loaded replay game object.
        """
        return ReplayGame(filepath)

manager = ReplayManager(SAVE_DIR)
files = manager.list_games()