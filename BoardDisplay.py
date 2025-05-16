import pygame as p

def drawBoard(screen, SQ_SIZE, DIMENSION):
    colors = [p.Color("white"), p.Color("gray")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[(r + c) % 2]
            p.draw.rect(screen, color, p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def drawPieces(screen, board, IMAGES, SQ_SIZE, DIMENSION):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != 0:
                screen.blit(IMAGES[int(piece)], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def highlightSquare(screen, gs, validMoves, sqSelected, SQ_SIZE):
    if sqSelected != ():
        r, c = sqSelected
        if (r < 0) or (r > 7) or (c < 0) or (c > 7):
            return
        if gs.board[r][c] // 10 == (1 if gs.whiteToMove else 2):
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)
            s.fill(p.Color('blue'))
            screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))
            s.fill(p.Color('yellow'))
            for move in validMoves:
                if move.startRow == r and move.startCol == c:
                    screen.blit(s, (move.endCol * SQ_SIZE, move.endRow * SQ_SIZE))

def drawGameState(screen, gs, validMoves, sqSelected, IMAGES, SQ_SIZE, DIMENSION):
    drawBoard(screen, SQ_SIZE, DIMENSION)
    highlightSquare(screen, gs, validMoves, sqSelected, SQ_SIZE)
    drawPieces(screen, gs.board, IMAGES, SQ_SIZE, DIMENSION)

