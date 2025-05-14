#include <boost/python.hpp>
#include <boost/python/stl_pair.hpp>
#include <vector>
#include <string>
#include <map>
#include <memory>
#include <iostream>

namespace py = boost::python;

inline int countTrailingZeros(uint64_t x) {
    if (x == 0) return 64;
    int count = 0;
    while ((x & 1) == 0) {
        x >>= 1;
        count++;
    }
    return count;
}

class Move {
public:
    int startRow, startCol, endRow, endCol;
    std::string pieceMoved, pieceCaptured;
    bool pawnPromotion, isEnPassantMove, isCastleMove;
    char promotionChoice;
    int moveID;

    Move(int startRow, int startCol, int endRow, int endCol, 
         const std::string& pieceMoved, const std::string& pieceCaptured,
         bool pawnPromotion = false, bool isEnPassantMove = false, 
         bool isCastleMove = false, char promotionChoice = '\0')
        : startRow(startRow), startCol(startCol), endRow(endRow), endCol(endCol),
          pieceMoved(pieceMoved), pieceCaptured(pieceCaptured),
          pawnPromotion(pawnPromotion), isEnPassantMove(isEnPassantMove),
          isCastleMove(isCastleMove), promotionChoice(promotionChoice){
        moveID = startRow * 1000 + startCol * 100 + endRow * 10 + endCol;
    }

    // Copy constructor
    Move(const Move& other)
        : startRow(other.startRow), startCol(other.startCol),
          endRow(other.endRow), endCol(other.endCol),
          pieceMoved(other.pieceMoved), pieceCaptured(other.pieceCaptured),
          pawnPromotion(other.pawnPromotion), isEnPassantMove(other.isEnPassantMove),
          isCastleMove(other.isCastleMove), promotionChoice(other.promotionChoice),
          moveID(other.moveID) {}

    bool operator==(const Move& other) const {
        return startRow == other.startRow && startCol == other.startCol &&
               endRow == other.endRow && endCol == other.endCol;
    }
};

class CastleRight {
public:
    bool wks, bks, wqs, bqs;  // White/Black King/Queen side

    CastleRight(bool wks = true, bool bks = true, bool wqs = true, bool bqs = true)
        : wks(wks), bks(bks), wqs(wqs), bqs(bqs) {}
};

class GameState {
public:
    std::vector<std::vector<std::string>> board;
    bool whiteToMove;
    std::vector<std::pair<Move, int>> moveLog;
    std::pair<int, int> whiteKingLocation, blackKingLocation;
    bool checkMate, staleMate, threefoldRepetition, fiftyMoveRule, insufficientMaterial;
    std::pair<int, int> enPassantPossible;
    std::map<std::string, int> positionCounts;
    int fiftyMoveCounter;
    std::vector<Move> validMovesCache;
    std::string cachedBoardHash;
    std::map<std::string, std::vector<Move>> moveCache;
    CastleRight currentCastlingRight;
    std::vector<CastleRight> castleRightsLog;
    std::vector<std::pair<int, int>> enPassantPossibleLog;

    // Optimize board representation with bitboards
    uint64_t whitePawns, whiteKnights, whiteBishops, whiteRooks, whiteQueens, whiteKing;
    uint64_t blackPawns, blackKnights, blackBishops, blackRooks, blackQueens, blackKing;
    uint64_t allPieces;

