import itertools
import json
import random
import threading
import time

import treys
import uuid

from Player import Player


class Game:
    MAX_BET_RAISES = 3

    STAGE_PREFLOP = 0
    STAGE_FLOP = 1
    STAGE_TURN = 2
    STAGE_RIVER = 3

    def __init__(self, name, entry_fee, big_blind, socketio):
        self.name = name
        self.id = str(uuid.uuid4())
        self.entry_fee = entry_fee
        self.big_blind = big_blind
        self.small_blind = big_blind // 2
        self.players = []
        self.socketio = socketio
        self.local = False
        self.started = False
        self.deal_started = False

        self.stage = self.STAGE_PREFLOP
        self.deal_pot = 0
        self.raise_counter = 0
        self.call_value = self.big_blind
        self.min_raise_value = 2 * self.call_value

        self.dealer_player_index = -2
        self.small_blind_player_index = -1
        self.big_blind_player_index = 0
        self.next_player_index = 1
        self.last_raiser_index = 0

        self.deck = treys.Deck()
        self.community_cards = []

        self.evaluator = treys.Evaluator()

    def get_dict(self):
        game_dict = {
            'name': self.name,
            'id': self.id,
            'entry_fee': self.entry_fee,
            'big_blind': self.big_blind,
            'small_blind': self.small_blind,
            'players': [player.get_dict() for player in self.players],
            'local': self.local,
            'stage': self.stage,
            'deal_pot': self.deal_pot,
            'raise_counter': self.raise_counter,
            'call_value': self.call_value,
            'min_raise_value': self.min_raise_value,
            'small_blind_player_index': self.small_blind_player_index,
            'big_blind_player_index': self.big_blind_player_index,
            'next_player_index': self.next_player_index,
            'last_raiser_index': self.last_raiser_index,
            'community_cards': [treys.Card.int_to_pretty_str(x)[1:3] for x in self.community_cards]
        }

        return game_dict

    def to_json(self):
        json_data = self.get_dict()
        return json.dumps(json_data)

    def add_player(self, player):
        if self.started:
            return

        player.money = self.entry_fee
        self.players.append(player)

    def shuffle_players(self):
        random.shuffle(self.players)

        self.reposition_player()

    def play(self):
        self.started = True
        self.shuffle_players()
        self.send_index()
        self.new_deal()

    def send_index(self):
        raise NotImplementedError

    def move_blinds_ahead(self):
        self.small_blind_player_index = self.small_blind_player_index + 1 if self.small_blind_player_index + 1 < len(self.players) else 0

        self.big_blind_player_index = self.small_blind_player_index + 1 if self.small_blind_player_index + 1 < len(self.players) else 0

        if len(self.players) > 2:
            self.dealer_player_index = self.small_blind_player_index - 1 if self.small_blind_player_index - 1 >= 0 else len(self.players) - 1
        else:
            self.dealer_player_index = self.small_blind_player_index

    def next_player(self, new_bet=False, everybody_all_in=False):
        # TODO: analyze all possibilities
        if everybody_all_in:
            return

        if new_bet:
            self.next_player_index = self.small_blind_player_index
        else:
            self.next_player_index = self.next_player_index + 1 if self.next_player_index + 1 < len(self.players) else 0

            if (self.next_player_index == self.last_raiser_index) and self.players[self.next_player_index].all_in:
                self.next_stage()
                return

            if (self.next_player_index == self.last_raiser_index) and (self.raise_counter == self.MAX_BET_RAISES):
                self.next_stage()
                return

        while self.players[self.next_player_index].folded or self.players[self.next_player_index].all_in:
            self.next_player_index = self.next_player_index + 1 if self.next_player_index + 1 < len(self.players) else 0

        self.send_next_player()

    def send_next_player(self):
        must_all_in = (self.call_value >= (self.players[self.next_player_index].money +
                                           self.players[self.next_player_index].bet_pot))

        json_data = {
            'next_player': self.next_player_index,
            'players': [
                p.get_dict() for p in self.players
            ],
            'call_value': self.call_value,
            'min_raise_value': self.min_raise_value,
            'must_all_in': must_all_in,
            'can_raise': (self.raise_counter < self.MAX_BET_RAISES) and not must_all_in,
            'can_check': (self.call_value == self.players[self.next_player_index].bet_pot)
        }

        json_str = json.dumps(json_data)

        self.socketio.emit('next_player', json_str, to=self.id)

    def new_deal(self):
        for p in self.players:
            p.new_deal()

        self.stage = self.STAGE_PREFLOP
        self.deal_pot = 0
        self.raise_counter = 0
        self.call_value = self.big_blind
        self.min_raise_value = 2 * self.call_value

        self.move_blinds_ahead()
        self.last_raiser_index = self.big_blind_player_index
        self.next_player_index = self.big_blind_player_index

        self.send_new_deal()

        self.players[self.small_blind_player_index].bet(self.small_blind)
        self.players[self.big_blind_player_index].bet(self.big_blind)

        self.community_cards = []

        self.deck = treys.Deck()
        self.deck.shuffle()

        for i in range(2):
            for p in itertools.chain(self.players[self.small_blind_player_index:],
                                     self.players[:self.small_blind_player_index]):
                p.cards.append(self.deck.draw())

        self.send_cards()
        self.deal_started = True
        self.next_player()

    def send_new_deal(self):
        json_data = {
            'small_blind': self.small_blind,
            'big_blind': self.big_blind,
            'dealer_player_index': self.dealer_player_index,
            'small_blind_player_index': self.small_blind_player_index,
            'big_blind_player_index': self.big_blind_player_index,
            'players': [p.get_dict() for p in self.players]
        }

        json_str = json.dumps(json_data)
        self.socketio.emit('new_deal', json_str, to=self.id)

    def send_cards(self):
        raise NotImplementedError

    def next_stage(self, everybody_all_in=False):
        if everybody_all_in:
            time.sleep(2)

        if self.stage == self.STAGE_PREFLOP:
            self.flop(everybody_all_in)
        elif self.stage == self.STAGE_FLOP:
            self.turn(everybody_all_in)
        elif self.stage == self.STAGE_TURN:
            self.river(everybody_all_in)
        elif self.stage == self.STAGE_RIVER:
            self.deal_started = False
            self.check_winner()
            return

        if self.everybody_all_in():
            self.next_stage(True)

    def flop_turn_river(self, everybody_all_in=False):
        for p in self.players:
            self.deal_pot += p.bet_pot
            p.new_bet()

        self.raise_counter = 0
        self.call_value = 0
        self.min_raise_value = self.big_blind
        self.last_raiser_index = -1

        self.next_player(True, everybody_all_in)

    def flop(self, everybody_all_in=False):
        self.stage = self.STAGE_FLOP

        self.flop_turn_river(everybody_all_in)

        self.community_cards.append(self.deck.draw())
        self.community_cards.append(self.deck.draw())
        self.community_cards.append(self.deck.draw())
        self.send_flop()

    def send_flop(self):
        json_data = {
            'cards': [treys.Card.int_to_pretty_str(x)[1:3] for x in self.community_cards],
            'deal_pot': self.deal_pot,
            'players': [p.get_dict() for p in self.players]
        }

        json_str = json.dumps(json_data)

        self.socketio.emit('flop', json_str, to=self.id)

    def turn(self, everybody_all_in=False):
        self.stage = self.STAGE_TURN

        self.flop_turn_river(everybody_all_in)

        self.community_cards.append(self.deck.draw())
        self.send_turn()

    def send_turn(self):
        json_data = {
            'card': treys.Card.int_to_pretty_str(self.community_cards[3])[1:3],
            'deal_pot': self.deal_pot,
            'players': [p.get_dict() for p in self.players]
        }

        json_str = json.dumps(json_data)

        self.socketio.emit('turn', json_str, to=self.id)

    def river(self, everybody_all_in=False):
        self.stage = self.STAGE_RIVER

        self.flop_turn_river(everybody_all_in)

        self.community_cards.append(self.deck.draw())
        self.send_river()

    def send_river(self):
        json_data = {
            'card': treys.Card.int_to_pretty_str(self.community_cards[4])[1:3],
            'deal_pot': self.deal_pot,
            'players': [p.get_dict() for p in self.players]
        }

        json_str = json.dumps(json_data)

        self.socketio.emit('river', json_str, to=self.id)

    def send_last_move(self, data):
        data_str = json.dumps(data)
        self.socketio.emit('command', data_str, to=self.id)

    def bust_players(self):
        busted_players = {}
        for i in range(len(self.players)):
            if self.players[i].all_in:
                busted_players[i] = self.players[i].get_dict()

        json_data = {
            'busted_players': busted_players
        }

        self.send_busted_info(json_data)

        if len(busted_players) > 0:
            self.players = [player for player in self.players if not player.all_in]
            self.reposition_player()

    def send_busted_info(self, data):
        self.socketio.emit('busted_info', json.dumps(data), to=self.id)

    def check_winner(self, win_by_fold=False):
        for p in self.players:
            self.deal_pot += p.bet_pot
            p.bet_pot = 0

        winning_players = []

        if win_by_fold:
            winning_players = [p for p in self.players if not p.folded]
        else:
            for p in self.players:
                if not p.folded:
                    p.hand_value = self.evaluator.evaluate(p.cards, self.community_cards)

            for p in self.players:
                if p.folded:
                    continue

                if not winning_players:
                    winning_players.append(p)
                else:
                    if p.hand_value == winning_players[0].hand_value:
                        winning_players.append(p)
                    elif p.hand_value < winning_players[0].hand_value:
                        winning_players = [p]

        if self.deal_pot % len(winning_players) != 0:
            to_pay = self.deal_pot // len(winning_players)
            change = self.deal_pot - to_pay * len(winning_players)

            if len(self.players) == 2:
                self.players[self.big_blind_player_index].money += change
            else:
                for p in itertools.chain(self.players[self.small_blind_player_index:],
                                         self.players[:self.small_blind_player_index]):
                    if p in winning_players:
                        p.money += change

        for p in winning_players:
            p.money += self.deal_pot // len(winning_players)
            p.all_in = False

        figure = self.evaluator.get_rank_class(winning_players[0].hand_value) if not win_by_fold else 10

        json_data = {
            'winning_players': [p.name for p in winning_players],
            'winning_value': (self.deal_pot // len(winning_players)),
            'figure': figure
        }
        self.send_end(json_data)

        self.bust_players()

        if self.finished():
            winner = self.get_table_winner()
            json_data = {
                'winner': winner.name
            }
            self.send_finish(json_data)
            return

        timer = threading.Timer(5.0, self.new_deal)
        timer.start()

    def reposition_player(self):
        self.players = [player for player in self.players if not player.all_in]

        for i in range(len(self.players)):
            self.players[i].index = i

        self.send_index()

    def finished(self):
        return len(self.players) == 1

    def get_table_winner(self):
        if len(self.players) == 1:
            return self.players[0]

    def send_end(self, data):
        json_str = json.dumps(data)
        self.socketio.emit('deal_end', json_str, to=self.id)

    def everybody_all_in(self):
        playing_players = 0

        for p in self.players:
            if (not p.folded) and (not p.all_in):
                playing_players += 1

        return playing_players <= 1

    def everybody_checked(self):
        for p in self.players:
            if not p.checked:
                return False

        return True

    def count_not_folded_players(self):
        counter = 0

        for p in self.players:
            counter = counter + 1 if not p.folded else counter

        return counter

    def send_finish(self, data):
        json_str = json.dumps(data)
        self.socketio.emit('table_finish', json_str, to=self.id)

    def call(self, player_index):
        if not self.deal_started:
            return
        if player_index is not self.next_player_index:
            return

        if self.call_value == self.players[player_index].bet_pot:
            json_data = {
                'player_name': self.players[player_index].name,
                'move_type': 'check'
            }
            self.send_last_move(json_data)

            if player_index == self.last_raiser_index:
                self.next_stage()
                return

            self.players[player_index].checked = True

            if self.everybody_checked():
                self.next_stage()
            else:
                self.next_player()
        else:
            real_call_value = self.players[player_index].bet(self.call_value)

            move_type = 'call'

            if real_call_value is not None:
                move_type = 'call_all_in'

            json_data = {
                'player_name': self.players[player_index].name,
                'move_type': move_type,
                'call_value': self.call_value if real_call_value is None else real_call_value
            }
            self.send_last_move(json_data)

            if self.everybody_all_in():
                self.next_stage(True)
            else:
                self.next_player()

    def fold(self, player_index):
        if not self.deal_started:
            return
        if player_index is not self.next_player_index:
            return

        json_data = {
            'player_name': self.players[player_index].name,
            'move_type': 'fold'
        }
        self.send_last_move(json_data)

        self.players[player_index].folded = True
        self.players[player_index].checked = True

        if self.count_not_folded_players() == 1:
            self.check_winner(True)
            return

        if player_index == self.last_raiser_index:
            self.next_stage(self.everybody_all_in())
        else:
            self.next_player()

    def all_in(self, player_index):
        self.raise_(player_index, self.players[player_index].money + self.players[player_index].bet_pot, True)

    def raise_(self, player_index, value, all_in=False):
        if not self.deal_started:
            return
        if player_index is not self.next_player_index:
            return
        if not (self.raise_counter < self.MAX_BET_RAISES):
            return
        if (not all_in) and (self.players[player_index].money + self.players[player_index].bet_pot) < value:
            return

        json_data = {
            'player_name': self.players[player_index].name,
            'move_type': ('raise' if not all_in else 'all_in'),
            'raise_value': value
        }
        self.send_last_move(json_data)

        self.raise_counter += 1
        self.players[player_index].bet(value)
        self.call_value = value
        self.min_raise_value = self.call_value * 2

        if self.raise_counter == 3:
            self.players[player_index].checked = True

        self.last_raiser_index = player_index
        self.next_player()
