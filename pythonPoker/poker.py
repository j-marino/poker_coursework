import pygame
import random

pygame.init()
pygame.font.init()
font = pygame.font.SysFont("Consolas", 35)
screenWidth, screenHeight = 1500, 900
POKERGREEN = pygame.Color("#3c7257")
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
actionButtonWidth, actionButtonHeight = 120, 40
# calculate the button x coordinate so that they are mathematically equally spaced across the screen
# since its going to be 3 buttons displayed at a time the x coordinates are decided by multipying the screen width by 0.25 * n
# half button width is subtracted since it is draw from the top left corner.
actionButtonX = {"check": (int(screenWidth * 0.25)) - actionButtonWidth / 2, "fold": (int(screenWidth * 0.50)) - actionButtonWidth / 2}
actionbuttonY = screenHeight - 70 # each action button will share the same height
# ^ both X and Y coords are calculated from screenHeight so that it scales accordingly
cardWidth = 125
cardHeight = 182
handCardXGap = 5 # horizontal pixel distance between 2 cards
handCardYGap = 275 # refers to pixel distance from bottom of screen
handCardX = [(screenWidth / 2 - cardWidth - handCardXGap), screenWidth / 2]
handCardY = screenHeight - handCardYGap

communityCardXGap = 10
communityCardYGap = 700
totalCardsWidth = (5 * cardWidth) + (4 * communityCardXGap)
startX = (screenWidth - totalCardsWidth) / 2
communityCardX = [
    startX + i * (cardWidth + communityCardXGap) 
    for i in range(0, 5)
]
communityCardY = screenHeight - communityCardYGap

screen = pygame.display.set_mode((screenWidth, screenHeight))

class GameController:
    def __init__(self):
        self._players = [] # list of Player() sublasses [AI/HUMAN] objects
        self._communityCards = [] # list of Card objects
        self._dealer = Dealer() # deck created in Dealer class
        self._currentPlayerTurn = 0
        self._gameTurn = 0
        humanPlayer = Player() # only 1 human in this poker game
        self._players.append(humanPlayer)
        self._buttons = ButtonManager({
            # key = buttonname, value = Button object
            # the action of the button e,g, humanPlayer.check comes from the previously created humanPlayer which is why humanPlayer is created before this
            "check": Button(actionButtonX["check"], actionbuttonY, actionButtonWidth, actionButtonHeight, humanPlayer.check, "check", WHITE),
            "fold": Button(actionButtonX["fold"], actionbuttonY, actionButtonWidth, actionButtonHeight, humanPlayer.fold, "fold", WHITE),
        }) # buttonManager takes the buttons as dictionary so it is easy to link to button
        # numbers not used since it would get confusing as which button i am refering to

        # this stores the games turns chronological order
        # its needed to cleanly go through the function calls without a if, else bird's nest mess
        self.gameTurnState = {
            1: self.flop, 
            2: self.turn,
            3: self.river
        } # ^ doesnt start with preFlop since it happens at the beginning of the game and it's much easier to start the index at 0 and begin the 
        # function calls after the preFlop is done
        self._handValue = {10: "royal flush",
                           9: "straight flush",
                           8: "four of a kind",
                           7: "full house",
                           6: "flush",
                           5: "straight",
                           4: "three of a kind",
                           3: "two pair",
                           2: "one pair",
                           1: "high card"}  

    def preFlop(self):
        self._dealer.dealPlayerHands(self._players)
        for player in self._players:
            if player.isHuman == True:
                for index, card in enumerate(player._hand):
                    card.setPos(handCardX[index], handCardY)
        
    def flop(self):
        self._dealer.dealFlop(self._communityCards)
        for index, card in enumerate(self._communityCards):
            card.setPos(communityCardX[index], communityCardY)

    def turn(self):
        self._dealer.dealTurn(self._communityCards)
        cardIndex = len(self._communityCards) - 1
        self._communityCards[-1].setPos(communityCardX[cardIndex], communityCardY)

    def river(self):
        self._dealer.dealRiver(self._communityCards)
        cardIndex = len(self._communityCards) - 1
        self._communityCards[-1].setPos(communityCardX[cardIndex], communityCardY)

        # for debugging
        self._communityCards = [Card("ace", "spades"), Card("2", "spades"), Card("3", "spades"), Card("4", "spades") ,Card("5", "spades")]
        for index, card in enumerate(self._communityCards):
            card.setPos(communityCardX[index], communityCardY)

        self.handEvaluator()

    def checkRoundEnd(self):
        # the round is considered ended when each player has made their turn
        # this condition will change when betting, i.e. essential feature balance system is added.
        return self._currentPlayerTurn > len(self._players) - 1
    
    def startNextRound(self):
        self._currentPlayerTurn = 0 # starting player will be at the 0th index
        self._gameTurn += 1 # goes to the next game turn e.g self.flop -> self.turn
        self.gameTurnState[self._gameTurn]() # calls the function from the key-value pair

    def drawCards(self):
        for player in self._players:
            for card in player._hand:
                card.draw() # draw to screen not from hand

        for card in self._communityCards:
            card.draw()
    
    def checkSuits(self, mergedCards): # check flush
        suitCount = {"clubs": 0, "hearts": 0, "spades": 0, "diamonds": 0}
        for card in mergedCards:
            suitCount[card._suit] += 1
        for value in suitCount.values():
            if value >= 5:
                return True # flush
        return False

    def checkInOrder(self, orderedCardList):
        count = 0 # fix the comment below
        print(orderedCardList)
        for cardIndex in range(len(orderedCardList) - 1): # so no last one since we checking the next index
            if orderedCardList[cardIndex].getValue() + 1 == orderedCardList[cardIndex + 1].getValue():
                count += 1
                print(f"counter {count}" )
                if count == 5:
                    return True
            elif orderedCardList[cardIndex].getValue() == orderedCardList[cardIndex + 1].getValue():
                continue
            else: 
                count = 0
        return False

    # TODO: rename some of these functions
    def checkValueOrder(self, mergedCards): # check straight
        communityValue = [card._value for card in mergedCards]
        ascendingCards = sorted(mergedCards, key=lambda card: card.getValue())
        if "ace" in communityValue:
            aceCount = 0
            for card in ascendingCards:
                if card._value == "ace":
                    aceCount += 1
            lowAce = ascendingCards[len(ascendingCards) - aceCount:]
            for card in ascendingCards[:len(ascendingCards) - aceCount]:
                lowAce.append(card) # ace = 1 
            return self.checkInOrder(ascendingCards) or self.checkInOrder(lowAce)
        return self.checkInOrder(ascendingCards)
        
    def handEvaluator(self):
        for player in self._players:
            mergedHandCommunity = self._communityCards
            for card in player._hand:
                mergedHandCommunity.append(card)
            #self.checkSuits(mergedHandCommunity)
            print(self.checkValueOrder(mergedHandCommunity))

    def gameLoop(self):
        self._dealer.shuffle() # must shuffle at beggining of every game 
        self.preFlop()
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # if left click
                        if self._buttons.checkButtonClicked() == True: # loops over all buttons to see if one was clicked
                            self._currentPlayerTurn += 1
                            # the HUMAN player's turn is finished after a button is clicked

            if self.checkRoundEnd() == True: 
                # ^ after all players are done w/ their turn deal the next card essentially
                self.startNextRound()

            screen.fill(POKERGREEN)
            self._buttons.drawAllButtons()
            self.drawCards()
            pygame.display.update()
            clock.tick(60) # 60 fps
        

