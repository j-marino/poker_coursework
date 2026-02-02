import pygame
import random
import time

pygame.init()
pygame.font.init()

infoFont = pygame.font.SysFont("consolas", 19)
infoFont.set_bold(True)

fontConsolas = pygame.font.SysFont("Consolas", 35)
fontVerdana = pygame.font.SysFont("Verdana", 30)
turnIndicatorFont = pygame.font.SysFont("Consolas", 25)
moneyFont = pygame.font.SysFont("Consolas", 25)

screenWidth, screenHeight = 1600, 900
POKERGREEN = pygame.Color("#3c7257")
WHITE = (255, 255, 255)
BLACK = (0, 0, 0) # used for button text
LIGHT_BLACK = (200, 200, 200) # action name.
HOVER_GREY = (190, 190, 190) # hovering over the button colour
RED = (255, 140, 140) # TURN INDICATOR
PLACEHOLDER_GREY = (150, 150, 150)
SCARY_RED = (200, 20, 20)

actionButtonWidth, actionButtonHeight = 120, 38
# calculate the button x coordinate so that they are mathematically equally spaced across the screen
# since its going to be 4 buttons displayed at a time the x coordinates are decided by multipying the screen width by 0.20 * n
# half button width is subtracted since it is draw from the top left corner.
# NOTE: this is subject to change with how the all-in is integrated, e.g. if its a separate button or not.
actionButtonX = {
    "check": (int(screenWidth * 0.20)) - actionButtonWidth / 2, 
    "fold": (int(screenWidth * 0.40)) - actionButtonWidth / 2,
    "call": (int(screenWidth * 0.60)) - actionButtonWidth / 2,
    "raise": (int(screenWidth * 0.80)) - actionButtonWidth / 2
}
# each action button will share the same height of 80 from the bottom of the screen
actionbuttonY = screenHeight - 50
# ^ both X and Y coords are calculated from screenHeight so that it scales accordingly

cardWidth = 125
cardHeight = 182
tableWidth = 1400 # original image width: 735
tableHeight = 700 # original image height: 350
# when scaling it must be somewhat close to the original 750x350 ratio.

handCardXGap = 5 # horizontal pixel distance between 2 cards
handCardYGap = 290 # refers to pixel distance from bottom of screen

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
pokerTableYSpacer = 40 # controls the height of the poker table from the bottom of the screen
pokerTableX = (screenWidth - tableWidth) / 2
pokerTableY = (screenHeight - tableHeight) / 2 - pokerTableYSpacer
pokerTable = pygame.transform.scale(pygame.image.load("assets/table/poker_table.png"), (tableWidth, tableHeight))

# must be loaded outside the card class for performance, since it would be computationally heavy for every card
# to have this inside the card class would mean every card loads its own image, makes it slow.
cardBack = pygame.transform.scale(pygame.image.load("assets/cardBacks/card_back_red.png"), (cardWidth, cardHeight)) 

