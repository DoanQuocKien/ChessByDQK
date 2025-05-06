"""
Main file to recieve user inputs and displaying chess matches (CurrentGameState object)
"""
import pygame as p
import ChessEngine

WIDTH = HEIGHT = 514
DIMENSION = 8 #dimensions of a chess board are 8x8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15 #for animation
IMAGES = {}



def loadImages():
    """
    Initialize a global dictionary of chess pieces. Call once
    """
    pieces = ['wp', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bp', 'bR', 'bN', 'bB', 'bQ', 'bK']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load(f"images/{piece}.png"), (SQ_SIZE, SQ_SIZE))

def main():
    """
    Main driver. Handle User Input and Updating Graphics
    """
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = ChessEngine.GameState()
    loadImages()
    running = True
    while running:
        for e in p.event.get():
            if(e.type == p.QUIT):
                running = False
        drawGameState(screen, gs)
        clock.tick(MAX_FPS)
        p.display.flip()

def drawGameState(screen, gs):
    """
    Display gamestates
    - screen: the size of the screen
    - gs: the coded gamestates
    """
    drawBoard(screen)
    drawPieces(screen, gs.board)

def drawBoard(screen):
    """
    Draw the board
    - screen: the size of the screen
    """
    colors = [p.Color("white"), p.Color("gray")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[(r + c) % 2]
            p.draw.rect(screen, color, p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def drawPieces(screen, board):
    """
    Draw the pieces
    - screen: the size of the screen
    - board: the states of pieces on the board taken out before
    """
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--": #not empty square
                screen.blit(IMAGES[piece], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

if __name__ == "__main__":
    main()

