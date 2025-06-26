from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, abort
)
import json
import random
import os
import re
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'
USERS_FILE = 'users.json'
HISTORY_FILE = Path('datos') / 'historial.json'  # NUEVO: ruta para historial de giros


# --------------------
# Helpers usuarios
# --------------------
def load_users():
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f).get('users', [])
    except:
        return []


def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'users': users}, f, indent=4, ensure_ascii=False)


def find_user(email):
    return next((u for u in load_users() if u['email'] == email), None)


# --------------------
# Rutas de usuario
# --------------------
@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        email    = request.form['email']
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
        nombre   = request.form['nombre']
        apellido = request.form['apellido']
        email    = request.form['email']
        password = request.form['password']

        if not re.match(r'^\S+@\S+\.\S+$', email):
            error = 'Email inválido.'
        elif find_user(email):
            error = 'El email ya está registrado.'
        else:
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
    user = find_user(session['email'])
    return render_template('menu.html',
        nombre=user['nombre'],
        apellido=user['apellido'],
        saldo=user['saldo']
    )


# ——————————————
#  Ruleta: lógica backend
# ——————————————

# NUEVO: inmutables y validaciones con tuplas/conjuntos
NUM_RED    = frozenset((1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36))
ALL_NUMS   = tuple(range(37))
VALID_BETS = set(ALL_NUMS) | {'red','black','even','odd','1to12','13to24','25to36','2to1'}

# ——————————————
# NUEVO: función para determinar el color de un número de ruleta
# ——————————————
def es_color(numero):
    # Fuera de 0–36 lo tratamos como 'ninguno'
    if not isinstance(numero, int) or numero < 0 or numero > 36:
        return 'ninguno'
    # El 0 no tiene color
    if numero == 0:
        return 'ninguno'
    # Rojo si está en NUM_RED, sino negro
    return 'rojo' if numero in NUM_RED else 'negro'

# NUEVO: excepción personalizada para apuestas
class InvalidBetError(Exception):
    """Se lanza cuando la apuesta no es válida o el saldo es insuficiente."""
    pass

# NUEVO: inicializar archivo de historial
def ensure_history_file():
    if not HISTORY_FILE.exists():
        HISTORY_FILE.parent.mkdir(exist_ok=True)
        HISTORY_FILE.write_text(json.dumps({'spins': []}, indent=2, ensure_ascii=False))

# NUEVO: función para registrar cada tirada
def record_spin(user_email, bet, amount, result, win, payout):
    ensure_history_file()
    data = json.loads(HISTORY_FILE.read_text(encoding='utf-8'))
    data['spins'].append({
        'user': user_email,
        'bet': bet,
        'amount': amount,
        'result': result,
        'win': win,
        'payout': payout
    })
    HISTORY_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))

# NUEVO: lógica de giro extraída y mejorada
def spin_logic(bet_choice, amount, user=None):
    if isinstance(bet_choice, str) and bet_choice.isdigit():
        bet_choice = int(bet_choice)

    if bet_choice not in VALID_BETS:
        raise InvalidBetError(f"Apuesta inválida: {bet_choice}")

    if user is not None and user['saldo'] < amount:
        raise InvalidBetError("Saldo insuficiente para la apuesta.")

    result = random.choice(ALL_NUMS)
    if isinstance(bet_choice, int):
        win, payout = (result == bet_choice), amount * 35
    elif bet_choice == 'red':
        win, payout = (result in NUM_RED), amount * 2
    elif bet_choice == 'black':
        win, payout = (result not in NUM_RED and result != 0), amount * 2
    elif bet_choice == 'even':
        win, payout = (result != 0 and result % 2 == 0), amount * 2
    elif bet_choice == 'odd':
        win, payout = (result % 2 == 1), amount * 2
    elif bet_choice == '1to12':
        win, payout = (1 <= result <= 12), amount * 3
    elif bet_choice == '13to24':
        win, payout = (13 <= result <= 24), amount * 3
    elif bet_choice == '25to36':
        win, payout = (25 <= result <= 36), amount * 3
    else:  # '2to1'
        win, payout = (result != 0), amount * 3

    if user is not None:
        user['saldo'] -= amount
        if win:
            user['saldo'] += payout

    return {
        'result': result,
        'win': win,
        'payout': payout
    }

@app.route('/ruleta')
def ruleta():
    if 'email' not in session:
        return redirect(url_for('login'))
    user = find_user(session['email'])
    return render_template('ruleta.html', saldo=user['saldo'])


@app.route('/api/spin', methods=['POST'])
def api_spin():
    if 'email' not in session:
        return jsonify({'error': 'No autenticado'}), 401

    data   = request.get_json() or {}
    bet    = data.get('bet')
    amount = data.get('amount', 0)

    users = load_users()
    user = next((u for u in users if u['email'] == session['email']), None)
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    try:
        res = spin_logic(bet, amount, user)
    except InvalidBetError as e:
        return jsonify({'error': str(e), 'saldo': user['saldo']}), 400

    # NUEVO: registrar en historial y guardar usuarios
    record_spin(session['email'], bet, amount, res['result'], res['win'], res['payout'])
    save_users(users)

    res['saldo'] = user['saldo']
    return jsonify(res)