dealerButtonWidth, dealerButtonHeight = 50, 50
dealerButton = pygame.transform.scale(pygame.image.load("assets/dealerButton/dealer_button.png"), (dealerButtonWidth, dealerButtonHeight)) 

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
Y_SPACER = 15
AIPosY = {
    1: handCardY - cardHeight / 2 - Y_SPACER,  # lower left (half card height above player)
    2: screenHeight * 0.05 + cardHeight / 2 - Y_SPACER,  # upper left (half card height below top)
    3: screenHeight * 0.05 - Y_SPACER,  # top center
    4: screenHeight * 0.05 + cardHeight / 2 - Y_SPACER,  # upper right (half card height below top)
    5: handCardY - cardHeight / 2 - Y_SPACER  # lower right (half card height above player)
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

AIs = ["human", "sharky", "rusher", "stackz", "sphinx", "richy"]

screen = pygame.display.set_mode((screenWidth, screenHeight))


class ScreenManager:
    def __init__(self):
        self._screens = [] # keep a "stack" of screens. menu -> gamescreen
        self._currentScreen = 0 # start at 0
    
    def addScreen(self, screenObject):
        self._screens.append(screenObject)
    
    def loadCurrentScreen(self):
        self._screens[self._currentScreen].runScreen() # runs the current screen.
    
    def nextScreen(self):
        self._currentScreen += 1 # increment the stack
    
    def getCurrentScreenIndex(self):
        return self._currentScreen
        

class Screen:
    def __init__(self, action):
        self._action = action
    
    def runScreen(self):
        if self._action: # stops from running invalid actions. (None type)
            return self._action()
    
    def setAction(self, action):
        self._action = action

class GameScreen(Screen): 
    def __init__(self, action): # action will be the GameController's gameloop.
        super().__init__(action)


class StartScreen(Screen):
    def __init__(self, action, screenManager):
        super().__init__(action)
        self._screenManager = screenManager
        self._buttons = ButtonManager({
            "start": Button(screenWidth / 2, screenHeight - 200, actionButtonWidth, actionButtonHeight, self.incrementStack, "start", WHITE)
        })
        self._usernameField = TextField(screenWidth / 2, screenHeight - 500, actionButtonWidth, actionButtonHeight, "username")

    # goes to the next screen in the assigned stack.
    def incrementStack(self):
        self._screenManager.nextScreen() 
        self._screenManager.loadCurrentScreen()

    def runScreen(self):
        clock = pygame.time.Clock()
        self._usernameField._active = True # set the field to active so it is drawn.

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

                usernameInput = self._usernameField.handleEvents(event) # handles enter, del, inputs.
                self.validateUsername(usernameInput) # username must be within a range of characters.

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # if left click
                        # loops over all buttons to see if one was clicked
                        if self._buttons.buttonWasClicked(): 
                            self._buttons.executeNamedButton(self._buttons.getActionName())
                        
                        
            self._usernameField._active = True # field must have persistence so it is continually drawn.                     
            screen.fill(POKERGREEN)
            self._buttons.drawAllButtons(True)
            self._usernameField.drawTextInput()
            pygame.display.update()
            clock.tick(60)

    def validateUsername(self, username):
        return True # implement later    
        

class GameController:
    def __init__(self):
        self._players = [] # list of Player() sublasses [AI/HUMAN] objects
        self._activePlayers = [] # separates the players who have folded from those who have not
        self._communityCards = [] # list of Card objects
        self._dealer = Dealer() # deck created in Dealer class
        self._banker = Banker()
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

        self._raiseField = TextField(actionButtonX["raise"], actionbuttonY, actionButtonWidth, actionButtonHeight, f"e.g: {self._banker._minRaise}") # temp values except for the x and y

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
        self._roundCycleFinished = False # when every person has made a bet/action, True if everyone has gone and raiseHappend = False
        self._raiser = None # is a Player/AIPlayer Object
        self._clearActions = False # each AI player's turns must be reset to none since it shouldn't have round persistence.

        # deal with picking up those who checked
        self._playersChecked = []

        # NOTE: these attributes are for the foundations of prototype 3, they have been made just so the AI can make valid moves
        # values for initialMinCall is a temp value
        self._initalMinCall = 20
        self._availableActions = ["call", "fold", "raise"] # used for validation of moves, check not included since you cannot check preflop
        self._showdownRunning = False # showdown is when everyone is all in
        self._lastPlayer = None
        self._smallBlind = None # blinds to be decided based off dealer button position.
        self._bigBlind = None

    def gameLoop(self):
        for nameIndex in AINames.keys():
            AIPlayer(AINames[nameIndex]).addToGame(self._players) # AI's are given their according name and positions in the game

        self._activePlayers += self._players[:] # uses a copy for safety
        self._banker.setFundedPlayers(self._activePlayers)
        self._banker.giveAllStartingMoney(1000) # everyone starting with £1000 
        self._banker.resetDebtList(self._activePlayers) # create the debt list -> player: 0 k-v pair
        self._dealer.shuffle() # must shuffle at beggining of every game 
    
        self._dealer.initialDealerButton(self._activePlayers) # randomly pick a person to get the dealer button.
        self.setBlinds() # blinds can now be set off the dealer button

        self.drawPokerAssets() # draw before the loop so that you can see the blinds make their action.

        # take the blind money
        self._banker.takeBlindMoney(self._smallBlind, self._smallBlind, self._bigBlind)
        self._banker.takeBlindMoney(self._bigBlind, self._smallBlind, self._bigBlind)

        self.preFlop() # deals everyone 2 cards and starts the game.
        clock = pygame.time.Clock()
     
        while True:
            if self._currentPlayerTurn >= len(self._activePlayers): # MUST MUST MUST validate this, or loads of errors, it is a circular list.
                self._currentPlayerTurn = 0 # set to 0 if past the active players.

            currentPlayer = self._activePlayers[self._currentPlayerTurn] # this variable used for checks and validation this persons turn.

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()

                raiseInput = int(self._raiseField.handleEvents(event)) # raise is a TextField, enter or key press or click are handled here

                # validate the raise input so its only run if its within the limits.
                if raiseInput != False and raiseInput >= self._banker._minRaise: # raise from box.
                    if self._banker._minRaise <= raiseInput <= currentPlayer._bank:
                        self._raiseField.resetInput() # sucessful execution, get rid of the text inside the box.
                        self.humanAction("raise", currentPlayer, raiseInput) # process the raise with the inputted value
                        currentPlayer = self._activePlayers[self._currentPlayerTurn]
                        raiseButton = self._buttons.getButtonObject("raise")
                        raiseButton._active = True # now draw the button instead of the Text Field
                        self._raiseField.setDrawError(False) # do not draw the error

                elif raiseInput != False: # if you inputted something that is not in the limits or correct
                    self._raiseField.setDrawError(True) # then error!
                    
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # if left click
                        # loops over all buttons to see if one was clicked
                        if self._buttons.buttonWasClicked(): 

                            # e.g. namedAction = "raise", used for validation and general processing
                            namedAction = self._buttons.getActionName()
                            buttonObject = self._buttons.getButtonObject(namedAction)

                            if namedAction == "raise" and buttonObject._active: # if the raise button was there
                                buttonObject._active = False # get rid of it (stop drawing)
                                self._raiseField._active = True # start drawing the input field.
                                
                            else:
                                self.humanAction(namedAction, currentPlayer, self._banker._minRaise)
                                currentPlayer = self._activePlayers[self._currentPlayerTurn]
                        
                        else: # a click occurs but a button not pressed
                            raiseButton = self._buttons.getButtonObject("raise")
                            raiseButton._active = True # draw the raise button again.
                    
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
                # elif self.getNumNonAllInPlayers() == len(self._playersChecked):
                    # self.processRoundEnd()

            # process the currentPlayer if they are not the human user
            if not currentPlayer._isHuman:
                if not self.currentPlayerIsAllIn(currentPlayer):
                    if self.computerAction(): # returns true on sucessessful action decision and execution, false if not.
                        # action is always valid at this point
                        self.processAction(currentPlayer._actionName, currentPlayer, currentPlayer._raiseAmount)
                        if currentPlayer == len(self._activePlayers): # after successful execution validate the current player to not go past the end of list
                            currentPlayer = self._activePlayers[0]

                        else:
                            try: # just incase it doesnt work
                                currentPlayer = self._activePlayers[self._currentPlayerTurn] 
                            except IndexError: # then dont do anything to the currentPlayer
                                pass
                            
                        if self.roundEnded(currentPlayer):
                            self.drawActionNames() # action e.g. call
                            self.drawActionValue() # value of action -> raise "20"
                            pygame.display.update()
                            pygame.time.wait(1000)  # wait 1s so you can digest what happened
                            self.resetRound()

                else: # the player is all-in
                    self.skipAllInPlayerTurn() # you do not get a turn if you are all in. there is nothing to do
            
            if currentPlayer._isHuman and self.currentPlayerIsAllIn(currentPlayer): # human handling of all in
                self.skipAllInPlayerTurn() # you do not get a turn if you are all in. there is nothing to do
            
            # draw order MUST be background then table 
            self.drawPokerAssets()
            self._buttons.drawAllButtons(currentPlayer._isHuman and not currentPlayer._isAllIn) # buttons are only drawn if it is the player's turn.
            self.drawTurnIndicator(currentPlayer) # indicates whose turn it is.

            if self._raiseField._showError:
                self.drawRaiseError() # if you entered a bad value for raising then tell the player the correct limits

            if self._showdownRunning and currentPlayer != self.lastPlayerInTurnOrder():
                self.showdown() # all cards face up and deal remaning cards
            
            pygame.display.update()
            clock.tick(60) # 60 fps
    
    # gets the AI's position based of which player it is using the global dictionaries and lists of coords.
    def getAIPosition(self, player):
        if player._isHuman or player._name not in AIs:
            return None
        
        index = AIs.index(player._name)
        if index not in AIPosX or index not in AIPosY:
            return None
        
        return (AIPosX[index], AIPosY[index], index)
    
    # index must go back to zero if we exceed the list length.
    def getNextIndex(self, current, list_length):
        return 0 if current >= list_length - 1 else current + 1
    
    # cards given coords so they can be drawn at a specific point on the screen.
    def assignCardPositions(self, cards, xCoords, yCoord):
        for index, card in enumerate(cards):
            card.setPos(xCoords[index], yCoord)

    def processRoundEnd(self):
        if self.checkPostRiver(): # gameTurn == 3 -> end
            self.postRiver() # and decide winner.

        else:
            self.startNextRound() # executes next gameTurn function.

            # reset flags.
            self._roundCycleFinished = False
            self._raiseHappened = False
            self._banker.resetDebtList(self._activePlayers) # set debts to 0
            self._banker.resetCurrentRoundBets() # no one has put any money on new round so set to 0.
    
    def resetRound(self):
        self._roundCycleFinished = True # changes flag to show that we can move onto the next gameTurn if no raise happened.
        self.resetAIActionNames() # to stop drawing the AI actions since they're going to be changed
        
    # draws an indicator to show who the winner is at the end of the rounds based of their cards.
    def drawWinnerText(self, winner):
        winnerText = turnIndicatorFont.render("WINNER", True, WHITE)
        textRect = winnerText.get_rect()
        heightSpacer = 5

        if winner._isHuman:
            # gets the middle of the 2 hand cards (for AI or human alike) and take away half the width of the text rect for a mathematical centre
            textRect.x = handCardX[1] - 0.5 * handCardXGap - textRect.width * 0.5
            textRect.y = handCardY - textRect.height - heightSpacer # position just above the card
        
        else:
            # math is same as human just different indexing for the AI dicts.
            aiIndex = self.getPlayerDisplayIndex(winner)
            if aiIndex is not None: # make sure the aiIndex is valid
                textRect.x = AIPosX[aiIndex][1] - 0.5 * handCardXGap - textRect.width * 0.5
                textRect.y = AIPosY[aiIndex] - textRect.height - heightSpacer

        screen.blit(winnerText, textRect) # bosh! put it on the screen

    def getPlayerDisplayIndex(self, player):
        if player._isHuman: # coords are calculated based of the hand cards
            return None
        
        else: # use the AI coord dicts and list if not human
            if player._name in AIs:
                return AIs.index(player._name)
            else:
                return None

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
    
    def validAction(self, actionName): # temp value for prot 3 to implement
        # used for the player only, the AI will always make a valid action
        if actionName in self._availableActions:
            return True # this is for "check" and is only allowed when you are either first or no one else has made a money bet.
        
        return False
            
    def processAction(self, action, player, raiseAmount):
        # if you didnt check then remove check from being an option this gameTurn round.
        if action != "check" and "check" in self._availableActions: # presence check otherwise it can error
            self._availableActions.remove("check")

        if action == "raise":
            # set flags for the raise round to occur instead of the non-raise round end.
            self._raiseHappened = True
            self._raiser = player
            self.removeFromCheckList(player) # if player previously checked get them out of the list now
            self.allInHandling(player, raiseAmount) # happens before the money is taken, or calculated wrong,               
            self._banker.handleRaise(player, raiseAmount)
            self._raiseField.changePlaceholderText(f"e.g: {self._banker._minRaise}") # usability design, show what the min value is.
            
        elif action == "fold":
            self._activePlayers.remove(player)
            self._currentPlayerTurn -= 1 # MUST minus one from this since it is incremented by 1 on every valid turn, including fold.
            # but removing a player and then incrementing would skip the next player so to negate this we -1

            # folding was causing some real issues with the current player so to fix use try-except block
            if self._raiser == player:
                try: # if the raiser is at the end of the list
                    self._raiser = self._activePlayers[self._currentPlayerTurn + 1]
                except IndexError: # then set to be zeroth index.
                    self._raiser = self._activePlayers[0] 
            
            self._banker.removeFromDebts(player) # you no longer have debt if you have folded
            if self.shouldTriggerShowdown(): # if everyone else now is all in then go showdown NOTE: this was causing bugs before
                self._showdownRunning = True
        
        elif action == "call":
            self.removeFromCheckList(player) # if player previously checked get them out of the list now
            self.allInHandling(player, self._banker._callValue)
            self._banker.handleCall(player) # handles debts too

        elif action == "check": # check = "skip my turn"
            self._playersChecked.append(player) # keep track of whom has checked
            if len(self._playersChecked) == self.getNumNonAllInPlayers() and self.hasAllInPlayers(): # if everyone checks then
                self._roundCycleFinished = True # go next round.

    def shouldTriggerShowdown(self):
        nonAllInCount = self.getNumNonAllInPlayers() # int num of those who are not all in
        if self.allPlayersAllIn(): # showdown occurs when all players all in
            return True
        
        # showdown can also occur when it is just one player who is not all in since they can have more money
        if nonAllInCount <= 1 and self.finishedBetting() and not self._playersChecked: # must account for checked players or bug.
            return True
        
        return False
    
    # checks if someone has gone all in
    def hasAllInPlayers(self):
        for player in self._activePlayers:
            if player._isAllIn:
                return True
            
        return False

    def getNumNonAllInPlayers(self):
        count = 0
        for player in self._activePlayers:
            if not player._isAllIn:
                count += 1

        return count # gets num of players still betting essentially ( == not all in)

    def playerIsGoingAllIn(self, player, bet):
        return self._banker.betGreaterThanBank(bet, player._bank) # counts if bet is equal to your bank.
    
    def setPlayerAllIn(self, player):
        player._isAllIn = True
    
    def skipAllInPlayerTurn(self):
        self._currentPlayerTurn += 1 # all in players do not get a turn so increment
    
    def currentPlayerIsAllIn(self, currentPlayer):
        return currentPlayer._isAllIn
    
    # all players all in accounts for if only 1 person is not all in
    def allPlayersAllIn(self):
        allIn = True
        count = 0
        for player in self._activePlayers:
            if not player._isAllIn:
                count += 1
                if count > 1: # if 1 person is all in then "not everyone is all in" but it is the same thing 
                    # since if you are not all in but everyone else is then the showdown is triggered regardless
                    return False
            
        return allIn

    def showdown(self):
        self.revealAICards() # all cards are shown face-up

        while not self.checkPostRiver(): # cycle through to the end of the game
            self.processRoundEnd()
            self.drawCards() # keep drawing all the cards.
            self.revealAICards() # re-reveal the cards
            pygame.display.update()
            time.sleep(1) # digest info time

        self.processRoundEnd()
        self._showdownRunning = False # set to False after the showdown is done so that it doesnt continually happen

    def removeFromCheckList(self, player):
        if self._playersChecked and player in self._playersChecked:
            self._playersChecked.remove(player) # keeps track of those who checked and removes if it cycles back and they make a turn.

    def waitForInput(self):
        # when the round has finished the player must click a button or their mouse to progess
        # TODO: add text saying something like "press and key to continue" 
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

    def setBlinds(self):
        if len(self._activePlayers) == 2: # special case for just 2 players
            # in heads-up poker, the dealer is the small blind
            # the dealer acts first pre-flop, but last post-flop
            dealerIndex = self._dealer._dealerButtonIndex
            smallBlindIndex = dealerIndex  # dealer is small blind
            bigBlindIndex = self.getNextIndex(dealerIndex, len(self._players))  # other player is big blind

            smallBlindIndex, bigBlindIndex = self.validateBlindIndexes(smallBlindIndex, bigBlindIndex)

            self._smallBlind = self._players[smallBlindIndex]
            self._bigBlind = self._players[bigBlindIndex]

            # pre-flop, small blind (dealer) acts first
            self._currentPlayerTurn = smallBlindIndex

        else: # normal case, > 2 players
            if self._dealer._dealerButton in self._players:
                dealerButtonIndex = self._players.index(self._dealer._dealerButton) # find where the dealer button is in player list
                smallBlindIndex = dealerButtonIndex + 1 # small blind is 1 clockwise after the dealer button
                bigBlindIndex = dealerButtonIndex + 2 # big blind is 2 clockwise after the dealer button
                
                smallBlindIndex, bigBlindIndex = self.validateBlindIndexes(smallBlindIndex, bigBlindIndex) # make sure indexes aren't outside the list boundaries.

                self._smallBlind = self._players[smallBlindIndex]
                self._bigBlind = self._players[bigBlindIndex]

                self._currentPlayerTurn = bigBlindIndex + 1 # first player to manually act is one clockwise after the big blind.
                if self._currentPlayerTurn == len(self._activePlayers): # make sure index isnt out of range ever.
                    self._currentPlayerTurn = 0

    def validateBlindIndexes(self, smallBlindIndex, bigBlindIndex):
        if smallBlindIndex == len(self._players): # this would be invalid if true
            smallBlindIndex = 0 # is a cyclical list so set 0 
            bigBlindIndex = 1

        elif smallBlindIndex == len(self._players) - 1: # if small blind is the last player
            smallBlindIndex = smallBlindIndex
            bigBlindIndex = 0 # big blind is now back to the start of the list
        
        return smallBlindIndex, bigBlindIndex

    # dealer button is passed onto the next player in clock-wise succession to keep game fair
    def rotateDealerButton(self): 
        if self._dealer._dealerButton in self._players: # safety!
            currentIndex = self._players.index(self._dealer._dealerButton)
            nextIndex = self.getNextIndex(currentIndex, len(self._players)) # gets next VALID index
            self._dealer._dealerButton = self._players[nextIndex]
            self._dealer._dealerButtonIndex = nextIndex

    def preFlop(self):
        # deals each player their hand -> then gives the cards their coordinates on the screen
        self._dealer.dealPlayerHands(self._players)

        for player in self._activePlayers:
            if player._isHuman:
                self.assignCardPositions(player._hand, handCardX, handCardY)
            else:
                # AI coords stored in dicts
                pos = self.getAIPosition(player)
                if pos:
                    x_coords, y_coord, index = pos
                    self.assignCardPositions(player._hand, x_coords, y_coord)
    
    def flop(self):
        # 3 cards are dealt from the deck and added to the GameController's self._communityCard list
        self._dealer.dealFlop(self._communityCards)

        # assigns the community card x-coordinate according to its index in the community card list
        self.assignCardPositions(self._communityCards, communityCardX, communityCardY)

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
        winner = self.decideWinner()

        self._banker.distributeMoney(self._activePlayers, winner) # give money returns if nededed
        self._banker.givePotToWinner(winner) # pot returned will be altered to correct value if money needs to be returned to loserz.
        
        self.revealAICards() # stop drawing red card back
        self.drawWinnerText(winner) 
        pygame.display.update()

        # check for broke ass players and then remove them
        brokePlayers = self._banker.getNoMoneyPlayers(self._players)
        if brokePlayers:
            self.removeFromGame(brokePlayers)
            
            # game over!!!
            if self.checkGameOver():
                return  # hahaaah

        # commence next game
        self.waitForInput()
        self.reset() # reset all flags, debts etc. for the new game start.
        self.rotateDealerButton() # + 1 to dealer button
        self.setBlinds() # blinds set at start of game.
        self._banker.takeBlindMoney(self._smallBlind, self._smallBlind, self._bigBlind)
        self.allInHandling(self._smallBlind, self._banker._smallBlindBet)
        self._banker.takeBlindMoney(self._bigBlind, self._smallBlind, self._bigBlind)
        self.allInHandling(self._bigBlind, self._banker._bigBlindBet)
        
        pygame.display.update()
        self.preFlop()
    
    def allInHandling(self, player, bet):
        if self.playerIsGoingAllIn(player, bet):
            self.setPlayerAllIn(player)
            if self.shouldTriggerShowdown():
                self._showdownRunning = True

    def checkGameOver(self):
        # human has run outta money
        humanPlayer = self._players[0]
        if humanPlayer._bank <= 0:
            print("GAME OVER - You're out of money!")
            self.displayGameOverScreen(False)
            return True
        
        # count how many people have money left if the human has money still
        playersWithMoney = [p for p in self._players if p._bank > 0]
        if len(playersWithMoney) == 1:
            print("AIs SMASHED GG EZ")
            self.displayGameOverScreen(True)
            return True
        
        return False

    def displayGameOverScreen(self, won):
        screen.fill(POKERGREEN)
        
        if won:
            message = "CONGRATULATIONS! YOU WON!"
            subMessage = "All opponents eliminated"
        else:
            message = "GAME OVER"
            subMessage = "You ran out of money"
        
        mainText = fontConsolas.render(message, True, WHITE)
        mainRect = mainText.get_rect(center=(screenWidth // 2, screenHeight // 2 - 50))
        screen.blit(mainText, mainRect)
        
        subText = fontVerdana.render(subMessage, True, LIGHT_BLACK)
        subRect = subText.get_rect(center=(screenWidth // 2, screenHeight // 2 + 10))
        screen.blit(subText, subRect)
        
        # CHANGE LATER TO RETRY AND CONTINUE
        continueText = turnIndicatorFont.render("click to exit", True, WHITE)
        continueRect = continueText.get_rect(center=(screenWidth // 2, screenHeight // 2 + 70))
        screen.blit(continueText, continueRect)
        
        pygame.display.update()
        
        # wait click to exit
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                    exit()

    # end of game
    def checkPostRiver(self):
        return self._gameTurn == 3
        
    def roundEnded(self, currentPlayer):   
        if self.finishedBetting():
            self._clearActions = True # flag for resetting AI's actions
            return True
    
    def finishedBetting(self):
        currentRoundBets = self._banker._currentRoundBets

        if len(self._playersChecked) == len(self._activePlayers): # all players checked
            return True # end round
        
        if not currentRoundBets: # no bets
            return False # then no keep going

        largestBet = max(currentRoundBets.values())

        for player in self._activePlayers:
            playerBet = currentRoundBets.get(player, 0) # if not in then -> 0

            if playerBet < largestBet: # accounts for checked players to keep playing since they have debts to pay still
                if player not in self._playersChecked or largestBet > 0:
                    return False
                
        return True
    
    # removes AI's from the game when they are poor, if the human were to lose then they trigger L screen instead of removing them.
    def removeFromGame(self, playersToBeRemoved):
        global AIs
        
        for player in playersToBeRemoved:
            if player in self._players:
                self._players.remove(player) # TODO: REMOVE ON L IMPLEMENT
                
                if not player._isHuman:
                    # DELETE THE AI SCRUBS
                    if player._name in AIs:
                        AIs.remove(player._name)

                # clean banker tracking -> no longer has money in the game, so remove
                if player in self._banker._playerToTotalMoneyIn:
                    del self._banker._playerToTotalMoneyIn[player]

                # broke players cannot pay debts so remove them
                if player in self._banker._raiseDebts:
                    del self._banker._raiseDebts[player]

                # broke player no longer funded so remove from there too
                if player in self._banker._fundedPlayers:
                    self._banker._fundedPlayers.remove(player)
            
    def computerAction(self):
        # was erroring before this due to indexing the next player's turn when the currentplayerturn needed to be indexed
        # now a turn is not executed or computed if the current player is at the end, since it should be finished
        if self._currentPlayerTurn >= len(self._activePlayers):
            return False
        
        currentPlayer = self._activePlayers[self._currentPlayerTurn]

        if currentPlayer._isHuman: # do not do an AI's turn if waiting for player to press button and do their turn
            return False 
        
        canCheck = "check" in self._availableActions

        # monteMethod(simulations, communityCards, canCheck, toCall, raiseMin)
        # num of simulations -> 8000, decided so it doesnt take too long and does enough to be adequate 
        currentPlayer.monteCarloSimulation(8000, self._communityCards, canCheck, self._banker._callValue, self._banker._minRaise)
        currentPlayer.doAction() # once it has the results of the simulations and set the action in its attributes then do the action!
        self._currentPlayerTurn += 1 # the player is valid so we can increment to the next player.

        print(f"{currentPlayer._actionName}, raise amt:{currentPlayer._raiseAmount}")
        return True

    def humanAction(self, namedAction, currentPlayer, raiseAmount):
        if self.validAction(namedAction) and currentPlayer._isHuman: # validation of humans actions
            self.processAction(namedAction, currentPlayer, raiseAmount)
            self._currentPlayerTurn += 1 # since the action is guaranteed valid we can move the next player.

            # round finished when the last player has in the original cycle has made their turn.
            # this does not necesarrily mean we start the next round, since a raise could have occured.
            if self.roundEnded(currentPlayer):
                self.resetRound()

    def startNextRound(self):
        self._gameTurn += 1
        self.gameTurnState[self._gameTurn]()

        # reset the available actions, allowing players to check again.
        self._availableActions = ["call", "check", "fold", "raise"]
        self._playersChecked.clear()
        self._raiseHappened = False
        self._raiser = None

    # stops AI's actions having persistance on a new round, they are reset back to an empty string
    def resetAIActionNames(self):
        for player in self._activePlayers:
            if not player._isHuman: # AI only
                player._actionName = ""

        self._clearActions = False # reset flag since action is now complete

    def drawRaiseField(self):
        if self._raiseField._active:
            self._raiseField.drawTextInput()

    def drawCards(self):
        for player in self._activePlayers: # activePlayers instead of players since it shows someone folds when their cards are not drawn
            if player._isHuman: 
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
        for player in self._players:
            if not player._isHuman:
                pos = self.getAIPosition(player)
                if pos:
                    x_coords, y_coord, index = pos
                    nameText = fontVerdana.render(player._name, True, WHITE)
                    screen.blit(nameText, (x_coords[0], y_coord + cardHeight))

    def drawPotMoney(self):
        potText = "pot £" + str(self._banker._pot) 
        potText = moneyFont.render(potText, True, WHITE)
        textRect =  potText.get_rect()

        # position at the mathematical center of the screen
        screen.blit(potText, (communityCardX[2] + (abs(textRect.width - cardWidth) / 2), communityCardY - textRect.height)) 
    
    def drawPlayerMoney(self):
        for player in self._players:
            bankText = "£" + str(player._bank)
            bankText = moneyFont.render(bankText, True, WHITE)
            textRect = bankText.get_rect()

            if player._isHuman:
                # position right underneath the cards, left hand card used for positioning
                bankTextX = handCardX[0]
                bankTextY = handCardY + cardWidth + textRect.height * 2.5
                screen.blit(bankText, (bankTextX, bankTextY))
                
                # if human is small or big blind
                if self._gameTurn < 1:
                    # show the blind input based of 2nd hand card coords
                    if player == self._smallBlind:
                        blindLabel = infoFont.render("small blind £" + str(self._banker._smallBlindBet), True, WHITE)
                        screen.blit(blindLabel, (handCardX[1], bankTextY))

                    elif player == self._bigBlind:
                        # big blind info
                        blindLabel = infoFont.render("big blind £" + str(self._banker._bigBlindBet), True, WHITE)
                        screen.blit(blindLabel, (handCardX[1], bankTextY))
            else:
                if player._name in AIs: # validate, only draw if in list
                    i = AIs.index(player._name)

                    if i in AIPosX and i in AIPosY:
                        bankTextX = AIPosX[i][0] # left most hand card.
                        bankTextY = AIPosY[i] + cardWidth + textRect.height * 4 # * 4 is a spacer for the height
                        screen.blit(bankText, (bankTextX, bankTextY))
                        
                        # if AI is small or big blind and label to the right
                        if self._gameTurn < 1:
                            if player == self._smallBlind:
                                blindLabel = infoFont.render("small blind £" + str(self._banker._smallBlindBet), True, WHITE)
                                blindLabelX = AIPosX[i][1] # pos to the right of the 2nd hand card
                                screen.blit(blindLabel, (blindLabelX, bankTextY))

                            elif player == self._bigBlind:
                                blindLabel = infoFont.render("big blind £" + str(self._banker._bigBlindBet), True, WHITE)
                                blindLabelX = AIPosX[i][1] # pos to the right of the 2nd hand card
                                screen.blit(blindLabel, (blindLabelX, bankTextY))
                    continue
                else:
                    continue
                
            screen.blit(bankText, (bankTextX, bankTextY))

    # draws "raise", "call", "fold" or "check" next to the AI's name
    def drawActionNames(self):
        for player in self._players:
            if not player._isHuman: # only for AI's
                pos = self.getAIPosition(player)
                AIAction = player.getActionName()

                if AIAction != "" and pos: # only draw valid actions
                    x_coords, y_coord, index = pos
                    actionText = fontVerdana.render(AIAction, True, LIGHT_BLACK)
                    screen.blit(actionText, (x_coords[1], y_coord + cardHeight)) # drawn off the underneath of right (2nd) hand card

    # draws the value of a bet, e.g. call -> "20" or raise -> "40"
    def drawActionValue(self):    
        for player in self._activePlayers:
            if not player._isHuman and player in self._banker._currentRoundBets: # only for non humans who have put money into this round.

                if player._actionName not in ["fold", "check", ""]: # only draw valid actions
                    pos = self.getAIPosition(player)

                    if pos:
                        # coords are calculated off the right hand card but it is drawn with a spacer so that it no 
                        # overlap with the action name
                        x_coords, y_coord, index = pos
                        totalBet = self._banker._currentRoundBets[player]
                        moneyText = fontVerdana.render(str(totalBet), True, LIGHT_BLACK)
                        
                        textX = x_coords[1] + 80 # + 80 is a spacer for the value so that its drawn appropriate spot.
                        textY = y_coord + cardHeight
                        screen.blit(moneyText, (textX, textY))
    
    # button is drawn on the bottom left of the left most hand card of the player
    def drawDealerButton(self):
        dealerButtonPlayer = self._dealer._dealerButton

        if dealerButtonPlayer in self._players: # validation
            if dealerButtonPlayer._isHuman:
                dealerButtonX = handCardX[0] # left hand card
                dealerButtonY = handCardY + cardHeight - dealerButtonHeight # bottom left of card

            else: # ai coords handled separetly
                pos = self.getAIPosition(dealerButtonPlayer)
                dealerButtonX = pos[0][0]  # left hand card
                dealerButtonY = pos[1] + cardHeight - dealerButtonHeight  # bottom left of card
        
            screen.blit(dealerButton, (dealerButtonX, dealerButtonY))
    
    def drawGameInfo(self):
        # key game information in the top right corner
        betX = screenWidth - 180  # pixels from right edge
        betY = 10  # pixels from top
        lineHeight = 25  # spacing between lines
        blindX = screenWidth - 350
        blindY = 10 # pixels from top
        
        # get all values from the Banker class
        callValue = self._banker._callValue
        minRaise = self._banker._minRaise
        smallBlindValue = self._banker._smallBlindBet
        bigBlindValue = self._banker._bigBlindBet

        # render the values into string and pygame form.
        callValueText = infoFont.render(f"bet call: £{callValue}", True, WHITE)
        minRaiseText = infoFont.render(f"minraise: £{minRaise}", True, WHITE)
        smallBlindText = infoFont.render(f"s.blind: £{smallBlindValue}", True, WHITE)
        bigBlindText = infoFont.render(f"b.blind: £{bigBlindValue}", True, WHITE)
        
        # draw it.
        screen.blit(callValueText, (betX, betY))
        screen.blit(minRaiseText, (betX, betY + lineHeight))
        screen.blit(smallBlindText, (blindX, blindY))
        screen.blit(bigBlindText, (blindX, blindY + lineHeight))

    # draws a "my turn" in the middle of the cards for clarity
    def drawTurnIndicator(self, currentPlayer):
        if not self.checkPostRiver() and not self._showdownRunning:
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
                if currentPlayer._name in AIs:
                    aiIndex = AIs.index(currentPlayer._name)

                    if aiIndex in AIPosX and aiIndex in AIPosY: # make sure index in coords
                        # mathematically calcualte the middle of the hand cards.
                        textRect.x = AIPosX[aiIndex][1] - 0.5 * handCardXGap - textRect.width * 0.5
                        textRect.y = AIPosY[aiIndex] - textRect.height - heightSpacer
                        screen.blit(turnText, textRect)

            screen.blit(turnText, textRect)
    
    def drawRaiseError(self):
        message = "min raise is " + str(self._banker._minRaise)
        errorInfo = self._raiseField.getWrongResponse(True, message)
        screen.blit(errorInfo[0], errorInfo[1])

    def drawPokerAssets(self):
        screen.fill(POKERGREEN) # background must be first
        self.drawTable() # table 2nd.
        self.drawCards() # method also draws the back of the cards, cards must be 3rd

        # order irrelevant after here:
        self.drawAINames()
        self.drawActionNames() 
        self.drawActionValue()
        self.drawPotMoney()
        self.drawPlayerMoney()
        self.drawRaiseField()
        self.drawDealerButton()
        self.drawGameInfo()

    # stop drawing the back of the AI's cards, this is when we decide a winner and everyone who still playing shows their cards
    def revealAICards(self):
        # using activePlayers, since folded players do not have to show their cards
        # since, it may be confusing if a folded player actually won and it says someone else won since they were still in the game
        for player in self._activePlayers:
            if not player._isHuman: # only applies to the AI, human cards always visible to the human player
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
            if currentCardStrValue == "ace" and isLowAce:
                currentCardIntValue = 1 # ace can be either 1 or max (14)
            if nextCardStrValue == "ace" and isLowAce:
                nextCardIntValue = 1

            # check if the next card continues the sequence
            if currentCardIntValue + 1 == nextCardIntValue:
                count += 1
                # once we hit 5 in a row we have a straight
                if count == 5:
                    # if we're not checking for straight flush we're done
                    if not checkStraightFlush:
                        return True
                    # otherwise check if these 5 cards share the same suit
                    if checkStraightFlush:
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

    def lastPlayerInTurnOrder(self):
        return self._activePlayers[-1]

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
        winner = self._activePlayers[0]
        for player in self._activePlayers: # skips all folded players
            # if the current player's value is higher than the winner they are the new winner,
            # repeats until end of list
            if self._handValue[player._evaluatedHand] > self._handValue[winner._evaluatedHand]:
                winner = player 
        
        # TODO: add a case of n num of winners with the same hand, for this i will simplify it to splitting the pot instead of who has higher variation.
        # for: prototype 3
        return winner
    
    def handlePrematureWin(self):
        # restructure this logic, used again in postriver
        self._banker.givePotToWinner(self._activePlayers[0])
        self.drawWinnerText(self._activePlayers[0])
        pygame.display.update()

        # Check for game over before continuing
        brokePlayers = self._banker.getNoMoneyPlayers(self._players)
        if brokePlayers:
            self.removeFromGame(brokePlayers)
            if self.checkGameOver():
                return

        self.waitForInput()
        self.reset()
        pygame.display.update()
        self.preFlop()

    # all flags must be reset
    # deck must be shuffled and reset
    def reset(self):
        self._dealer.recreateDeck()
        self._communityCards = [] # no community cards
        self._currentPlayerTurn = 0 # rehandled off the setBlinds method

        self._gameTurn = 0 # start of the game (preflop)
        self._raiser = None # no raises happened
        self._raiseHappened = False
        self._roundCycleFinished = False 
        self._dealer.shuffle() # shuffle the deck otherwise the cards given will the exact same as an unshuffled deck
        self._activePlayers = self._players[:]
        self._playersChecked = []
        self._availableActions = ["call", "fold", "raise"] # used for validation of moves. -> no check since you cannot check at the start of game!!
        self._banker._callValue = self._banker._bigBlindBet # call value is based dynamically off the big blind
        self._banker._previousBet = self._banker._smallBlindBet # for calc of minraise
        self._banker._currentBet = self._banker._bigBlindBet # for calc of minraise
        self._banker._minRaise = (self._banker._currentBet - self._banker._previousBet) + self._banker._currentBet 
        self._banker.resetCurrentRoundBets() # NO BETS at the begginig of game
        self._banker.resetDebtList(self._activePlayers) # no debts either
        self._showdownRunning = False # showdown not running

        for player in self._players:
            player._isAllIn = False # no one is all in on reset, can be changed if a blind causes player to go all in though

        for player in self._players:
            # ALL player flags and attributes reset
            player._hand = []  
            player._evaluatedHand = ""  
            player._isFolded = False  

            if not player._isHuman: # handle the AI's
                player._action = ""
                player._actionName = ""


class Dealer:
    def __init__(self):
        self._deck = Deck().createDeck() # list of 52 Card objects, in order
        self._dealerButton = None
        self._dealerButtonIndex = 0

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
    
    def initialDealerButton(self, players):
        pickedPlayer = random.choice(players)
        self._dealerButton = pickedPlayer
        self._dealerButtonIndex = players.index(pickedPlayer)


class Banker:
    def __init__(self):
        self._fundedPlayers = [] # will be a list of Player objects with money left
        self._pot = 0 # initally the pot starts at 0
        self._smallBlindBet = 10 # the inital s.blind, NOTE: will increase as rounds progress.
        self._bigBlindBet = self._smallBlindBet * 2 # is double the small blind
        self._previousBet = self._smallBlindBet 
        self._currentBet = self._bigBlindBet 

        # min raise formula is to add the raise total to the most recent bet. needs to be recalulated on every raise.
        self._minRaise = (self._currentBet - self._previousBet) + self._currentBet 
        self._callValue = self._bigBlindBet # call becomes the most recent bet.
        self._lastRaise = 0
        self._currentRoundBets = {} # player-bet dict for collecting the debts of those who need to pay after a raise to continue.
        self._raiseDebts = {} # debt needed to be paid if someone raises by the other players.
        self._playerToTotalMoneyIn = {} # player object - money inputted k-v pair.
        self._biggestAllIn = 0
    
    # initialies the list of players with money
    def setFundedPlayers(self, playerList):
        self._fundedPlayers = playerList
    
    # everyone will start with the same amount, so their banks are changed here to initialBank.
    def giveAllStartingMoney(self, initalBank):
        for player in self._fundedPlayers:
            player._bank = initalBank
    
    # this method is the logic that call and raise both reuse to handle money processing.
    def processBet(self, player, amount):
        player._bank -= amount
        self._pot += amount # add the money to the pot that the player has put in
        self.addToCurrentRoundBets(player, amount) # keep track of who put in x money.
        self.addToBetTotal(player, amount) # keep track of how much money x person has inputted this round.
    
    def handleCall(self, player):
        if self.playerHasDebt(player): # when someone raises, all active players have a "debt" to pay so they can continue playing
            debtToPay = self._raiseDebts[player]
            # if you cannot pay the debt required to stay but decide to call then the remainder of your bank is taken instead.
            debtPaid = player._bank if self.betGreaterThanBank(debtToPay, player._bank) else debtToPay
            self.processBet(player, debtPaid) # add debtPaid to the total a player puts in not the debt they need to pay, so money can be returned properly.

        else: # no debts, regular call happens.
            moneyIn = player._bank if player._bank < self._callValue else self._callValue # too broke for a call, so just take what is left of bank.
            self._raiseDebts[player] -= moneyIn # subtract to make the raisedebt negative so you dont have to input more than you have to.
            self.processBet(player, moneyIn)
    
    def moneyAlreadyIn(self, player):
        return self._currentRoundBets.get(player, 0) > 0 # robustness & validation, if the player not in current round bets then -> 0

    def setMinRaise(self):
        self._minRaise = self._callValue + self._lastRaise # calculates min raise off the formula

    def handleRaise(self, player, raiseAmount):
        self._previousBet = self._currentBet # change the current and previous bet so minraise can be calculated properly.
        self._currentBet = raiseAmount if self._currentBet else self._callValue
        self._lastRaise = raiseAmount - self._previousBet # raiseAmount refers to what you are raising to, so the difference is calculated to get the lastRaise.
        self.processBet(player, raiseAmount)
        self._callValue = self._currentBet # call value must change to new raise value.
        self.setMinRaise()
        self._raiseDebts[player] -= raiseAmount # take away from debt so you dont pay more than you have to.
        self.calculatePlayerDebts(player, raiseAmount) # give everyone debt to pay since someone raised

    # keep track of bets for this round.
    def addToCurrentRoundBets(self, player, bet): 
        if player not in self._currentRoundBets:# if not in bet then set bet to their bet
            self._currentRoundBets[player] = bet 

        else:
            self._currentRoundBets[player] += bet # if they are in the current round bet add instead of overwriting.
        
    def resetCurrentRoundBets(self):
        self._currentRoundBets = {} # must reset on round start.
    
    def resetDebtList(self, activePlayers): # debts start at 0 and become 0 when a round ends.
        for player in activePlayers:
            self._raiseDebts[player] = 0

    def calculatePlayerDebts(self, raiser, moneyIn): # debts must be calculated based on the money you already put in if you have put money in.
        for player in self._raiseDebts.keys():
            if player != raiser:
                self._raiseDebts[player] += moneyIn # add to raiseDebts instead of assigning NOTE: this is a major bug if its assigned.
    
    def removeFromDebts(self, player):
        if player in self._raiseDebts: # validate
            del self._raiseDebts[player] # delete the k-v debt pair 

    def givePotToWinner(self, player):
        player._bank += self._pot # winner gets pot, but not always the whole pot, extra money will be returned if necessary to those who put more than the winner.
        self._pot = 0 # reset pot

    def playerHasDebt(self, player):
        return player in self._raiseDebts and self._raiseDebts[player] > 0
    
    def betGreaterThanBank(self, bet, playerBank):
        return bet >= playerBank # >= here instead of >, since this logic is used for all in too, which is when the bet can be equal to your bank

    def isBiggestAllIn(self, allInValue):
        return allInValue > self._biggestAllIn # for calculating money returns, if someones all in is bigger than other person's all in.
    
    # keep track of TOTAL money person has inputted.
    def addToBetTotal(self, player, bet): 
        if player in self._playerToTotalMoneyIn:
            self._playerToTotalMoneyIn[player] += bet
        else:
            self._playerToTotalMoneyIn[player] = bet
        
    # why is money returned? -> when someone has less money than the others and e.g. everyone goes all in and they win, they dont get everything
    # those who all-ined more money will get their money back if they lose, otherwise you could win with £1!
    def moneyReturnsDict(self, activePlayers, winner): # returns a dictionary of those who need money given back to them if they lose.
        winnerMoneyIn = self._playerToTotalMoneyIn.get(winner, 0) # robustness with the .get()
        moneyReturns = {}

        for player in activePlayers: # must go over the active players only, not everyone.
            if player != winner and player in self._playerToTotalMoneyIn: # do not give the winner a return for money
                playerMoneyIn = self._playerToTotalMoneyIn.get(player, 0) # get for safety.
                moneyReturned = playerMoneyIn - winnerMoneyIn 
                
                if moneyReturned < 0: # if you inputted less or the same as the winner
                    moneyReturned = 0 # ZERO bucks given back

                moneyReturns[player] = moneyReturned
        
        return moneyReturns

    # gives everyone their money back if they need to be given moeny back
    def distributeMoney(self, activePlayers, winner):
        moneyReturns = self.moneyReturnsDict(activePlayers, winner)
        if winner._isAllIn: # money is returned *ONLY IN THE CASE OF THE WINNER GOING ALL IN* 
            for player, moneyBack in moneyReturns.items():
                player._bank += moneyBack
                self._pot -= moneyBack # the returned money is taken from the pot, so when the pot is given to winner is correct amount

    # if players are broke, remove them from the game, they have lost
    def getNoMoneyPlayers(self, players):
        playersToRemove = []
        for player in players:
            if player._bank <= 0:
                playersToRemove.append(player)
            
        return playersToRemove

    # the money the blinds put in, accounts for all in scenario too.
    def takeBlindMoney(self, blind, smallBlind, bigBlind):
        if blind == smallBlind:
            bet = self._smallBlindBet
            self._raiseDebts[blind] = self._bigBlindBet - self._smallBlindBet # money has been inputted so must account for it if someone raises

        elif blind == bigBlind:
            bet = self._bigBlindBet
            self._raiseDebts[blind] = 0 # money has been inputted so must account for it if someone raises

        debtPaid = blind._bank if self.betGreaterThanBank(bet, blind._bank) else bet
        self.processBet(blind, debtPaid)

class Card:
    def __init__(self, value, suit, loadImage=True):
        self._value = value
        self._suit = suit
        self._path = f"assets/cards/{self.getName()}.png"
        self._width = cardWidth
        self._height = cardHeight
        self._x = self._y = None
        if loadImage:
            path = f"assets/cards/{self.getName()}.png"
            self._image = pygame.transform.scale(pygame.image.load(path), (cardWidth, cardHeight))
        else:
            self._image = None

    # returns the name of the card in the convention of the card images
    def getName(self):
        return f"{self._value}_of_{self._suit}"
    
    def getIntValue(self):
        faceCardToNum = {"jack": 11, "queen": 12, "king": 13, "ace": 14} # ace is the greatest value, can also be 1
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
        self._isAllIn = False
        self._isHuman = True
        self._bank = 0

    def fold(self):
        self._isFolded = True

    def check(self): # skips player turn, if previous turn was check or nothing
        pass # literally it does this, nothing
        # since the current player index is incremented elsewhere i wont do it here

    def giveCard(self, card):
        self._hand.append(card) # append Card object to hand attribute
    
    def addToGame(self, playerList):
        playerList.append(self)
    
    # all methods here are inherited and rewritten by the AI for their functionality.
    def raisePot(self):
        pass

    def call(self):
        pass

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
        self._raiseAmount = 0
    
    def doAction(self):
        # store previous action name to bias future decisions (prevents stupid) -> reduces repetition
        self._previousActionName = self._actionName
        if self._actionName == "raise":
            return self._action(self._raiseAmount)
        
        return self._action()
    
    def raisePot(self, amount):
        self._raiseAmount = amount

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
                self._raiseAmount = self.raiseQuant(toCall, raiseMin)
                print("RAISE", self._raiseAmount)
                # TODO: prototype 3 implement all in 
                return
            
            # raise decisions -> the threshold for a raise will depend on how strong the hand is percieved to be
            if handStrength == "very strong":
                if self._aggressiveness > 0.35: # more likely to raise on a "very strong" hand
                    self._action = self.raisePot
                    self._actionName = "raise"
                    self._raiseAmount = self.raiseQuant(toCall, raiseMin)
                    print("RAISE", self._raiseAmount)
                    return

            elif handStrength == "strong":
                if self._aggressiveness > 0.55: # less likely to raise on a "strong" hand
                    self._action = self.raisePot
                    self._actionName = "raise"
                    self._raiseAmount = self.raiseQuant(toCall, raiseMin)
                    print("RAISE", self._raiseAmount)
                    return
            
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
                self._raiseAmount = self.raiseQuant(toCall, raiseMin)
                print("RAISE", self._raiseAmount)
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
                self._raiseAmount = self.raiseQuant(toCall, raiseMin)
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
    
    # determine the amount to raise to.
    def raiseQuant(self, callValue, minRaise):
        roll = random.random() * 5 # randomness for how much to raise by
        self._raiseAmount = callValue * (self._aggressiveness + self._confidence + roll) # calculate based off previous attributes and random roll
        if self._raiseAmount < minRaise: # but if you so happen to raise by a small amount (low confidence and low aggression)
            self._raiseAmount = minRaise # validate to the min amount.

        return int(self.normaliseRaise(self._raiseAmount, minRaise))

    # make sure raise is within the boundaries of the player's bank and minimum raise. 
    def normaliseRaise(self, raiseAmount, minRaise):
        if raiseAmount > self._bank or minRaise > self._bank:
            self._raiseAmount = self._bank # if you raise more than your bank, set raise to be your bank instead

        return self._raiseAmount

class Button(pygame.Rect): # uses the pre-made Rect class from pygame library
    def __init__(self, x, y, width, height, action, text, colour):
        super().__init__(x, y, width, height)
        self._action = action
        self._text = fontConsolas.render(text, True, BLACK)
        self._colour = colour
        self._hoverColour = HOVER_GREY
        self._active = True # TODO: decide what to do with this in prototype 3: for the all-in feature, separate button or inactive/active buttons.

    def renderButtonText(self):
        textRect = self._text.get_rect(center=self.center) # center text in the button rectangle
        screen.blit(self._text, textRect) 

    def drawButton(self):
        if self._active:
            # draw the button a darker shade to show that you are hovering over it.
            if self.isHoveringOverButton():
                # hover colour is a greyish colour
                pygame.draw.rect(screen, self._hoverColour, self) # draw rectangle of button first

            else:
                pygame.draw.rect(screen, self._colour, self) # regular white colour

            self.renderButtonText() # then do the button text so that it shows ontop
    
    def isHoveringOverButton(self):
        return self.collidepoint(pygame.mouse.get_pos())

    def wasClicked(self):
        if self.collidepoint(pygame.mouse.get_pos()) and self._active:
            # if the player clicks this button then hadouken! do the button's action
            return True # signifies yes (True) this button has been pressed
        
        else:
            return False # signifies no (False) if the button was not pressed
    
    def runAction(self):
        return self._action()


class TextField(pygame.Rect):
    def __init__(self, x, y, width, height, placeholder=""): # default no placeholder
        super().__init__(x, y, width, height)
        self._active = False # not active on default.
        self._text = ""
        self._colour = WHITE
        self._placeholder = placeholder
        self._showError = False

    # draws the key presses (num or letter) than you input
    def drawTextInput(self):
        if self._active:
            pygame.draw.rect(screen, self._colour, self) # draw box first.

            if self._text: # if there is text you have entered
                screen.blit(moneyFont.render(self._text, True, BLACK), (self.x + 5, self.y + 5)) 

            elif not self._text: # draw place holder instead if there is no text inputted
                screen.blit(moneyFont.render(str(self._placeholder), True, PLACEHOLDER_GREY), (self.x + 5, self.y + 5)) 
                    
    def handleEvents(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            # clicking on the text field makes it active, so any keyboard press when its active will start typing.
            if self.collidepoint(pygame.mouse.get_pos()):
                self._active = True

            else:
                self._active = False # stop taking characters to add to text.
                self._text = "" # reset the field.

        if event.type == pygame.KEYDOWN and self._active:
            if event.key == pygame.K_BACKSPACE: # handle deleting
                self._text = self._text[:-1] # slice up to last num, so last num is removed

            elif event.key == pygame.K_RETURN:
                return self._text # send text through on enter

            else:
                self._text += event.unicode # unicode normalises your input.

        return False

    def getWrongResponse(self, aboveBox, errorMessage):
        messageX = self.x # positioning
        errorMessage = infoFont.render(errorMessage, True, SCARY_RED)
        errorMessageRect = errorMessage.get_rect()

        if aboveBox: # draw the error above the box
            messageY = self.y - errorMessageRect.height

        else: # below box
            messageY = self.y + self.height + errorMessageRect.height
        
        return (errorMessage, (messageX, messageY)) # tuple of coords included.
    
    def setDrawError(self, expression):
        self._showError = expression # control when the error is drawn.
        
    def resetInput(self):
        self._text = ""
    
    def changePlaceholderText(self, value):
        self._placeholder = str(value) # in raise field the placeholder changes to the min raise.


class ButtonManager:
    def __init__(self, buttons):
        self._buttons = buttons # buttons is a dict(buttonName:buttonObject)

    # check if any button on screen was clicked, returns True if so, False if not.
    def buttonWasClicked(self):
        for button in self._buttons.values(): # loops over dict() keys
            if button.wasClicked():
                return True
            
        return False # must always return something

    def executeNamedButton(self, buttonName):
        # run a specific button from the button list
        self._buttons[buttonName].runAction()

    # returns the name of button that was pressed
    # it is used to process the action so i know what button human actually presses
    def getActionName(self):
        if self.buttonWasClicked():
            for buttonName, button in self._buttons.items(): # loops over dict() k-v pairs
                if button.wasClicked():
                    return buttonName
                
        return False # must always return something

    def drawAllButtons(self, isHumanTurn):
        if isHumanTurn: # only draw the buttons if its the humans turn for added turn clarity.
            for buttonName in self._buttons:
                self._buttons[buttonName].drawButton() # accesses the the Button() object value in the dict

    def getButtonObject(self, name):
        for buttonName in self._buttons.keys(): # loops over dict() keys
            if buttonName == name:
                return self._buttons[buttonName]
            

screenManager = ScreenManager()
startScreen = StartScreen(StartScreen.runScreen, screenManager)
gameScreen = GameScreen(GameController().gameLoop)
screenManager.addScreen(startScreen)
screenManager.addScreen(gameScreen)

screenManager.loadCurrentScreen()