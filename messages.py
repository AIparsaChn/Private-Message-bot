from telebot.formatting import mbold, hbold

REQUEST_DESCRIPTION_MESSAGE = f"""
Now, write your description.
if you don't want to write any caption, just type /no_description.
{hbold('Note: everyone can see your description in the specific gorup.')}
"""

AFFIRMATION_MESSAGE = """
target user first name: *{0}*
target group name: *{1}*
description: *{2}*
private message: *{3}*
"""

REQUEST_GROUP_MESSAGE = f"""
Choose a group you want to send your private message.
"""

REQUEST_USER_MESSAGE = """
Choose a user to send your private message.
"""

BOT_NOT_JOINED_MESSAGE = """
The bot doesn't join this group.
"""

USER_NOT_JOINED_MESSAGE = """
The user doesn't join this group.
"""

REQUEST_PRIVATE_MESSAGE = f"""
Write your private message for the user.
"""

WARNING_LIMIT_PRIVATE_MESSAGE ="""
Youre private message must be less than *{0}*
Your current length of private message: *{1}*
"""

GROUP_NOTIFICATION_MESSAGE = """
Mr, Ms. {0}, you have message from {1}:
descritpion: {2}
"""

SENT_TO_GROUP = """
Now your message has been sent to the group.
"""

WARNING_LIMIT_DESCRIPTION_MESSAGE = """
Your Description must be less than *{0}*
Your current length of description: *{1}*
"""

WARNING_FOLLOW_STRUCTURE = """
Please follow the structure or if your want to cancel the operation click on 'Cancel' button.
"""

CANCELED_OPERATION = """
The operation has been canceled.
"""
