import copy
import pygame
import random
import time

pygame.init()
pygame.font.init()
font = pygame.font.SysFont("Consolas", 35)
screenWidth, screenHeight = 1800, 1000
POKERGREEN = pygame.Color("#3c7257")
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
actionButtonWidth, actionButtonHeight = 120, 40
# calculate the button x coordinate so that they are mathematically equally spaced across the screen
# since its going to be 3 buttons displayed at a time the x coordinates are decided by multipying the screen width by 0.25 * n
# half button width is subtracted since it is draw from the top left corner.
actionButtonX = {"check": (int(screenWidth * 0.20)) - actionButtonWidth / 2, 
                 "fold": (int(screenWidth * 0.40)) - actionButtonWidth / 2,
                 "raise": (int(screenWidth * 0.60)) - actionButtonWidth / 2,
                 "call": (int(screenWidth * 0.80)) - actionButtonWidth / 2}
actionbuttonY = screenHeight - 70 # each action button will share the same height
# ^ both X and Y coords are calculated from screenHeight so that it scales accordingly
cardWidth = 125
cardHeight = 182
handCardXGap = 5 # horizontal pixel distance between 2 cards
handCardYGap = 275 # refers to pixel distance from bottom of screen
handCardX = [(screenWidth / 2 - cardWidth - handCardXGap), screenWidth / 2]
handCardY = screenHeight - handCardYGap

communityCardXGap = 10 # the horizontal pixel distance between each community card
communityCardYGap = (screenHeight / 2) + (cardHeight / 2) # vertical pixel distance from the bottom of the screen
# ^ scales with screen height due to screen dimensions possibly changing in future prototypes
totalCardsWidth = (5 * cardWidth) + (4 * communityCardXGap) # 4 gaps in between 5 cards
startX = (screenWidth - totalCardsWidth) / 2  
# ^  where the left most community card wil lbe
communityCardX = [
    startX + i * (cardWidth + communityCardXGap) 
    for i in range(0, 5)
] # list comprehension - > evenly spaced x-coords for community cards
communityCardY = screenHeight - communityCardYGap

# pygame.transform.scale(pygame.image.load(path), (cardWidth, cardHeight))
cardBack = pygame.transform.scale(pygame.image.load("cardBacks/card_back_red.png"), (cardWidth, cardHeight)) # must be loaded outside the card class for performance.
AIPosX = [handCardX[0]] # temp to see if image loads
AIPosY = [handCardY - 600]

screen = pygame.display.set_mode((screenWidth, screenHeight))

