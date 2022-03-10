import threading

from flask_socketio import join_room, leave_room

from Game import Game


class OnlineGame(Game):
    def __init__(self, name, entry_fee, big_blind, number_of_players, socketio):
        super().__init__(name, entry_fee, big_blind, socketio)
        self.required_number_of_players = number_of_players

    def get_dict(self):
        game_dict = super().get_dict()
        game_dict['required_number_of_players'] = self.required_number_of_players
        return game_dict

    def join(self, player):
        if self.started:
            return False

        if len(self.players) == self.required_number_of_players:
            return False

        self.add_player(player)
        join_room(self.id)
        self.socketio.emit('user_connection', player.to_json(), to=self.id)

        nop = len(self.players)

        if nop == self.required_number_of_players:
            timer = threading.Timer(2.0, self.play)
            timer.start()

        return True

    def send_index(self):
        for i in range(len(self.players)):
            self.players[i].send_index(i)

    def send_cards(self):
        for p in self.players:
            p.send_cards()

    def send_busted_info(self, data):
        super().send_busted_info(data)

        for key in data['busted_players']:
            leave_room(self.id, data['busted_players'][key]['sid'])
