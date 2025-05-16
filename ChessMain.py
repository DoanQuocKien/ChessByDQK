"""
Main file to receive user inputs and display chess matches (CurrentGameState object)
"""
import pygame as p
import ChessEngine as CsE
import copy
import SmartMoveFinder
import BoardDisplay
import time
import ReplayViewer
import os
import pickle
from datetime import datetime

WIDTH = 700
HEIGHT = 514
NAV_BAR_HEIGHT = 60
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

RESIGN_BUTTON = p.Rect(514, 470, 180, 35)
OFFER_DRAW_BUTTON = p.Rect(514, 420, 180, 35)

SAVE_DIR = "saved_games"

pieces = {
    11: "wp", 12: "wN", 13: "wB", 14: "wR", 15: "wQ", 16: "wK",
    21: "bp", 22: "bN", 23: "bB", 24: "bR", 25: "bQ", 26: "bK"
}
pieceChoose = {
    "wp": 11, "wK": 12, "wB": 13, "wR": 14, "wQ": 15, "wK": 16,
    "bp": 21, "bK": 22, "bB": 23, "bR": 24, "bQ": 25, "bK": 26
}

def loadImages():
    for piece, filename in pieces.items():
        IMAGES[piece] = p.transform.scale(p.image.load(f"images/{filename}.png"), (SQ_SIZE, SQ_SIZE))

def saveGame(moveLog, positions):
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{now}.pkl"
    filepath = os.path.join(SAVE_DIR, filename)
    with open(filepath, "wb") as f:
        pickle.dump({"moveLog": moveLog, "positions": positions}, f)