    void initializeBitboards() {
        whitePawns = whiteKnights = whiteBishops = whiteRooks = whiteQueens = whiteKing = 0;
        blackPawns = blackKnights = blackBishops = blackRooks = blackQueens = blackKing = 0;
        allPieces = 0;

        for (int r = 0; r < 8; r++) {
            for (int c = 0; c < 8; c++) {
                std::string piece = board[r][c];
                if (piece != "--") {
                    uint64_t bit = 1ULL << (r * 8 + c);
                    allPieces |= bit;
                    if (piece[0] == 'w') {
                        switch (piece[1]) {
                            case 'p': whitePawns |= bit; break;
                            case 'N': whiteKnights |= bit; break;
                            case 'B': whiteBishops |= bit; break;
                            case 'R': whiteRooks |= bit; break;
                            case 'Q': whiteQueens |= bit; break;
                            case 'K': whiteKing |= bit; break;
                        }
                    } else {
                        switch (piece[1]) {
                            case 'p': blackPawns |= bit; break;
                            case 'N': blackKnights |= bit; break;
                            case 'B': blackBishops |= bit; break;
                            case 'R': blackRooks |= bit; break;
                            case 'Q': blackQueens |= bit; break;
                            case 'K': blackKing |= bit; break;
                        }
                    }
                }
            }
        }
    }

    bool insideBoard(int r, int c) const {
        return r >= 0 && r < 8 && c >= 0 && c < 8;
    }

    std::string getBoardHash() const {
        std::string hash;
        for (const auto& row : board) {
            for (const auto& piece : row) {
                hash += piece;
            }
        }
        hash += whiteToMove ? "1" : "0";
        return hash;
    }

    void updateCastleRights(const Move& move) {
        if (move.pieceMoved == "wK") {
            currentCastlingRight.wks = false;
            currentCastlingRight.wqs = false;
        } else if (move.pieceMoved == "bK") {
            currentCastlingRight.bks = false;
            currentCastlingRight.bqs = false;
        } else if (move.pieceMoved == "wR") {
            if (move.startRow == 7) {
                if (move.startCol == 0) currentCastlingRight.wqs = false;
                else if (move.startCol == 7) currentCastlingRight.wks = false;
            }
        } else if (move.pieceMoved == "bR") {
            if (move.startRow == 0) {
                if (move.startCol == 0) currentCastlingRight.bqs = false;
                else if (move.startCol == 7) currentCastlingRight.bks = false;
            }
        }
        if (move.pieceCaptured == "wR") {
            if (move.endRow == 7) {
                if (move.endCol == 0) currentCastlingRight.wqs = false;
                else if (move.endCol == 7) currentCastlingRight.wks = false;
            }
        } else if (move.pieceCaptured == "bR") {
            if (move.endRow == 0) {
                if (move.endCol == 0) currentCastlingRight.bqs = false;
                else if (move.endCol == 7) currentCastlingRight.bks = false;
            }
        }
    }

    GameState() : whiteToMove(true), checkMate(false), staleMate(false), fiftyMoveCounter(0),
                 currentCastlingRight(true, true, true, true) {
        // Initialize board
        board = {
            {"bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"},
            {"bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"},
            {"--", "--", "--", "--", "--", "--", "--", "--"},
            {"--", "--", "--", "--", "--", "--", "--", "--"},
            {"--", "--", "--", "--", "--", "--", "--", "--"},
            {"--", "--", "--", "--", "--", "--", "--", "--"},
            {"wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"},
            {"wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"}
        };
        whiteKingLocation = {7, 4};
        blackKingLocation = {0, 4};
        enPassantPossible = {-1, -1};
        castleRightsLog.push_back(currentCastlingRight);
        enPassantPossibleLog.push_back(enPassantPossible);
        positionCounts[getBoardHash()] = 1;
        initializeBitboards();
    }

