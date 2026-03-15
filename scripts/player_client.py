import json
import uuid
import random
import sys
import time
import requests


class PlayerClient:
    def __init__(self, server_url='http://localhost:8888'):
        self.uuid = str(uuid.uuid4())
        self.server_url = server_url

    def connect(self):
        response = requests.post(
            f'{self.server_url}/connect',
            json={'uuid': self.uuid},
            timeout=5
        )
        return response.status_code == 200

    def get_state(self):
        response = requests.get(
            f'{self.server_url}/state',
            params={'uuid': self.uuid},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        return None

    def make_move(self, move_type, amount=0):
        response = requests.post(
            f'{self.server_url}/move',
            json={
                'uuid': self.uuid,
                'move_type': move_type,
                'amount': amount
            },
            timeout=5
        )
        return response.status_code == 200

    def make_random_move(self, valid_moves, current_bet, chips):
        if 'fold' in valid_moves and random.random() < 0.1:
            return 'fold', 0

        if 'check' in valid_moves and random.random() < 0.5:
            return 'check', 0

        if 'call' in valid_moves:
            return 'call', 0

        if 'bet' in valid_moves:
            max_bet = min(chips, current_bet + 20)
            bet_amount = random.randint(current_bet + 1, max_bet) if current_bet > 0 else random.randint(1, 10)
            return 'bet', bet_amount

        return 'fold', 0

    def run(self):
        if not self.connect():
            print(f"Failed to connect: {self.uuid}")
            return

        print(f"Connected: {self.uuid}")

        while True:
            state = self.get_state()
            if not state:
                time.sleep(1)
                continue

            phase = state.get('phase')
            if phase == 'finished':
                print(f"Game finished. Winner: {state.get('winner_id')}")
                break

            if state.get('is_your_turn'):
                valid_moves = state.get('valid_moves', [])
                current_bet = state.get('current_bet', 0)
                chips = state.get('your_chips', 100)

                move_type, amount = self.make_random_move(valid_moves, current_bet, chips)
                self.make_move(move_type, amount)
                print(f"Move: {move_type} (amount={amount})")
            else:
                time.sleep(0.5)


if __name__ == '__main__':
    port = 8888
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    server_url = f'http://localhost:{port}'
    client = PlayerClient(server_url)
    client.run()
