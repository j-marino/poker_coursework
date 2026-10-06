class Banker:
    def __init__(self):
        self.pot = 0
        self.small_blind_bet = 10   # initial small blind, increases as rounds progress
        self.big_blind_bet = self.small_blind_bet * 2
        self.previous_bet = self.small_blind_bet
        self.current_bet = self.big_blind_bet

        # min raise = the size of the last raise added to the most recent bet
        self.min_raise = (self.current_bet - self.previous_bet) + self.current_bet
        self.call_value = self.big_blind_bet
        self.last_raise = 0

        self.current_round_bets = {}     # player -> money put in this betting round
        self.raise_debts = {}           # player -> money still owed after a raise
        self.player_to_total_money_in = {}  # player -> money put in this hand

    #
    # Starting money and betting
    #
    def give_all_starting_money(self, players, initial_bank):
        for player in players:
            player.bank = initial_bank

    def process_bet(self, player, amount):
        # Shared by calls, raises and blinds: move money from a player to the pot.
        player.bank -= amount
        self.pot += amount
        self.add_to_current_round_bets(player, amount)
        self.add_to_bet_total(player, amount)

    def handle_call(self, player):
        if self.player_has_debt(player):
            # After a raise every active player owes a "debt" to stay in the hand.
            debt_to_pay = self.raise_debts[player]
            # If they can't afford it, the rest of their bank is taken instead.
            debt_paid = player.bank if self.bet_greater_than_bank(debt_to_pay, player.bank) else debt_to_pay
            self.process_bet(player, debt_paid)
        else:
            money_in = player.bank if player.bank < self.call_value else self.call_value
            self.raise_debts[player] -= money_in  # goes negative so they never overpay later
            self.process_bet(player, money_in)

    def set_min_raise(self):
        self.min_raise = self.call_value + self.last_raise

    def handle_raise(self, player, raise_amount):
        self.previous_bet = self.current_bet
        self.current_bet = raise_amount if self.current_bet else self.call_value
        # raise_amount is what the player raises *to*, so the difference is the raise size
        self.last_raise = raise_amount - self.previous_bet
        self.process_bet(player, raise_amount)
        self.call_value = self.current_bet
        self.set_min_raise()
        self.raise_debts[player] -= raise_amount
        self.calculate_player_debts(player, raise_amount)

    def bet_greater_than_bank(self, bet, player_bank):
        # >= (not >) because this is also the all-in check, where bet == bank
        return bet >= player_bank

    #
    # Bookkeeping
    #
    def add_to_current_round_bets(self, player, bet):
        self.current_round_bets[player] = self.current_round_bets.get(player, 0) + bet

    def reset_current_round_bets(self):
        self.current_round_bets = {}

    def add_to_bet_total(self, player, bet):
        self.player_to_total_money_in[player] = self.player_to_total_money_in.get(player, 0) + bet

    def reset_total_money_in(self):
        self.player_to_total_money_in = {}

    def reset_debt_list(self, active_players):
        for player in active_players:
            self.raise_debts[player] = 0

    def calculate_player_debts(self, raiser, money_in):
        for player in self.raise_debts:
            if player != raiser:
                self.raise_debts[player] += money_in  # add, never assign: assigning is a major bug

    def remove_from_debts(self, player):
        self.raise_debts.pop(player, None)

    def player_has_debt(self, player):
        return self.raise_debts.get(player, 0) > 0

    #
    # End of a hand
    #
    def money_returns_dict(self, active_players, winner):
        # Money owed back to players who put in more than the winner could match.
        winner_money_in = self.player_to_total_money_in.get(winner, 0)
        money_returns = {}

        for player in active_players:
            if player != winner and player in self.player_to_total_money_in:
                money_returned = self.player_to_total_money_in[player] - winner_money_in
                money_returns[player] = max(money_returned, 0)

        return money_returns

    def distribute_money(self, active_players, winner):
        # If the winner was all in, others get back what they bet above the winner's stake.
        #
        # Without this a player could win the whole pot with only £1 in it.
        if winner.is_all_in:
            for player, money_back in self.money_returns_dict(active_players, winner).items():
                player.bank += money_back
                self.pot -= money_back

    def give_pot_to_winner(self, player):
        player.bank += self.pot
        self.pot = 0

    def get_no_money_players(self, players):
        return [player for player in players if player.bank <= 0]

    #
    # Blinds
    #
    def take_blind_money(self, blind, small_blind, big_blind):
        # Take a blind from a player; if they can't afford it they go all in.
        if blind == small_blind:
            bet = self.small_blind_bet
            self.raise_debts[blind] = self.big_blind_bet - self.small_blind_bet
        elif blind == big_blind:
            bet = self.big_blind_bet
            self.raise_debts[blind] = 0

        amount = blind.bank if self.bet_greater_than_bank(bet, blind.bank) else bet
        self.process_bet(blind, amount)

    def increase_blind_bet(self, rounds_passed):
        if rounds_passed % 3 == 0:
            self.small_blind_bet = int(self.small_blind_bet * 1.5)
        self.big_blind_bet = self.small_blind_bet * 2
        self.previous_bet = self.small_blind_bet  # history needed to calculate the min raise
        self.current_bet = self.big_blind_bet
        self.call_value = self.big_blind_bet
