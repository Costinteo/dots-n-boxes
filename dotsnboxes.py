import pygame
import pygame_menu
import math
import random
import copy
import time

# init pygame
successes, failures = pygame.init()
print("{0} successes and {1} failures".format(successes, failures))

# Screen Size and others
WIDTH, HEIGHT = 800, 800
PADDING = 75
ROWS, COLS = 8, 8
FPS = 60
X_OFFSET = ((WIDTH - PADDING * 2) // COLS)
Y_OFFSET = ((HEIGHT - PADDING * 2) // ROWS)

# Colours and aesthetics
BACKGROUNDCOLOUR = (255, 255, 255)
DOTSCOLOUR = (0, 0, 0)
P1COLOUR = (255, 0, 0)
P2COLOUR = (0, 0, 255)
BLACK = (10, 10, 80)
FONT = "dejavusans"

# Game-related settings
PVP = True
ALGORITHM = "randomAlgState"
DEPTH = 1

settingsFile = None

try:
    settingsFile = open("settings.txt")
except:
    print("Settings file not found! Resuming with default values.")

# if settings exist, then we parse them
if settingsFile:
    screenSize = settingsFile.readline().split()
    WIDTH, HEIGHT = int(screenSize[0]), int(screenSize[1])

    screenSize = settingsFile.readline().split()
    ROWS, COLS = int(screenSize[0]), int(screenSize[1])
    X_OFFSET = ((WIDTH - PADDING * 2) // COLS)
    Y_OFFSET = ((HEIGHT - PADDING * 2) // ROWS)

    BACKGROUNDCOLOUR = tuple(list(map(int, settingsFile.readline().split())))
    DOTSCOLOUR = tuple(list(map(int, settingsFile.readline().split())))
    P1COLOUR = tuple(list(map(int, settingsFile.readline().split())))
    P2COLOUR = tuple(list(map(int, settingsFile.readline().split())))

    PVP = bool(int(settingsFile.readline()))
    ALGORITHM, DEPTH = settingsFile.readline().split()
    DEPTH = int(DEPTH)

# algorithm package
# each function returns a state
class Algorithms():
    # outdated randomAlg function returning 2 ints and a bool for coordinates and whether or not the line is horizontal
    @staticmethod
    def randomAlg(scoreMatrix, horizontal, vertical):
        possiblePicks = []
        for y in range(len(scoreMatrix)):
            for x in range(len(scoreMatrix[y])):
                if not horizontal[y][x][0]:
                    possiblePicks.append([x, y, True])
                    if scoreMatrix[y][x] == 3:
                        return [x, y, True]
                elif not horizontal[y + 1][x][0]:
                    possiblePicks.append([x, y + 1, True])
                    if scoreMatrix[y][x] == 3:
                        return [x, y + 1, True]
                elif not vertical[y][x][0]:
                    possiblePicks.append([x, y, False])
                    if scoreMatrix[y][x] == 3:
                        return [x, y, False]
                elif not vertical[y][x + 1][0]:
                    possiblePicks.append([x + 1, y, False])
                    if scoreMatrix[y][x] == 3:
                        return [x + 1, y, False]
        return random.sample(possiblePicks, 1)[0]
    
    @staticmethod
    def randomAlgState(state):
        state.picks()
        for newState in state.possibleStates:
            if newState.players[1][1] > state.players[1][1]:
                return newState
        return random.sample(state.possibleStates, 1)[0]

    @staticmethod
    def minmaxAlg(state):
        # if I reached a final state or depth limit
        if state.depth == 0 or state.isFinal():
            firstPlayerWon = state.players[0][1] > state.players[1][1]
            secondPlayerWon = state.players[0][1] < state.players[1][1]
            draw = state.players[0][1] == state.players[1][1]
            maxPossibleRemainingScore = state.players[1][1] + ((ROWS - 1) * (COLS - 1) * 4 - state.players[0][1])
            state.estimation = 99 + state.depth if secondPlayerWon and state.isFinal() else -99 - state.depth if firstPlayerWon and state.isFinal() else 0 if draw and state.isFinal() else maxPossibleRemainingScore
            return state
        
        # generate possible states
        state.picks()

        estimatedMoves = [Algorithms.minmaxAlg(x) for x in state.possibleStates]
        # player 2 (computer) will always be the maximising player
        if state.players[state.turn][0] == "Player2":
            state.bestState = max(estimatedMoves, key = lambda x: x.estimation)
        else:
            state.bestState = min(estimatedMoves, key = lambda x: x.estimation)
            
        state.estimation = state.bestState.estimation
        return state
	
        
algorithmPack = Algorithms()


class Game():
    def __init__(self, copy = False):
        if not copy:
            # set screen, caption, clock
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
            pygame.display.set_caption("Costin Grigore - Dots'n'Boxes")
            self.clock = pygame.time.Clock()

        # initializing arrays for horizontal and vertical lines (the string will be the player who has that line)
        self.horizontal = [[[False, "None"] for _ in range(COLS - 1)] for _ in range(ROWS)]
        self.vertical = [[[False, "None"] for _ in range(COLS)] for _ in range(ROWS - 1)]
        self.scoreMatrix = [[0 for _ in range(COLS - 1)] for _ in range(ROWS - 1)]

        # initialize a player array with playername and score and turn
        self.players = [["Player1", 0], ["Player2", 0]]
        self.turn = 0
        # we will be using turn to keep track which players turn it is

        # sets whether we want player vs player or not and gamestate
        self.pvp = PVP
        self.gameState = "game in-progress"

    def update(self):

        # checking gamestate
        if self.gameState == "game in-progress":
            self.gameState = self.getGameState()
        else:
            print("Game closing in 10 seconds...")
            time.sleep(10)
            exit()

        # sleep to sync with fps
        self.clock.tick(FPS)
        
        # colour screen
        self.screen.fill(BACKGROUNDCOLOUR)

        # computer player move
        if not self.pvp and self.players[self.turn][0] == "Player2" and self.gameState == "game in-progress":
            alg = getattr(algorithmPack, ALGORITHM) # we pick the algorithm from settings to do the job
            # x, y, isHorizontal =  alg(self.scoreMatrix, self.horizontal, self.vertical)
            # self.pickLine(x, y, isHorizontal)
            chosenState = alg(State(self))
            self.horizontal = chosenState.bestState.horizontal
            self.vertical = chosenState.bestState.vertical
            self.scoreMatrix = chosenState.bestState.scoreMatrix
            self.players = chosenState.bestState.players
            self.turn = chosenState.bestState.turn
            self.printScoreMatrix()

        # get mouse position
        mousePos = pygame.mouse.get_pos()
        mx = (mousePos[0] - X_OFFSET // 2 - PADDING) // X_OFFSET
        my = (mousePos[1] - Y_OFFSET // 2 - PADDING) // Y_OFFSET
        isHorizontal = abs(mousePos[1] - PADDING - my * Y_OFFSET) < abs(mousePos[0] - PADDING - mx * X_OFFSET)

        self.drawHoverLine(mx, my, isHorizontal)

        # print(mx, my, isHorizontal)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.pickLine(mx, my, isHorizontal)
            elif event.type == pygame.KEYDOWN:
                # we can press q to end the game earlier
                if event.key == pygame.K_q:
                    self.gameState = "game ended"
        
        
        self.draw()

        pygame.display.flip()

    def draw(self):
        for x in range(COLS - 1):
            for y in range(ROWS):
                #draw the horizontal lines if there are any
                if self.horizontal[y][x][0]:
                    CURRENTPLAYERCOLOUR = P1COLOUR if self.horizontal[y][x][1] == "Player1" else P2COLOUR if self.horizontal[y][x][1] == "Player2" else None
                    if CURRENTPLAYERCOLOUR is None:
                        raise Exception("Current Player Unknown")
                    x_start_pos = x * X_OFFSET + PADDING + X_OFFSET // 2
                    y_start_pos = y * Y_OFFSET + PADDING + Y_OFFSET // 2
                    # draw line of width 7
                    pygame.draw.line(self.screen, CURRENTPLAYERCOLOUR, (x_start_pos, y_start_pos), (x_start_pos + X_OFFSET, y_start_pos), 7)

        for x in range(COLS):
            for y in range(ROWS - 1):
                #draw the vetical lines if there are any
                if self.vertical[y][x][0]:
                    CURRENTPLAYERCOLOUR = P1COLOUR if self.vertical[y][x][1] == "Player1" else P2COLOUR if self.vertical[y][x][1] == "Player2" else None
                    if CURRENTPLAYERCOLOUR is None:
                        raise Exception("Current Player Unknown")
                    x_start_pos = x * X_OFFSET + PADDING + X_OFFSET // 2
                    y_start_pos = y * Y_OFFSET + PADDING + Y_OFFSET // 2
                    # draw line of width 7
                    pygame.draw.line(self.screen, CURRENTPLAYERCOLOUR, (x_start_pos, y_start_pos), (x_start_pos, y_start_pos + Y_OFFSET), 7)

        for x in range(COLS):
            for y in range(ROWS):
                # draw the dots, center (offset by PADDING and half of the offset, basically dividing it in cells), radius 12px
                pygame.draw.circle(self.screen, DOTSCOLOUR, (x * X_OFFSET + PADDING + X_OFFSET // 2, y * Y_OFFSET + PADDING + Y_OFFSET // 2), 12)

        for x in range(COLS - 1):
            for y in range(ROWS - 1):
                # draw dots of winning colour for each box
                if self.scoreMatrix[y][x] == 5:
                    pygame.draw.circle(self.screen, P1COLOUR, (x * X_OFFSET + PADDING + X_OFFSET, y * Y_OFFSET + PADDING + Y_OFFSET), 30)
                elif self.scoreMatrix[y][x] == 6:
                    pygame.draw.circle(self.screen, P2COLOUR, (x * X_OFFSET + PADDING + X_OFFSET, y * Y_OFFSET + PADDING + Y_OFFSET), 30)

        if self.gameState == "game ended":
            font = pygame.font.SysFont(FONT, 64)
            gameOverText = font.render("GAME OVER", True, BLACK)
            gameOverTextRect = gameOverText.get_rect()
            gameOverTextRect.center = (WIDTH // 2, HEIGHT // 2 - 100)
            winner = "Player1" if self.players[0][1] > self.players[1][1] else "Player2" if self.players[0][1] < self.players[1][1] else "Nobody"
            draw = ""
            if winner == "Nobody":
                draw = " Draw!"
            winnerText = font.render(winner + " has won!" + draw, True, BLACK)
            winnerTextRect = winnerText.get_rect()
            winnerTextRect.center = (WIDTH // 2, HEIGHT // 2)

            self.screen.blit(gameOverText, gameOverTextRect)
            self.screen.blit(winnerText, winnerTextRect)

    def drawHoverLine(self, mx, my, isHorizontal):
        isOutOfBounds = mx < 0 or my < 0 or (isHorizontal and (mx >= COLS - 1 or my >= ROWS)) or (not isHorizontal and (mx >= COLS or my >= ROWS - 1))

        if not isOutOfBounds:
            # use transparent versions of the colours
            CURRENTPLAYERCOLOUR = tuple(min((x + 50), 255) for x in P1COLOUR) if self.players[self.turn][0] == "Player1" else tuple(min((x + 50), 255) for x in P2COLOUR)
            x_start_pos = mx * X_OFFSET + PADDING + X_OFFSET // 2
            y_start_pos = my * Y_OFFSET + PADDING + Y_OFFSET // 2
            if isHorizontal:
                pygame.draw.line(self.screen, CURRENTPLAYERCOLOUR, (x_start_pos, y_start_pos), (x_start_pos + X_OFFSET, y_start_pos), 7)
            else:
                pygame.draw.line(self.screen, CURRENTPLAYERCOLOUR, (x_start_pos, y_start_pos), (x_start_pos, y_start_pos + Y_OFFSET), 7)


    # we use bool actualPick to determine if the picking is legitimate or just used when generating states
    def pickLine(self, mx, my, isHorizontal, actualPick = True):

        # checking if the line picked is out of bounds
        isOutOfBounds = mx < 0 or my < 0 or (isHorizontal and (mx >= COLS - 1 or my >= ROWS)) or (not isHorizontal and (mx >= COLS or my >= ROWS - 1))

        if not isOutOfBounds:
            if isHorizontal and not self.horizontal[my][mx][0]:
                self.horizontal[my][mx][0] = True
                self.horizontal[my][mx][1] = self.players[self.turn][0]
                self.scoreCellUpdate(mx, my, isHorizontal)
                self.turn = (self.turn + 1) % 2
                if actualPick:
                    # printing score matrix and playerscore to console
                    self.printScoreMatrix()
            elif not isHorizontal and not self.vertical[my][mx][0]:
                self.vertical[my][mx][0] = True
                self.vertical[my][mx][1] = self.players[self.turn][0]
                self.scoreCellUpdate(mx, my, isHorizontal)
                self.turn = (self.turn + 1) % 2
                if actualPick:
                    # printing score matrix and playerscore to console
                    self.printScoreMatrix()
                
        else:
            # console message
            print("Out of bounds! Picked an invalid line.")


    def scoreCellUpdate(self, x, y, isHorizontal):
        # to do: implement a better way of adding the score, without so many ifs

        isOutOfBounds = x >= COLS - 1 or y >= ROWS - 1

        # cases where x == COLS - 1 or y == ROWS - 1
        if isHorizontal and y == ROWS - 1:
            self.scoreMatrix[y - 1][x] += 1
        elif not isHorizontal and x == COLS - 1:
            self.scoreMatrix[y][x - 1] += 1

        if not isOutOfBounds:
            self.scoreMatrix[y][x] += 1

        if isHorizontal and y - 1 >= 0 and not isOutOfBounds:
            self.scoreMatrix[y - 1][x] += 1
        elif not isHorizontal and x - 1 >= 0 and not isOutOfBounds:
            self.scoreMatrix[y][x - 1] += 1

        # this is probably less efficient than a ton of ifs, but it certainly doesn't look so horrible
        for y in range(ROWS - 1):
            for x in range(COLS - 1):
                if self.scoreMatrix[y][x] == 4:
                    self.players[self.turn][1] += 4
                    # we add the turn of the player + 1 to differentiate between the two when drawing the completed box
                    # we also do it so it doesn't get counted again when checking for completed boxes
                    self.scoreMatrix[y][x] += self.turn + 1


        
    
    def printScoreMatrix(self):
        for y in range(ROWS - 1):
            for x in range(COLS - 1):
                print(self.scoreMatrix[y][x], end = " ")
            print("\n", end = "")
        print(self.players, end = "\n\n")

    # returns "game ended" or "game in-progress"
    def getGameState(self):
        for y in range(ROWS - 1):
            for x in range(COLS - 1):
                if self.scoreMatrix[y][x] < 4:
                    return "game in-progress"
        return "game ended"
    
class State:
    def __init__(self, game, depth = DEPTH, parent = None, estimation = None):
        # we save the current state of the game in this class
        self.horizontal = copy.deepcopy(game.horizontal)
        self.vertical = copy.deepcopy(game.vertical)
        self.scoreMatrix = copy.deepcopy(game.scoreMatrix)
        self.players = copy.deepcopy(game.players)
        self.turn = game.turn

        self.parent = parent
        self.depth = depth
        self.possibleStates = []
        self.bestState = None
        self.estimation = estimation

    
    def picks(self):
        possiblePicks = []
        for y in range(len(self.scoreMatrix)):
            for x in range(len(self.scoreMatrix[y])):
                if not self.horizontal[y][x][0]:
                    possiblePicks.append([x, y, True])
                elif not self.horizontal[y + 1][x][0]:
                    possiblePicks.append([x, y + 1, True])
                elif not self.vertical[y][x][0]:
                    possiblePicks.append([x, y, False])
                elif not self.vertical[y][x + 1][0]:
                    possiblePicks.append([x + 1, y, False])

        for pick in possiblePicks:
            newGame = Game(True)
            newGame.turn = self.turn
            newGame.horizontal = copy.deepcopy(self.horizontal)
            newGame.vertical = copy.deepcopy(self.vertical)
            newGame.scoreMatrix = copy.deepcopy(self.scoreMatrix)
            newGame.players = copy.deepcopy(self.players)
            newGame.pickLine(pick[0], pick[1], pick[2], actualPick = False)
            self.possibleStates.append(State(newGame, self.depth - 1, parent = self))
        # newGame = Game(True)
        # newGame.turn = self.turn
        # newGame.horizontal = copy.deepcopy(self.horizontal)
        # newGame.vertical = copy.deepcopy(self.vertical)
        # newGame.scoreMatrix = copy.deepcopy(self.scoreMatrix)
        # newGame.players = copy.deepcopy(self.players)
        # newGame.pickLine(possiblePicks[0][0], possiblePicks[0][1], possiblePicks[0][2], actualPick = False)
        # print(newGame.turn)
        # self.possibleStates.append(State(newGame, self.depth - 1, parent = self))

    def isFinal(self):
        for y in range(len(self.scoreMatrix)):
            for x in range(len(self.scoreMatrix[y])):
                if self.scoreMatrix[y][x] < 4:
                    return False
        return True

game = Game()

while True:
    game.update()
    
