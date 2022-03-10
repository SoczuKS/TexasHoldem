import json
import threading

from AI import AI
from Game import Game
from Player import Player


class LocalGame(Game):
    def __init__(self, entry_fee, big_blind, number_of_cpu_players, human_player_names, cpu_player_types, socketio):
        super().__init__('Local Game', entry_fee, big_blind, socketio)

        self.local = True

        for i in range(number_of_cpu_players):
            cpu_player_name = "CPU " + str(i)
            player = Player(cpu_player_name)
            player.cpu = True
            player.ai = AI(int(cpu_player_types[i]), self.evaluator)
            super().add_player(player)

        for human_player_name in human_player_names:
            player = Player(human_player_name, self.socketio)
            super().add_player(player)

    def send_index(self):
        data = {
            'player_index': []
        }

        for i in range(len(self.players)):
            if not self.players[i].cpu:
                data['player_index'].append(i)

        self.socketio.emit('my_index', json.dumps(data), to=self.id)

    def send_cards(self):
        json_data = {
            'cards': {}
        }

        for i in range(len(self.players)):
            if self.players[i].cpu:
                continue

            json_data['cards'][i] = self.players[i].get_cards_str()

        json_str = json.dumps(json_data)
        self.socketio.emit('my_cards', json_str, to=self.id)

    def next_player(self, new_bet=False, everybody_all_in=False):
        super().next_player(new_bet, everybody_all_in)

        if self.players[self.next_player_index].cpu:
            timer = threading.Timer(2, self.make_cpu_move)
            timer.start()

    def make_cpu_move(self):
        self.players[self.next_player_index].make_cpu_move(self)