class GameController:
    def __init__(self):
        self._players = [] # list of Player() sublasses [AI/HUMAN] objects
        self._communityCards = [] # list of Card objects
        self._dealer = Dealer() # deck created in Dealer class
        self._currentPlayerTurn = 0
        self._gameTurn = 0
        humanPlayer = Player() # only 1 human in this poker game
        humanPlayer.addToGame(self._players)       
        self._buttons = ButtonManager({
            # key = buttonname, value = Button object
            # the action of the button e,g, humanPlayer.check comes from the previously created humanPlayer which is why humanPlayer is created before this
            "check": Button(actionButtonX["check"], actionbuttonY, actionButtonWidth, actionButtonHeight, humanPlayer.check, "check", WHITE),
            "fold": Button(actionButtonX["fold"], actionbuttonY, actionButtonWidth, actionButtonHeight, humanPlayer.fold, "fold", WHITE),
            "raise": Button(actionButtonX["raise"], actionbuttonY, actionButtonWidth, actionButtonHeight, humanPlayer.call, "raise", WHITE),
            "call": Button(actionButtonX["call"], actionbuttonY, actionButtonWidth, actionButtonHeight, humanPlayer.call, "call", WHITE)
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
        # stores a dictionary of the hands mapped to their value in descending order
        self._handValue = {"royal flush": 10, 
                        "straight flush": 9,
                        "four of a kind": 8,
                        "full house": 7,
                        "flush": 6,
                        "straight": 5,  
                        "three of a kind": 4,
                        "two pair": 3,
                        "one pair": 2,
                        "high card": 1}
        self._turn_history = []

    def gameLoop(self):
        AIPlayer1 = AIPlayer("monte")
        AIPlayer1.addToGame(self._players)
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
                            self.addToTurnHistory(self._buttons.getActionName())
                            print(self.getTurnHistory())
                            self._currentPlayerTurn += 1

            if self.checkRoundEnd() == True: 
                # ^ after all players are done w/ their turn deal the next card essentially
                self.startNextRound()
                #print([card.getName() for card in self._communityCards])

            self.computerAction()
            screen.fill(POKERGREEN)
            self._buttons.drawAllButtons()
            self.drawCards()
            screen.blit(cardBack, (AIPosX[0], AIPosY[0]))

            pygame.display.update()
            clock.tick(60) # 60 fps

    def addToTurnHistory(self, name):
        self._turn_history.append(name)
    
    def getTurnHistory(self):
        return self._turn_history
    
    def preFlop(self):
            # deals each player their hand -> then gives the cards their coordinates on the screen
            self._dealer.dealPlayerHands(self._players)
            for player in self._players:
                if player._isHuman == True: # human player will have their cards visible 
                    for index, card in enumerate(player._hand):
                        # this loop gets the index of the card in the player hand#
                        # then at that same index in the handCardX list, that x-coordinate is given
                        card.setPos(handCardX[index], handCardY)
        
    def flop(self):
        # 3 cards are dealt from the deck and added to the GameController's self._communityCard list
        self._dealer.dealFlop(self._communityCards)
        for index, card in enumerate(self._communityCards):
            # assigns the community card x-coordinate according to its index in the community card list
            card.setPos(communityCardX[index], communityCardY)

    def turn(self):
        # deal 1 community card from the deck and add to communityCard list
        self._dealer.dealTurn(self._communityCards)
        cardIndex = len(self._communityCards) - 1
        # ^ this is always the 4th community card but its index is 3
        # this index is used to assign the value at the 3rd index of the list of community card x-coords
        self._communityCards[-1].setPos(communityCardX[cardIndex], communityCardY)
        # the card has just been added so [-1] just allows me to access this newly added card

    # this method looks the same as the turn() method it functionally is, except at the end of this method another method will be called
    # the called method will evaluate the best hand that everyone has from merging the community cards and each player's respective cards
    def river(self):
        self._dealer.dealRiver(self._communityCards)
        cardIndex = len(self._communityCards) - 1
        self._communityCards[-1].setPos(communityCardX[cardIndex], communityCardY)
        # handEvaluator() method called here -> will be done in prototype 2 

        # for debugging
        """
        self._communityCards = [Card("5", "hearts"), Card("6", "hearts"), Card("7", "hearts"), Card("king", "spades"), Card("2", "spades")]
        for index, card in enumerate(self._communityCards):
            card.setPos(communityCardX[index], communityCardY)

        self._players[0]._hand = [Card("9", "hearts"), Card("3", "diamonds")]
        for index, card in enumerate(self._players[0]._hand):
                    card.setPos(handCardX[index], handCardY)
        """
        self.evaluatePlayerHands()

    def checkRoundEnd(self):
        # the round is considered ended when each player has made their turn
        # this condition will change when betting, i.e. essential feature balance system is added.
        if self._currentPlayerTurn > len(self._players) - 1:
            for action in self._turn_history:
                if action == "raise": # the turn for this round resets if someone raised. 
                    print("raise reset round!")
                    self._currentPlayerTurn = 0 # reset player turn
                    self._turn_history = []
                    # ^raisePot must have quanitity restrictions bababababaab
        return self._currentPlayerTurn > len(self._players) - 1
    
    def computerAction(self):
        currentPlayer = self._players[self._currentPlayerTurn]
        if currentPlayer._isHuman == True: # do not do an AI's turn if waiting for player to press button and do their turn
            return None # return None for now -> change to something better later?
        self._currentPlayerTurn += 1
        currentPlayer.monteCarloSimulation(10000, self._communityCards)
        self.addToTurnHistory(currentPlayer.getActionName()) # bobbobobobbobobobobob
        currentPlayer.doAction()

    def startNextRound(self):
        self._currentPlayerTurn = 0 # starting player will be at the 0th index
        self._gameTurn += 1 # goes to the next game turn e.g self.flop -> self.turn
        self.gameTurnState[self._gameTurn]() # calls the function from the key-value pair

    def drawCards(self):
        for player in self._players:
            for card in player._hand:
                if card._x != None and card._y != None: # was trying to draw AI cards and error 
                    card.draw() # draw to screen not from hand

        for card in self._communityCards:
            if card._x != None and card._y != None:
                card.draw()
    
    # takes the 2 player cards and community cards as one list
    def hasFlush(self, mergedCards): 
        # dictionary to keep track of the highest suit.
        suitCount = {"clubs": 0, "hearts": 0, "spades": 0, "diamonds": 0}
        for card in mergedCards:
            # add one to the value from the k-v pair
            suitCount[card._suit] += 1
        for value in suitCount.values():
            # a flush occurs when there are 5 or more of the same suit in your merged cards.
            if value >= 5:
                return True # flush
        return False

    # this method is used for the logic of the straight
    # dealing with the possiblites of having Ace of x as its 2 possible values (1 or highest card)
    # and checking for a straight flush by using the hasFlush() method
    def hasConsecutiveSequence(self, orderedCardList, isLowAce, checkStraightFlush):
        # the count starts at 1 instead of 0 because the first card in the ordered check would not
        # be counted due to checking if the next card is +1 of the current card.
        count = 1
        # loop through all cards except the last since we compare to the next card
        for cardIndex in range(len(orderedCardList) - 1):
            currentCardIntValue = orderedCardList[cardIndex].getIntValue()
            nextCardIntValue = orderedCardList[cardIndex + 1].getIntValue()

            # str value allows me to check for aces or not.
            currentCardStrValue = orderedCardList[cardIndex]._value
            nextCardStrValue = orderedCardList[cardIndex + 1]._value

            # adjust ace value if low ace mode is on
            if currentCardStrValue == "ace" and isLowAce == True:
                currentCardIntValue = 1 # ace can be either 1 or max (14)
            if nextCardStrValue == "ace" and isLowAce == True:
                nextCardIntValue = 1

            # check if the next card continues the sequence
            if currentCardIntValue + 1 == nextCardIntValue:
                count += 1
                # once we hit 5 in a row we have a straight
                if count == 5:
                    # if we're not checking for straight flush we're done
                    if checkStraightFlush == False:
                        return True
                    # otherwise check if these 5 cards share the same suit
                    if checkStraightFlush == True:
                        # card index - 3 refers to the start of the straight
                        # card index + 2 refers to the end of the straight
                        #  we must also check if the straight has a flush too
                        if self.hasFlush(orderedCardList[cardIndex - 3 : cardIndex + 2]):
                            return True
                        else:
                            return False
                        
            # duplicated values don't break the sequence, just skip them
            elif currentCardIntValue == nextCardIntValue:
                continue
            else:
                count = 1 # if the sequence is broken reset back to 1 NOT 0!!!
                # this is due to counting logic. (more in depth at start of method)

        # no straight so return False.
        return False

    def hasStraight(self, mergedCards, checkStraightFlush): # check straight
        # only interested in the card's value not the object so list of card values is made
        communityValue = [card._value for card in mergedCards]
        ascendingCards = sorted(mergedCards, key=lambda card: card.getIntValue())

        # counts the number of aces
        if "ace" in communityValue:
            aceCount = 0
            for card in ascendingCards:
                if card._value == "ace":
                    aceCount += 1
            # to account for aces dual value i make a new list that moves the aces to the front
            # via making a list of all the aces 
            acesEndIndex = len(ascendingCards) - aceCount
            lowAce = ascendingCards[acesEndIndex:]
            
            # then looping until where the aces end.
            for card in ascendingCards[:acesEndIndex]:
                lowAce.append(card) # ace = 1 
            # this returns True if the aces as 1 or aces as 14 form a straight
            return self.hasConsecutiveSequence(ascendingCards, False, checkStraightFlush) or self.hasConsecutiveSequence(lowAce, True, checkStraightFlush)
        
        # return for no aces in the mergedCards.
        return self.hasConsecutiveSequence(ascendingCards, False, checkStraightFlush)
    
    def sumValueCount(self, mergedCards):
        # makes a dictionary where each card value maps to how many times it appears
        # e.g. {"king": 2, "7": 1, "ace": 1}
        valueCount = {}
        for card in mergedCards:
            if card._value not in valueCount:
                valueCount[card._value] = 1  # first time seeing this value
            else:
                valueCount[card._value] += 1  # increment count for duplicates
        return valueCount


    def hasXOfAKind(self, mergedCards, matchingValue):
        # checks if any card value appears exactly matchingValue amount of times
        for num in self.sumValueCount(mergedCards).values():
            if num == matchingValue:
                return True  # found an X of a kind
        return False  # no X of a kind


    def twoPair(self, mergedCards):
        # checks for 2, 2 of a kinds
        # e.g. king of spades, king of hearts + queen of clubs, queen of diamonds
        twoPairCount = 0
        for num in self.sumValueCount(mergedCards).values():
            if num == 2:
                twoPairCount += 1  # found another pair
        return twoPairCount == 2  # this is always == 2 and never more since its impossible to have 3 occurnces for 2 of a kinds

    # i check in reverse order of hand value for simplicity and time complexity
    # as once the value has been found we can guarantee that is the best hand for that player's hand
    # this needs to be performant since it will be used for the monte-carlo simulations
    def evaluatePlayerHands(self):
        for player in self._players: # check each player
            mergedHandCommunity = self._communityCards[:] # use a shallow copy for safety this was bug remember later julius
            for card in player._hand:
                mergedHandCommunity.append(card) # add the current player's cards to the merged list (reset on next player)
            if self.hasStraight(mergedHandCommunity, checkStraightFlush=True):
                player._evaluatedHand = "straight flush"
                
            elif self.hasXOfAKind(mergedHandCommunity, 4): # 4 of a kind
                player._evaluatedHand = "four of a kind"
            
            elif self.hasXOfAKind(mergedHandCommunity, 3) and self.hasXOfAKind(mergedHandCommunity, 2):
                player._evaluatedHand = "full house"
            
            elif self.hasFlush(mergedHandCommunity):
                player._evaluatedHand = "flush"
            
            elif self.hasStraight(mergedHandCommunity, checkStraightFlush=False):
                player._evaluatedHand = "straight"

            elif self.hasXOfAKind(mergedHandCommunity, 3):
                player._evaluatedHand = "three of a kind"
            
            elif self.twoPair(mergedHandCommunity):
                player._evaluatedHand = "two pair"
            
            elif self.hasXOfAKind(mergedHandCommunity, 2):
                player._evaluatedHand = "one pair"
            
            else:
                player._evaluatedHand = "high card"

    def decideWinner(self): # added in prototype 2
        # playerToScore = {} possible solution?
        winner = self._players[0] # default value
        for player in self._players:
            if self._handValue[player._evaluatedHand] > self._handValue[winner._evaluatedHand]:
                winner = player # TODO: tied cases????
        return winner

class Dealer:
    def __init__(self):
        self._deck = Deck().createDeck() # list of 52 Card objects, in order

    def dealCard(self):
        if len(self._deck) > 1:
            return self._deck.pop()
        else:
            print("deck empty")
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


class Card:
    def __init__(self, value, suit, loadImage=True):
        self._value = value
        self._suit = suit
        self._path = f"cards/{self.getName()}.png"
        self._width = cardWidth
        self._height = cardHeight
        self._x = self._y = None
        if loadImage:
            path = f"cards/{self.getName()}.png"
            self._image = pygame.transform.scale(pygame.image.load(path), (cardWidth, cardHeight))
        else:
            self._image = None
    # returns the name of the card in the convention of the card images
    def getName(self):
        return f"{self._value}_of_{self._suit}"
    
    def getIntValue(self):
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


class Player:
    def __init__(self):
        self._hand = []
        self._evaluatedHand = ""
        self._isFolded = False
        self._x = screenWidth / 2
        self._y = screenHeight / 2
        self._isHuman = True

    def fold(self):
        # print("I FOLDED")
        self._isFolded = True

    def check(self): # skips player turn, if previous turn was check or nothing
        # print("I CHECKED") # debugging
        pass

    def giveCard(self, card):
        self._hand.append(card) # append Card object to hand attribute
    
    def addToGame(self, playerList):
        playerList.append(self)
    
    def raisePot(self, amount):
        print(f"raising by {amount}")

    def call(self):
        print("calling")


class AIPlayer(Player):
    def __init__(self, name="monte"):
        super().__init__()
        self._name = name
        self._isHuman = False
        self._action = self.check # temp action value
        self._actionName = "check"
        self._bluffConstant = 1 / random.randint(1, 100) # random float value betwwen 0.01 and 1
        self._aggressiveness =  1 / random.randint(1, 100) 
        self._confidence = 1 / random.randint(20, 55) # idk rn? 0.x as a average value??
        self._tiltLevel = 0 # decide later ^^^
    
    def doAction(self):
        if self._action == self.raisePot:
            return self._action(100)
        return self._action()
    
    def getActionName(self):
        return self._actionName
    
    def monteCarloSimulation(self, simulations, communityCards):
        wins = 0 # counter for the wins
        gameEnv = GameController() # recreate the game env outside the game loop
        opponent = AIPlayer() # opponent to play against in the simulations
        gameEnv._players = [self, opponent]
        startTime = time.time() # temporarily here for time benchmarking

        # create copy of the deck and remove what we know from copies
        deckCopy = [Card(value, suit, loadImage=False) for value in Deck()._values for suit in Deck()._suits]
        knownNamedCards = [card.getName() for mergedCards in (self._hand, communityCards) for card in mergedCards]
        cardsNeeded = (5 - len(communityCards)) + 2 # the +2 is for the opponnent cards needed
        # the simulations only work for 1 simulated oppponent, may change based on results?
        knownDeck = [card for card in deckCopy if card.getName() not in knownNamedCards]

        for simulation in range(0, simulations):
            # get a list of randomly picked cards for the community cards and the opponent hand cards.
            sampledCards = random.sample(knownDeck, cardsNeeded)
            opponent._hand = sampledCards[:2] # slice the last 2 cards for the opponent cards.

            # slice up to the last 2 for the community cards
            generatedCommunityCards = sampledCards[2:] 

            # have to use a copy of the communityCards for safety so we dont affect the actual game
            communityCardsCopy = communityCards[:] + generatedCommunityCards
            gameEnv._communityCards = communityCardsCopy

            gameEnv.evaluatePlayerHands() # each player's attribute of evaluatedHand gets changed accordingly
            if gameEnv.decideWinner() == self:
                wins += 1

        print(f"after {simulations} simulations this AI won {wins} times")
        # print(time.time() - startTime)
        self.attributeMath(wins, simulations)
    
    def attributeMath(self, wins, simulations):
        winrate = wins / simulations
        if winrate > self._confidence:
            if self._aggressiveness > self._confidence:
                # add an all in chance and how get the call value!
                self._action = self.raisePot # temp value to raise by
                self._actionName = "raise"

            else:
                self._action = self.call
                self._actionName = "call"

        elif self._aggressiveness > self._bluffConstant:

            if self._aggressiveness > self._confidence:
                self._action = self.raisePot # temp val

        else:
            self._action = self.fold
            self._actionName = "fold"

        # print(f"conf {self._confidence}")
        # print(f"bluff {self._bluffConstant}")
        # print(f"aggro {self._aggressiveness}")
        # print(f"tilt{self._tiltLevel}")

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
        
    def getActionName(self):
        if self.checkButtonClicked():
            return self.button._action


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

    # RENAME THIS FUNCTION LATER
    def getActionName(self):
        if self.checkButtonClicked():
            for buttonName in self._buttons: # loops over dict() keys
                if self._buttons[buttonName].wasClicked() == True:
                    return buttonName

    def drawAllButtons(self):
        for buttonName in self._buttons:
            self._buttons[buttonName].drawButton() # accesses the the Button() object value in the dict

game = GameController()
game.gameLoop()