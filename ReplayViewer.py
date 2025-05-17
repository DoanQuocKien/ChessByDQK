"""
ReplayViewer.py

Handles loading, listing, and managing replay (saved) games.

Author: Doan Quoc Kien
"""

import os
import pickle
import copy
import ChessEngine as CsE

SAVE_DIR = "saved_games"

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
    def __init__(self):
        self.games = self._get_saved_games()

    def _get_saved_games(self):
        if not os.path.exists(SAVE_DIR):
            os.makedirs(SAVE_DIR)
        files = [f for f in os.listdir(SAVE_DIR) if f.endswith(".pkl")]
        files.sort()
        return [os.path.join(SAVE_DIR, f) for f in files]

    def list_games(self, directory=SAVE_DIR):
        """
        Lists all saved game files in the given directory.

        Parameters:
            directory (str): Path to the user's save directory.

        Returns:
            list: List of file paths for saved games.
        """
        if not os.path.exists(directory):
            return []
        return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".pkl")]

    def load_game(self, filepath):
        """
        Loads a saved game from a file.

        Parameters:
            filepath (str): Path to the saved game file.

        Returns:
            ReplayGame: The loaded replay game object.
        """
        return ReplayGame(filepath)

manager = ReplayManager()
files = manager.list_games()