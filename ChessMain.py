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
    validMoves = gs.getValidMoves()
    moveMade = False #flag variables for when a move is made

    loadImages()
    running = True
    squareSelected = () #keep track of last click: tuple(row, col)
    playerClicks = [] #keep track of players click: two tuples(row_from, col_from), (row_to, col_to)
    
    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            elif e.type == p.MOUSEBUTTONDOWN:
                location = p.mouse.get_pos() #x, y location of mouse
                col = location[0] // SQ_SIZE
                row = location[1] // SQ_SIZE
                if squareSelected == (row, col): #User click again (an Unclick)
                    squareSelected = ()
                    playerClicks = []
                else:
                    
                    squareSelected = (row, col)
                    playerClicks.append(squareSelected)
                if len(playerClicks) == 2:
                    move = ChessEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                    for possible_move in validMoves:
                        if move == possible_move:
                            promotionChoice = None
                            if possible_move.pawnPromotion:
                                promotionChoice = promotionMenu(screen, 'w' if gs.whiteToMove else 'b')
                            move.promotionChoice = promotionChoice  # Set the promotion choice in the Move object
                            gs.makeMove(move)
                            moveMade = True
                            squareSelected = ()
                            playerClicks = []
                    if not moveMade:  # If the move is invalid, reset player clicks
                        playerClicks = [squareSelected]
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    gs.undoMove()
                    moveMade = True
                    
        if moveMade:
            validMoves = gs.getValidMoves()
            moveMade = False

        drawGameState(screen, gs, validMoves, squareSelected)
        clock.tick(MAX_FPS)
        p.display.flip()

def highlightSquare(screen, gs, validMoves, sqSelected):
    """
    Highlight square selected and moves for piece selected
    """
    if sqSelected != ():
        r, c = sqSelected
        if gs.board[r][c][0] == ('w' if gs.whiteToMove else 'b'): #sqSelected is a piece that can be moved
            #highlight selected square
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)
            s.fill(p.Color('blue'))
            screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))
            #highlight moves from that square
            s.fill(p.Color('yellow'))
            for move in validMoves:
                if move.startRow == r and move.startCol == c:
                    screen.blit(s, (move.endCol * SQ_SIZE, move.endRow * SQ_SIZE))

def drawGameState(screen, gs, validMoves, sqSelected):
    """
    Display gamestates
    parameters:
    - screen: the size of the screen
    - gs: the coded gamestates
    """
    drawBoard(screen)
    highlightSquare(screen, gs, validMoves, sqSelected)
    drawPieces(screen, gs.board)

def drawBoard(screen):
    """
    Draw the board
    parameters:
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
    parameters:
    - screen: the size of the screen
    - board: the states of pieces on the board taken out before
    """
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--": #not empty square
                screen.blit(IMAGES[piece], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def promotionMenu(screen, color):
    """
    Display a promotion menu for the player to choose a piece.
    Parameters:
    - screen: the Pygame screen
    - color: 'w' for white, 'b' for black
    Returns:
    - The chosen piece ('Q', 'R', 'B', 'N')
    """
    font = p.font.SysFont("Arial", 32)
    options = ['Q', 'R', 'B', 'N']
    menuWidth = 200
    menuHeight = 100
    menuX = (WIDTH - menuWidth) // 2
    menuY = (HEIGHT - menuHeight) // 2
    optionRects = []

    # Draw menu background
    p.draw.rect(screen, p.Color("gray"), (menuX, menuY, menuWidth, menuHeight))
    for i, option in enumerate(options):
        text = font.render(option, True, p.Color("black"))
        rect = text.get_rect(center=(menuX + (i + 1) * menuWidth // 5, menuY + menuHeight // 2))
        optionRects.append((rect, option))
        screen.blit(text, rect)

    p.display.flip()

    # Wait for player to click an option
    while True:
        for e in p.event.get():
            if e.type == p.MOUSEBUTTONDOWN:
                mouseX, mouseY = e.pos
                for rect, option in optionRects:
                    if rect.collidepoint(mouseX, mouseY):
                        return option
    
if __name__ == "__main__":
    main()

