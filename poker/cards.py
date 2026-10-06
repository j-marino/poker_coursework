# Cards, the deck and the dealer. No pygame here, so this is easy to test.
import random

VALUES = ["ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king"]
SUITS = ["clubs", "diamonds", "hearts", "spades"]
FACE_CARD_VALUES = {"jack": 11, "queen": 12, "king": 13, "ace": 14}  # ace is high, or 1 in a low straight


class Card:
    def __init__(self, value, suit):
        self.value = value  # e.g. "4" or "king"
        self.suit = suit    # e.g. "hearts"
        self.x = self.y = None  # screen position, set once the card is dealt

    def get_name(self):
        # Name matching the card image files, e.g. 'king_of_hearts'.
        return f"{self.value}_of_{self.suit}"

    def get_int_value(self):
        return FACE_CARD_VALUES.get(self.value) or int(self.value)

    def set_pos(self, x, y):
        self.x, self.y = x, y

    def has_pos(self):
        return self.x is not None and self.y is not None


def create_deck():
    # A fresh, ordered 52 card deck.
    return [Card(value, suit) for value in VALUES for suit in SUITS]


class Dealer:
    def __init__(self):
        self.deck = create_deck()
        self.dealer_button = None   # the Player holding the dealer button
        self.dealer_button_index = 0

    def deal_card(self):
        # pop() mimics taking the top card off the deck
        if not self.deck:
            raise RuntimeError("the deck is empty")
        return self.deck.pop()

    def shuffle(self):
        random.shuffle(self.deck)

    def recreate_deck(self):
        self.deck = create_deck()

    # Named after the stages of a hand of poker
    def deal_player_hands(self, players):
        for _ in range(2):  # one card at a time, twice round the table
            for player in players:
                player.give_card(self.deal_card())

    def deal_flop(self, community_cards):
        for _ in range(3):
            community_cards.append(self.deal_card())

    def deal_turn(self, community_cards):
        community_cards.append(self.deal_card())

    def deal_river(self, community_cards):
        community_cards.append(self.deal_card())

    def initial_dealer_button(self, players):
        picked_player = random.choice(players)
        self.dealer_button = picked_player
        self.dealer_button_index = players.index(picked_player)
