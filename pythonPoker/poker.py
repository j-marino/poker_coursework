import pygame
import random
import time

pygame.init()
pygame.font.init()
fontConsolas = pygame.font.SysFont("Consolas", 35)
fontVerdana = pygame.font.SysFont("Verdana", 32)
turnIndicatorFont = pygame.font.SysFont("Consolas", 25)

screenWidth, screenHeight = 1600, 900
POKERGREEN = pygame.Color("#3c7257")
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (210, 210, 210)
RED = (255, 180, 180)

actionButtonWidth, actionButtonHeight = 120, 40
# calculate the button x coordinate so that they are mathematically equally spaced across the screen
# since its going to be 4 buttons displayed at a time the x coordinates are decided by multipying the screen width by 0.20 * n
# half button width is subtracted since it is draw from the top left corner.
# NOTE: this is subject to change with how the all-in is integrated, e.g. if its a separate button or not.
actionButtonX = {
    "check": (int(screenWidth * 0.20)) - actionButtonWidth / 2, 
    "fold": (int(screenWidth * 0.40)) - actionButtonWidth / 2,
    "raise": (int(screenWidth * 0.60)) - actionButtonWidth / 2,
    "call": (int(screenWidth * 0.80)) - actionButtonWidth / 2
}
# each action button will share the same height of 80 from the bottom of the screen
actionbuttonY = screenHeight - 80
# ^ both X and Y coords are calculated from screenHeight so that it scales accordingly

cardWidth = 125
cardHeight = 182
tableWidth = 1400 # original image width: 735
tableHeight = 700 # original image height: 350
# when scaling it must be somewhat close to the original 750x350 ratio.

handCardXGap = 5 # horizontal pixel distance between 2 cards
handCardYGap = 275 # refers to pixel distance from bottom of screen

# hand cards (player cards) and positioned in the bottom middle of the screen.
handCardX = [(screenWidth / 2 - cardWidth - handCardXGap), screenWidth / 2]
handCardY = screenHeight - handCardYGap

communityCardXGap = 10 # the horizontal pixel distance between each community card
communityCardYGap = (screenHeight / 2) + (cardHeight / 2) # vertical pixel distance from the bottom of the screen

totalCardsWidth = (5 * cardWidth) + (4 * communityCardXGap) # 4 gaps in between 5 cards
startX = (screenWidth - totalCardsWidth) / 2 # position of the left most community card wil lbe

# this list comprensions creates the x-coords of the middle cards, it adds nth position * cardwidth + spacers
# to create 5 coordinates mathematically spaced out.
communityCardX = [startX + i * (cardWidth + communityCardXGap) for i in range(0, 5)]
communityCardY = screenHeight - communityCardYGap # all community cards share this same coord.

# the mathematical centre of the poker table is visually unpleasing, to fix a spacer is used.
pokerTableYSpacer = 20 # controls the height of the poker table from the bottom of the screen
pokerTableX = (screenWidth - tableWidth) / 2
pokerTableY = (screenHeight - tableHeight) / 2 - pokerTableYSpacer
pokerTable = pygame.transform.scale(pygame.image.load("table/poker_table.png"), (tableWidth, tableHeight))

# must be loaded outside the card class for performance, since it would be computationally heavy for every card
# to have this inside the card class would mean every card loads its own image, makes it slow.
cardBack = pygame.transform.scale(pygame.image.load("cardBacks/card_back_red.png"), (cardWidth, cardHeight)) 

# AI positions -> clockwise from player's left
# the left 2 positions start at 23/100ths of the screen width, therefore the right 2 must be at 1 - 0.23 = 0.77
# this is a dict for robustness, instead of relying on indexes i would rather have the k-v pair for this.
# it also makes a better link for the Y pos of the key.
AIPosX = {
    1: [screenWidth * 0.23 - cardWidth * 2 - handCardXGap, screenWidth * 0.23 - cardWidth],  # lower left (player's left)
    2: [screenWidth * 0.23 - cardWidth * 2 - handCardXGap, screenWidth * 0.23 - cardWidth],  # upper left
    3: [handCardX[0], handCardX[1]],  # top center
    4: [screenWidth * 0.77, screenWidth * 0.77 + cardWidth + handCardXGap],  # upper right
    5: [screenWidth * 0.77, screenWidth * 0.77 + cardWidth + handCardXGap]   # lower right (player's right)
}