    void makeMove(const Move& move) {
        // Update bitboards
        uint64_t fromBit = 1ULL << (move.startRow * 8 + move.startCol);
        uint64_t toBit = 1ULL << (move.endRow * 8 + move.endCol);
        uint64_t capturedBit = (move.pieceCaptured != "--") ? toBit : 0;

        // Remove piece from old position
        if (move.pieceMoved[0] == 'w') {
            switch (move.pieceMoved[1]) {
                case 'p': whitePawns &= ~fromBit; break;
                case 'N': whiteKnights &= ~fromBit; break;
                case 'B': whiteBishops &= ~fromBit; break;
                case 'R': whiteRooks &= ~fromBit; break;
                case 'Q': whiteQueens &= ~fromBit; break;
                case 'K': whiteKing &= ~fromBit; break;
            }
        } else {
            switch (move.pieceMoved[1]) {
                case 'p': blackPawns &= ~fromBit; break;
                case 'N': blackKnights &= ~fromBit; break;
                case 'B': blackBishops &= ~fromBit; break;
                case 'R': blackRooks &= ~fromBit; break;
                case 'Q': blackQueens &= ~fromBit; break;
                case 'K': blackKing &= ~fromBit; break;
            }
        }

        // Remove captured piece
        if (move.pieceCaptured != "--") {
            if (move.pieceCaptured[0] == 'w') {
                switch (move.pieceCaptured[1]) {
                    case 'p': whitePawns &= ~capturedBit; break;
                    case 'N': whiteKnights &= ~capturedBit; break;
                    case 'B': whiteBishops &= ~capturedBit; break;
                    case 'R': whiteRooks &= ~capturedBit; break;
                    case 'Q': whiteQueens &= ~capturedBit; break;
                    case 'K': whiteKing &= ~capturedBit; break;
                }
            } else {
                switch (move.pieceCaptured[1]) {
                    case 'p': blackPawns &= ~capturedBit; break;
                    case 'N': blackKnights &= ~capturedBit; break;
                    case 'B': blackBishops &= ~capturedBit; break;
                    case 'R': blackRooks &= ~capturedBit; break;
                    case 'Q': blackQueens &= ~capturedBit; break;
                    case 'K': blackKing &= ~capturedBit; break;
                }
            }
        }

        // Add piece to new position
        if (move.pieceMoved[0] == 'w') {
            switch (move.pieceMoved[1]) {
                case 'p': whitePawns |= toBit; break;
                case 'N': whiteKnights |= toBit; break;
                case 'B': whiteBishops |= toBit; break;
                case 'R': whiteRooks |= toBit; break;
                case 'Q': whiteQueens |= toBit; break;
                case 'K': whiteKing |= toBit; break;
            }
        } else {
            switch (move.pieceMoved[1]) {
                case 'p': blackPawns |= toBit; break;
                case 'N': blackKnights |= toBit; break;
                case 'B': blackBishops |= toBit; break;
                case 'R': blackRooks |= toBit; break;
                case 'Q': blackQueens |= toBit; break;
                case 'K': blackKing |= toBit; break;
            }
        }

        // Update allPieces
        allPieces = whitePawns | whiteKnights | whiteBishops | whiteRooks | whiteQueens | whiteKing |
                   blackPawns | blackKnights | blackBishops | blackRooks | blackQueens | blackKing;

        board[move.startRow][move.startCol] = "--";
        board[move.endRow][move.endCol] = move.pieceMoved;
        whiteToMove = !whiteToMove;

        if (move.pieceMoved == "wK") {
            whiteKingLocation = {move.endRow, move.endCol};
        } else if (move.pieceMoved == "bK") {
            blackKingLocation = {move.endRow, move.endCol};
        }

        if (move.pawnPromotion) {
            std::string promotionPiece = move.promotionChoice ? 
                std::string(1, move.promotionChoice) : "Q";
            board[move.endRow][move.endCol] = 
                (move.pieceMoved[0] == 'w' ? "w" : "b") + promotionPiece;
        }

        if (move.isEnPassantMove) {
            board[move.startRow][move.endCol] = "--";
        }

        if (move.pieceMoved[1] == 'p' && abs(move.startRow - move.endRow) == 2) {
            enPassantPossible = {(move.startRow + move.endRow) / 2, move.startCol};
        } else {
            enPassantPossible = {-1, -1};
        }
        enPassantPossibleLog.push_back(enPassantPossible);

        if (move.isCastleMove) {
            if (move.endCol - move.startCol == 2) {
                board[move.endRow][move.endCol - 1] = board[move.endRow][move.endCol + 1];
                board[move.endRow][move.endCol + 1] = "--";
            } else {
                board[move.endRow][move.endCol + 1] = board[move.endRow][move.endCol - 2];
                board[move.endRow][move.endCol - 2] = "--";
            }
        }

        updateCastleRights(move);
        castleRightsLog.push_back(currentCastlingRight);

        std::string boardHash = getBoardHash();
        positionCounts[boardHash]++;
        fiftyMoveCounter = (move.pieceMoved[1] == 'p' || move.pieceCaptured != "--") ? 
            0 : fiftyMoveCounter + 1;
        moveLog.push_back({move, fiftyMoveCounter});
        validMovesCache.clear();
        cachedBoardHash.clear();
    }

