let playerIndex = []
let canRaise
let myTurn
let nextPlayer = -1
let smallBlindPlayerIndex = -1
let bigBlindPlayerIndex = -1
let dealerPlayerIndex = -1
let game
let localPlayersCards

const RANK_CLASS_TO_STRING = {
        1: "Poker",
        2: "Kareta",
        3: "Full",
        4: "Kolor",
        5: "Strit",
        6: "Trójka",
        7: "Dwie pary",
        8: "Para",
        9: "Wysoka karta",
        10: "Pas"
    }

let formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
})

window.addEventListener('load', () => {
    document.getElementById('player_name_button')?.addEventListener('click', () => {
        let playerName = document.getElementById('player_name_input').value

        if (playerName === undefined || playerName === null || playerName === '') return

        socket.emit('join', {game_id: gameId, player_name: playerName}, (...args) => {
            let json = JSON.parse(args)
            game = json['game']
            let joined = json['joined']

            if (!joined) return

            document.getElementById('player_name_div').remove()
            document.getElementById('waiting_info').style.display = 'flex'
        })
    })

    document.getElementById('player_name_input')?.addEventListener('keyup', (ev) => {
        if (ev.key === 'Enter') {
            document.getElementById('player_name_button').dispatchEvent(new Event('click'))
        }
    })

    document.getElementById('start_local_game_button')?.addEventListener('click', () => {
        socket.emit('start_local', {game_id: gameId}, (...args) => {
            let json = JSON.parse(args)
            game = json['game']

            document.getElementById('start_local_game_button').remove()
        })
    })

    document.getElementById('fold_button').addEventListener('click', fold)
    document.getElementById('call_button').addEventListener('click', call)
    document.getElementById('raise_button').addEventListener('click', raise)
    document.getElementById('all_in_button').addEventListener('click', allIn)

    document.getElementById('raise_input').addEventListener('input', (ev) => {
        document.getElementById('raise_value').innerText = formatter.format(ev.target.value)
    })

    document.getElementById('show_cards_button')?.addEventListener('mousedown', (ev) => {
        let playerCardsData = localPlayersCards[nextPlayer]

        let playerCards = document.querySelectorAll('.card.player' + (nextPlayer + 1).toString())

        for (let i = 0; i < 2; ++i) {
            let card = playerCards[i]

            let rank = playerCardsData[i][0]
            let suit = playerCardsData[i][1]

            cardSet(card, rank, suit, false)
        }
    })
    document.getElementById('show_cards_button')?.addEventListener('mouseup', (ev) => {
        allCardReset()
    })
})

function resetTable() {
    allCardReset()
    clearCommunityCards()
    clearCommands()
    clearButtons()
    document.getElementById('deal_pot').innerText = formatter.format(0)
}

function clearCommands() {
    document.getElementById('commands').innerHTML = ''
}

function clearCommunityCards() {
    let communityCardsDiv = document.getElementById('community_cards')

    for (let i = 0; i < 5; ++i) {
        let card = communityCardsDiv.getElementsByClassName('card')[i]

        cardSet(card, '', '', true)
    }
}

function setupButtons() {
    let smallBlindPlayerCardsDiv = document.querySelector('.player_buttons.player' + (smallBlindPlayerIndex + 1).toString())
    let smallBlindButton = document.createElement('div')
    smallBlindButton.id = 'small_blind_button'
    smallBlindButton.classList.add('button')
    smallBlindButton.innerText = 'SB'
    smallBlindPlayerCardsDiv.appendChild(smallBlindButton)

    let bigBlindPlayerCardsDiv = document.querySelector('.player_buttons.player' + (bigBlindPlayerIndex + 1).toString())
    let bigBlindButton = document.createElement('div')
    bigBlindButton.id = 'big_blind_button'
    bigBlindButton.classList.add('button')
    bigBlindButton.innerText = 'BB'
    bigBlindPlayerCardsDiv.appendChild(bigBlindButton)

    let dealerPlayerCardsDiv = document.querySelector('.player_buttons.player' + (dealerPlayerIndex + 1).toString())
    let dealerButton = document.createElement('div')
    dealerButton.id = 'dealer_button'
    dealerButton.classList.add('button')
    dealerButton.innerText = 'D'
    dealerPlayerCardsDiv.appendChild(dealerButton)
}

function clearButtons() {
    document.getElementById('small_blind_button')?.remove()
    document.getElementById('big_blind_button')?.remove()
    document.getElementById('dealer_button')?.remove()
}

function allCardReset() {
    let cards = document.querySelectorAll('.card:not(.community_card)')

    for (let card of cards) {
        cardSet(card, '', '', true)
    }
}

function cardSet(card, rank, suit, bgEnable) {
    rank = rank === 'T' ? '10' : rank

    switch (suit) {
        case '♠': case '♣':
            card.style.color = 'black'
            break

        case '♥': case '♦':
            card.style.color = 'red'
            break
    }

    let ranks = card.getElementsByClassName('card_rank')
    for (let i = 0; i < ranks.length; ++i) {
        ranks[i].innerText = rank
    }

    let suits = card.getElementsByClassName('card_suit')
    for (let i = 0; i < suits.length; ++i) {
        suits[i].innerText = suit
    }

    if (bgEnable) {
        card.style.background = ''
    } else {
        card.style.background = 'white'
    }
}

