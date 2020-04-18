import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import string
import random

BOT_TOKEN = '1282833871:AAF4jJhL6Rqt-hdYs4PfsvEdD-GZNU1QC8Y'

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

active_games = {}
active_users = {}

class User:
    def __init__(self, userObj, chatObj):
        self.fname = userObj.first_name
        self.lname = userObj.last_name
        self.name = userObj.first_name + ' ' + userObj.last_name
        self.chatid = chatObj.id
        self.id = userObj.id
        self.username = userObj.username

class Game:
    def __init__(self, gameid):
        self.userlist = []
        self.gameid = gameid

    def addUser(self, user):
        self.userlist.append(user)
    
    def getUserList(self):
        msg = ''
        for x in self.userlist:
            msg += x.name + '\n'
        return msg

def help(update, context):
    update.message.reply_text("Use /newgame to create a game.\nUse \join <gameid> to join a game.")

def start(update, context):
    update.message.reply_text("Welcome to Court Piece")

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def joingame(update, context):
    gameid = "".join(context.args)
    if(gameid in active_games):
        newuser = User(update.message.from_user, update.effective_chat)
        update.message.reply_text('Joined game successfully. Players in room: \n' + active_games[gameid].getUserList())
        for x in active_games[gameid].userlist:
            update.message.bot.send_message(x.chatid, update.message.from_user.name + ' has joined the game')
        active_games[gameid].addUser(newuser)
    else:
        update.message.reply_text('Game does not exist. You can create a game using /newgame')

def newgame(update, context):
    gameid = ''.join(random.choices(string.ascii_uppercase, k=5))
    active_games[gameid] = Game(gameid)
    newuser = User(update.message.from_user, update.effective_chat)
    active_games[gameid].addUser(newuser)
    update.message.reply_text('New game created. Ask your friends to join using \"/join ' + gameid + '\"')


def main():
    updater = Updater(BOT_TOKEN, use_context=True)

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('newgame', newgame))
    updater.dispatcher.add_handler(CommandHandler('join', joingame))
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