# the Y positions must form an oval shape. to achieve this y positions are calculated with half the card width,
# it works well for common screen sizes, tested at 1920x1080 and 2560x1440 monitors
AIPosY = {
    1: handCardY - cardHeight / 2,  # lower left (half card height above player)
    2: screenHeight * 0.05 + cardHeight / 2,  # upper left (half card height below top)
    3: screenHeight * 0.05,  # top center
    4: screenHeight * 0.05 + cardHeight / 2,  # upper right (half card height below top)
    5: handCardY - cardHeight / 2   # lower right (half card height above player)
}

# each position will have the AI name drawn beneath it
# names must be kept short (len<=6) so they dont take up too much screen space
# for future feature implementation of balance
AINames = { 
    1: "sharky",
    2: "rusher",
    3: "stackz",
    4: "sphinx",
    5: "richy"
}

screen = pygame.display.set_mode((screenWidth, screenHeight))

class GameController:
    def __init__(self):
        self._players = [] # list of Player() sublasses [AI/HUMAN] objects
        self._activePlayers = [] # separates the players who have folded from those who have not
        self._communityCards = [] # list of Card objects
        self._dealer = Dealer() # deck created in Dealer class
        self._currentPlayerTurn = 0
        self._gameTurn = 0

        # humanPlayer not initisalised in constructor with self for the purpose of its buttons.
        humanPlayer = Player() # only 1 human in this poker game
        humanPlayer.addToGame(self._players)

        self._buttons = ButtonManager({
            # key = buttonname, value = Button object
            # the action of the button e,g, humanPlayer.check comes from the previously created humanPlayer which is why humanPlayer is created before this
            # NOTE: future changes to buttons may occur with the potential addition of an "all-in" button
            "check": Button(actionButtonX["check"], actionbuttonY, actionButtonWidth, actionButtonHeight, humanPlayer.check, "check", WHITE),
            "fold": Button(actionButtonX["fold"], actionbuttonY, actionButtonWidth, actionButtonHeight, humanPlayer.fold, "fold", WHITE),
            "raise": Button(actionButtonX["raise"], actionbuttonY, actionButtonWidth, actionButtonHeight, humanPlayer.raisePot, "raise", WHITE),
            "call": Button(actionButtonX["call"], actionbuttonY, actionButtonWidth, actionButtonHeight, humanPlayer.call, "call", WHITE)
        }) # buttonManager takes the buttons as dictionary so it is easy to link to button
        # numbers not used since it would get confusing as which button i am refering to

        # this stores the games function calls after the preFlop is done
        # its needed to cleanly go through the function calls without a if, else bird's nest mess
        self.gameTurnState = {
            1: self.flop, 
            2: self.turn,
            3: self.river
        } # ^ doesnt start with preFlop since it happens at the beginning of the game and it's much easier to start the index at 0 and begin the 
        
        # stores a dictionary of the hands mapped to their value in descending order
        self._handValue = {
            "royal flush": 10, 
            "straight flush": 9,
            "four of a kind": 8,
            "full house": 7,
            "flush": 6,
            "straight": 5,  
            "three of a kind": 4,
            "two pair": 3,
            "one pair": 2,
            "high card": 1
        }
        
        # flags for the game loop
        self._raiseHappened = False # flag for the logic of keeping the betting round going when a raise occurs
        self._waitingForPlayer = True # True inital since at the very start of the game i will make the player be the first person to go.
        self._roundCycleFinished = False # relates to when every person has made a bet/action, turns to True if everyone has gone and raiseHappend = False
        self._raiser = None # is a Player/AIPlayer Object
        self._clearActions = False # each AI player's turns must be reset to none since it shouldn't have round persistence.

        # deal with picking up those who checked
        self._playersChecked = []

        # NOTE: these attributes are for the foundations of prototype 3, they have been made just so the AI can make valid moves
        # values for initialMinCall is a temp value
        self._initalMinCall = 5
        self._moneyLimits = {"call": 5, "raise": self._initalMinCall * 2} # raise value to be corrected in prototype 3.
        self._availableActions = ["call", "check", "fold", "raise"] # used for validation of moves.

    def gameLoop(self):
        for nameIndex in AINames.keys():
            AIPlayer(AINames[nameIndex]).addToGame(self._players) # AI's are given their according name and positions in the game

        self._activePlayers += self._players[:] # uses a copy for safety
        self._dealer.shuffle() # must shuffle at beggining of every game 

        # TODO: preFlop will have to consider the dealer button position, big and small blinds value and rotation.
        self.preFlop() # deals everyone 2 cards and starts the game.
        clock = pygame.time.Clock()
        
        while True:
            currentPlayer = self._activePlayers[self._currentPlayerTurn] # this variable used for checks and validation this persons turn.

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # if left click
                        # loops over all buttons to see if one was clicked
                        if self._buttons.checkButtonClicked() == True: 
                            # e.g. namedAction = "raise", used for validation and general processing
                            namedAction = self._buttons.getActionName()

                            # sanity check
                            if self.validAction(namedAction):
                                if self._clearActions == True:
                                    self.resetAIActionNames()

                                # flags are changed after this method call, e.g. raiseHappened
                                # TODO: will to integrate changing bet limits next.
                                self.processAction(namedAction, currentPlayer)
                                self._currentPlayerTurn += 1 # since the action is guaranteed valid we can move the next player.

                                # round finished when the last player has in the original cycle has made their turn.
                                # this does not necesarrily mean we start the next round, since a raise could have occured.
                                if self.roundEnded():
                                    self.resetRound()

            # round end if raise
            if self._raiseHappened:
                if self.raiseCycleFinished(): # checks if we are back to the raiser's turn.
                    # the method changes and resets flags, and also starts the next round
                    self.processRoundEnd()

            # round end if no raise
            elif self._roundCycleFinished and not self._raiseHappened:
                # must not end round if only some people checked
                if not self._playersChecked or len(self._playersChecked) == len(self._activePlayers):
                    self.processRoundEnd()

            # process the currentPlayer if they are not the human user
            if not currentPlayer._isHuman:
                if self.computerAction(): # returns true on sucessessful action decision and execution, false if not.
                    # TODO: must change bet limits based on a valid turn
                    # action is always valid at this point
                    self.processAction(currentPlayer._actionName, currentPlayer) 
                    
                    if self.roundEnded():
                        self.resetRound()

            # draw order MUST be background then table 
            screen.fill(POKERGREEN) # background
            self.drawTable()
            self._buttons.drawAllButtons()
            self.drawCards() # method also draws the back of the cards
            self.drawAINames()
            self.drawActionNames() # TODO: show the value of bet next to action
            self.drawTurnIndicator(currentPlayer)
            # e.g. -> raise (50). call (10), all-in (200)

            pygame.display.update()
            clock.tick(60) # 60 fps

    def processRoundEnd(self):
        if self.checkPostRiver(): # gameTurn == 3 -> end
            self.postRiver() # and decide winner.

        else:
            self.startNextRound() # executes next gameTurn function.

            # reset flags.
            self._roundCycleFinished = False
            self._raiseHappened = False
    
    def resetRound(self):
        self._currentPlayerTurn = 0 # back to start of active player list.
        self._roundCycleFinished = True # changes flag to show that we can move onto the next gameTurn if no raise happened.

    def raiseCycleFinished(self):
        # in poker the next turn starts when we are back to the most recent raiser's turn
        # this is the same as saying is the next persons turn complete? yes -> then set the flag to start the next round
        if self.getNextPlayerTurn() == self._raiser:
            return True
        
        return False
    
    def getNextPlayerTurn(self):
        # edge case, if we are at the last person in the activePlayer list then treated it as a cyclical list, go back to start
        if self._currentPlayerTurn >= len(self._activePlayers): # must use active players, folded players do not count.
            return self._activePlayers[0]
        
        return self._activePlayers[self._currentPlayerTurn]
    
    def validAction(self, actionName, amount=100): # temp value for prot 3 to implement
        # used for the player only, the AI will always make a valid action
        if actionName in self._availableActions:
            if actionName in self._moneyLimits.keys(): # raise or call -> blueprints for the features of protoype 3
                if amount < self._moneyLimits[actionName]: # if you were too poor then your raise/call is invalid
                    return False
                
            return True # this is for "check" and is only allowed when you are either first or no one else has made a money bet.
        
        return False
            
    def processAction(self, action, player):
        # if you didnt check then remove check from being an option this gameTurn round.
        if action != "check" and "check" in self._availableActions: # presence check otherwise it can error
            self._availableActions.remove("check")

        if action == "raise":
            # set flags for the raise round to occur instead of the non-raise round end.
            self._raiseHappened = True
            self._raiser = player
            self.removeFromCheckList(player)

        elif action == "fold":
            self._activePlayers.remove(player)
            self._currentPlayerTurn -= 1 # MUST minus one from this since it is incremented by 1 on every valid turn, including fold.
            # but removing a player and then incrementing would skip the next player so to negate this we -1
            self.removeFromCheckList(player)
        
        elif action == "call":
            self.removeFromCheckList(player)

        elif action == "check":
            self._playersChecked.append(player)

    def removeFromCheckList(self, player):
        if self._playersChecked and player in self._playersChecked:
            self._playersChecked.remove(player)

    def waitForInput(self):
        # when the round has finished the player must click a button or their mouse to progess
        # TODO: add text saying something like "press and key to continue" -> for prototype 3!!!
        waitingForInput = True

        while waitingForInput:
            events = pygame.event.get()

            for event in events:
                # still allow quitting in this state
                if event.type == pygame.QUIT:
                    exit()

                # any button press or mouse press
                if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                    waitingForInput = False
                
    def preFlop(self):
            # deals each player their hand -> then gives the cards their coordinates on the screen
            self._dealer.dealPlayerHands(self._players)

            for player in self._activePlayers:
                if player._isHuman == True: # human player will have their cards visible 
                    for index, card in enumerate(player._hand):

                        # this loop gets the index of the card in the player hand#
                        # then at that same index in the handCardX list, that x-coordinate is given
                        card.setPos(handCardX[index], handCardY)

                # AI's done separately since they have different coord lists and data types
                elif player._isHuman == False:
                    # AI coords stored in dicts, this is used to access the value from the k-v pair
                    AiIndex = self._players.index(player)

                    # looping over the player's hand here to set the AI's hand coords in the same way as the player since its modular
                    for index, card in enumerate(player._hand):
                        handCardPosXList = AIPosX[AiIndex]
                        handCardPosY = AIPosY[AiIndex]
                        card.setPos(handCardPosXList[index], handCardPosY)
        
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

        # for debugging and setting the commnunity cards and my cards to what i want for testing.
        """
        self._communityCards = [Card("5", "hearts"), Card("6", "hearts"), Card("7", "hearts"), Card("king", "spades"), Card("2", "spades")]
        for index, card in enumerate(self._communityCards):
            card.setPos(communityCardX[index], communityCardY)

        self._activePlayers[0]._hand = [Card("9", "hearts"), Card("3", "diamonds")]
        for index, card in enumerate(self._activePlayers[0]._hand):
                    card.setPos(handCardX[index], handCardY)
        """
    
    def postRiver(self):
        self.evaluatePlayerHands() # set each player's attributes of self._evaluatedHand to a string
        print(self.decideWinner()) # currently prints AI object
        # will change to names once main screen done (protoype 3), so the user can input their username

        self.revealAICards() # stop drawing red card back
        pygame.display.update()

        # commence next game
        # TODO: need a win/loss screen, if they run outta money -> lose, if everyone else broke -> win! -> retry/exit screen
        self.waitForInput()
        self.reset()
        pygame.display.update()
        self.preFlop()

    # end of game
    def checkPostRiver(self):
        return self._gameTurn == 3
        
    def roundEnded(self):
        if self._currentPlayerTurn > len(self._activePlayers) - 1:
            self._clearActions = True # flag for resetting AI's actions
            return True
    
    def computerAction(self):
        # was erroring before this due to indexing the next player's turn when the currentplayerturn needed to be indexed
        # now a turn is not executed or computed if the current player is at the end, since it should be finished
        if self._currentPlayerTurn >= len(self._activePlayers):
            return False
        
        currentPlayer = self._activePlayers[self._currentPlayerTurn]

        if currentPlayer._isHuman == True: # do not do an AI's turn if waiting for player to press button and do their turn
            return False 
        
        canCheck = "check" in self._availableActions

        # monteMethod(simulations, communityCards, canCheck, toCall, raiseMin)
        # num of simulations -> 11000, decided so it doesnt take too long and does enough to be adequate 
        currentPlayer.monteCarloSimulation(11000, self._communityCards, canCheck, self._moneyLimits["call"], self._moneyLimits["raise"])
        currentPlayer.doAction() # once it has the results of the simulations and set the action in its attributes then do the action!
        self._currentPlayerTurn += 1 # the player is valid so we can increment to the next player.

        return True

    def startNextRound(self):
        self._currentPlayerTurn = 0 # starting player will be at the 0th index
        self._gameTurn += 1 # goes to the next game turn e.g self.flop -> self.turn
        self.gameTurnState[self._gameTurn]() # calls the function from the key-value pair
        self._availableActions = ["call", "check", "fold", "raise"] # reset the available actions, allowing players to check again.

    # stops AI's actions having persistance on a new round, they are reset back to an empty string
    def resetAIActionNames(self):
        for player in self._activePlayers:
            if not player._isHuman: # AI only
                player._actionName = ""

        self._clearActions = False # reset flag since action is now complete

    def drawCards(self):
        for player in self._activePlayers: # activePlayers instead of players since it shows someone folds when their cards are not drawn
            if player._isHuman == True: 
                for card in player._hand:
                    if card._x != None and card._y != None: # was trying to draw AI cards and error 
                        card.draw() # draw to screen not from hand

            else: # the player we are at is AI
                 for card in player._hand:
                    if card._x != None and card._y != None: # was trying to draw AI cards and error 

                        # PLAYER MUST NOT BE ABLE TO SEE THE AI CARDS UNTIL END OF GAME
                        card.drawCardBack() # draw to screen not from hand

        # draw community cards (middle cards)
        for card in self._communityCards:
            if card._x != None and card._y != None:
                card.draw()
        
    def drawTable(self):
        screen.blit(pokerTable, (pokerTableX, pokerTableY))

    # AI names are positioned to the bottom left-most spot of the hand cards
    # this gives me space to draw their action
    def drawAINames(self):
        for posIndex in AINames.keys():
            nameText = fontVerdana.render((AINames[posIndex]), True , WHITE) # render the text 

            # draw in a spot according the k-v pair from the dict of coords
            screen.blit(nameText, (AIPosX[posIndex][0], AIPosY[posIndex] + cardHeight))
            # drawn on bottom left by using the 0th index, which is the left most card of the AI
            # adding cardHeight so that their name is drawn underneath the cards

    # draws "raise", "call", "fold" or "check" next to the AI's name
    # TODO: implement quantity of money next to action name (prototype 3)
    def drawActionNames(self):
        for posIndex in AINames.keys():
            # string of their action, this will makeup the text i draw e.g. "raise"
            AIAction = self._players[posIndex].getActionName()

            if AIAction != "":
                actionText = fontVerdana.render(AIAction, True, GREY) # render text in a different colour to their name
                screen.blit(actionText, (AIPosX[posIndex][1], AIPosY[posIndex] + cardHeight))
                # drawn on bottom right of hand cards by using the 1st index, which is the right most card of the AI

    # draws a "my turn" in the middle of the cards for clarity
    def drawTurnIndicator(self, currentPlayer):
        turnText = turnIndicatorFont.render("my turn", True, RED)
        textRect = turnText.get_rect() # use the rectangle for positions it
        heightSpacer = 5 # visuals, so it's not too close to the cards, looks more pleasant

        # player and AI coords treated differently since the player coords are not in the AI coord dict
        if currentPlayer._isHuman:
            # gets the middle of the 2 hand cards (for AI or human alike) and take away half the width of the text rect for a mathematical centre
            textRect.x = handCardX[1] - 0.5 * handCardXGap - textRect.width * 0.5
            textRect.y = handCardY - textRect.height - heightSpacer # position just above the card
        
        elif not currentPlayer._isHuman:
            # math is same as human just different indexing for the AI dicts.
            textRect.x = AIPosX[self._players.index(currentPlayer)][1] - 0.5 * handCardXGap - textRect.width * 0.5
            textRect.y = AIPosY[self._players.index(currentPlayer)] - textRect.height - heightSpacer

        screen.blit(turnText, textRect)

    # stop drawing the back of the AI's cards, this is when we decide a winner and everyone who still playing shows their cards
    def revealAICards(self):
        # using activePlayers, since folded players do not have to show their cards
        # since, it may be confusing if a folded player actually won and it says someone else won since they were still in the game
        for player in self._activePlayers:
            if player._isHuman == False: # only applies to the AI, human cards always visible to the human player
                for card in player._hand:
                    if card._x != None and card._y != None: 
                        card.draw() # draw to screen not from hand

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
        # straight's can only occurs in ascending order so this list is created
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
    def evaluatePlayerHands(self):#
        # for performance we only check the active players instead of all players since there is no need to know what someone who folded had, it would waste time
        for player in self._activePlayers: # check each activeplayer
            mergedHandCommunity = self._communityCards[:] # use a shallow copy for safety, or it modifies the original, which is very bad. and causes errors
            for card in player._hand:
                mergedHandCommunity.append(card) # add the current player's cards to the merged list (reset on next player)

            if self.hasStraight(mergedHandCommunity, checkStraightFlush=True):
                player._evaluatedHand = "straight flush" # is synonomous to a royal flush as well. (its just tbe best straight flush possible)
                
            elif self.hasXOfAKind(mergedHandCommunity, 4):
                player._evaluatedHand = "four of a kind"
            
            # full house is a 3 of a kind and a 2 of a kind.
            elif self.hasXOfAKind(mergedHandCommunity, 3) and self.hasXOfAKind(mergedHandCommunity, 2):
                player._evaluatedHand = "full house"
            
            elif self.hasFlush(mergedHandCommunity):
                player._evaluatedHand = "flush"
            
            # not checking for straight flush here, to save time, since it was already checked.
            elif self.hasStraight(mergedHandCommunity, checkStraightFlush=False):
                player._evaluatedHand = "straight"

            elif self.hasXOfAKind(mergedHandCommunity, 3):
                player._evaluatedHand = "three of a kind"
            
            elif self.twoPair(mergedHandCommunity):
                player._evaluatedHand = "two pair"
            
            # one 2 of a kind is a one pair.
            elif self.hasXOfAKind(mergedHandCommunity, 2):
                player._evaluatedHand = "one pair"
            
            else:
                player._evaluatedHand = "high card"

    def decideWinner(self): # added in prototype 2
        winner = self._activePlayers[0] # default value
        for player in self._activePlayers: # skips all folded players
            # if the current player's value is higher than the winner they are the new winner,
            # repeats until end of list
            if self._handValue[player._evaluatedHand] > self._handValue[winner._evaluatedHand]:
                winner = player 
        
        # TODO: add a case of n num of winners with the same hand, for this i will simplify it to splitting the pot instead of who has higher variation.
        # for: prototype 3
        return winner

    # all flags must be reset
    # deck must be shuffled and reset
    def reset(self):
        self._dealer.recreateDeck()
        self._communityCards = [] # no community cards
        self._currentPlayerTurn = 0 # TODO: This MUST change on the big, small blind and dealer button (proto 3)

        self._gameTurn = 0
        self._raiser = None
        self._raiseHappened = False
        self._roundCycleFinished = False
        self._dealer.shuffle() # shuffle the deck otherwise the cards given will the exact same as an unshuffled deck
        self._activePlayers = self._players[:]
        self._playersChecked = []
        self._moneyLimits = {"call": 5, "raise": self._initalMinCall * 2} # raise value to be corrected in prototype 3.
        self._availableActions = ["call", "check", "fold", "raise"] # used for validation of moves.

        for player in self._players: # was a bug when using self._activePlayers 
            # ALL player flags and attributes reset
            player._hand = []  
            player._evaluatedHand = ""  
            player._isFolded = False  
            if not player._isHuman:
                player._action = ""
                player._actionName = ""


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

    # has uses for when resetting a game, e.g. the end of a game or the monte-carlo sims.
    def recreateDeck(self):
        self._deck = Deck().createDeck()
        

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

    # this is the red back of a card, the image is loaded not inside this method
    def drawCardBack(self):
        screen.blit(cardBack, (self._x, self._y))

    # cards pos on screen
    def setPos(self, x, y):
        self._x, self._y = x, y