    /**
     * @brief Undoes the last move made.
     * 
     * Restores the previous board state by:
     * - Moving pieces back
     * - Restoring captured pieces
     * - Restoring castling rights
     * - Restoring en passant state
     * - Updating bitboards
     * - Removing the move from history
     */
    void undoMove() {
        if (moveLog.empty()) return;

        auto [move, oldFiftyMoveCounter] = moveLog.back();
        moveLog.pop_back();

        std::string boardHash = getBoardHash();
        if (positionCounts[boardHash] > 0) {
            positionCounts[boardHash]--;
            if (positionCounts[boardHash] == 0) {
                positionCounts.erase(boardHash);
            }
        }

        board[move.startRow][move.startCol] = move.pieceMoved;
        if(!move.isEnPassantMove)
            board[move.endRow][move.endCol] = move.pieceCaptured;

        if (move.pieceMoved == "wK") {
            whiteKingLocation = {move.startRow, move.startCol};
        } else if (move.pieceMoved == "bK") {
            blackKingLocation = {move.startRow, move.startCol};
        }

        if (move.isEnPassantMove) {
            board[move.endRow][move.endCol] = "--";
            board[move.startRow][move.endCol] = move.pieceCaptured;
        }

        enPassantPossibleLog.pop_back();
        enPassantPossible = enPassantPossibleLog.back();

        if (move.isCastleMove) {
            if (move.endCol - move.startCol == 2) {
                board[move.endRow][move.endCol + 1] = board[move.endRow][move.endCol - 1];
                board[move.endRow][move.endCol - 1] = "--";
            } else {
                board[move.endRow][move.endCol - 2] = board[move.endRow][move.endCol + 1];
                board[move.endRow][move.endCol + 1] = "--";
            }
        }

        castleRightsLog.pop_back();
        currentCastlingRight = castleRightsLog.back();

        whiteToMove = !whiteToMove;
        fiftyMoveCounter = moveLog.back().second;

        validMovesCache.clear();
        cachedBoardHash.clear();
    }

    bool checkThreeFoldRepetition() const {
        for (const auto& [hash, count] : positionCounts) {
            if (count >= 3) return true;
        }
        return false;
    }

    bool checkFiftyMoveRule() const {
        return fiftyMoveCounter >= 100;
    }