class Dealer:
    def __init__(self):
        self._deck = Deck().createDeck() # list of 52 Card objects, in order

    def dealCard(self):
        return self._deck.pop()
        # .pop() used to mimic how dealing is actually done, by removing the top card in the deck 
    
    def shuffle(self):
        random.shuffle(self._deck)

    # dealer methods named after their turn in poker
    def dealFlop(self, communityCards):
        # this takes 3 cards from the deck and adds them the to community card list
        for _ in range(0, 3): # iterator not important so "_" used
            card = self.dealCard()
            communityCards.append(card)
    
    # the turn and river in poker deals 1 community card and the 2 following methods do that
    def dealTurn(self, communityCards):
        card = self.dealCard()
        communityCards.append(card)

    def dealRiver(self, communityCards):
        card = self.dealCard()
        communityCards.append(card)
        # trigger hand strength evaluator function
    
    def dealPlayerHands(self, playerList):
        # this for loop deals a card to each player and repeats it so that each player gets 2 cards
        for _ in range(0, 2):
            for player in playerList:
                card = self.dealCard()
                player.giveCard(card)


class Card():
    def __init__(self, value, suit):
        self._value = value
        self._suit = suit
        self._path = f"cards/{self.getName()}.png"
        self._width = cardWidth
        self._height = cardHeight
        self._image = pygame.transform.scale(pygame.image.load(self._path), (125, 182))
        self._x = None
        self._y = None

    # returns the name of the card in the convention of the card images
    def getName(self):
        return f"{self._value}_of_{self._suit}"
    
    def getValue(self):
        faceCardToNum = {"jack": 11, "queen": 12, "king": 13, "ace": 14}
        return int(self._value) if self._value not in faceCardToNum.keys() else faceCardToNum[self._value]
    
    # original size: 500 × 726
    def draw(self):
        screen.blit(self._image, (self._x, self._y))

    def setPos(self, x, y):
        self._x, self._y = x, y

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
    def __init__(self):
        self._hand = []
        self._evaluatedHand = ""
        self._isFolded = False
        self._x = screenWidth / 2
        self._y = screenHeight / 2
        self.isHuman = True

    def fold(self):
        self._isFolded = True

    def check(self): # skips player turn, if previous turn was check or nothing
        print("I CHECKED") # debugging
        pass

    def giveCard(self, card):
        self._hand.append(card) # append Card object to hand attribute
    
    def addToGame(self, playerList):
        playerList.append(self)


class Button(pygame.Rect): # uses the pre-made Rect class from pygame library
    def __init__(self, x, y, width, height, action, text, color):
        super().__init__(x, y, width, height)
        self._action = action
        self._text = font.render(text, True, BLACK)
        self._color = color
        self._active = True

    def renderButtonText(self):
        textRect = self._text.get_rect(center=self.center) # center text in the button rectangle
        screen.blit(self._text, textRect) 

    def drawButton(self):
        pygame.draw.rect(screen, self._color, (self.x, self.y, self.width, self.height)) # draw rectangle of button first
        self.renderButtonText() # then do the button text so that it shows ontop
    
    def wasClicked(self):
        if self.collidepoint(pygame.mouse.get_pos()):
            # if the player clicks this button then hadouken! do the button's action
            self._action()
            return True # signifies yes this button has been pressed
        else:
            return False # returns False if the button was not pressed


class ButtonManager:
    def __init__(self, buttons):
        self._buttons = buttons # buttons is a dict()

    def checkButtonClicked(self):
        clicked = False # starts false and remains unchanged if a button was not pressed
        for buttonName in self._buttons: # loops over dict() keys
            if self._buttons[buttonName].wasClicked() == True:
                clicked = True
        return clicked # this function is needed to check that a button has been pressed 
    # so i can change the game state accorindgly

    def drawAllButtons(self):
        for buttonName in self._buttons:
            self._buttons[buttonName].drawButton()

game = GameController()
game.gameLoop()