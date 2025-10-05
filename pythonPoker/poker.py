import pygame
import random

class GameController:
    def __init__(self):
        self._communityCards = []
        self._deck = Deck()
        self._players = []
        self._dealer = Dealer(self._deck)

    def gameLoop(self):
        self._deck.createDeck()
        self._deck.shuffle()
        player1 = HumanPlayer("timmy")
        player2 = HumanPlayer("bobby")
        player1.addToGame(self._players)
        player2.addToGame(self._players)
        self._dealer.dealPlayerHands(self._players)
        self._dealer.dealflop(self._communityCards)
        for player in self._players:
            hand = player.getHand()
            for card in hand:
                print(card.getName())

        print("\ncommunity")
        for card in self._communityCards:
            print(card.getName())

class Dealer:
    def __init__(self, deck):
        self._deck = deck
    
    def dealflop(self, communityCards):
        for _ in range(0, 3):
            card = self._deck.removeCard()
            communityCards.append(card)

    def dealTurn(self):
        pass

    def dealRiver(self):
        pass
    
    def dealPlayerHands(self, playerList):
        for _ in range(0, 2):
            for player in playerList:
                player.giveCard(self._deck.removeCard())

class Card:
    def __init__(self, value, suit):
        self._value = value
        self._suit = suit

    def getName(self):
        return f"{self._value}_of_{self._suit}"


class Deck:
    def __init__(self):
        self._values = ["ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king"]
        self._suits = ["clubs", "diamonds", "hearts", "spades"]
        self._deck = []

    def createDeck(self):
        for value in self._values:
            for suit in self._suits:
                self._deck.append(Card(value, suit))

    def getDeck(self):
        return self._deck
    
    def shuffle(self):
        random.shuffle(self._deck)

    def removeCard(self):
        return self._deck.pop()


class Player():
    def __init__(self, name):
        self._name = name
        self._hand = []

    def fold(self):
        pass

    def check(self):
        pass

    def raiseBet(amount):
        pass

    def call(amount):
        pass

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

game = GameController()
game.gameLoop()