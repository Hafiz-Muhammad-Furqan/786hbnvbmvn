from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
import os

try:
    os.remove("db.sqlite3")
    print("Old database removed. Training new database")
except FileNotFoundError:
    print('No database found. Creating new database.')

# Create the chatbot instance
english_bot = ChatBot(
    'Bot',
    storage_adapter='chatterbot.storage.SQLStorageAdapter',
    logic_adapters=[
        'chatterbot.logic.BestMatch',
        'chatterbot.logic.MathematicalEvaluation'
    ],
    database_uri='sqlite:///db.sqlite3'  # Specify the database URI (SQLite in this case)
)

# Create an instance of the ListTrainer
trainer = ListTrainer(english_bot)

# Iterate over files in 'data' directory and train the bot
for file in os.listdir('data'):
    print(f'Training using {file}')
    with open(f'data/{file}', 'r') as f:
        conv_data = f.readlines()
        trainer.train(conv_data)
    print(f"Training completed for {file}")