class Deck:
    def __init__(self):
        self._values = ["ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king"] # all possible values
        self._suits = ["clubs", "diamonds", "hearts", "spades"] # all possible suits
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
        self._isFolded = False # flag to remove a player from the activePlayers of a game
        self._isHuman = True
        # TODO: prototype 3: AI AND HUMAN need a bank account

    def fold(self):
        self._isFolded = True

    def check(self): # skips player turn, if previous turn was check or nothing
        pass # literally it does this, nothing
        # since the current player index is incremented elsewhere i wont do it here

    def giveCard(self, card):
        self._hand.append(card) # append Card object to hand attribute
    
    def addToGame(self, playerList):
        playerList.append(self)
    
    # TODO: prototype 3 feature, given temp values and simplified so that the AI can work with it and function
    def raisePot(self):
        print("raising by 1000")

    # TODO: add amounts to both the raise and the call methods.
    def call(self):
        print("calling")

    def allIn(self):
        print("ALL IN BABY") # temp for AI, this is just a raise equal to your bank account though

class AIPlayer(Player):
    def __init__(self, name="monte"): # default name but all AI's are given a name
        super().__init__()
        self._name = name
        self._isHuman = False
        self._action = self.check # default action value
        self._actionName = ""
        # randomness to make each AI have different behaviour chances
        self._bluffConstant = random.uniform(0.1, 0.4) # decides whether an AI will bluff
        self._aggressiveness = random.uniform(0.2, 0.6) # affects -> raising (by how much in proto 3) or calling 
        self._confidence = random.uniform(0.2, 0.7) # threshold for when the AI will act without bluffing
        self._previousActionName = None
    
    def doAction(self):
        # store previous action name to bias future decisions (prevents stupid) -> reduces repetition
        self._previousActionName = self._actionName
        return self._action()

    def getActionName(self):
        return self._actionName
    
    def recalculateAttributes(self):
         # randomise attributes between rounds so AI doesn't become predictable
        self._bluffConstant = random.uniform(0.1, 0.3)
        self._aggressiveness = random.uniform(0.1, 0.6)
        self._confidence = random.uniform(0.4, 0.7)
    
    def monteCarloSimulation(self, simulations, communityCards, canCheck, toCall, raiseMin):
        wins = 0 # counter for the wins

         # recreate a tiny game env to evaluate showdown outcomes without touching the real game
        gameEnv = GameController() 
        opponent = AIPlayer() # single simulation opponent to play against in the simulations
        gameEnv._activePlayers = [self, opponent]
        # startTime = time.time() # time benchmarking

        # create a copy of the current game deck WITHOUT loading images and remove what is known
        deckCopy = [Card(value, suit, loadImage=False) for value in Deck()._values for suit in Deck()._suits]
        knownNamedCards = [card.getName() for mergedCards in (self._hand, communityCards) for card in mergedCards]
        cardsNeeded = (5 - len(communityCards)) + 2 # the + 2 is for the opponnent cards needed

        # remove known cards from the simulated deck
        # knownDeck is the pool sample from each sim
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

            # each player's attribute of evaluatedHand gets changed accordingly
            gameEnv.evaluatePlayerHands() 
            if gameEnv.decideWinner() == self:
                wins += 1   

        # print(f"after {simulations} simulations this AI won {wins} times")
        # print(time.time() - startTime)

        # update bluff constant relative to observed win rate
        self._bluffConstant = self._aggressiveness * (1 - wins)
        self.attributeMath(wins, simulations, canCheck, toCall, raiseMin)
    
    def assignHandStrength(self, winrate):
        # uses a tuple as the key since its hashable
        # the 0th index of the tuple is the lower bound of the hand that type/strength
        # and the 1st index of the tuple is the upper bound of that hand type/strength
        handTypes = {
            (0.48, 0.55): "average",
            (0.55, 0.68): "strong",
            (0.68, 1.0): "very strong",
            (0.42, 0.48): "weak",
            (0.0, 0.42): "very weak"
        }

        for handType in handTypes.keys():
            if handType[0] < winrate < handType[1]: # if within range it is that hand strength
                return handTypes[handType]

    def attributeMath(self, wins, simulations, canCheck, toCall, raiseMin):
        # make the AI more semi-random on each turn
        self.recalculateAttributes()

        winrate = wins / simulations

        # the winrate must be normalised since it is too high for what i want
        # i want a percieved average hand (e.g. off suited with a face card and a low/mid - high/mid card) to be around 0.5
        # 0.72 is a number that will take the winrates and reduce them to something i can manage properly   
        winrate *= 0.72 

        handStrength =  self.assignHandStrength(winrate)
        print(f"\n{handStrength}") # debugging
        print(f"{self._name}: {[card.getName() for card in self._hand]}") # debugging

        print(winrate) # debugging

        # strong & v. strong hand 
        if handStrength == "strong" or handStrength == "very strong":

            # if ai hand is super strong then all in
            # and if the AI is an agressive and confidence player
            if handStrength == "very strong" and (self._aggressiveness + self._confidence) > winrate:
                self._action = self.raisePot  
                self._actionName = "raise" # will be a max raise
                # TODO: prototype 3 implement all in 
                return
            
            # raise decisions -> the threshold for a raise will depend on how strong the hand is percieved to be
            if handStrength == "very strong":
                if self._aggressiveness > 0.35: # more likely to raise on a "very strong" hand
                    self._action = self.raisePot
                    self._actionName = "raise"

            elif handStrength == "strong":
                if self._aggressiveness > 0.55: # less likely to raise on a "strong" hand
                    self._action = self.raisePot
                    self._actionName = "raise"
            
            # if checking is not an option (since toCall will have a value IMPLEMENTED IN PROT 3) then call
            if toCall > 0:
                self._action = self.call
                self._actionName = "call"
                return
            
            # if all else fails then just check (skip turn)
            if canCheck:
                self._action = self.check
                self._actionName = "check"
                return
        # NOTE: there is no folding option for a strong or very strong hand because it would be really stupid in a real game to fold such a hand
        # regardless of playstyle you should never fold a strong or strongish hand, since you would just be losing money for no reason. (applies to most situations, not all)

        # average hand
        if handStrength == "average":
            # this float will help dictate whether to raise or call
            roll = random.random() # random float between 0 and 1

            # aggressive AI and random roll chance of 1/4 -> then raise
            if self._aggressiveness > 0.50 and roll < 0.25:
                self._action = self.raisePot
                self._actionName = "raise"
                return
            
            # if not aggressive then check confidence.
            # this is the most likely action for an average hand.
            if self._confidence > 0.45 and roll < 0.7:
                self._action = self.call
                self._actionName = "call"
                return  

            # always have to see if checking is an option, it would be silly to fold when they can check instead.
            if canCheck:
                self._action = self.check
                self._actionName = "check"
                return
            
        # fold if all else fails.
            self._action = self.fold
            self._actionName = "fold"
            return
        
        # weakhand -> bluff, or fold
        if handStrength == "weak" or handStrength == "very weak":
            # this float will help dictate whether bluff or not
            roll = random.random() # random float between 0 and 1

            # if weak hand in play and confidence is very low and aggression is low then just fold
            if self._confidence < 0.3 and self._aggressiveness < 0.3:
                # but always see if you can check first!!
                if canCheck:
                    self._action = self.check
                    self._actionName = "check"
                    return
                
                self._action = self.fold
                self._actionName = "fold"
                return
            
            # bluff raise
            # the result of the roll can be a float between 0 and 1
            # bluffconstant and agressiveness multiplied is at a maximun of around 0.24
            # making a bluff less likely but possible, dont wanna get predictable here.
            if roll < self._bluffConstant * self._aggressiveness:
                print("im totally bluffing") # debugging
                self._action = self.raisePot
                self._actionName = "raise"
                return
            
            # again, check first then fold, never fold first
            if canCheck:
                self._action = self.check
                self._actionName = "check"
                return
            
            # fold the trash weak hand then.
            self._action = self.fold
            self._actionName = "fold"
            return    

