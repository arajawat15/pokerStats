class HeroFlushDrawCalculator:
    def __init__(self, hero_name, hands_data):
        self.hero_name = hero_name
        self.hands_data = hands_data
        self.total_suited_hands = 0
        self.flush_draw_flops = 0

    def normalize_name(self, name):
        return name.strip().replace('"', '').split(" @ ")[0]

    def get_suit(self, card):
        return card[-1] if card and len(card) > 1 else None

    def parse_hand(self, hand):
        hero = hand.get('hero', {})
        hero_name_in_hand = self.normalize_name(hero.get('name', ''))

        if hero_name_in_hand != self.hero_name:
            return

        hole_cards = hero.get('hole_cards')
        flop_data = hand.get('actions', {}).get('flop')

        if not hole_cards or not flop_data or not isinstance(flop_data, dict):
            return

        suit1 = self.get_suit(hole_cards[0])
        suit2 = self.get_suit(hole_cards[1])

        if not suit1 or not suit2 or suit1 != suit2:
            return  # Not a suited hand

        self.total_suited_hands += 1

        flop_board = flop_data.get('board', [])
        flop_suits = [self.get_suit(card) for card in flop_board]

        same_suit_count = flop_suits.count(suit1)
        if same_suit_count >= 2:
            self.flush_draw_flops += 1

    def calculate_flush_draw_percent(self):
        if self.total_suited_hands == 0:
            return 0.0
        return (self.flush_draw_flops / self.total_suited_hands) * 100

    def process(self):
        for hand in self.hands_data:
            self.parse_hand(hand)
        return round(self.calculate_flush_draw_percent(), 2)
