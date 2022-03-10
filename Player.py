import json

import treys

from flask_socketio import join_room


class Player:
    def __init__(self, name, socketio=None, sid=None):
        self.name = name
        self.cpu = False
        self.money = 0
        self.cards = []
        self.sid = sid
        self.folded = False
        self.hand_value = -1
        self.bet_pot = 0
        self.checked = False
        self.all_in = False
        self.socketio = socketio
        self.ai = None
        self.index = None

        if self.sid is not None:
            join_room(self.sid)

    def get_dict(self):
        player_dict = {
            'name': self.name,
            'cpu': self.cpu,
            'money': self.money,
            'sid': self.sid,
            'folded': self.folded,
            'bet_pot': self.bet_pot,
            'checked': self.checked,
            'all_in': self.all_in
        }
        return player_dict

    def to_json(self):
        json_data = self.get_dict()
        return json.dumps(json_data)

    def send_index(self, index):
        data = {'player_index': index}
        self.socketio.emit('my_index', json.dumps(data), to=self.sid)

    def new_deal(self):
        self.folded = False
        self.all_in = False
        self.cards = []
        self.hand_value = -1
        self.new_bet()

    def new_bet(self):
        self.checked = self.all_in or self.folded
        self.bet_pot = 0

    def send_cards(self):
        data = {
            'my_cards': [treys.Card.int_to_pretty_str(card)[1:3] for card in self.cards]
        }
        self.socketio.emit('my_cards', json.dumps(data), to=self.sid)

    def bet(self, value):
        diff = value - self.bet_pot

        if diff >= self.money:
            return self.play_all_in()

        self.money -= diff
        self.bet_pot += diff

    def play_all_in(self):
        self.bet_pot += self.money
        self.money = 0
        self.all_in = True
        return self.bet_pot

    def get_cards_str(self):
        return [treys.Card.int_to_pretty_str(card)[1:3] for card in self.cards]

    def make_cpu_move(self, game):
        if self.ai:
            self.ai.make_move(game, self)
