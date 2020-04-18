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
        active_games[gameid].append(update.message.from_user.first_name + ' ' + update.message.from_user.last_name)
        msg = ''
        for x in active_games[gameid]:
            msg += x + '\n'
        update.message.reply_text('Joined game successfully. Players in room: \n' + msg)
    else:
        update.message.reply_text('Game does not exist. You can create a game using /newgame')

def newgame(update, context):
    gameid = ''.join(random.choices(string.ascii_uppercase, k=5))
    active_games[gameid] = []
    active_games[gameid].append(update.message.from_user.first_name + ' ' + update.message.from_user.last_name)
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
