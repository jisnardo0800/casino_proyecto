from flask import Flask, render_template, request, redirect, url_for, session
import json, random
import re  # <- para expresión regular
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'
USERS_FILE = 'users.json'

#excepcion

def load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f).get('users', [])
    except:
        return []

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump({'users': users}, f, indent=4)

def find_user(email):
    return next((u for u in load_users() if u['email'] == email), None)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = find_user(email)
        if user and check_password_hash(user['password'], password):
            session['email'] = email
            return redirect(url_for('menu'))
        else:
            error = 'Email o contraseña incorrectos.'
    return render_template('login.html', error=error)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    error = ''
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        email = request.form['email']
        password = request.form['password']

        # Validación con expresión regular
        if not re.match(r'^\S+@\S+\.\S+$', email):
            error = 'Email inválido.'
        elif find_user(email):
            error = 'El email ya está registrado.'
        else:
            # Lambda para saldo inicial
            saldo_inicial = (lambda base: base * 1)(5000)

            user = {
                'nombre': nombre,
                'apellido': apellido,
                'email': email,
                'password': generate_password_hash(password),
                'saldo': saldo_inicial
            }
            users = load_users()
            users.append(user)
            save_users(users)
            session['email'] = email
            return redirect(url_for('menu'))

    return render_template('registro.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/menu', methods=['GET', 'POST'])
def menu():
    if 'email' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        users = load_users()
        for u in users:
            if u['email'] == session['email']:
                u['saldo'] += 1000
                save_users(users)
                break
    user = find_user(session['email'])
    return render_template('menu.html', nombre=user['nombre'], apellido=user['apellido'], saldo=user['saldo'])
@app.route('/ruleta', methods=['GET', 'POST'])
def ruleta():
    if 'email' not in session:
        return redirect(url_for('login'))
#matriz de la ruleta
    ROJO = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
    NEGRO = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]

    ruleta_tablero = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        [12,13,14,15,16,17,18,19,20,21,22,23],
        [24,25,26,27,28,29,30,31,32,33,34,35,36]
    ]

    grid_numbers = []
    for fila in ruleta_tablero:
        for num in fila:
            color = 'green'
            if num in ROJO:
                color = 'red'
            elif num in NEGRO:
                color = 'black'
            grid_numbers.append({'num': num, 'color': color})

    return render_template('ruleta.html', grid_numbers=grid_numbers, result='', bet_type='', bet_value='', amount='')


@app.route('/blackjack', methods=['GET', 'POST'])
def blackjack():
    if 'email' not in session:
        return redirect(url_for('login'))

    def card_value(card):
        rank = card[:-1]
        if rank in ['J','Q','K','10']: return 10
        elif rank == 'A': return 11
        return int(rank)

    def hand_value(cards):
        total = sum(card_value(c) for c in cards)
        aces = sum(1 for c in cards if c[:-1] == 'A')
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    def new_deck():
        suits = ['H','D','C','S']
        ranks = ['A'] + [str(i) for i in range(2,11)] + ['J','Q','K']
        deck = [r+s for r in ranks for s in suits]
        random.shuffle(deck)
        return deck

    #  SIEMPRE reiniciar la partida al entrar
    deck = new_deck()
    player = [deck.pop(), deck.pop()]
    dealer = [deck.pop(), deck.pop()]
    game_over = False
    message = ''

    if request.method == 'POST':
        action = request.form.get('action')
        player = session.get('player', player)
        dealer = session.get('dealer', dealer)
        deck = session.get('deck', deck)

        if action == 'hit':
            player.append(deck.pop())
            if hand_value(player) > 21:
                game_over = True
                message = 'Te pasaste. Perdiste.'
        elif action == 'stand':
            while hand_value(dealer) < 17:
                dealer.append(deck.pop())
            p_val = hand_value(player)
            d_val = hand_value(dealer)
            if d_val > 21 or p_val > d_val:
                message = '¡Ganaste!'
            elif p_val < d_val:
                message = 'Perdiste.'
            else:
                message = 'Empate.'
            game_over = True

        session['player'] = player
        session['dealer'] = dealer
        session['deck'] = deck
        session['game_over'] = game_over
        session['message'] = message

        if game_over:
            users = load_users()
            for u in users:
                if u['email'] == session['email']:
                    if 'Ganaste' in message:
                        u['saldo'] += 1000
                    elif 'Perdiste' in message:
                        u['saldo'] -= 1000
                    break
            save_users(users)

    else:
        session['player'] = player
        session['dealer'] = dealer
        session['deck'] = deck
        session['game_over'] = game_over
        session['message'] = message

    def img(card):
        return url_for('static', filename=f'images/{card}.png')
        
    return render_template('blackjack.html',
                        player_cards=[img(c) for c in session['player']],
                        dealer_cards=[img(c) for c in session['dealer']],
                        player_total=hand_value(session['player']),
                        dealer_total=hand_value(session['dealer']),
                        game_over=session['game_over'],
                        message=session['message'])

if __name__ == '__main__':
    app.run(debug=True)
