import pickle

# Replace with the path to your .pkl file
filename = "saved_games/2025-05-15_23-19-49.pkl"

with open(filename, "rb") as f:
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