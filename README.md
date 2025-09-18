# 🔐 Private Message Bot
A telegram bot that allows you to send your messages in a public group, but only one selected user can access to that message!!

## ✨ How to work with
1. **Start a Private Message:** Type /private_message in the bot's private chat.
2. **Select the Target Group:** Choose your target group from the button bellow.
   - Note: The bot must be a member of the group. It will automatically detect which groups it is in.
4. **select a User:** Choose the recipient
   - Note: the recipient must joined the group, bot can automatically detect the user joined the group or not.
6. **Compose Your Message:** Write your private message.
7. **Add a Description (Optional):**  Add your description, if your don't want, simply type /no_description.
8. **Send:** That's it!! It finally sends the message in the public group. The recipient can click the button there to reveal and read the private message you sent.

## 🛠️ Built With
- Python
- pyTelegramBotAPI framework
- Redis
- SQLAlchemy
- alembic

## ⚙️ How to run?
1. Clone the repository and install dependencies:
   ```
   git clone https://github.com/your-username/private-message-bot.git
   cd private-message-bot
   pip install -r requirements.txt
   ```
2. Export your token bot as an environment variable:
   ```
   export BOT_TOEKN='your_actual_bot_token_here'
   ```  
3. Run Alembic migrations to create the database and tables:
   ```
   alembic upgrade head
   ```
4. Finally, run the bot:
   ```
   python3 main.py
   ```
### related Links
- [Official Github repo for pyTelegramBotAPI framework](https://github.com/eternnoir/pyTelegramBotAPI)
- [Official Python website](https://www.python.org/)
- [Official Redis website](https://redis.io/)
- [Official SQLAlechemy website](https://www.sqlalchemy.org/)
- [Alembic documentation](https://alembic.sqlalchemy.org/en/latest/)

---
