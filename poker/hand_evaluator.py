HAND_VALUES = {
    "royal flush": 10,
    "straight flush": 9,  # also covers a royal flush, which is just the best straight flush
    "four of a kind": 8,
    "full house": 7,
    "flush": 6,
    "straight": 5,
    "three of a kind": 4,
    "two pair": 3,
    "one pair": 2,
    "high card": 1,
}


def has_flush(cards):
    """True if 5 or more cards share a suit."""
    suit_count = {"clubs": 0, "hearts": 0, "spades": 0, "diamonds": 0}
    for card in cards:
        suit_count[card.suit] += 1
    return any(count >= 5 for count in suit_count.values())


def _has_consecutive_sequence(ordered_cards, is_low_ace, check_straight_flush):
    """Look for 5 consecutive values in an ordered list of cards.

    is_low_ace treats aces as 1. check_straight_flush additionally requires the
    straight's cards to share a suit.
    """
    # Starts at 1 because the first card is never counted by the "next is +1" check.
    count = 1
    for index in range(len(ordered_cards) - 1):
        current = ordered_cards[index].get_int_value()
        following = ordered_cards[index + 1].get_int_value()

        if ordered_cards[index].value == "ace" and is_low_ace:
            current = 1
        if ordered_cards[index + 1].value == "ace" and is_low_ace:
            following = 1

        if current + 1 == following:
            count += 1
            if count == 5:
                if not check_straight_flush:
                    return True
                # The 5 cards that make up the straight end at index + 1.
                return has_flush(ordered_cards[index - 3: index + 2])
        elif current == following:
            continue  # duplicated values don't break a sequence
        else:
            count = 1  # sequence broken: reset to 1 (not 0) for the same reason as above

    return False


def has_straight(cards, check_straight_flush):
    ascending = sorted(cards, key=lambda card: card.get_int_value())

    aces = [card for card in ascending if card.value == "ace"]
    if aces:
        # An ace is either high (14) or low (1), so try both orderings.
        low_ace_order = aces + [card for card in ascending if card.value != "ace"]
        return (_has_consecutive_sequence(ascending, False, check_straight_flush)
                or _has_consecutive_sequence(low_ace_order, True, check_straight_flush))

    return _has_consecutive_sequence(ascending, False, check_straight_flush)


def sum_value_count(cards):
    """Map each card value to how many times it appears, e.g. {"king": 2, "7": 1}."""
    value_count = {}
    for card in cards:
        value_count[card.value] = value_count.get(card.value, 0) + 1
    return value_count


def has_x_of_a_kind(cards, matching_value):
    """True if any value appears exactly matching_value times."""
    return matching_value in sum_value_count(cards).values()


def has_two_pair(cards):
    return list(sum_value_count(cards).values()).count(2) == 2


def evaluate_hand(cards):
    """Return the name of the best hand the cards make, e.g. 'full house'."""
    if has_straight(cards, check_straight_flush=True):
        return "straight flush"
    if has_x_of_a_kind(cards, 4):
        return "four of a kind"
    if has_x_of_a_kind(cards, 3) and has_x_of_a_kind(cards, 2):
        return "full house"
    if has_flush(cards):
        return "flush"
    if has_straight(cards, check_straight_flush=False):
        return "straight"
    if has_x_of_a_kind(cards, 3):
        return "three of a kind"
    if has_two_pair(cards):
        return "two pair"
    if has_x_of_a_kind(cards, 2):
        return "one pair"
    return "high card"