    bool checkInsufficientMaterial() const {
        // Count pieces for each side
        int whitePieces = 0, blackPieces = 0;
        bool whiteHasKnight = false, blackHasKnight = false;
        bool whiteHasBishop = false, blackHasBishop = false;
        bool whiteHasPawn = false, blackHasPawn = false;
        bool whiteHasRook = false, blackHasRook = false;
        bool whiteHasQueen = false, blackHasQueen = false;

        for (int r = 0; r < 8; r++) {
            for (int c = 0; c < 8; c++) {
                std::string piece = board[r][c];
                if (piece != "--") {
                    if (piece[0] == 'w') {
                        whitePieces++;
                        switch (piece[1]) {
                            case 'p': whiteHasPawn = true; break;
                            case 'R': whiteHasRook = true; break;
                            case 'N': whiteHasKnight = true; break;
                            case 'B': whiteHasBishop = true; break;
                            case 'Q': whiteHasQueen = true; break;
                        }
                    } else {
                        blackPieces++;
                        switch (piece[1]) {
                            case 'p': blackHasPawn = true; break;
                            case 'R': blackHasRook = true; break;
                            case 'N': blackHasKnight = true; break;
                            case 'B': blackHasBishop = true; break;
                            case 'Q': blackHasQueen = true; break;
                        }
                    }
                }
            }
        }

        // King vs King
        if (whitePieces == 1 && blackPieces == 1) {
            return true;
        }

        // King and Knight vs King
        if ((whitePieces == 2 && blackPieces == 1 && whiteHasKnight) ||
            (whitePieces == 1 && blackPieces == 2 && blackHasKnight)) {
            return true;
        }

        // King and Bishop vs King
        if ((whitePieces == 2 && blackPieces == 1 && whiteHasBishop) ||
            (whitePieces == 1 && blackPieces == 2 && blackHasBishop)) {
            return true;
        }

        // King and Bishop vs King and Bishop (same color squares)
        if (whitePieces == 2 && blackPieces == 2 && 
            whiteHasBishop && blackHasBishop) {
            // Check if bishops are on same color squares
            bool whiteBishopOnLight = false, blackBishopOnLight = false;
            for (int r = 0; r < 8; r++) {
                for (int c = 0; c < 8; c++) {
                    if (board[r][c] == "wB") {
                        whiteBishopOnLight = ((r + c) % 2 == 0);
                    } else if (board[r][c] == "bB") {
                        blackBishopOnLight = ((r + c) % 2 == 0);
                    }
                }
            }
            return whiteBishopOnLight == blackBishopOnLight;
        }

        return false;
    }

    std::vector<Move> getValidMoves() {
        std::string currentHash = getBoardHash();
        if (!validMovesCache.empty() && cachedBoardHash == currentHash) {
            return validMovesCache;
        }

        std::vector<Move> moves = getAllPossibleMoves();
        std::vector<Move> validMoves;

        // Add castle moves
        if (whiteToMove) {
            getCastleMoves(whiteKingLocation.first, whiteKingLocation.second, moves);
        } else {
            getCastleMoves(blackKingLocation.first, blackKingLocation.second, moves);
        }

        for (const auto& move : moves) {

            makeMove(move);
            whiteToMove = !whiteToMove;
            if (!inCheck()) {
                validMoves.push_back(move);
            }
            whiteToMove = !whiteToMove;
            undoMove();
        }
        
        if(!validMoves.size())
        {
            if(inCheck()) checkMate = true;
            else staleMate = true;
        }
        else if(checkFiftyMoveRule()) fiftyMoveRule = true;
        else if(checkThreeFoldRepetition()) threefoldRepetition = true;
        else if(checkInsufficientMaterial()) insufficientMaterial = true;
        else
        {
            checkMate = staleMate = fiftyMoveRule = threefoldRepetition = insufficientMaterial = false;
        }

        validMovesCache = validMoves;
        cachedBoardHash = currentHash;
        return validMoves;
    }

    bool inCheck() const {
        return squareUnderAttack(whiteToMove ? whiteKingLocation.first : blackKingLocation.first,
                               whiteToMove ? whiteKingLocation.second : blackKingLocation.second);
    }

