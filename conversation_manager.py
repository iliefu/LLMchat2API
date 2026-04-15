import sqlite3

class ConversationManager:
    def __init__(self, db_name='conversations.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        with self.conn:
            self.conn.execute('''
            CREATE TABLE IF NOT EXISTS conversation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            ''')

    def save_conversation(self, user_input, bot_response):
        with self.conn:
            self.conn.execute('''
            INSERT INTO conversation (user_input, bot_response)
            VALUES (?, ?)
            ''', (user_input, bot_response))

    def fetch_conversations(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM conversation')
        return cursor.fetchall()

    def close(self):
        self.conn.close()