# ——————————————
# Ruleta: endpoint para múltiples apuestas
# ——————————————
@app.route('/api/spin_multi', methods=['POST'])
def api_spin_multi():
    if 'email' not in session:
        return jsonify({'error': 'No autenticado'}), 401

    data = request.get_json() or {}
    bets = data.get('bets', [])

    if not isinstance(bets, list) or not bets:
        return jsonify({'error': 'No se recibieron apuestas'}), 400

    users = load_users()
    user = next((u for u in users if u['email'] == session['email']), None)
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    # NUEVO: verificación de saldo total
    total_amount = sum(b.get('amount', 0) for b in bets)
    if user['saldo'] < total_amount:
        return jsonify({'error': 'Saldo insuficiente', 'saldo': user['saldo']}), 400

    result = random.choice(ALL_NUMS)
    resultados = []

    for b in bets:
        bet_choice = b.get('bet')
        amount     = b.get('amount', 0)
        try:
            if isinstance(bet_choice, str) and bet_choice.isdigit():
                bet_choice = int(bet_choice)
            if bet_choice not in VALID_BETS:
                raise InvalidBetError(f"Apuesta inválida: {bet_choice}")

            # NUEVO: reaplicar lógica de pago al mismo resultado
            if isinstance(bet_choice, int):
                win, payout = (result == bet_choice), amount * 35
            elif bet_choice == 'red':
                win, payout = (result in NUM_RED), amount * 2
            elif bet_choice == 'black':
                win, payout = (result not in NUM_RED and result != 0), amount * 2
            elif bet_choice == 'even':
                win, payout = (result != 0 and result % 2 == 0), amount * 2
            elif bet_choice == 'odd':
                win, payout = (result % 2 == 1), amount * 2
            elif bet_choice == '1to12':
                win, payout = (1 <= result <= 12), amount * 3
            elif bet_choice == '13to24':
                win, payout = (13 <= result <= 24), amount * 3
            elif bet_choice == '25to36':
                win, payout = (25 <= result <= 36), amount * 3
            else:  # '2to1'
                win, payout = (result != 0), amount * 3

            user['saldo'] -= amount
            if win:
                user['saldo'] += payout

            resultados.append({
                'bet': bet_choice,
                'amount': amount,
                'win': win,
                'payout': payout
            })

            record_spin(session['email'], bet_choice, amount, result, win, payout)  # NUEVO

        except InvalidBetError as e:
            resultados.append({
                'bet': bet_choice,
                'amount': amount,
                'error': str(e)
            })

    save_users(users)
    return jsonify({
        'result': result,
        'results': resultados,
        'saldo': user['saldo']
    })


# --------------------
# Blackjack (existente)
# --------------------
@app.route('/blackjack', methods=['GET', 'POST'])
def blackjack():
    if 'email' not in session:
        return redirect(url_for('login'))

    def card_value(card):
        rank = card[:-1]
        if rank in ['J','Q','K','10']:
            return 10
        elif rank == 'A':
            return 11
        return int(rank)

    def hand_value(cards):
        total = sum(card_value(c) for c in cards)
        aces  = sum(1 for c in cards if c[:-1] == 'A')
        while total > 21 and aces:
            total -= 10
            aces  -= 1
        return total

    def new_deck():
        suits = ['H','D','C','S']
        ranks = ['A'] + [str(i) for i in range(2,11)] + ['J','Q','K']
        deck  = [r+s for r in ranks for s in suits]
        random.shuffle(deck)
        return deck

    deck      = new_deck()
    player    = [deck.pop(), deck.pop()]
    dealer    = [deck.pop(), deck.pop()]
    game_over = False
    message   = ''

    if request.method == 'POST':
        action = request.form.get('action')
        player = session.get('player', player)
        dealer = session.get('dealer', dealer)
        deck   = session.get('deck', deck)

        if action == 'hit':
            player.append(deck.pop())
            if hand_value(player) > 21:
                game_over = True
                message   = 'Te pasaste. Perdiste.'
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

        session['player']    = player
        session['dealer']    = dealer
        session['deck']      = deck
        session['game_over'] = game_over
        session['message']   = message

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
        session['player']    = player
        session['dealer']    = dealer
        session['deck']      = deck
        session['game_over'] = game_over
        session['message']   = message

    def img(card):
        return url_for('static', filename=f'images/{card}.png')

    return render_template('blackjack.html',
        player_cards=[img(c) for c in session['player']],
        dealer_cards=[img(c) for c in session['dealer']],
        player_total=hand_value(session['player']),
        dealer_total=hand_value(session['dealer']),
        game_over=session['game_over'],
        message=session['message']
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