def main():
    p.init()
    loadImages()
    screen = p.display.set_mode((WIDTH, HEIGHT + NAV_BAR_HEIGHT))
    clock = p.time.Clock()

    while True:
        mode, color = startingMenu(screen)
        ai1_depth = ai2_depth = None

        if mode == "replay":
            while True:
                selected_file = replayMenuUI(screen)
                if not selected_file:
                    break
                replay_game = ReplayViewer.ReplayManager().load_game(selected_file)
                BoardDisplay.replayBoardUI(screen, replay_game, IMAGES, SQ_SIZE, DIMENSION, HEIGHT, WIDTH)
            continue

        if mode == "pve":
            ai_depth = difficultyMenu(screen, "Choose Difficulty for AI")
            if ai_depth is None:
                continue
            playAsWhite = color
            playerOne = playAsWhite
            playerTwo = not playAsWhite
            ai1_depth = ai_depth
        elif mode == "pvp":
            playAsWhite = True
            playerOne = True
            playerTwo = True
        elif mode == "aivai":
            ai1_depth = difficultyMenu(screen, "Choose Difficulty for White AI")
            if ai1_depth is None:
                continue
            ai2_depth = difficultyMenu(screen, "Choose Difficulty for Black AI")
            if ai2_depth is None:
                continue
            playAsWhite = True
            playerOne = False
            playerTwo = False

        screen.fill(p.Color("white"))
        gs = CsE.GameState()
        gs.whiteToMove = True
        validMoves = gs.getValidMoves()
        moveMade = False
        forwardMove = False
        drawOfferPending = False
        drawOfferedBy = None
        resignAccept = False
        moveLogPage = 0
        moveLog = []
        positions = [copy.deepcopy(gs.board)]

        running = True
        squareSelected = ()
        playerClicks = []

        while running:
            screen.fill(p.Color("white"))
            upArrowRect, downArrowRect, totalPages = BoardDisplay.drawMoveLog(screen, moveLog, moveLogPage, HEIGHT)
            BoardDisplay.drawGameState(screen, gs, validMoves, squareSelected, IMAGES, SQ_SIZE, DIMENSION)
            # Draw the offer draw and resign buttons
            p.draw.rect(screen, p.Color("gray"), OFFER_DRAW_BUTTON)
            p.draw.rect(screen, p.Color("gray"), RESIGN_BUTTON)
            fontBtn = p.font.SysFont("Arial", 24)
            screen.blit(fontBtn.render("Offer Draw", True, p.Color("black")), (OFFER_DRAW_BUTTON.x + 20, OFFER_DRAW_BUTTON.y + 5))
            screen.blit(fontBtn.render("Resign", True, p.Color("black")), (RESIGN_BUTTON.x + 50, RESIGN_BUTTON.y + 5))
            p.display.flip()

            humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)
            move = None
            for e in p.event.get():
                if e.type == p.QUIT:
                    p.quit()
                    exit()
                elif e.type == p.MOUSEBUTTONDOWN:
                    mouseX, mouseY = e.pos
                    if OFFER_DRAW_BUTTON.collidepoint(mouseX, mouseY):
                        if not drawOfferPending:
                            drawOfferPending = True
                            drawOfferedBy = "white" if gs.whiteToMove else "black"
                            if not humanTurn:
                                if len(moveLog) >= 80:
                                    ai_score = SmartMoveFinder.scoreBoard(gs)
                                    if (gs.whiteToMove and ai_score <= 0) or (not gs.whiteToMove and ai_score >= 0):
                                        moveLog.append("1/2 - 1/2 (Draw agreed)")
                                        endingScreen(screen, "Draw", gs, moveLog, positions)
                                        break
                        continue
                    if RESIGN_BUTTON.collidepoint(mouseX, mouseY):
                        # Show resign confirmation box
                        yes_rect, no_rect = BoardDisplay.drawResignBox(screen, WIDTH, HEIGHT)
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
                                        # Handle resignation (e.g., end game, update moveLog, etc.)
                                        winner = "Black" if gs.whiteToMove else "White"
                                        moveLog.append("0 - 1 (Give up)" if gs.whiteToMove else "1 - 0 (Give up)")
                                        endingScreen(screen, f"{winner} Wins (Opponent gave up)", gs, moveLog, positions)
                                        waiting = False
                                        running = False
                                        break
                                    elif no_rect.collidepoint(mouseX, mouseY):
                                        # Cancel resignation
                                        waiting = False
                                        break
                        continue
                    if upArrowRect and upArrowRect.collidepoint(mouseX, mouseY):
                        moveLogPage = 0
                        continue
                    if downArrowRect and downArrowRect.collidepoint(mouseX, mouseY):
                        moveLogPage = (moveLogPage + 1) % totalPages
                        continue
                    if humanTurn:
                        location = p.mouse.get_pos()
                        col = location[0] // SQ_SIZE
                        row = location[1] // SQ_SIZE
                        if 0 <= col < 8 and 0 <= row < 8:
                            if squareSelected == (row, col):
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
                                            promotionChoice = BoardDisplay.promotionMenu(
                                                screen, 1 if gs.whiteToMove else 2, IMAGES, SQ_SIZE, WIDTH, HEIGHT
                                            )
                                        move.promotionChoice = promotionChoice
                                        gs.makeMove(move)
                                        moveMade = True
                                        forwardMove = True
                                        squareSelected = ()
                                        playerClicks = []
                                if not moveMade:
                                    playerClicks = [squareSelected]
                elif e.type == p.KEYDOWN:
                    if e.key == p.K_z:
                        gs.undoMove()
                        gs.undoMove()
                        forwardMove = False
                        moveMade = True
                    elif e.key == p.K_UP:
                        moveLogPage = (moveLogPage - 1) % totalPages
                    elif e.key == p.K_DOWN:
                        moveLogPage = (moveLogPage + 1) % totalPages

            if resignAccept:
                winner = "Black" if gs.whiteToMove else "White"
                moveLog.append("0 - 1 (Give up)" if gs.whiteToMove else "1 - 0 (Give up)")
                endingScreen(screen, f"{winner} Wins (Opponent gave up)", gs, moveLog, positions)
                break

            if drawOfferPending and humanTurn and drawOfferedBy != ("white" if gs.whiteToMove else "black"):
                yes_rect, no_rect = BoardDisplay.drawAcceptDrawBox(screen, WIDTH, HEIGHT)
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
                                endingScreen(screen, "Draw", gs, moveLog, positions)
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
                    moveLog.append(move.getChessNotation() + checkAdd)
                    positions.append(copy.deepcopy(gs.board))
                else:
                    if len(moveLog) != 0:
                        moveLog.pop()
                    if len(moveLog) != 0:
                        moveLog.pop()
                    if len(positions) > 1:
                        positions.pop()
                    if len(positions) > 1:
                        positions.pop()
                moveMade = False

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
                endingScreen(screen, result, gs, moveLog, positions)
                break

            if not humanTurn:
                if not playerOne and not playerTwo:
                    SmartMoveFinder.DEPTH = ai1_depth if gs.whiteToMove else ai2_depth
                else:
                    SmartMoveFinder.DEPTH = ai1_depth
                move = SmartMoveFinder.getMove(gs, validMoves)
                gs.makeMove(move)
                moveMade = True
                forwardMove = True

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
                    moveLog.append(move.getChessNotation() + checkAdd)
                    positions.append(copy.deepcopy(gs.board))
                else:
                    if len(moveLog) != 0:
                        moveLog.pop()
                    if len(moveLog) != 0:
                        moveLog.pop()
                moveMade = False

