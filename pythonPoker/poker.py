import pygame
import random

pygame.init()
screenWidth, screenHeight = 1200, 700
POKERGREEN = pygame.Color("#35654d")
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
pygame.font.init()
font = pygame.font.SysFont("Copperplate Gothic", 90)


screen = pygame.display.set_mode((screenWidth, screenHeight))

class GameController:
    def __init__(self):
        self._communityCards = []
        self._players = []
        self._foldedPlayers = []
        self._dealer = Dealer()

    def playerAction(self, players):
        for player in players:
            player.check()

    def gameLoop(self):
        self._dealer.shuffle()  
        player1 = HumanPlayer("timmy")
        player1.addToGame(self._players)
        clock = pygame.time.Clock()
        buttonTest = Button(100, 100, 250, 100, player1.check, "check", WHITE)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        buttonTest.onClick()
            screen.fill(POKERGREEN)
            buttonTest.drawButton()
            pygame.display.update()
            clock.tick(60)

class Dealer:
    def __init__(self):
        self._deck = Deck().createDeck()

    def dealCard(self):
        return self._deck.pop()
    
    def shuffle(self):
        random.shuffle(self._deck)

    # dealer methods named after their turn in poker
    def dealFlop(self, communityCards):
        # this takes 3 cards from the deck and adds them the to community card list
        for _ in range(0, 3):
            card = self.dealCard()
            communityCards.append(card)
    
    # the turn in poker deals 1 community card and this method does that,
    def dealTurn(self, communityCards):
        card = self.dealCard()
        communityCards.append(card)

    def dealRiver(self, communityCards):
        card = self.dealCard()
        communityCards.append(card)
        #trigger hand strength evaluator function
    
    def dealPlayerHands(self, playerList):
        # this for loop deals a card to each player and repeats it so that each player gets 2 cards
        for _ in range(0, 2):
            for player in playerList:
                player.giveCard(self.dealCard())


class Card:
    def __init__(self, value, suit):
        self._value = value
        self._suit = suit

    # this returns the name of the card in the convention of the card images
    def getName(self):
        return f"{self._value}_of_{self._suit}"


class Deck:
    def __init__(self):
        self._values = ["ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king"]
        self._suits = ["clubs", "diamonds", "hearts", "spades"]
        self._deck = [] # use a list for indexing

    # this method loops over all the possible values and suits and creates all the possible cards
    def createDeck(self):
        for value in self._values:
            for suit in self._suits:
                # uses the iterators of value and suit to create a Card object 
                # adds Cards object to the end of the deck list
                self._deck.append(Card(value, suit))
        return self._deck 


class Player():
    def __init__(self, name):
        self._name = name
        self._hand = []
        self._isFolded = False

    def fold(self):
        self._isFolded = True

    def check(self):
        print("I CHECKED")

    def getName(self):
        return self._name

    def giveCard(self, card):
        self._hand.append(card)

    def getHand(self):
        return self._hand
    
    def addToGame(self, playerList):
        playerList.append(self)


class HumanPlayer(Player):
    def __init__(self, name):
        super().__init__(name)
        pass


class Button(pygame.Rect):
    def __init__(self, x, y, width, height, action, text, color):
        super().__init__(x, y, width, height)
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._text = font.render(text, True, BLACK)
        self._action = action
        self._color = color
        self._rect = pygame.Rect(self._x, self._y, self._width, self._height)

    def renderButtonText(self):
        screen.blit(self._text, (self._x, self._y))

    def drawButton(self):
        pygame.draw.rect(screen, self._color, (self._x, self._y, self._width, self._height))
        self.renderButtonText()
    
    def onClick(self):
        if self._rect.collidepoint((pygame.mouse.get_pos())):
            # if the player clicks this button, hadouken!
            self._action()

game = GameController()
game.gameLoop()