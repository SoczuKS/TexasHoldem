import json
import threading

from flask import Flask, redirect, render_template, request, url_for
from flask_socketio import SocketIO, join_room

from LocalGame import LocalGame
from OnlineGame import OnlineGame
from Player import Player

app = Flask(__name__)
app.secret_key = 'fa032fdd10f3323260f22d51dd9cc862c5d8ef0f0b007d7e831dd71faf9b0f76'
socketio = SocketIO(app)
games = []


@app.route('/')
def index():
    return render_template('main.html')


@app.route('/rules')
def rules():
    return render_template('rules.html')


@app.route('/mode_selector')
def mode_selector():
    return render_template('mode_selector.html')


@app.route('/local_setup', methods={'GET', 'POST'})
def local_setup():
    if request.method == 'POST':
        entry_fee = int(request.form['entry_fee'])
        big_blind = int(request.form['big_blind'])
        number_of_cpu_players = int(request.form['number_of_cpu_players'])
        human_player_names = request.form.getlist('players[]')
        cpu_types = request.form.getlist('cpu_types[]')

        if [x for x in (entry_fee, big_blind, number_of_cpu_players, human_player_names) if x is None]:
            return redirect(url_for('local_setup'))

        local_game = LocalGame(entry_fee, big_blind, number_of_cpu_players, human_player_names, cpu_types, socketio)
        games.append(local_game)

        return redirect(url_for('play_game', identifier=local_game.id))

    return render_template('local_setup.html')


@app.route('/online_list')
def online_list():
    return render_template('online_list.html', games=[x for x in games if not x.local and not x.started])


@app.route('/online_setup', methods={'GET', 'POST'})
def online_setup():
    if request.method == 'POST':
        game_name = request.form['game_name']
        entry_fee = int(request.form['entry_fee'])
        big_blind = int(request.form['big_blind'])
        number_of_players = int(request.form['number_of_players'])

        if [x for x in (game_name, entry_fee, big_blind, number_of_players) if x is None]:
            return redirect(url_for('online_setup'))

        game = OnlineGame(game_name, entry_fee, big_blind, number_of_players, socketio)
        games.append(game)

        return redirect(url_for('online_list'))

    return render_template('online_setup.html')


@app.route('/game/<identifier>')
def play_game(identifier):
    game = None

    for g in games:
        if g.id == identifier:
            game = g

    if game is None:
        return redirect(url_for('index'))

    return render_template('game.html', game=game)


@socketio.on('join')
def on_join(data):
    game_id = data['game_id']
    player_name = data['player_name']

    game = None

    for g in games:
        if g.id == game_id:
            game = g

    if game is None:
        return False

    p = Player(player_name, socketio, request.sid)
    player_index = game.join(p)

    to_return = {
        'game': game.get_dict(),
        'joined': player_index
    }

    return json.dumps(to_return)


@socketio.on('start_local')
def on_start_local(data):
    game_id = data['game_id']

    game = None

    for g in games:
        if g.id == game_id:
            game = g

    if game is None:
        return

    join_room(game.id)

    timer = threading.Timer(2.0, game.play)
    timer.start()

    to_return = {
        'game': game.get_dict()
    }

    return json.dumps(to_return)


@socketio.on('fold')
def on_fold(data):
    game_id = data['game_id']
    player_index = data['player_index']

    game = None

    for g in games:
        if g.id == game_id:
            game = g

    if game is None:
        return

    game.fold(player_index)


@socketio.on('call')
def on_call(data):
    game_id = data['game_id']
    player_index = data['player_index']

    game = None

    for g in games:
        if g.id == game_id:
            game = g

    if game is None:
        return

    game.call(player_index)


@socketio.on('raise')
def on_raise(data):
    game_id = data['game_id']
    player_index = data['player_index']
    raise_value = data['raise_value']

    game = None

    for g in games:
        if g.id == game_id:
            game = g

    if game is None:
        return

    game.raise_(player_index, raise_value)


@socketio.on('all_in')
def on_all_in(data):
    game_id = data['game_id']
    player_index = data['player_index']

    game = None

    for g in games:
        if g.id == game_id:
            game = g

    if game is None:
        return

    game.all_in(player_index)


if __name__ == '__main__':
    socketio.run(app=app, host='0.0.0.0', port=5128, debug=True)
