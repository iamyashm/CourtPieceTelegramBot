import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ForceReply, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import logging
import string
import random
from emoji import emojize
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = '1282833871:AAF4jJhL6Rqt-hdYs4PfsvEdD-GZNU1QC8Y'

HEARTS = emojize(":hearts:", use_aliases=True)
CLUBS = emojize(":clubs:", use_aliases=True)
DIAMONDS = emojize(":diamonds:", use_aliases=True)
SPADES = emojize(":spades:", use_aliases=True)

SUITS = [HEARTS, CLUBS, DIAMONDS, SPADES]

DECK = []
vals = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

for i in range(52):
    DECK.append('|' + vals[i % 13] + ' ' +  SUITS[i // 13] + '|')

active_games = {}
user_game = {}
bot = telegram.Bot(BOT_TOKEN)

class User:
    def __init__(self, userObj, chatObj, gameid):
        self.userObj = userObj
        self.fname = userObj.first_name
        self.name = userObj.full_name
        self.chatid = chatObj.id
        self.id = userObj.id
        self.username = userObj.username
        self.gameid = gameid
        self.cards = []
        self.team = 0
    
    def setTeam(self, team):
        self.team = team

    def getCards(self):
        print(self.cards)
        c = 0
        res = 'Cards in Hand:\n'
        for x in self.cards:
            res += x + ' , '
            c += 1
            if (c % 7 == 0):
                res += '\n'
        
        return res
    
class Game:
    def __init__(self, gameid):
        self.userlist = []
        self.gameid = gameid
        self.numPlayers = 0
        self.roundNo = 0
        self.scores = {'1':0, '2':0}
        self.teams = {'1': None, '2': None}
        self.state = 'SETUP'
        self.playerIdx = -1
        self.availableCards = DECK
        self.trump = None
        self.currPlayer = None

    def addUser(self, user):
        self.userlist.append(user)
        if(self.numPlayers == 0):
            self.host = user
            self.currPlayer = self.host
        self.numPlayers += 1
    
    def getUserList(self):
        msg = ''
        for x in self.userlist:
            msg += x.name + '\n'
        return msg
    
    def setTeams(self, update):
        if(self.playerIdx == -1):
            self.playerIdx = 0
            self.teams['1'] = []
            self.teams['2'] = []
        elif (self.playerIdx == 3):
            t1txt = self.teams['1'][0].name + ' , ' + self.teams['1'][1].name
            t2txt = self.teams['2'][0].name + ' , ' + self.teams['2'][1].name
            for u in self.userlist:
                update.message.bot.send_message(u.id, 'Teams: \n' + 'Team 1: ' + t1txt + '\nTeam 2: ' + t2txt)
            self.dealCards()
            return
        else:
            self.playerIdx += 1
        markup = ReplyKeyboardMarkup(keyboard=[['Team 1', 'Team 2']], one_time_keyboard=True)
        update.message.bot.send_message(self.host.id, 'Enter team number for ' + self.userlist[self.playerIdx].name, reply_markup=markup)
            

    def respond(self, update, context):
        print(update.message.text)
        if(self.currPlayer.id == update.message.from_user.id):
            if('Team' in update.message.text):
                self.teams[update.message.text[5]].append(self.userlist[self.playerIdx])
                self.userlist[self.playerIdx].team = update.message.text[5]
                self.setTeams(update)
            elif(self.state == 'TRUMP CALL 1' or self.state == 'TRUMP CALL 2'):
                self.trump = update.message.text
                self.dealCards()
            else:
                update.message.reply_text('Invalid command')
        else:
            update.message.reply_text('Invalid command. Please wait for game updates.')

    def dealCards(self):
        
        if(self.state == 'SETUP'):
            random.shuffle(self.availableCards)
            self.callingTeam = str(random.randrange(2) + 1)
            otherTeam = '2' if self.callingTeam == '1' else  '1'
            self.userlist[0] = self.teams[self.callingTeam][0]
            self.userlist[1] = self.teams[otherTeam][0]
            self.userlist[2] = self.teams[self.callingTeam][1]
            self.userlist[3] = self.teams[otherTeam][1]
            self.state = 'TRUMP CALL 1'
            self.currPlayer = self.userlist[0]
            for j in range(5):
                self.userlist[0].cards.append(self.availableCards[j])               
            
            suitMarkup = ReplyKeyboardMarkup(keyboard=[[HEARTS, DIAMONDS], [SPADES, CLUBS], ['Pass']], one_time_keyboard=True)
            bot.send_message(self.userlist[0].id, self.userlist[0].getCards(), reply_markup=ReplyKeyboardRemove())  
            bot.send_message(self.userlist[0].id, 'Choose the trump suit', reply_markup=suitMarkup)

        elif(self.state == 'TRUMP CALL 1'):
            if(self.trump == 'Pass'):
                for i in range(1, 4):
                    for j in range(5):
                        self.userlist[i].cards.append(self.availableCards[13 * i + j])
                    bot.send_message(self.userlist[i].id, self.userlist[i].getCards(), reply_markup=ReplyKeyboardRemove())
                self.currPlayer = self.userlist[2]   
                self.state = 'TRUMP CALL 2'
                suitMarkup = ReplyKeyboardMarkup(keyboard=[[HEARTS, DIAMONDS], [SPADES, CLUBS], ['Suit of teammate\'s 7th card']], one_time_keyboard=True)
                bot.send_message(self.userlist[2].id, 'Choose the trump suit', reply_markup=suitMarkup)
            else:
                for i in range(4):
                    for j in range(len(self.userlist[i].cards), 13):
                        self.userlist[i].cards.append(self.availableCards[13 * i + j])
                    bot.send_message(self.userlist[i].id, self.userlist[i].getCards(), reply_markup=ReplyKeyboardRemove())
                    bot.send_message(self.userlist[i].id, 'The trump suit is ' + self.trump)
                self.state = 'ROUNDS'
                self.currPlayer = self.teams[self.callingTeam][0]
                print(self.trump)
        elif(self.state == 'TRUMP CALL 2'):    
            for i in range(4):
                for j in range(5, 13):
                    self.userlist[i].cards.append(self.availableCards[13 * i + j])
                bot.send_message(self.userlist[i].id, self.userlist[i].getCards(), reply_markup=ReplyKeyboardRemove())
            
            if(self.trump == 'Suit of teammate\'s 7th card'):
                self.trump = self.userlist[0].cards[6][3:-1]
            for i in range(4):
                bot.send_message(self.userlist[i].id, 'The trump suit is ' + self.trump)
            self.currPlayer = self.teams[self.callingTeam][0]
            self.state = 'ROUNDS'
            print(self.trump)
        else: 
            pass

def reset(update, context):
    active_games = {}

def helper(update, context):
    update.message.reply_text("Use /newgame to create a game.\nUse \join <gameid> to join a game.")

def start(update, context):
    update.message.reply_text("Welcome to Court Piece")

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def joingame(update, context):
    gameid = "".join(context.args)
    if(gameid in active_games):
        if(active_games[gameid].numPlayers < 4):
            newuser = User(update.message.from_user, update.effective_chat, gameid)
            update.message.reply_text('Joined game successfully. Players in room: \n' + active_games[gameid].getUserList())
            for x in active_games[gameid].userlist:
                update.message.bot.send_message(x.chatid, update.message.from_user.name + ' has joined the game')
            active_games[gameid].addUser(newuser)
            user_game[update.message.from_user.id] = gameid
            if(active_games[gameid].numPlayers == 4):
                active_games[gameid].setTeams(update)
        else:
            update.message.reply_text('Could not join game. Room is full.')
    else:
        update.message.reply_text('Game does not exist. You can create a game using /newgame')

def newgame(update, context):
    gameid = ''.join(random.choices(string.ascii_uppercase, k=5))
    active_games[gameid] = Game(gameid)
    newuser = User(update.message.from_user, update.effective_chat, gameid)
    active_games[gameid].addUser(newuser)
    user_game[update.message.from_user.id] = gameid
    update.message.reply_text('New game created. Ask your friends to join using \"/join ' + gameid + '\"')

def respond(update, context):
    gameid = user_game[update.message.from_user.id]
    if (gameid in active_games):
        gm = active_games[gameid]
        gm.respond(update, context)
    else:
        update.message.reply_text('Invalid option. Please create or join a game')

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    bot = updater.bot
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('newgame', newgame))
    updater.dispatcher.add_handler(CommandHandler('join', joingame))
    updater.dispatcher.add_handler(CommandHandler('help', helper))
    updater.dispatcher.add_handler(CommandHandler('reset', reset))
    updater.dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), respond))
    updater.dispatcher.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
