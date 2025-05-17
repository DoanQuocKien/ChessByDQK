"""
InspectSave.py

Provides utilities for inspecting and analyzing saved chess games.

Author: Doan Quoc Kien
"""

import pickle

def inspect_save(filepath):
    """
    Inspects and prints details of a saved game file.

    Parameters:
        filepath (str): Path to the saved game file.

    Returns:
        None
    """
    with open(filepath, "rb") as f:
        data = pickle.load(f)

    print("Keys in file:", data.keys())
    print("Number of moves:", len(data["moveLog"]))
    print("Number of positions:", len(data["positions"]))

    # Print first move and first board position
    if data["moveLog"]:
        print("First move:", data["moveLog"][0])
    if data["positions"]:
        print("First board position:")
        for row in data["positions"][0]:
            print(row)