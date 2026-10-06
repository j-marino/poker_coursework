import random

from poker.cards import SUITS, VALUES, Card
from poker.hand_evaluator import HAND_VALUES, evaluate_hand

# The raw win rate from the simulation is too high for the thresholds below.
# Scaling it makes an average looking hand (e.g. off-suit face card + a middling
# card) land around 0.5.
WINRATE_SCALE = 0.72

# (lower bound inclusive, upper bound exclusive) -> hand strength
HAND_STRENGTH_RANGES = {
    (0.0, 0.42): "very weak",
    (0.42, 0.48): "weak",
    (0.48, 0.55): "average",
    (0.55, 0.68): "strong",
    (0.68, 1.01): "very strong",
}


class Player:
    # The human player. The AI subclass overrides the actions it needs.

    def __init__(self):
        self.hand = []
        self.evaluated_hand = ""
        self.is_folded = False
        self.is_all_in = False
        self.is_human = True
        self.bank = 0
        self.seat = None  # screen seat, only used by AI players

    def give_card(self, card):
        self.hand.append(card)

    def add_to_game(self, player_list):
        player_list.append(self)

    # Actions. The game controller moves the money and advances the turn, so for
    # the human these only need to exist (the buttons call them).
    def fold(self):
        self.is_folded = True

    def check(self):
        pass

    def call(self):
        pass

    def raise_pot(self):
        pass


class AIPlayer(Player):
    def __init__(self, name="monte", seat=None):
        super().__init__()
        self.name = name
        self.seat = seat
        self.is_human = False
        self.action = self.check  # the method to run for this turn
        self.action_name = ""
        self.raise_amount = 0
        self.recalculate_attributes()

    #
    # Personality
    #
    def recalculate_attributes(self):
        # Re-roll the personality every turn so the AI doesn't become predictable.
        self.bluff_constant = random.uniform(0.1, 0.3)  # how likely it is to bluff
        self.aggressiveness = random.uniform(0.1, 0.6)  # affects raising and calling
        self.confidence = random.uniform(0.4, 0.7)      # threshold for acting without bluffing

    #
    # Acting
    #
    def do_action(self):
        if self.action_name == "raise":
            return self.action(self.raise_amount)
        return self.action()

    def raise_pot(self, amount):
        self.raise_amount = amount

    def get_action_name(self):
        return self.action_name

    def _set_action(self, action_name):
        actions = {"raise": self.raise_pot, "call": self.call, "check": self.check, "fold": self.fold}
        self.action = actions[action_name]
        self.action_name = action_name

    def _set_raise(self, to_call, raise_min):
        self._set_action("raise")
        self.raise_amount = self.raise_quant(to_call, raise_min)

    #
    # Decision making
    #
    def monte_carlo_simulation(self, simulations, community_cards, can_check, to_call, raise_min):
        # Estimate the win rate against one random opponent, then pick an action.
        #
        # Each simulation deals the unknown community cards and a random opponent
        # hand from the cards this player can't see, then compares the best hands.
        # Ties count as wins.
        known = {card.get_name() for card in self.hand + community_cards}
        unseen_cards = [Card(value, suit) for value in VALUES for suit in SUITS
                       if f"{value}_of_{suit}" not in known]
        cards_needed = (5 - len(community_cards)) + 2  # + 2 for the opponent's hand

        wins = 0
        for _ in range(simulations):
            sampled = random.sample(unseen_cards, cards_needed)
            opponent_hand = sampled[:2]
            board = community_cards + sampled[2:]

            my_value = HAND_VALUES[evaluate_hand(board + self.hand)]
            opponent_value = HAND_VALUES[evaluate_hand(board + opponent_hand)]
            if my_value >= opponent_value:
                wins += 1

        self.attribute_math(wins, simulations, can_check, to_call, raise_min)

    def assign_hand_strength(self, winrate):
        for (lower, upper), strength in HAND_STRENGTH_RANGES.items():
            if lower <= winrate < upper:
                return strength

    def attribute_math(self, wins, simulations, can_check, to_call, raise_min):
        # Turn the simulated win rate into an action, shaped by the AI's personality.
        self.recalculate_attributes()

        winrate = (wins / simulations) * WINRATE_SCALE
        hand_strength = self.assign_hand_strength(winrate)

        if hand_strength in ("strong", "very strong"):
            self._play_strong_hand(hand_strength, winrate, can_check, to_call, raise_min)
        elif hand_strength == "average":
            self._play_average_hand(can_check, raise_min, to_call)
        elif hand_strength in ("weak", "very weak"):
            self._play_weak_hand(can_check, to_call, raise_min)

    def _play_strong_hand(self, hand_strength, winrate, can_check, to_call, raise_min):
        # There is deliberately no fold here: folding a strong hand just loses money.
        # A very strong hand with an aggressive and confident AI raises.
        if hand_strength == "very strong" and (self.aggressiveness + self.confidence) > winrate:
            self._set_raise(to_call, raise_min)
            return

        # Otherwise the raise threshold depends on how strong the hand is
        if hand_strength == "very strong" and self.aggressiveness > 0.35:
            self._set_raise(to_call, raise_min)
            return
        if hand_strength == "strong" and self.aggressiveness > 0.55:
            self._set_raise(to_call, raise_min)
            return

        if to_call > 0:
            self._set_action("call")
        elif can_check:
            self._set_action("check")

    def _play_average_hand(self, can_check, raise_min, to_call):
        roll = random.random()

        if self.aggressiveness > 0.50 and roll < 0.25:
            self._set_raise(to_call, raise_min)
        elif self.confidence > 0.45 and roll < 0.7:  # the most likely action
            self._set_action("call")
        elif can_check:  # never fold when you can check for free
            self._set_action("check")
        else:
            self._set_action("fold")

    def _play_weak_hand(self, can_check, to_call, raise_min):
        roll = random.random()

        if self.confidence < 0.3 and self.aggressiveness < 0.3:
            self._set_action("check" if can_check else "fold")
        elif roll < self.bluff_constant * self.aggressiveness:  # bluff (at most ~0.18)
            self._set_raise(to_call, raise_min)
        else:
            self._set_action("check" if can_check else "fold")

    def raise_quant(self, call_value, min_raise):
        # Amount to raise to, based on personality and a random roll, kept within limits.
        roll = random.random() * 5
        amount = call_value * (self.aggressiveness + self.confidence + roll)
        amount = max(amount, min_raise)
        if amount > self.bank or min_raise > self.bank:
            amount = self.bank  # can't raise more than the bank: go all in instead
        return int(amount)
