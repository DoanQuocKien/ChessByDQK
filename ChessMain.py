"""
Main file to recieve user inputs and displaying chess matches (CurrentGameState object)
"""
import pygame as p
import ChessEngine
import copy
import SmartMoveFinder
import time

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

    while True:  # Loop to restart the game after returning to the main menu
        # Starting menu
        playAsWhite = startingMenu(screen)

        screen.fill(p.Color("white"))
        gs = ChessEngine.GameState()
        gs.whiteToMove = playAsWhite  # Set the starting player based on the menu choice
        validMoves = gs.getValidMoves()
        moveMade = False  # Flag variables for when a move is made
        playerOne = True # True if a Human is playing white
        playerTwo = False # True if a Human is playing black

        loadImages()
        running = True
        squareSelected = ()  # Keep track of last click: tuple(row, col)
        playerClicks = []  # Keep track of players click: two tuples(row_from, col_from), (row_to, col_to)

        while running:
            humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)
            for e in p.event.get():
                if e.type == p.QUIT:
                    p.quit()
                    exit()
                elif e.type == p.MOUSEBUTTONDOWN:
                    if humanTurn:
                        location = p.mouse.get_pos()  # x, y location of mouse
                        col = location[0] // SQ_SIZE
                        row = location[1] // SQ_SIZE
                        if squareSelected == (row, col):  # User clicked the same square twice
                            squareSelected = ()
                            playerClicks = []
                        else:
                            squareSelected = (row, col)
                            playerClicks.append(squareSelected)
                        if len(playerClicks) == 2:
                            move = ChessEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                            for possible_move in validMoves:
                                if move == possible_move:
                                    move = copy.deepcopy(possible_move)
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
                    if e.key == p.K_z:  # Undo move
                        gs.undoMove()
                        moveMade = True

            if moveMade:
                validMoves = gs.getValidMoves()
                moveMade = False

            drawGameState(screen, gs, validMoves, squareSelected)
            clock.tick(MAX_FPS)
            p.display.flip()

            # Check for game over
            if gs.checkMate or gs.draw:
                result = "White Wins" if gs.checkMate and not gs.whiteToMove else \
                        "Black Wins" if gs.checkMate and gs.whiteToMove else "Draw"
                endingScreen(screen, result, gs)  # Pass the game state to the ending screen
                break  # Break out of the game loop to return to the main menu
            
            # AI turn
            if not humanTurn:
                AImove = SmartMoveFinder.getMove(gs, validMoves, SmartMoveFinder.DEPTH)
                gs.makeMove(AImove)
                moveMade = True

            if moveMade:
                validMoves = gs.getValidMoves()
                moveMade = False

def highlightSquare(screen, gs, validMoves, sqSelected):
    """
    Highlight square selected and moves for piece selected
    """
    if sqSelected != ():
        r, c = sqSelected
        if (r < 0) or (r > 7) or (c < 0) or (c > 7):
            return
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
    options = ['Q', 'R', 'B', 'N']
    pieceImages = [IMAGES[color + option] for option in options]  # Get images for the promotion options
    menuWidth = 4 * SQ_SIZE
    menuHeight = SQ_SIZE
    menuX = (WIDTH - menuWidth) // 2
    menuY = (HEIGHT - menuHeight) // 2
    optionRects = []

    # Draw menu background
    p.draw.rect(screen, p.Color("gray"), (menuX, menuY, menuWidth, menuHeight))
    for i, pieceImage in enumerate(pieceImages):
        rect = p.Rect(menuX + i * SQ_SIZE, menuY, SQ_SIZE, SQ_SIZE)
        optionRects.append((rect, options[i]))
        screen.blit(pieceImage, rect)

    p.display.flip()

    # Wait for player to click an option
    while True:
        for e in p.event.get():
            if e.type == p.MOUSEBUTTONDOWN:
                mouseX, mouseY = e.pos
                for rect, option in optionRects:
                    if rect.collidepoint(mouseX, mouseY):
                        return option
def startingMenu(screen):
    """
    Display the starting menu with options to play as White or Black.
    Parameters:
    - screen: the Pygame screen
    Returns:
    - True if the player chooses White, False if the player chooses Black
    """
    font = p.font.SysFont("Arial", 36)
    titleText = font.render("A Chess Game - by Doan Quoc Kien", True, p.Color("black"))
    whiteButton = p.Rect(WIDTH // 2 - 125, HEIGHT // 2 - 60, 250, 50)
    blackButton = p.Rect(WIDTH // 2 - 125, HEIGHT // 2 + 10, 250, 50)

    while True:
        screen.fill(p.Color("white"))
        screen.blit(titleText, (WIDTH // 2 - titleText.get_width() // 2, HEIGHT // 4))

        # Draw buttons
        p.draw.rect(screen, p.Color("gray"), whiteButton)
        p.draw.rect(screen, p.Color("gray"), blackButton)
        whiteText = font.render("Play as White", True, p.Color("black"))
        blackText = font.render("Play as Black", True, p.Color("black"))
        screen.blit(whiteText, (whiteButton.x + 35, whiteButton.y + 5))
        screen.blit(blackText, (blackButton.x + 35, blackButton.y + 5))

        p.display.flip()

        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                exit()
            elif e.type == p.MOUSEBUTTONDOWN:
                mouseX, mouseY = e.pos
                if whiteButton.collidepoint(mouseX, mouseY):
                    return True  # Play as White
                elif blackButton.collidepoint(mouseX, mouseY):
                    return False  # Play as Black

def endingScreen(screen, result, gs):
    """
    Display the ending screen with the result of the game.
    Parameters:
    - screen: the Pygame screen
    - result: a string indicating the result ("White Wins", "Black Wins", "Draw")
    - gs: the current game state (to display the last board position)
    """
    font = p.font.SysFont("Arial", 36)
    resultText = font.render(result, True, p.Color("black"))
    menuButton = p.Rect(WIDTH // 2 - 125, HEIGHT // 2 + 50, 250, 50)

    # Create a semi-transparent overlay
    overlay = p.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(150)  # Set transparency (0 = fully transparent, 255 = fully opaque)
    overlay.fill(p.Color("gray"))  # Fill the overlay with a gray color

    while True:
        # Draw the last board position
        drawGameState(screen, gs, [], ())  # Draw the board and pieces without highlights

        # Draw the semi-transparent overlay on top of the board
        screen.blit(overlay, (0, 0))

        # Draw the result text
        screen.blit(resultText, (WIDTH // 2 - resultText.get_width() // 2, HEIGHT // 3))

        # Draw the "Back to Menu" button
        p.draw.rect(screen, p.Color("gray"), menuButton)
        menuText = font.render("Back to Menu", True, p.Color("black"))
        screen.blit(menuText, (menuButton.x + 35, menuButton.y + 5))

        p.display.flip()

        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                exit()
            elif e.type == p.MOUSEBUTTONDOWN:
                mouseX, mouseY = e.pos
                if menuButton.collidepoint(mouseX, mouseY):
                    return  # Return to the main menu
                
if __name__ == "__main__":
    main()