function setupPlayersMoney(players) {
    for (let i = 0; i < players.length; ++i) {
        let hrindex = (i + 1).toString()
        let player = players[i]

        if (player['folded']) {
            let cards = document.querySelectorAll('.card.player' + hrindex)

            for (let j = 0; j < cards.length; ++j) {
                cards[j].style.visibility = 'hidden'
            }
        }

        document.querySelector('.bet_pot.player' + hrindex).innerHTML = formatter.format(player['bet_pot'])
        document.querySelector('.player_money.player' + hrindex).innerHTML = formatter.format(player['money'])
    }
}

function flopTurnRiver(players, dealPot) {
    setupPlayersMoney(players)

    document.getElementById('deal_pot').innerText = formatter.format(dealPot)
}

socket.on('flop', (...args) => {
    let json = JSON.parse(args)

    let cards = json['cards']

    let div = document.getElementById('community_cards')

    for (let i = 0; i < 3; ++i) {
        let card = div.getElementsByClassName('card')[i]

        let rank = cards[i][0]
        let suit = cards[i][1]

        cardSet(card, rank, suit)
    }

    flopTurnRiver(json['players'], json['deal_pot'])
})

socket.on('turn', (...args) => {
    let json = JSON.parse(args)
    let cardStr = json['card']

    let div = document.getElementById('community_cards')
    let card = div.getElementsByClassName('card')[3]

    let rank = cardStr[0]
    let suit = cardStr[1]

    cardSet(card, rank, suit)

    flopTurnRiver(json['players'], json['deal_pot'])
})

socket.on('river', (...args) => {
    let json = JSON.parse(args)
    let cardStr = json['card']

    let div = document.getElementById('community_cards')
    let card = div.getElementsByClassName('card')[4]

    let rank = cardStr[0]
    let suit = cardStr[1]

    cardSet(card, rank, suit)

    flopTurnRiver(json['players'], json['deal_pot'])
})

socket.on('my_cards', (...args) => {
    if (game['local']) {
        let json = JSON.parse(args)

        localPlayersCards = json['cards']
    } else {
        let cards = JSON.parse(args[0])['my_cards']

        let myCards = document.querySelectorAll('.card.player' + (playerIndex[0] + 1).toString())

        for (let i = 0; i < 2; ++i) {
            let rank = cards[i][0]
            let suit = cards[i][1]

            let myCard = myCards[i]

            cardSet(myCard, rank, suit, false)
        }
    }
})

socket.on('user_connection', (...args) => {
    let json = JSON.parse(args)

    let playerName = json['name']
    let commandText = "Gracz " + playerName + " dołączył do gry"
    addCommand(commandText)
})

socket.on('new_deal', (...args) => {
    let waitingInfo = document.getElementById('waiting_info')
    if (null !== waitingInfo) {
        waitingInfo.style.display = 'none'
    }

    let json = JSON.parse(args)

    smallBlindPlayerIndex = json['small_blind_player_index']
    bigBlindPlayerIndex = json['big_blind_player_index']
    dealerPlayerIndex = json['dealer_player_index']

    resetTable()

    for (let i = 0; i < 8; ++i) {
        let hrindex = (i + 1).toString()

        if (i < json['players'].length) {
            document.querySelector('.player_name.player' + hrindex).innerHTML = json['players'][i]['name']
        }

        let all = document.querySelectorAll('.player' + hrindex)

        for (let j = 0; j < all.length; ++j) {
            if (i < json['players'].length) {
                all[j].style.visibility = 'visible'
            } else {
                all[j].style.visibility = 'hidden'
            }
        }
    }

    setupButtons()
})

socket.on('command', (...args) => {
    let json = JSON.parse(args)

    switch(json['move_type']) {
        case 'check':
            addCommand('Gracz ' + json['player_name'] + ' czeka')
            break

        case 'call_all_in':
            addCommand('Gracz ' + json['player_name'] + ' sprawdza za wszystko (' + formatter.format(json['call_value']) + ')')
            break

        case 'call':
            addCommand('Gracz ' + json['player_name'] + ' sprawdza (' + formatter.format(json['call_value']) + ')')
            break

        case 'raise':
            addCommand('Gracz ' + json['player_name'] + ' podbija (' + formatter.format(json['raise_value']) + ')')
            break

        case 'fold':
            addCommand('Gracz ' + json['player_name'] + ' pasuje')
            break

        case 'all_in':
            addCommand('Gracz ' + json['player_name'] + ' gra za wszystko (' + formatter.format(json['raise_value']) + ')')
            break
    }
})

