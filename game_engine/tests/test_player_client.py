import unittest
from scripts.player_client import PlayerClient


class TestPlayerClient(unittest.TestCase):
    def test_init(self):
        client = PlayerClient()
        self.assertIsNotNone(client.uuid)
        self.assertEqual(client.server_url, 'http://localhost:8888')
    
    def test_make_random_move_fold(self):
        client = PlayerClient()
        move_type, amount = client.make_random_move(['fold', 'call'], 5, 100)
        self.assertIn(move_type, ['fold', 'call'])
    
    def test_make_random_move_check(self):
        client = PlayerClient()
        move_type, amount = client.make_random_move(['check', 'bet'], 0, 100)
        self.assertIn(move_type, ['check', 'bet'])
    
    def test_make_random_move_call(self):
        client = PlayerClient()
        move_type, amount = client.make_random_move(['call'], 10, 100)
        self.assertEqual(move_type, 'call')
        self.assertEqual(amount, 0)
    
    def test_make_random_move_bet(self):
        client = PlayerClient()
        move_type, amount = client.make_random_move(['bet'], 0, 100)
        self.assertEqual(move_type, 'bet')
        self.assertGreater(amount, 0)


if __name__ == '__main__':
    unittest.main()
