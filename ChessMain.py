"""
Main file to recieve user inputs and displaying chess matches (CurrentGameState object)
"""
import pygame as p
import ChessEngine as CsE
import copy
import SmartMoveFinder as SmartMoveFinder
import time

WIDTH = 700  # Increase width to include sidebar
HEIGHT = 514
DIMENSION = 8 #dimensions of a chess board are 8x8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15 #for animation
IMAGES = {}

RESIGN_BUTTON = p.Rect(514, 470, 180, 35)
OFFER_DRAW_BUTTON = p.Rect(514, 420, 180, 35)

moveLog = []

pieces = {
    11: "wp", 12: "wN", 13: "wB", 14: "wR", 15: "wQ", 16: "wK",
    21: "bp", 22: "bN", 23: "bB", 24: "bR", 25: "bQ", 26: "bK"
}
pieceChoose = {
    "wp": 11, "wK": 12, "wB": 13, "wR": 14, "wQ": 15, "wK": 16,
    "bp": 21, "bK": 22, "bB": 23, "bR": 24, "bQ": 25, "bK": 26
}
def loadImages():
    """
    Initialize a global dictionary of chess pieces. Call once.
    """
    for piece, filename in pieces.items():
        IMAGES[piece] = p.transform.scale(p.image.load(f"images/{filename}.png"), (SQ_SIZE, SQ_SIZE))

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
        gs = CsE.GameState()
        gs.whiteToMove = playAsWhite  # Set the starting player based on the menu choice
        validMoves = gs.getValidMoves()
        moveMade = False  # Flag variables for when a move is made
        forwardMove = False # Flag variables to determine whether the move is made or undid
        playerOne = True # True if a Human is playing white
        playerTwo = True # True if a Human is playing black
        drawOfferPending = False
        drawOfferedBy = None
        drawAcceptBox = False
        resignAccept = False
        moveLogPage = 0
        moveLog = []
        moveLogPage = 0

        loadImages()
        running = True
        squareSelected = ()  # Keep track of last click: tuple(row, col)
        playerClicks = []  # Keep track of players click: two tuples(row_from, col_from), (row_to, col_to)

        while running:
            humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)
            move = None
            for e in p.event.get():
                if e.type == p.QUIT:
                    p.quit()
                    exit()
                elif e.type == p.MOUSEBUTTONDOWN:
                    mouseX, mouseY = e.pos
                    # Offer Draw button
                    if OFFER_DRAW_BUTTON.collidepoint(mouseX, mouseY):
                        if not drawOfferPending:
                            drawOfferPending = True
                            drawOfferedBy = "white" if gs.whiteToMove else "black"
                            # If AI is the receiver, check auto-accept
                            if (not humanTurn):
                                # Only accept if move number >= 40 and AI is worse or equal
                                if len(moveLog) >= 80:  # 40 moves per side
                                    ai_score = SmartMoveFinder.scoreBoard(gs)
                                    if (gs.whiteToMove and ai_score <= 0) or (not gs.whiteToMove and ai_score >= 0):
                                        moveLog.append("1/2 - 1/2 (Draw agreed)")
                                        endingScreen(screen, "Draw", gs)
                                        break
                        continue
                    # Give Up button
                    if RESIGN_BUTTON.collidepoint(mouseX, mouseY):
                        resignAccept = True
                        break
                    # Move log paging arrows
                    upArrowRect, downArrowRect, totalPages = drawMoveLog(screen, moveLog, moveLogPage)
                    if upArrowRect and upArrowRect.collidepoint(mouseX, mouseY):
                        moveLogPage = 0  # Go to first page
                        continue
                    if downArrowRect and downArrowRect.collidepoint(mouseX, mouseY):
                        moveLogPage = (moveLogPage + 1) % totalPages  # Next page, wrap around
                        continue
                    if humanTurn:
                        location = p.mouse.get_pos()  # x, y location of mouse
                        col = location[0] // SQ_SIZE
                        row = location[1] // SQ_SIZE
                        if 0 <= col < 8 and 0 <= row < 8:
                            if squareSelected == (row, col):  # User clicked the same square twice
                                squareSelected = ()
                                playerClicks = []
                            else:
                                squareSelected = (row, col)
                                playerClicks.append(squareSelected)
                            if len(playerClicks) == 2:
                                move = CsE.Move(playerClicks[0], playerClicks[1], gs.board)
                                for possible_move in validMoves:
                                    if move == possible_move:
                                        move = copy.deepcopy(possible_move)
                                        promotionChoice = None
                                        if possible_move.pawnPromotion:
                                            promotionChoice = promotionMenu(screen, 1 if gs.whiteToMove else 2)
                                        move.promotionChoice = promotionChoice  # Set the promotion choice in the Move object
                                        gs.makeMove(move)
                                        moveMade = True
                                        forwardMove = True
                                        squareSelected = ()
                                        playerClicks = []
                                if not moveMade:  # If the move is invalid, reset player clicks
                                    playerClicks = [squareSelected]
                elif e.type == p.KEYDOWN:
                    if e.key == p.K_z:  # Undo move
                        gs.undoMove()
                        forwardMove = False
                        moveMade = True\
            
            if resignAccept:
                winner = "Black" if gs.whiteToMove else "White"
                moveLog.append("0 - 1 (Give up)" if gs.whiteToMove else "1 - 0 (Give up)")
                endingScreen(screen, f"{winner} Wins (Opponent gave up)", gs)
                break

            # --- Draw offer accept box appears immediately if pending and it's the other player's turn ---
            if drawOfferPending and humanTurn and drawOfferedBy != ("white" if gs.whiteToMove else "black"):
                yes_rect, no_rect = drawAcceptDrawBox(screen)
                p.display.flip()
                waiting = True
                while waiting:
                    for e in p.event.get():
                        if e.type == p.QUIT:
                            p.quit()
                            exit()
                        elif e.type == p.MOUSEBUTTONDOWN:
                            mouseX, mouseY = e.pos
                            if yes_rect.collidepoint(mouseX, mouseY):
                                moveLog.append("1/2 - 1/2 (Draw agreed)")
                                endingScreen(screen, "Draw", gs)
                                waiting = False
                                running = False
                                break
                            elif no_rect.collidepoint(mouseX, mouseY):
                                drawOfferPending = False
                                waiting = False
                                break

            if moveMade:
                validMoves = gs.getValidMoves()
                moveMade = False
                checkAdd = "" 
                if (gs.whiteToMove and gs.squareUnderAttack(gs.whiteKingLocation[0], gs.whiteKingLocation[1])) or (not gs.whiteToMove and gs.squareUnderAttack(gs.blackKingLocation[0], gs.blackKingLocation[1])):
                    if gs.checkMate:
                        checkAdd = "#"
                    else:
                        checkAdd = "+"
                if forwardMove:
                    moveLog.append(move.getChessNotation() + checkAdd)  # Add move notation to the log
                elif len(moveLog) != 0:
                    moveLog.pop()
                moveMade = False 

            drawGameState(screen, gs, validMoves, squareSelected, moveLog, moveLogPage)
            clock.tick(MAX_FPS)
            p.display.flip()

            # Check for game over
            if gs.checkMate or gs.draw:
                if gs.checkMate:
                    if not gs.whiteToMove:
                        result = "White Wins"
                        moveLog.append("1 - 0")
                    else:
                        result = "Black Wins"
                        moveLog.append("0 - 1")
                else:
                    result = "Draw"
                    moveLog.append("1/2 - 1/2")
                endingScreen(screen, result, gs)  # Pass the game state to the ending screen
                break  # Break out of the game loop to return to the main menu
            
            # AI turn
            if not humanTurn:
                move = SmartMoveFinder.getMove(gs, validMoves)
                gs.makeMove(move)
                moveMade = True

            if moveMade:
                moveLog.append(move.getChessNotation())  # Add move notation to the log
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
        if gs.board[r][c] // 10 == (1 if gs.whiteToMove else 2): #sqSelected is a piece that can be moved
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