def drawMoveLog(screen, moveLog, moveLogPage, HEIGHT):
    font = p.font.SysFont("Arial", 18, False, False)
    moveLogRect = p.Rect(514, 0, 186, HEIGHT)
    p.draw.rect(screen, p.Color("white"), moveLogRect)
    p.draw.rect(screen, p.Color("black"), moveLogRect, 2)
    moveTexts = []
    for i in range(0, len(moveLog), 2):
        moveText = f"{i // 2 + 1}. {moveLog[i]}"
        if i + 1 < len(moveLog):
            moveText += f" {moveLog[i + 1]}"
        moveTexts.append(moveText)
    moveLogLinePerPage = 15
    totalPages = max(1, (len(moveTexts) + moveLogLinePerPage - 1) // moveLogLinePerPage)
    moveLogPage = moveLogPage % totalPages
    start = moveLogPage * moveLogLinePerPage
    end = min(start + moveLogLinePerPage, len(moveTexts))
    for i, text in enumerate(moveTexts[start:end]):
        textObj = font.render(text, True, p.Color("black"))
        screen.blit(textObj, (moveLogRect.x + 5, moveLogRect.y + 5 + 20 * i))
    # Optionally return rects for up/down arrows if you use them
    return None, None, totalPages

def promotionMenu(screen, IMAGES, SQ_SIZE, WIDTH, HEIGHT, color):
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

def drawAcceptDrawBox(screen, WIDTH, HEIGHT):
    import pygame as p
    font = p.font.SysFont("Arial", 24)
    box = p.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 60, 300, 120)
    p.draw.rect(screen, p.Color("lightgray"), box)
    p.draw.rect(screen, p.Color("black"), box, 2)
    text = font.render("Accept draw offer?", True, p.Color("black"))
    screen.blit(text, (box.x + (box.width - text.get_width()) // 2, box.y + 20))
    yes_rect = p.Rect(box.x + 30, box.y + 70, 80, 30)
    no_rect = p.Rect(box.x + 190, box.y + 70, 80, 30)
    p.draw.rect(screen, p.Color("green"), yes_rect)
    p.draw.rect(screen, p.Color("red"), no_rect)
    screen.blit(font.render("Yes", True, p.Color("white")), (yes_rect.x + 15, yes_rect.y + 5))
    screen.blit(font.render("No", True, p.Color("white")), (no_rect.x + 20, no_rect.y + 5))
    return yes_rect, no_rect

def drawResignBox(screen, WIDTH, HEIGHT):
    """
    Draws a resign confirmation box and returns rects for Yes/No buttons.
    """
    font = p.font.SysFont("Arial", 24)
    box = p.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 100)
    p.draw.rect(screen, p.Color("lightgray"), box)
    p.draw.rect(screen, p.Color("black"), box, 2)
    text = font.render("Are you sure you want to resign?", True, p.Color("black"))
    # Center the text horizontally in the box
    screen.blit(text, (box.x + (box.width - text.get_width()) // 2, box.y + 15))
    yes_rect = p.Rect(box.x + 20, box.y + 60, 60, 30)
    no_rect = p.Rect(box.x + 120, box.y + 60, 60, 30)
    p.draw.rect(screen, p.Color("green"), yes_rect)
    p.draw.rect(screen, p.Color("red"), no_rect)
    screen.blit(font.render("Yes", True, p.Color("white")), (yes_rect.x + 10, yes_rect.y + 5))
    screen.blit(font.render("No", True, p.Color("white")), (no_rect.x + 15, no_rect.y + 5))
    return yes_rect, no_rect

def replayBoardUI(screen, replay_game, IMAGES, SQ_SIZE, DIMENSION, HEIGHT, WIDTH, navBarHeight=60):
    import ChessEngine as CsE
    import pygame as p

    idx = 0
    font = p.font.SysFont("Arial", 24)
    backButton = p.Rect(10, HEIGHT + 10, 150, 40)
    moveLog = replay_game.moveLog
    moveLogPage = 0
    currPositions = replay_game.positions
    while True:
        screen.fill(p.Color("white"))
        upArrowRect, downArrowRect, totalPages = drawMoveLog(screen, moveLog, moveLogPage, HEIGHT)
        if not currPositions:
            msg = font.render("No positions to display.", True, p.Color("red"))
            screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2))
            p.display.flip()
            for e in p.event.get():
                if e.type == p.QUIT or e.type == p.KEYDOWN or e.type == p.MOUSEBUTTONDOWN:
                    return None
            continue

        idx = max(0, min(idx, len(currPositions) - 1))
        gs_temp = CsE.GameState()
        gs_temp.board = currPositions[idx]
        drawGameState(screen, gs_temp, [], (), IMAGES, SQ_SIZE, DIMENSION)
        p.draw.rect(screen, p.Color("lightgray"), (0, HEIGHT, WIDTH, navBarHeight))
        p.draw.rect(screen, p.Color("gray"), backButton)
        screen.blit(font.render("Return to List", True, p.Color("black")), (backButton.x + 10, backButton.y + 5))
        moveNumText = font.render(f"Move {idx}/{len(currPositions)-1}", True, p.Color("black"))
        screen.blit(moveNumText, (WIDTH // 2 - moveNumText.get_width() // 2, HEIGHT + 10))
        hintFont = p.font.SysFont("Arial", 16)
        hintText = hintFont.render("Use ← and → keys to navigate moves. ESC to return.", True, p.Color("dimgray"))
        screen.blit(hintText, (WIDTH // 2 - hintText.get_width() // 2, HEIGHT + navBarHeight - 25))
        p.display.flip()

        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                exit()
            elif e.type == p.MOUSEBUTTONDOWN:
                mouseX, mouseY = e.pos
                if backButton.collidepoint(mouseX, mouseY):
                    return
                if upArrowRect and upArrowRect.collidepoint(mouseX, mouseY):
                    moveLogPage = 0
                    continue
                if downArrowRect and downArrowRect.collidepoint(mouseX, mouseY):
                    moveLogPage = (moveLogPage + 1) % totalPages
                    continue
            elif e.type == p.KEYDOWN:
                if e.key == p.K_ESCAPE:
                    return
                elif e.key == p.K_LEFT:
                    idx = max(0, idx - 1)
                elif e.key == p.K_RIGHT:
                    idx = min(len(currPositions) - 1, idx + 1)
                elif e.key == p.K_UP:
                    moveLogPage = (moveLogPage - 1) % totalPages
                elif e.key == p.K_DOWN:
                    moveLogPage = (moveLogPage + 1) % totalPages

# Add any other board-related display functions here!