    bool squareUnderAttack(int r, int c) const {
        char attackingColor = whiteToMove ? 'b' : 'w';
        uint64_t targetBit = 1ULL << (r * 8 + c);
        
        // Check pawn attacks
        uint64_t pawnAttacks = 0;
        if (attackingColor == 'w') {
            pawnAttacks = ((whitePawns & ~0x00000000000000FF) >> 7) | ((whitePawns & ~0x0000000000000001) >> 9);
        } else {
            pawnAttacks = ((blackPawns & ~0xFF00000000000000) << 7) | ((blackPawns & ~0x0100000000000000) << 9);
        }
        if (pawnAttacks & targetBit) return true;

        // Check knight attacks
        uint64_t knightBits = attackingColor == 'w' ? whiteKnights : blackKnights;
        uint64_t knightAttacks = 0;
        while (knightBits) {
            int pos = countTrailingZeros(knightBits);
            int kr = pos / 8, kc = pos % 8;
            uint64_t attacks = 0;
            for (int dr : {-2, -1, 1, 2}) {
                for (int dc : {-2, -1, 1, 2}) {
                    if (abs(dr) != abs(dc)) {
                        int nr = kr + dr, nc = kc + dc;
                        if (nr >= 0 && nr < 8 && nc >= 0 && nc < 8) {
                            attacks |= 1ULL << (nr * 8 + nc);
                        }
                    }
                }
            }
            knightAttacks |= attacks;
            knightBits &= knightBits - 1;
        }
        if (knightAttacks & targetBit) return true;

        // Check sliding piece attacks
        uint64_t slidingPieces = (attackingColor == 'w' ? 
            (whiteBishops | whiteRooks | whiteQueens) : 
            (blackBishops | blackRooks | blackQueens));
        
        while (slidingPieces) {
            int pos = countTrailingZeros(slidingPieces);
            int sr = pos / 8, sc = pos % 8;
            std::string piece = board[sr][sc];
            
            if (piece[1] == 'B' || piece[1] == 'Q') {
                // Diagonal moves
                for (int dr : {-1, 1}) {
                    for (int dc : {-1, 1}) {
                        int nr = sr + dr, nc = sc + dc;
                        while (nr >= 0 && nr < 8 && nc >= 0 && nc < 8) {
                            if (nr == r && nc == c) return true;
                            if (board[nr][nc] != "--") break;
                            nr += dr; nc += dc;
                        }
                    }
                }
            }
            if (piece[1] == 'R' || piece[1] == 'Q') {
                // Straight moves
                for (int dr : {-1, 0, 1}) {
                    for (int dc : {-1, 0, 1}) {
                        if (dr == 0 && dc == 0) continue;
                        if (dr != 0 && dc != 0) continue;
                        int nr = sr + dr, nc = sc + dc;
                        while (nr >= 0 && nr < 8 && nc >= 0 && nc < 8) {
                            if (nr == r && nc == c) return true;
                            if (board[nr][nc] != "--") break;
                            nr += dr; nc += dc;
                        }
                    }
                }
            }
            slidingPieces &= slidingPieces - 1;
        }

        return false;
    }

    std::vector<Move> getAllPossibleMoves() const {
        std::vector<Move> moves;
        for (int r = 0; r < 8; r++) {
            for (int c = 0; c < 8; c++) {
                std::string piece = board[r][c];
                if (piece != "--" && 
                    ((piece[0] == 'w' && whiteToMove) || (piece[0] == 'b' && !whiteToMove))) {
                    getPieceMoves(r, c, moves);
                }
            }
        }
        return moves;
    }

    void getPieceMoves(int r, int c, std::vector<Move>& moves) const {
        std::string piece = board[r][c];
        char pieceType = piece[1];

        switch (pieceType) {
            case 'p': getPawnMoves(r, c, moves); break;
            case 'R': getRookMoves(r, c, moves); break;
            case 'N': getKnightMoves(r, c, moves); break;
            case 'B': getBishopMoves(r, c, moves); break;
            case 'Q': getQueenMoves(r, c, moves); break;
            case 'K': getKingMoves(r, c, moves); break;
        }
    }

