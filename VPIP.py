class HeroVPIPCalculator:
    def __init__(self, hero_name, hands_data):
        """
        :param hero_name: str, name of the hero (e.g., 'CFA level 1')
        :param hands_data: list, list of hand dictionaries
        """
        self.hero_name = hero_name
        self.hands_data = hands_data
        self.total_hands = 0
        self.vpip_hands = 0

    def normalize_name(self, name):
        """Removes excess formatting and quotes around player names."""
        return name.strip().replace('"', '').split(" @ ")[0]

    def parse_hand(self, hand):
        hero = hand.get('hero', {})
        hero_name_in_hand = self.normalize_name(hero.get('name', ''))
        
        if hero_name_in_hand != self.hero_name:
            return  # This hand doesn't involve the specified hero

        self.total_hands += 1

        preflop_actions = hand.get('actions', {}).get('preflop', [])
        
        for action in preflop_actions:
            player_name = self.normalize_name(action.get('player', ''))
            if player_name == self.hero_name and action.get('action') in ['calls', 'raises']:
                self.vpip_hands += 1
                break  # Only count once per hand

    def calculate_vpip(self):
        if self.total_hands == 0:
            return 0.0
        return (self.vpip_hands / self.total_hands) * 100

    def process(self):
        for hand in self.hands_data:
            self.parse_hand(hand)
        return round(self.calculate_vpip(), 2)
