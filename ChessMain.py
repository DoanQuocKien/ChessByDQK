"""
ChessMain.py

Main file for the Chess game. Handles user input, game state, menus, saving/loading games,
and user interface. Each username has a separate save folder.

Author: Doan Quoc Kien
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

USERNAME = "Guest"

pieces = {
    11: "wp", 12: "wN", 13: "wB", 14: "wR", 15: "wQ", 16: "wK",
    21: "bp", 22: "bN", 23: "bB", 24: "bR", 25: "bQ", 26: "bK"
}
pieceChoose = {
    "wp": 11, "wK": 12, "wB": 13, "wR": 14, "wQ": 15, "wK": 16,
    "bp": 21, "bK": 22, "bB": 23, "bR": 24, "bQ": 25, "bK": 26
}

ai_draw_status = None  # None, "considering", or "rejected"
ai_draw_status_time = 0

def loadImages():
    """
    Loads chess piece images into the global IMAGES dictionary.
    """
    for piece, filename in pieces.items():
        IMAGES[piece] = p.transform.scale(p.image.load(f"images/{filename}.png"), (SQ_SIZE, SQ_SIZE))

def get_save_dir():
    """
    Returns the directory path for the current user's saved games.

    Returns:
        str: Path to the user's save directory.
    """
    return os.path.join("saved_games", USERNAME)

def saveGame(moveLog, positions):
    """
    Saves the current game's move log and positions to a file in the user's save directory.

    Parameters:
        moveLog (list): List of move notations.
        positions (list): List of board positions (2D arrays).
    """
    save_dir = get_save_dir()
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{now}.pkl"
    filepath = os.path.join(save_dir, filename)
    with open(filepath, "wb") as f:
        pickle.dump({"moveLog": moveLog, "positions": positions}, f)

def promptUsername(screen, WIDTH, HEIGHT, current_name):
    """
    Prompts the user to enter a new username.

    Parameters:
        screen (pygame.Surface): The Pygame display surface.
        WIDTH (int): Width of the window.
        HEIGHT (int): Height of the window.
        current_name (str): The current username.

    Returns:
        str: The new username entered by the user, or the current name if cancelled.
    """
    font_path = "font/DejaVuSans.ttf"
    font = p.font.Font(font_path, 32)
    input_box = p.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 30, 300, 50)
    color_inactive = p.Color('lightskyblue3')
    color_active = p.Color('dodgerblue2')
    color = color_inactive
    text = ""
    done = False

    while not done:
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                exit()
            elif event.type == p.KEYDOWN:
                if event.key == p.K_RETURN:
                    if text.strip():
                        return text.strip()
                    else:
                        return current_name
                elif event.key == p.K_ESCAPE:
                    return current_name
                elif event.key == p.K_BACKSPACE:
                    text = text[:-1]
                else:
                    if len(text) < 16 and event.unicode.isprintable():
                        text += event.unicode

        screen.fill(p.Color("white"))
        prompt = font.render("Enter username:", True, p.Color("black"))
        screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT // 2 - 80))
        p.draw.rect(screen, color, input_box, 2)
        txt_surface = font.render(text or current_name, True, p.Color("black"))
        screen.blit(txt_surface, (input_box.x + 10, input_box.y + 10))
        p.display.flip()
    return current_name

def main():
    """
    Main entry point for the chess application.
    Handles the main loop, menu navigation, and game state transitions.
    """
    global USERNAME
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
            p.display.flip()

            humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)
            move = None
            for e in p.event.get():
                if e.type == p.QUIT:
                    p.quit()
                    exit()
                elif e.type == p.MOUSEBUTTONDOWN:
                    mouseX, mouseY = e.pos
                    if BoardDisplay.OFFER_DRAW_BUTTON.collidepoint(mouseX, mouseY):
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
                    if BoardDisplay.RESIGN_BUTTON.collidepoint(mouseX, mouseY):
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
                                        winner = "Black" if gs.whiteToMove else "White"
                                        moveLog.append("0 - 1 (Give up)" if gs.whiteToMove else "1 - 0 (Give up)")
                                        endingScreen(screen, f"{winner} Wins (Opponent gave up)", gs, moveLog, positions)
                                        waiting = False
                                        running = False
                                        break
                                    elif no_rect.collidepoint(mouseX, mouseY):
                                        waiting = False
                                        break
                        continue
                    if upArrowRect and upArrowRect.collidepoint(mouseX, mouseY):
                        moveLogPage = (moveLogPage - 1) % totalPages
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
                                        if possible_move.isPawnPromotion:
                                            promotionChoice = BoardDisplay.promotionMenu(
                                                screen, IMAGES, SQ_SIZE, WIDTH, HEIGHT, 1 if gs.whiteToMove else 2
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

            if drawOfferPending and drawOfferedBy != ("white" if gs.whiteToMove else "black"):
                if mode == "pvp":
                    # Prompt the human to accept or reject the draw
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
                else:
                    # Let the AI consider the draw
                    ai_draw_status_time = time.time()
                    p.display.flip()
                    waiting = True
                    while waiting:
                        for e in p.event.get():
                            if e.type == p.QUIT:
                                p.quit()
                                exit()
                        fontBtn = p.font.Font("font/DejaVuSans.ttf", 16)
                        status_text = fontBtn.render("AI consider accepting draw...", True, p.Color("black"))
                        # Clear the area before drawing the text
                        clear_rect = p.Rect(BoardDisplay.RESIGN_BUTTON.x - 40, BoardDisplay.RESIGN_BUTTON.y + 35, 200, 30)
                        p.draw.rect(screen, p.Color("white"), clear_rect)
                        screen.blit(status_text, (BoardDisplay.RESIGN_BUTTON.x - 30, BoardDisplay.RESIGN_BUTTON.y + 40))
                        p.display.flip()
                        if time.time() - ai_draw_status_time > 1.5:
                            waiting = False

                    ai_score = SmartMoveFinder.scoreBoard(gs)
                    if len(moveLog) >= 80 and ((gs.whiteToMove and ai_score <= 0) or (not gs.whiteToMove and ai_score >= 0)):
                        moveLog.append("1/2 - 1/2 (Draw agreed)")
                        endingScreen(screen, "Draw", gs, moveLog, positions)
                        running = False
                    else:
                        ai_draw_status = "rejected"
                        ai_draw_status_time = time.time()
                        # Turn off "considering" status immediately
                        # Show "AI rejected" for 1.5 seconds
                        waiting = True
                        while waiting:
                            for e in p.event.get():
                                if e.type == p.QUIT:
                                    p.quit()
                                    exit()
                            fontBtn = p.font.Font("font/DejaVuSans.ttf", 16)
                            status_text = fontBtn.render("AI rejected", True, p.Color("red"))
                            clear_rect = p.Rect(BoardDisplay.RESIGN_BUTTON.x - 40, BoardDisplay.RESIGN_BUTTON.y + 35, 200, 30)
                            p.draw.rect(screen, p.Color("white"), clear_rect)
                            screen.blit(status_text, (BoardDisplay.RESIGN_BUTTON.x - 30, BoardDisplay.RESIGN_BUTTON.y + 40))
                            p.display.flip()
                            if time.time() - ai_draw_status_time > 1.5:
                                waiting = False
                        drawOfferPending = False

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
    """
    Displays the main menu and handles user selection.

    Parameters:
        screen (pygame.Surface): The Pygame display surface.

    Returns:
        tuple: (mode, color) where mode is a string and color is a bool or None.
    """
    global USERNAME
    font_path = "font/DejaVuSans.ttf"
    font = p.font.Font(font_path, 36)
    fontBtn = p.font.Font(font_path, 28)
    fontBtnUser = p.font.Font(font_path, 20)
    fontUser = p.font.Font(font_path, 24)
    titleText = font.render("A Chess Game - by Doan Quoc Kien", True, p.Color("black"))
    whiteButton = p.Rect(WIDTH // 2 - 175, HEIGHT // 2 - 40, 350, 50)
    blackButton = p.Rect(WIDTH // 2 - 175, HEIGHT // 2 + 20, 350, 50)
    pvpButton = p.Rect(WIDTH // 2 - 175, HEIGHT // 2 + 80, 350, 50)
    aivaiButton = p.Rect(WIDTH // 2 - 175, HEIGHT // 2 + 140, 350, 50)
    replayButton = p.Rect(WIDTH // 2 - 175, HEIGHT // 2 + 200, 350, 50)

    while True:
        screen.fill(p.Color("white"))
        screen.blit(titleText, (WIDTH // 2 - titleText.get_width() // 2, HEIGHT // 4))
        for btn, label, x_offset in [
            (whiteButton, "Play as White (vs AI)", 32),
            (blackButton, "Play as Black (vs AI)", 35),
            (pvpButton, "Player vs Player", 63),
            (aivaiButton, "AI vs AI", 117),
            (replayButton, "Replay Saved Games", 27)
        ]:
            p.draw.rect(screen, p.Color("gray"), btn)
            screen.blit(fontBtn.render(label, True, p.Color("black")), (btn.x + x_offset, btn.y + 10))

        # Draw username and change button at top right
        userText = fontUser.render(f"User: {USERNAME}", True, p.Color("black"))
        user_rect = userText.get_rect()
        changeBtn_width = 90
        gap = 10
        total_width = userText.get_width() + gap + changeBtn_width
        start_x = WIDTH - 20 - total_width  # 20px padding from right edge
        user_rect.topleft = (start_x, 10)
        screen.blit(userText, user_rect)
        changeBtn = p.Rect(user_rect.right + gap, user_rect.y, changeBtn_width, 30)
        p.draw.rect(screen, p.Color("lightblue"), changeBtn)
        screen.blit(fontBtnUser.render("Change", True, p.Color("black")), (changeBtn.x + 5, changeBtn.y + 3))

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
                elif changeBtn.collidepoint(mouseX, mouseY):
                    USERNAME = promptUsername(screen, WIDTH, HEIGHT, USERNAME)

def endingScreen(screen, result, gs, moveLog, positions):
    """
    Display the ending screen with the result of the game.

    Parameters:
        screen (pygame.Surface): The Pygame display surface.
        result (str): The result string ("White Wins", "Black Wins", "Draw").
        gs (GameState): The current game state (to display the last board position).
        moveLog (list): List of move notations.
        positions (list): List of board positions.
    """
    font_path = "font/DejaVuSans.ttf"
    font_display = p.font.Font(font_path, 36)
    font_menu = p.font.Font(font_path, 30)
    resultText = font_display.render(result, True, p.Color("black"))
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
        menuText = font_menu.render("Back to Menu", True, p.Color("black"))
        screen.blit(menuText, (menuButton.x + 15, menuButton.y + 10))
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

    Parameters:
        screen (pygame.Surface): The Pygame display surface.
        text (str): The title text for the menu.

    Returns:
        int or None: The selected AI depth, or None if user chooses to go back.
    """
    font_path = "font/DejaVuSans.ttf"
    font = p.font.Font(font_path, 36)
    titleText = font.render(text, True, p.Color("black"))
    easyButton = p.Rect(WIDTH // 2 - 175, HEIGHT // 2 - 80, 350, 50)
    normalButton = p.Rect(WIDTH // 2 - 175, HEIGHT // 2 - 10, 350, 50)
    hardButton = p.Rect(WIDTH // 2 - 175, HEIGHT // 2 + 60, 350, 50)
    backButton = p.Rect(WIDTH // 2 - 175, HEIGHT // 2 + 130, 350, 50)

    while True:
        screen.fill(p.Color("white"))
        screen.blit(titleText, (WIDTH // 2 - titleText.get_width() // 2, HEIGHT // 4))
        fontBtn = p.font.Font(font_path, 28)
        p.draw.rect(screen, p.Color("gray"), easyButton)
        p.draw.rect(screen, p.Color("gray"), normalButton)
        p.draw.rect(screen, p.Color("gray"), hardButton)
        p.draw.rect(screen, p.Color("gray"), backButton)
        screen.blit(fontBtn.render("Easy (Depth 2)", True, p.Color("black")), (easyButton.x + 68, easyButton.y + 10))
        screen.blit(fontBtn.render("Normal (Depth 3)", True, p.Color("black")), (normalButton.x + 52, normalButton.y + 10))
        screen.blit(fontBtn.render("Hard (Depth 4)", True, p.Color("black")), (hardButton.x + 68, hardButton.y + 10))
        screen.blit(fontBtn.render("Back to Menu", True, p.Color("black")), (backButton.x + 78, backButton.y + 10))

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
    """
    Display the replay menu for selecting and managing saved games.

    Parameters:
        screen (pygame.Surface): The Pygame display surface.

    Returns:
        str or None: The selected save file path, or None if returning to menu.
    """
    font_path = "font/DejaVuSans.ttf"
    font = p.font.Font(font_path, 25)
    smallFont = p.font.Font(font_path, 18)
    manager = ReplayViewer.ReplayManager()
    files = manager.list_games(get_save_dir())
    if not files:
        screen.fill(p.Color("white"))
        msg = font.render("No saved games found.", True, p.Color("black"))
        screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2))
        p.display.flip()
        p.time.wait(1500)
        return None

    selected = 0
    returnBtn = p.Rect(WIDTH // 2 - 113, HEIGHT - 60, 225, 40)
    savesPerPage = 5
    page = 0

    arrowY = HEIGHT - 20
    arrowLeft = p.Rect(WIDTH // 2 - 60, arrowY, 40, 40)
    arrowRight = p.Rect(WIDTH // 2 + 20, arrowY, 40, 40)

    def get_page_files():
        """
        Returns the list of files for the current page.

        Returns:
            list: List of file paths for the current page.
        """
        start = page * savesPerPage
        end = min(start + savesPerPage, len(files))
        return files[start:end]

    while True:
        screen.fill(p.Color("white"))
        title = font.render("Select a saved game to replay", True, p.Color("black"))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

        page_files = get_page_files()
        del_btn_rects = []
        for i, fname in enumerate(page_files):
            color = p.Color("gray")
            btn = p.Rect(WIDTH // 2 - 200, 120 + i * 60, 400, 50)
            p.draw.rect(screen, color, btn)
            screen.blit(font.render(os.path.basename(fname).replace(".pkl", ""), True, p.Color("black")), (btn.x + 20, btn.y + 10))
            # Draw small red delete button just to the right of the save button
            del_btn = p.Rect(btn.right + 10, btn.y + 10, 30, 30)
            p.draw.rect(screen, p.Color("red"), del_btn)
            screen.blit(smallFont.render("X", True, p.Color("white")), (del_btn.x + 8, del_btn.y + 4))
            del_btn_rects.append((del_btn, fname))

        # Draw return to menu button
        p.draw.rect(screen, p.Color("gray"), returnBtn)
        screen.blit(font.render("Return to Menu", True, p.Color("black")), (returnBtn.x + 15, returnBtn.y + 5))

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
                # Check per-save delete buttons
                for del_btn, fname in del_btn_rects:
                    if del_btn.collidepoint(mouseX, mouseY):
                        try:
                            os.remove(fname)
                            files.remove(fname)
                            # Adjust selection/page if needed
                            if selected >= len(files):
                                selected = max(0, len(files) - 1)
                            page = selected // savesPerPage
                        except Exception:
                            pass
                        break  # Only allow one delete per click

if __name__ == "__main__":
    """
    Entry point for the chess application.
    """
    main()