    void getPawnMoves(int r, int c, std::vector<Move>& moves) const {
        bool isWhite = board[r][c][0] == 'w';
        int direction = isWhite ? -1 : 1;
        int startRow = isWhite ? 6 : 1;

        // Forward move
        if (insideBoard(r + direction, c) && board[r + direction][c] == "--") {
            moves.push_back(Move(r, c, r + direction, c, board[r][c], "--", ((isWhite & (r + direction == 0)) | (((!isWhite) & (r + direction == 7))))));
            if (r == startRow && board[r + 2 * direction][c] == "--") {
                moves.push_back(Move(r, c, r + 2 * direction, c, board[r][c], "--"));
            }
        }

        // Captures
        for (int dc : {-1, 1}) {
            if (insideBoard(r + direction, c + dc)) {
                std::string targetPiece = board[r + direction][c + dc];
                if (targetPiece != "--" && targetPiece[0] != board[r][c][0]) {
                    moves.push_back(Move(r, c, r + direction, c + dc, board[r][c], targetPiece, ((isWhite & (r + direction == 0)) | (((!isWhite) & (r + direction == 7))))));
                }
            }
        }

        // En passant
        if (enPassantPossible.first != -1) {
            for (int dc : {-1, 1}) {
                if (r + direction == enPassantPossible.first && c + dc == enPassantPossible.second) {
                    moves.push_back(Move(r, c, r + direction, c + dc, board[r][c], board[r][c + dc], ((isWhite & (r + direction == 0)) | (((!isWhite) & (r + direction == 7)))), true));
                }
            }
        }
    }

    void getRookMoves(int r, int c, std::vector<Move>& moves) const {
        std::vector<std::pair<int, int>> directions = {{0, 1}, {0, -1}, {1, 0}, {-1, 0}};
        getSlidingMoves(r, c, moves, directions);
    }

    void getBishopMoves(int r, int c, std::vector<Move>& moves) const {
        std::vector<std::pair<int, int>> directions = {{1, 1}, {1, -1}, {-1, 1}, {-1, -1}};
        getSlidingMoves(r, c, moves, directions);
    }

    void getKnightMoves(int r, int c, std::vector<Move>& moves) const {
        std::vector<std::pair<int, int>> knightMoves = {
            {2, 1}, {2, -1}, {-2, 1}, {-2, -1},
            {1, 2}, {1, -2}, {-1, 2}, {-1, -2}
        };

        for (const auto& [dr, dc] : knightMoves) {
            int nr = r + dr;
            int nc = c + dc;
            if (insideBoard(nr, nc) && 
                (board[nr][nc] == "--" || board[nr][nc][0] != board[r][c][0])) {
                moves.push_back(Move(r, c, nr, nc, board[r][c], board[nr][nc]));
            }
        }
    }

    void getQueenMoves(int r, int c, std::vector<Move>& moves) const {
        std::vector<std::pair<int, int>> directions = {
            {0, 1}, {0, -1}, {1, 0}, {-1, 0},
            {1, 1}, {1, -1}, {-1, 1}, {-1, -1}
        };
        getSlidingMoves(r, c, moves, directions);
    }

    void getKingMoves(int r, int c, std::vector<Move>& moves) const {
        std::vector<std::pair<int, int>> directions = {
            {0, 1}, {0, -1}, {1, 0}, {-1, 0},
            {1, 1}, {1, -1}, {-1, 1}, {-1, -1}
        };

        for (const auto& [dr, dc] : directions) {
            int nr = r + dr;
            int nc = c + dc;
            if (insideBoard(nr, nc) && 
                (board[nr][nc] == "--" || board[nr][nc][0] != board[r][c][0])) {
                moves.push_back(Move(r, c, nr, nc, board[r][c], board[nr][nc]));
            }
        }
    }

    void getSlidingMoves(int r, int c, std::vector<Move>& moves, 
                        const std::vector<std::pair<int, int>>& directions) const {
        for (const auto& [dr, dc] : directions) {
            for (int i = 1; i < 8; i++) {
                int nr = r + dr * i;
                int nc = c + dc * i;
                if (!insideBoard(nr, nc)) break;

                std::string targetPiece = board[nr][nc];
                if (targetPiece == "--") {
                    moves.push_back(Move(r, c, nr, nc, board[r][c], "--"));
                } else {
                    if (targetPiece[0] != board[r][c][0]) {
                        moves.push_back(Move(r, c, nr, nc, board[r][c], targetPiece));
                    }
                    break;
                }
            }
        }
    }