class Button(pygame.Rect): # uses the pre-made Rect class from pygame library
    def __init__(self, x, y, width, height, action, text, color):
        super().__init__(x, y, width, height)
        self._action = action
        self._text = fontConsolas.render(text, True, BLACK)
        self._color = color
        self._active = True # TODO: decide what to do with this in prototype 3: for the all-in feature, separate button or inactive/active buttons.

    def renderButtonText(self):
        textRect = self._text.get_rect(center=self.center) # center text in the button rectangle
        screen.blit(self._text, textRect) 

    def drawButton(self):
        pygame.draw.rect(screen, self._color, (self.x, self.y, self.width, self.height)) # draw rectangle of button first
        self.renderButtonText() # then do the button text so that it shows ontop
    
    def wasClicked(self):
        if self.collidepoint(pygame.mouse.get_pos()):
            # if the player clicks this button then hadouken! do the button's action
            return True # signifies yes this button has been pressed
        else:
            return False # returns False if the button was not pressed
        
    def getActionName(self):
        if self.checkButtonClicked():
            return self.button._action
    
    def runAction(self):
        return self._action()


class ButtonManager:
    def __init__(self, buttons):
        self._buttons = buttons # buttons is a dict(buttonName:buttonObject)

    def checkButtonClicked(self):
        clicked = False # starts false and remains unchanged if a button was not pressed
        for buttonName, button in self._buttons.items(): # loops over dict() keys
            if self._buttons[buttonName].wasClicked() == True:
                button.runAction()
                clicked = True
        return clicked # this function is needed to check that a button has been pressed 
    # so i can change the game state accorindgly

    def getActionName(self):
        for buttonName in self._buttons: # loops over dict() keys
            if self._buttons[buttonName].wasClicked() == True:
                return buttonName

    def drawAllButtons(self):
        for buttonName in self._buttons:
            self._buttons[buttonName].drawButton() # accesses the the Button() object value in the dict

game = GameController()
game.gameLoop()