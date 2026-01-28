import json
import uuid
import logging
import redis
from flask import Flask, request, jsonify
from threading import Thread
from game_engine.poker import GameState, GamePhase, MoveType, start_game, process_move

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('game.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
game_state = None
players_connected = {}
match_id = None
STATE_CHANNEL = 'game:state'
MOVES_CHANNEL = 'game:moves'


def publish_state():
    if game_state:
        state_data = {
            'match_id': game_state.match_id,
            'phase': game_state.phase.value,
            'current_bet': game_state.current_bet,
            'pot': game_state.pot,
            'players': [
                {
                    'bot_id': p.bot_id,
                    'chips': p.chips,
                    'current_bet': p.current_bet,
                    'is_folded': p.is_folded
                }
                for p in game_state.players
            ]
        }
        
        if game_state.get_current_player():
            state_data['current_player'] = game_state.get_current_player().bot_id
            current = game_state.get_current_player()
            if current.current_bet < game_state.current_bet:
                state_data['valid_moves'] = ['call', 'fold']
            elif current.current_bet == game_state.current_bet:
                state_data['valid_moves'] = ['check', 'bet', 'fold']
            else:
                state_data['valid_moves'] = ['check', 'fold']
        else:
            state_data['current_player'] = None
            state_data['valid_moves'] = []
        
        if game_state.phase == GamePhase.FINISHED:
            state_data['winner_id'] = game_state.winner_id
        
        redis_client.publish(STATE_CHANNEL, json.dumps(state_data))
        logger.info(f"Published state: phase={game_state.phase.value}")


def process_game():
    global game_state
    
    while True:
        try:
            message = redis_client.blpop(MOVES_CHANNEL, timeout=1)
            if message and game_state and game_state.phase == GamePhase.BETTING:
                _, move_data = message
                move_json = json.loads(move_data)
                
                player_uuid = move_json.get('uuid')
                move_type_str = move_json.get('move_type')
                amount = move_json.get('amount', 0)
                
                current = game_state.get_current_player()
                if not current or current.bot_id != player_uuid:
                    continue
                
                move_map = {
                    'bet': MoveType.BET,
                    'call': MoveType.CALL,
                    'check': MoveType.CHECK,
                    'fold': MoveType.FOLD
                }
                
                move_type = move_map.get(move_type_str)
                if not move_type:
                    continue
                
                try:
                    process_move(game_state, player_uuid, move_type, amount)
                    logger.info(f"Move processed: {player_uuid} {move_type_str} {amount}")
                    publish_state()
                    
                    if game_state.phase == GamePhase.FINISHED:
                        logger.info(f"Game finished. Winner: {game_state.winner_id}")
                        break
                except Exception as e:
                    logger.error(f"Error processing move: {e}")
        except Exception as e:
            if game_state and game_state.phase == GamePhase.BETTING:
                continue
            break


@app.route('/connect', methods=['POST'])
def connect():
    global game_state, match_id, players_connected
    
    data = request.json
    player_uuid = data.get('uuid')
    
    if not player_uuid:
        return jsonify({'error': 'uuid required'}), 400
    
    if player_uuid in players_connected:
        return jsonify({'status': 'already_connected'}), 200
    
    players_connected[player_uuid] = True
    logger.info(f"Player connected: {player_uuid}")
    
    if len(players_connected) == 2:
        match_id = str(uuid.uuid4())
        game_state = GameState(match_id=match_id)
        player_ids = list(players_connected.keys())
        start_game(game_state, player_ids)
        logger.info(f"Game started: {match_id}")
        publish_state()
        
        game_thread = Thread(target=process_game, daemon=True)
        game_thread.start()
    
    return jsonify({'status': 'connected', 'match_id': match_id})


@app.route('/state', methods=['GET'])
def get_state():
    player_uuid = request.args.get('uuid')
    
    if not player_uuid or player_uuid not in players_connected:
        return jsonify({'error': 'invalid uuid'}), 400
    
    if not game_state:
        return jsonify({'status': 'waiting'}), 200
    
    current = game_state.get_current_player()
    player = game_state.get_player(player_uuid)
    
    response = {
        'phase': game_state.phase.value,
        'current_bet': game_state.current_bet,
        'pot': game_state.pot,
        'current_player': current.bot_id if current else None,
        'your_chips': player.chips if player else 0,
        'your_bet': player.current_bet if player else 0,
        'is_your_turn': current.bot_id == player_uuid if current else False
    }
    
    if current and current.bot_id == player_uuid:
        if player.current_bet < game_state.current_bet:
            response['valid_moves'] = ['call', 'fold']
        elif player.current_bet == game_state.current_bet:
            response['valid_moves'] = ['check', 'bet', 'fold']
        else:
            response['valid_moves'] = ['check', 'fold']
    
    if game_state.phase == GamePhase.FINISHED:
        response['winner_id'] = game_state.winner_id
    
    return jsonify(response)


@app.route('/move', methods=['POST'])
def make_move():
    data = request.json
    player_uuid = data.get('uuid')
    move_type = data.get('move_type')
    amount = data.get('amount', 0)
    
    if not player_uuid or player_uuid not in players_connected:
        return jsonify({'error': 'invalid uuid'}), 400
    
    if not game_state or game_state.phase != GamePhase.BETTING:
        return jsonify({'error': 'game not in betting phase'}), 400
    
    move_data = {
        'uuid': player_uuid,
        'move_type': move_type,
        'amount': amount
    }
    
    redis_client.rpush(MOVES_CHANNEL, json.dumps(move_data))
    
    return jsonify({'status': 'move_received'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=False)