def drawGameState(screen, gs, validMoves, sqSelected, moveLog, moveLogPage):
    drawBoard(screen)
    highlightSquare(screen, gs, validMoves, sqSelected)
    drawPieces(screen, gs.board)
    drawMoveLog(screen, moveLog, moveLogPage)

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
            if piece != 0: #not empty square
                screen.blit(IMAGES[piece], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def drawMoveLog(screen, moveLog, moveLogPage):
    """
    Draw the move log in the sidebar with paging arrows if too long.
    """
    font = p.font.SysFont("Arial", 18, False, False)
    moveLogRect = p.Rect(514, 0, 186, HEIGHT)  # Sidebar dimensions
    p.draw.rect(screen, p.Color("white"), moveLogRect)
    p.draw.rect(screen, p.Color("black"), moveLogRect, 2)  # Border

    moveTexts = []
    for i in range(0, len(moveLog), 2):
        moveText = f"{i // 2 + 1}. {moveLog[i]}"
        if i + 1 < len(moveLog):  # Check if black's move exists
            moveText += f" {moveLog[i + 1]}"
        moveTexts.append(moveText)

    moveLogLinePerPage = 5
    totalPages = max(1, (len(moveTexts) + moveLogLinePerPage - 1) // moveLogLinePerPage)
    moveLogPage = moveLogPage % totalPages  # wrap around

    startLine = moveLogPage * moveLogLinePerPage
    endLine = min(startLine + moveLogLinePerPage, len(moveTexts))

    padding = 5
    textY = padding
    for text in moveTexts[startLine:endLine]:
        textObject = font.render(text, True, p.Color("black"))
        screen.blit(textObject, (moveLogRect.x + padding, textY))
        textY += textObject.get_height() + 5

    # Draw arrows if needed
    arrowFont = p.font.SysFont("Arial", 28, True, False)
    if totalPages > 1:
        # Down arrow (next page)
        downArrowRect = p.Rect(moveLogRect.x + moveLogRect.width - 40, moveLogRect.y + HEIGHT - 130, 30, 30)
        p.draw.polygon(screen, p.Color("black"), [
            (downArrowRect.x + 15, downArrowRect.y + 20),
            (downArrowRect.x + 5, downArrowRect.y + 10),
            (downArrowRect.x + 25, downArrowRect.y + 10)
        ])
        # Up arrow (back to first page)
        upArrowRect = p.Rect(moveLogRect.x + 10, moveLogRect.y + HEIGHT - 130, 30, 30)
        p.draw.polygon(screen, p.Color("black"), [
            (upArrowRect.x + 15, upArrowRect.y + 10),
            (upArrowRect.x + 5, upArrowRect.y + 20),
            (upArrowRect.x + 25, upArrowRect.y + 20)
        ])
    else:
        downArrowRect = upArrowRect = None

    # Draw Offer Draw button
    p.draw.rect(screen, p.Color("lightgray"), OFFER_DRAW_BUTTON)
    offerText = font.render("Offer Draw", True, p.Color("black"))
    screen.blit(offerText, (OFFER_DRAW_BUTTON.x + 20, OFFER_DRAW_BUTTON.y + 5))

    # Draw Give Up button
    p.draw.rect(screen, p.Color("lightgray"), RESIGN_BUTTON)
    giveUpText = font.render("Resign", True, p.Color("black"))
    screen.blit(giveUpText, (RESIGN_BUTTON.x + 35, RESIGN_BUTTON.y + 5))

    # Return arrow rects for click detection
    return upArrowRect, downArrowRect, totalPages

def promotionMenu(screen, color):
    """
    Display a promotion menu for the player to choose a piece.
    Parameters:
    - screen: the Pygame screen
    - color: 'w' for white, 'b' for black
    Returns:
    - The chosen piece ('Q', 'R', 'B', 'N')
    """
    options = [5, 4, 3, 2]
    pieceImages = [IMAGES[color * 10 + option] for option in options]  # Get images for the promotion options
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

def drawAcceptDrawBox(screen):
    font = p.font.SysFont("Arial", 24)
    box = p.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 100)
    p.draw.rect(screen, p.Color("lightgray"), box)
    p.draw.rect(screen, p.Color("black"), box, 2)
    text = font.render("Accept draw offer?", True, p.Color("black"))
    screen.blit(text, (box.x + 20, box.y + 20))
    yes_rect = p.Rect(box.x + 20, box.y + 60, 60, 30)
    no_rect = p.Rect(box.x + 120, box.y + 60, 60, 30)
    p.draw.rect(screen, p.Color("green"), yes_rect)
    p.draw.rect(screen, p.Color("red"), no_rect)
    screen.blit(font.render("Yes", True, p.Color("white")), (yes_rect.x + 10, yes_rect.y + 5))
    screen.blit(font.render("No", True, p.Color("white")), (no_rect.x + 15, no_rect.y + 5))
    return yes_rect, no_rect

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
        drawGameState(screen, gs, [], (), moveLog, 0)  # Draw the board and pieces without highlights

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


