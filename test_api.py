import unittest
import requests

class TestEmojiAPI(unittest.TestCase):
    def test_send_emoji(self):
        url = 'http://localhost:5000/send_emoji'
        data = {
            "user_id": "user123",
            "emoji_type": "smile",
            "timestamp": "2023-10-01T12:00:00Z"
        }
        response = requests.post(url, json=data)
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()