socket.on('deal_end', (...args) => {
    let json = JSON.parse(args)

    let winnerText = json['winning_players'].length === 1 ? 'Gracz ' : 'Gracze '
    let players = ''
    let value = json['winning_value']
    let figure = json['figure']

    for (let p of json['winning_players']) {
        players += p
        players += ', '
    }

    players = players.substring(0, players.length - 2)

    winnerText += players

    winnerText += json['winning_players'].length === 1 ? ' wygrywa ' : ' wygrywają po '
    winnerText += formatter.format(value)

    winnerText += ' [' + RANK_CLASS_TO_STRING[figure] + ']'

    addCommand(winnerText)
})

socket.on('busted_info', (...args) => {
    let json = JSON.parse(args)

    if (Object.keys(json['busted_players']).length > 0) {
        let bustedText = Object.keys(json['busted_players']).length === 1 ? 'Gracz ' : 'Gracze '

        for (let key in json['busted_players']) {
            bustedText += json['busted_players'][key]['name']
            bustedText += ', '
        }

        bustedText = bustedText.substring(0, bustedText.length - 2)
        bustedText += Object.keys(json['busted_players']).length === 1 ? ' odpada' : ' odpadają'

        addCommand(bustedText)
    }
})

socket.on('my_index', (...args) => {
    let json = JSON.parse(args[0])
    playerIndex = json['player_index']

    if (!game['local']) {
        playerIndex = [playerIndex]
    }
    document.getElementById('game_content').style.display = 'flex'
})

socket.on('next_player', (...args) => {
    let json = JSON.parse(args)

    setupPlayersMoney(json['players'])

    if (playerIndex.includes(json['next_player'])) {
        myTurn = true
        nextPlayer = json['next_player']
        document.getElementById('action_buttons').style.visibility = 'visible'

        if (game['local']) {
            allCardReset()
            document.getElementById('player_turn_info').innerText = 'Kolej gracza ' + json['players'][nextPlayer]['name']
        }

        let callValue = json['call_value']
        let mustAllIn = json['must_all_in']
        let players = json['players']

        if (json['can_check']) {
            document.getElementById('action_buttons_check_action_span').innerText = 'Czekaj'
            document.getElementById('call_value').innerText = ''
            document.getElementById('call_button').style.backgroundColor = 'rgb(233, 233, 237)'
        } else {
            if (mustAllIn) {
                document.getElementById('call_button').style.backgroundColor = 'gold'
                document.getElementById('action_buttons_check_action_span').innerText = 'Sprawdź'
                document.getElementById('call_value').innerText = formatter.format(callValue)
            } else {
                document.getElementById('call_button').style.backgroundColor = 'rgb(233, 233, 237)'
                document.getElementById('action_buttons_check_action_span').innerText = 'Sprawdź'
                document.getElementById('call_value').innerText = formatter.format(callValue)
            }
        }

        canRaise = json['can_raise']

        if (canRaise) {
            document.getElementById('raise_div').style.visibility = 'inherit'
            document.getElementById('all_in_button').style.visibility = 'inherit'
        } else {
            document.getElementById('raise_div').style.visibility = 'hidden'
            document.getElementById('all_in_button').style.visibility = 'hidden'
        }

        document.getElementById('raise_value').innerText = formatter.format(json['min_raise_value'])
        let sliderInput = document.getElementById('raise_input')
        sliderInput.min = json['min_raise_value']
        sliderInput.max = players[nextPlayer]['money'] + players[nextPlayer]['bet_pot']
        sliderInput.value = json['min_raise_value']
    } else {
        myTurn = false
        document.getElementById('action_buttons').style.visibility = 'hidden'

        if (game['local']) {
            allCardReset()
        }
    }
})

socket.on('table_finish', (...args) => {
    let json = JSON.parse(args)
    addCommand('Koniec rozgrywki! Stół wygrywa gracz ' + json['winner'], 'winner_info')
})

function call() {
    if (!myTurn) return

    let data = {
        'game_id': gameId,
        'player_index': nextPlayer
    }

    socket.emit('call', data)
    myTurn = false
    document.getElementById('action_buttons').style.visibility = 'hidden'
}

function raise() {
    if (!myTurn || !canRaise) return

    let data = {
        'game_id': gameId,
        'player_index': nextPlayer,
        'raise_value': parseInt(document.getElementById('raise_input').value)
    }

    socket.emit('raise', data)
    myTurn = false
    document.getElementById('action_buttons').style.visibility = 'hidden'
}

function allIn() {
    if (!myTurn) return

    let data = {
        'game_id': gameId,
        'player_index': nextPlayer
    }

    socket.emit('all_in', data)
    myTurn = false
    document.getElementById('action_buttons').style.visibility = 'hidden'
}

function fold() {
    if (!myTurn) return

    let data = {
        'game_id': gameId,
        'player_index': nextPlayer
    }

    socket.emit('fold', data)
    myTurn = false
    document.getElementById('action_buttons').style.visibility = 'hidden'
}

function addCommand(commandString, specialCommandId = null) {
    let commandsDiv = document.getElementById('commands')
    let el = document.createElement('div')

    if (specialCommandId !== null) {
        el.id = specialCommandId
    }

    if (commandsDiv.children.length === 11) {
        commandsDiv.removeChild(commandsDiv.firstChild)
    }

    el.innerText = commandString

    commandsDiv.appendChild(el)
}
