import random

from Game import Game


class AI:
    AI_TYPE_CAREFULLY = 0
    AI_TYPE_NORMAL = 1
    AI_TYPE_AGGRESSIVE = 2

    def __init__(self, ai_type, evaluator):
        self.evaluator = evaluator
        self.ai_type = ai_type if ai_type < 3 else random.randint(AI.AI_TYPE_CAREFULLY, AI.AI_TYPE_AGGRESSIVE)
        self.must_all_in = False
        self.can_raise = True
        self.can_check = True
        self.hand_value = -1

    def make_move(self, game, player):
        self.must_all_in = (game.call_value >= (player.money + player.bet_pot))
        self.can_raise = (game.raise_counter < Game.MAX_BET_RAISES) and not self.must_all_in
        self.can_check = (game.call_value == player.bet_pot)
        self.hand_value = None if game.stage == Game.STAGE_PREFLOP else self.evaluator.evaluate(player.cards, game.community_cards)

        if self.ai_type == AI.AI_TYPE_CAREFULLY:
            self.make_move_carefully(game, player)
        elif self.ai_type == AI.AI_TYPE_NORMAL:
            self.make_move_normal(game, player)
        elif self.ai_type == AI.AI_TYPE_AGGRESSIVE:
            self.make_move_aggressive(game, player)

    def make_move_carefully(self, game, player):
        if self.can_check:
            game.call(player.index)
        elif self.must_all_in:
            game.fold(player.index)
        else:
            if game.call_value < player.money // 4:
                game.call(player.index)
            else:
                game.fold(player.index)

    def make_move_normal(self, game, player):
        if self.must_all_in:
            game.fold(player.index)
        elif self.can_check and self.can_raise:
            game.raise_(player.index, game.min_raise_value)
        else:
            game.call(player.index)

    def make_move_aggressive(self, game, player):
        if self.must_all_in:
            game.call(player.index)
        elif self.can_raise:
            game.raise_(player.index, game.min_raise_value)
        else:
            game.call(player.index)