def startingMenu(screen):
    font = p.font.SysFont("Arial", 36)
    titleText = font.render("A Chess Game - by Doan Quoc Kien", True, p.Color("black"))
    whiteButton = p.Rect(WIDTH // 2 - 175, HEIGHT // 2 - 40, 350, 50)
    blackButton = p.Rect(WIDTH // 2 - 175, HEIGHT // 2 + 20, 350, 50)
    pvpButton = p.Rect(WIDTH // 2 - 175, HEIGHT // 2 + 80, 350, 50)
    aivaiButton = p.Rect(WIDTH // 2 - 175, HEIGHT // 2 + 140, 350, 50)
    replayButton = p.Rect(WIDTH // 2 - 175, HEIGHT // 2 + 200, 350, 50)

    while True:
        screen.fill(p.Color("white"))
        screen.blit(titleText, (WIDTH // 2 - titleText.get_width() // 2, HEIGHT // 4))
        fontBtn = p.font.SysFont("Arial", 28)
        for btn, label, x_offset in [
            (whiteButton, "Play as White (vs AI)", 75),
            (blackButton, "Play as Black (vs AI)", 75),
            (pvpButton, "Player vs Player", 95),
            (aivaiButton, "AI vs AI", 135),
            (replayButton, "Replay Saved Games", 60)
        ]:
            p.draw.rect(screen, p.Color("gray"), btn)
            screen.blit(fontBtn.render(label, True, p.Color("black")), (btn.x + x_offset, btn.y + 10))
        p.display.flip()

        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                exit()
            elif e.type == p.MOUSEBUTTONDOWN:
                mouseX, mouseY = e.pos
                if whiteButton.collidepoint(mouseX, mouseY):
                    return ("pve", True)
                elif blackButton.collidepoint(mouseX, mouseY):
                    return ("pve", False)
                elif pvpButton.collidepoint(mouseX, mouseY):
                    return ("pvp", None)
                elif aivaiButton.collidepoint(mouseX, mouseY):
                    return ("aivai", None)
                elif replayButton.collidepoint(mouseX, mouseY):
                    return ("replay", None)

def endingScreen(screen, result, gs, moveLog, positions):
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
    overlay = p.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(150)
    overlay.fill(p.Color("gray"))
    saveGame(moveLog, positions)

    while True:
        BoardDisplay.drawGameState(screen, gs, [], (), IMAGES, SQ_SIZE, DIMENSION)
        BoardDisplay.drawMoveLog(screen, moveLog, 0, HEIGHT)
        screen.blit(overlay, (0, 0))
        screen.blit(resultText, (WIDTH // 2 - resultText.get_width() // 2, HEIGHT // 3))
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
                    return

def difficultyMenu(screen, text):
    """
    Display the difficulty selection menu for AI.
    Returns: depth (int) or None if user chooses to go back.
    """
    font = p.font.SysFont("Arial", 36)
    titleText = font.render(text, True, p.Color("black"))
    easyButton = p.Rect(WIDTH // 2 - 175, HEIGHT // 2 - 80, 350, 50)
    normalButton = p.Rect(WIDTH // 2 - 175, HEIGHT // 2 - 10, 350, 50)
    hardButton = p.Rect(WIDTH // 2 - 175, HEIGHT // 2 + 60, 350, 50)
    backButton = p.Rect(WIDTH // 2 - 175, HEIGHT // 2 + 130, 350, 50)

    while True:
        screen.fill(p.Color("white"))
        screen.blit(titleText, (WIDTH // 2 - titleText.get_width() // 2, HEIGHT // 4))
        fontBtn = p.font.SysFont("Arial", 28)
        p.draw.rect(screen, p.Color("gray"), easyButton)
        p.draw.rect(screen, p.Color("gray"), normalButton)
        p.draw.rect(screen, p.Color("gray"), hardButton)
        p.draw.rect(screen, p.Color("gray"), backButton)
        screen.blit(fontBtn.render("Easy (Depth 2)", True, p.Color("black")), (easyButton.x + 90, easyButton.y + 10))
        screen.blit(fontBtn.render("Normal (Depth 3)", True, p.Color("black")), (normalButton.x + 80, normalButton.y + 10))
        screen.blit(fontBtn.render("Hard (Depth 4)", True, p.Color("black")), (hardButton.x + 90, hardButton.y + 10))
        screen.blit(fontBtn.render("Back to Menu", True, p.Color("black")), (backButton.x + 100, backButton.y + 10))

        p.display.flip()

        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                exit()
            elif e.type == p.MOUSEBUTTONDOWN:
                mouseX, mouseY = e.pos
                if easyButton.collidepoint(mouseX, mouseY):
                    return 2
                elif normalButton.collidepoint(mouseX, mouseY):
                    return 3
                elif hardButton.collidepoint(mouseX, mouseY):
                    return 4
                elif backButton.collidepoint(mouseX, mouseY):
                    return None  # Signal to go back to main menu

def replayMenuUI(screen):
    font = p.font.SysFont("Arial", 32)
    smallFont = p.font.SysFont("Arial", 18)
    manager = ReplayViewer.ReplayManager()
    files = manager.list_games()
    if not files:
        screen.fill(p.Color("white"))
        msg = font.render("No saved games found.", True, p.Color("black"))
        screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2))
        p.display.flip()
        p.time.wait(1500)
        return None

    selected = 0
    returnBtn = p.Rect(WIDTH // 2 - 113, HEIGHT - 60, 225, 40)
    deleteBtn = p.Rect(WIDTH - 70, 20, 60, 24)
    savesPerPage = 5
    page = 0

    arrowY = HEIGHT - 20  # 40 pixels from the bottom, adjust as needed
    arrowLeft = p.Rect(WIDTH // 2 - 60, arrowY, 40, 40)
    arrowRight = p.Rect(WIDTH // 2 + 20, arrowY, 40, 40)

    def get_page_files():
        start = page * savesPerPage
        end = min(start + savesPerPage, len(files))
        return files[start:end]

    while True:
        screen.fill(p.Color("white"))
        title = font.render("Select a saved game to replay", True, p.Color("black"))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

        # Draw delete all saves button
        p.draw.rect(screen, p.Color("red"), deleteBtn)
        screen.blit(smallFont.render("Delete", True, p.Color("white")), (deleteBtn.x + 7, deleteBtn.y + 2))

        page_files = get_page_files()
        for i, fname in enumerate(page_files):
            color = p.Color("yellow") if (selected - page * savesPerPage) == i else p.Color("gray")
            btn = p.Rect(WIDTH // 2 - 200, 120 + i * 60, 400, 50)
            p.draw.rect(screen, color, btn)
            screen.blit(font.render(os.path.basename(fname).replace(".pkl", ""), True, p.Color("black")), (btn.x + 20, btn.y + 10))

        # Draw return to menu button
        p.draw.rect(screen, p.Color("gray"), returnBtn)
        screen.blit(font.render("Return to Menu", True, p.Color("black")), (returnBtn.x + 20, returnBtn.y + 2))

        # Draw paging arrows if needed
        totalPages = (len(files) + savesPerPage - 1) // savesPerPage
        if totalPages > 1:
            # Left arrow
            p.draw.polygon(screen, p.Color("black"), [
                (arrowLeft.x + 30, arrowLeft.y + 10),
                (arrowLeft.x + 10, arrowLeft.y + 20),
                (arrowLeft.x + 30, arrowLeft.y + 30)
            ])
            # Right arrow
            p.draw.polygon(screen, p.Color("black"), [
                (arrowRight.x + 10, arrowRight.y + 10),
                (arrowRight.x + 30, arrowRight.y + 20),
                (arrowRight.x + 10, arrowRight.y + 30)
            ])
            # Page indicator
            pageText = font.render(f"{page+1}/{totalPages}", True, p.Color("black"))
            screen.blit(pageText, (WIDTH // 2 - pageText.get_width() // 2, HEIGHT - 20))

        p.display.flip()

        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                exit()
            elif e.type == p.KEYDOWN:
                if e.key == p.K_UP:
                    if selected > 0:
                        selected -= 1
                    else:
                        selected = len(files) - 1
                    page = selected // savesPerPage
                elif e.key == p.K_DOWN:
                    if selected < len(files) - 1:
                        selected += 1
                    else:
                        selected = 0
                    page = selected // savesPerPage
                elif e.key == p.K_ESCAPE:
                    return None
                elif e.key == p.K_RETURN:
                    return files[selected]
                elif e.key == p.K_LEFT and totalPages > 1:
                    page = (page - 1) % totalPages
                    selected = page * savesPerPage
                elif e.key == p.K_RIGHT and totalPages > 1:
                    page = (page + 1) % totalPages
                    selected = page * savesPerPage
            elif e.type == p.MOUSEBUTTONDOWN:
                mouseX, mouseY = e.pos
                # Delete all saves
                if deleteBtn.collidepoint(mouseX, mouseY):
                    for f in files:
                        try:
                            os.remove(f)
                        except Exception:
                            pass
                    files = []
                    selected = 0
                    page = 0
                    screen.fill(p.Color("white"))
                    msg = font.render("All saves deleted.", True, p.Color("black"))
                    screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2))
                    p.display.flip()
                    p.time.wait(1000)
                    return None
                # Return to menu
                if returnBtn.collidepoint(mouseX, mouseY):
                    return None
                # Left arrow
                if totalPages > 1 and arrowLeft.collidepoint(mouseX, mouseY):
                    page = (page - 1) % totalPages
                    selected = page * savesPerPage
                # Right arrow
                if totalPages > 1 and arrowRight.collidepoint(mouseX, mouseY):
                    page = (page + 1) % totalPages
                    selected = page * savesPerPage
                # File selection
                for i, fname in enumerate(page_files):
                    btn = p.Rect(WIDTH // 2 - 200, 120 + i * 60, 400, 50)
                    if btn.collidepoint(mouseX, mouseY):
                        return fname

if __name__ == "__main__":
    main()