    void getCastleMoves(int r, int c, std::vector<Move>& moves) const {
        if (inCheck()) return;  // Cannot castle if in check

        if ((whiteToMove && currentCastlingRight.wks) || (!whiteToMove && currentCastlingRight.bks)) {
            // King-side castle
            if (board[r][c+1] == "--" && board[r][c+2] == "--") {
                if (!squareUnderAttack(r, c+1) && !squareUnderAttack(r, c+2)) {
                    moves.push_back(Move(r, c, r, c+2, board[r][c], "--", false, false, true));
                }
            }
        }
        if ((whiteToMove && currentCastlingRight.wqs) || (!whiteToMove && currentCastlingRight.bqs)) {
            // Queen-side castle
            if (board[r][c-1] == "--" && board[r][c-2] == "--" && board[r][c-3] == "--") {
                if (!squareUnderAttack(r, c-1) && !squareUnderAttack(r, c-2)) {
                    moves.push_back(Move(r, c, r, c-2, board[r][c], "--", false, false, true));
                }
            }
        }
    }

    // Getters and setters
    const std::vector<std::vector<std::string>>& getBoard() const { return board; }
    bool isWhiteToMove() const { return whiteToMove; }
    void setWhiteToMove(bool value) { whiteToMove = value; }
    bool isCheckMate() const { return checkMate; }
    bool isStaleMate() const { return staleMate; }
    bool isThreefoldRepetition() const { return threefoldRepetition; }
    bool isFiftyMoveRule() const { return fiftyMoveRule; }
    bool isInsufficientMaterial() const { return insufficientMaterial; }
    bool isDraw() const { return staleMate | threefoldRepetition | fiftyMoveRule | insufficientMaterial; }
};

BOOST_PYTHON_MODULE(chess_engine)
{
    using namespace boost::python;

    class_<Move>("Move", init<int, int, int, int, const std::string&, const std::string&, bool, bool, bool, char>())
        .def_readwrite("startRow", &Move::startRow)
        .def_readwrite("startCol", &Move::startCol)
        .def_readwrite("endRow", &Move::endRow)
        .def_readwrite("endCol", &Move::endCol)
        .def_readwrite("pieceMoved", &Move::pieceMoved)
        .def_readwrite("pieceCaptured", &Move::pieceCaptured)
        .def_readwrite("pawnPromotion", &Move::pawnPromotion)
        .def_readwrite("isEnPassantMove", &Move::isEnPassantMove)
        .def_readwrite("isCastleMove", &Move::isCastleMove)
        .def_readwrite("promotionChoice", &Move::promotionChoice)
        .def_readwrite("moveID", &Move::moveID);

    class_<CastleRight>("CastleRight", init<bool, bool, bool, bool>())
        .def_readwrite("wks", &CastleRight::wks)
        .def_readwrite("bks", &CastleRight::bks)
        .def_readwrite("wqs", &CastleRight::wqs)
        .def_readwrite("bqs", &CastleRight::bqs);

    class_<GameState>("GameState")
        .def(init<>())
        .def("makeMove", &GameState::makeMove)
        .def("undoMove", &GameState::undoMove)
        .def("getValidMoves", &GameState::getValidMoves)
        .def("getAllPossibleMoves", &GameState::getAllPossibleMoves)
        .def("isWhiteToMove", &GameState::isWhiteToMove)
        .def("setWhiteToMove", &GameState::setWhiteToMove)
        .def("isCheckMate", &GameState::isCheckMate)
        .def("isStaleMate", &GameState::isStaleMate)
        .def("isThreefoldRepetition", &GameState::isThreefoldRepetition)
        .def("isFiftyMoveRule", &GameState::isFiftyMoveRule)
        .def("isInsufficientMaterial", &GameState::isInsufficientMaterial)
        .def("isDraw", &GameState::isDraw)
        .def("getBoard", &GameState::board, return_value_policy<reference_existing_object>());
} 