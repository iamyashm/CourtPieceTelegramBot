import os
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ForceReply, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import logging
import string
import random
import ujson
from emoji import emojize
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from dotenv import load_dotenv

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
MODE = os.getenv("MODE")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
HEARTS = emojize(":hearts:", use_aliases=True)
CLUBS = emojize(":clubs:", use_aliases=True)
DIAMONDS = emojize(":diamonds:", use_aliases=True)
SPADES = emojize(":spades:", use_aliases=True)

SUITS = [HEARTS, CLUBS, DIAMONDS, SPADES]

DECK = []
vals = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

for i in range(52):
    DECK.append(vals[i % 13] + ' ' +  SUITS[i // 13])

active_games = {}
user_game = {}
bot = telegram.Bot(BOT_TOKEN)

if (MODE == "dev"):
    def run(updater):
        updater.start_polling()
        updater.idle()
elif (MODE == "deploy"):
    def run(updater):
        PORT = int(os.getenv("PORT", "8443"))
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=BOT_TOKEN)
        updater.bot.set_webhook("https://court-piece-bot.herokuapp.com/" + BOT_TOKEN)
        updater.idle()
else:
    logger.error("No mode specified")
    sys.exit(1)

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
            c += 1
            if (c % 4 == 0):
                res += x + '\n'
            else:
                res += x + '  |  '
        
        return res

    def removeCard(self, card):
        self.cards.remove(card)

    def getCardKeyboard(self):
        keys = []
        row = []
        for i in range(min(5, len(self.cards))):
            row.append(self.cards[i])
        keys.append(row)
        row = []
        for i in range(5, min(9, len(self.cards))):
            row.append(self.cards[i])
        keys.append(row)
        row = []
        for i in range(9, min(13, len(self.cards))):
            row.append(self.cards[i])
        keys.append(row)

        return ReplyKeyboardMarkup(keyboard=keys, one_time_keyboard = True)
    
    def cardOrder(self, x):
        v, s = active_games[self.gameid].parseCard(x)
        return s, v

    def sortCards(self):
        self.cards.sort(key=self.cardOrder)

    def hasCardOfSuit(self, suit):
        for x in self.cards:
            _, s = active_games[self.gameid].parseCard(x)
            if(s == suit):
                return True
        return False

class Game:
    def __init__(self, gameid):
        self.userlist = []
        self.gameid = gameid
        self.numPlayers = 0
        self.gameNo = 1
        self.roundNo = 0
        self.gameScores = {'1': 0, '2': 0}
        self.scores = {'1':0, '2':0}
        self.teams = {'1': None, '2': None}
        self.state = 'SETUP'
        self.playerIdx = -1
        self.availableCards = DECK
        self.trump = None
        self.currPlayer = None
        self.roundParams = {'First Player': None, 'Suit': None, 'Highest Card': None, 'Highest Player': None, 'Turn Count': 0, 'Current Player': None, 'Messages': None} 
        self.lastWinner = None
    
    def playAgain(self):
        for u in self.userlist:
            u.cards = []
            bot.send_message(u.id, 'Starting new game....', reply_markup=ReplyKeyboardRemove())
        self.roundNo = 0
        self.gameNo += 1
        self.scores = {'1': 0, '2': 0}
        self.state = 'SETUP'
        self.trump = None
        self.roundParams = {'First Player': None, 'Suit': None, 'Highest Card': None, 'Highest Player': None, 'Turn Count': 0, 'Current Player': None, 'Messages': None} 
        self.dealCards()

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
   
    def getGameInfo(self):
        if(self.gameNo == 1 and self.roundNo < 1):
            return 'Game has not started'
        else:
            data = ''
            data += 'Current Game: ' + str(self.gameNo) + '\n\n'
            data += 'Current Round: ' + str(self.roundNo) + '\n\n'
            data += 'Round wins (current game):\nTeam 1: ' + str(self.scores['1']) + '    Team 2: ' + str(self.scores['2']) + '\n\n'
            data += 'Total Game wins:\nTeam 1: ' + str(self.gameScores['1']) + '    Team 2: ' + str(self.gameScores['2']) + '\n\n'
            data += 'Trump Card: ' + self.trump + '\n'
            return data

    def setTeams(self, update, flag = 0):
        if(flag == 0):
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

    def parseCard(self, card):
        v = -1
        s = ''
        if(card[1] == ' '):
            v = card[0]
            s = card[2:]
        else:
            v = card[0:2]
            s = card[3:]
        if(v == 'J'):
            v = '11'
        if(v == 'Q'):
            v = '12'
        if(v == 'K'):
            v = '13'
        if(v == 'A'):
            v = '14'
        return int(v), s
    
    def compareCards(self, a, b):
        val1, suit1 = self.parseCard(a)
        val2, suit2 = self.parseCard(b)
        if(suit1 == suit2):
            if(val1 > val2):
                return 1
            elif(val1 == val2):
                return 0
            else:
                return -1
        else:
            if(self.trump == suit1):
                return 1
            elif(self.trump == suit2):
                return -1
            else:
                return -1
    
    def validateMove(self, card):

        #Player does not have card
        if(card not in self.currPlayer.cards):
            return False

        val, suit = self.parseCard(card)
        #Player playing card of illegal suit
        if(self.roundParams['Suit'] != None and (suit != self.roundParams['Suit'] and self.currPlayer.hasCardOfSuit(self.roundParams['Suit']))):
            return False

        return True

    def respond(self, update, context):
        if(self.currPlayer.id == update.message.from_user.id):
            f = 0
            if(self.state == 'SETUP'):
                if(update.message.text == 'Team 1' or update.message.text == 'Team 2'):
                    if(len(self.teams[update.message.text[5]]) < 2):
                        self.teams[update.message.text[5]].append(self.userlist[self.playerIdx])
                        self.userlist[self.playerIdx].team = update.message.text[5]
                    else:
                        update.message.reply_text('Team is full.')
                        f = 1
                else:
                    f = 1
                    update.message.reply_text('Invalid choice')
                self.setTeams(update, f)
            
            elif(self.state == 'TRUMP CALL 1' or self.state == 'TRUMP CALL 2'):
                if(update.message.text in SUITS or (self.state == 'TRUMP CALL 1' and  update.message.text == 'Pass') or (self.state == 'TRUMP CALL 2' and update.message.text == 'Suit of teammate\'s 7th card')):
                    self.trump = update.message.text
                    index, name = 0, ""
                    for i in range(4):
                        if self.userlist[i].id==update.message.from_user.id:
                            index, name = i, self.userlist[i].name
                            break
                    if self.trump=='Pass':
                        for i in range(4):
                            if i!=index:
                                bot.send_message(self.userlist[i].id, name + " has passed the Trump Suit selection to their teammate!" , reply_markup=ReplyKeyboardRemove())
                    elif self.trump=='Suit of teammate\'s 7th card':
                        for i in range(4):
                            if i!=index:
                                bot.send_message(self.userlist[i].id, name + " has passed the Trump Suit selection! Their teammate's 7th card will be the Trump Suit." , reply_markup=ReplyKeyboardRemove())
                    self.dealCards()
                else:
                    if(self.state == 'TRUMP CALL 1'):
                        option = 'Pass'
                    else:
                        option = 'Suit of teammate\'s 7th card'
                    suitMarkup = ReplyKeyboardMarkup(keyboard=[[HEARTS, DIAMONDS], [SPADES, CLUBS], [option]], one_time_keyboard=True)
                    update.message.reply_text('Invalid choice. Try again.', reply_markup=suitMarkup)
            
            elif (self.state == 'ROUNDS'):
                val, suit = self.parseCard(update.message.text)
                
                #add validation for card here
                if(self.validateMove(update.message.text) == False):
                    bot.send_message(self.currPlayer.id, 'Invalid move, please try again.', reply_markup=self.currPlayer.getCardKeyboard())
                
                else:
                    self.currPlayer.removeCard(update.message.text)
                    if(self.roundParams['Turn Count'] == 1):
                        self.roundParams['Suit'] = suit
                        self.roundParams['Highest Card'] = update.message.text
                        self.roundParams['Highest Player'] = self.roundParams['Current Player']
                    
                    else:
                        highval, highsuit = self.parseCard(self.roundParams['Highest Card'])
                        if(self.compareCards(update.message.text, self.roundParams['Highest Card']) == 1 ):
                            self.roundParams['Highest Card'] = update.message.text
                            self.roundParams['Highest Player'] = self.roundParams['Current Player']
                        
                    for i in range(4):
                        if (i != self.roundParams['Current Player']):
                            mess = bot.send_message(self.userlist[i].id, self.currPlayer.name + ' played ' + update.message.text)
                            self.roundParams['Messages'].append(mess)
                    self.roundParams['Turn Count'] += 1
                    self.roundParams['Current Player'] = (self.roundParams['Current Player'] + 1) % 4
                    self.currPlayer = self.userlist[self.roundParams['Current Player']]
                    print(self.roundParams)
                    self.beginRound()
            elif(self.state == 'GAMEOVER'):
                if(update.message.text == 'Yes'):
                    self.playAgain()
                elif(update.message.text == 'No'):
                    for u in self.userlist:
                        bot.send_message(u.id, 'The host has ended the game', reply_markup=ReplyKeyboardRemove())
                else:
                    update.reply_text('Invalid input')
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
            self.lastWinner = 0

            for j in range(5):
                self.userlist[0].cards.append(self.availableCards[j])               
            self.userlist[0].sortCards()
            suitMarkup = ReplyKeyboardMarkup(keyboard=[[HEARTS, DIAMONDS], [SPADES, CLUBS], ['Pass']], one_time_keyboard=True)
            bot.send_message(self.userlist[0].id, self.userlist[0].getCards(), reply_markup=ReplyKeyboardRemove())  
            bot.send_message(self.userlist[0].id, 'Choose the trump suit:', reply_markup=suitMarkup)

        elif(self.state == 'TRUMP CALL 1'):
            if(self.trump == 'Pass'):
                for i in range(1, 4):
                    for j in range(5):
                        self.userlist[i].cards.append(self.availableCards[13 * i + j])
                    self.userlist[i].sortCards()
                    bot.send_message(self.userlist[i].id, self.userlist[i].getCards(), reply_markup=ReplyKeyboardRemove())
                self.currPlayer = self.userlist[2]   
                self.state = 'TRUMP CALL 2'
                suitMarkup = ReplyKeyboardMarkup(keyboard=[[HEARTS, DIAMONDS], [SPADES, CLUBS], ['Suit of teammate\'s 7th card']], one_time_keyboard=True)
                bot.send_message(self.userlist[2].id, 'Choose the trump suit:', reply_markup=suitMarkup)
            else:
                for i in range(4):
                    for j in range(len(self.userlist[i].cards), 13):
                        self.userlist[i].cards.append(self.availableCards[13 * i + j])
                    self.userlist[i].sortCards()
                    bot.send_message(self.userlist[i].id, self.userlist[i].getCards(), reply_markup=ReplyKeyboardRemove())
                    bot.send_message(self.userlist[i].id, 'The trump suit is ' + self.trump)
                self.state = 'ROUNDS'
                self.currPlayer = self.teams[self.callingTeam][0]
                print(self.trump)
                self.beginRound()
        elif(self.state == 'TRUMP CALL 2'):    
            for i in range(4):
                for j in range(5, 13):
                    self.userlist[i].cards.append(self.availableCards[13 * i + j])
            
            if(self.trump == 'Suit of teammate\'s 7th card'):
                card = self.userlist[0].cards[6]
                if(card[1] == ' '):
                    self.trump = card[2:]
                else:
                    self.trump = card[3:]
            for i in range(4):
                self.userlist[i].sortCards()
                bot.send_message(self.userlist[i].id, self.userlist[i].getCards(), reply_markup=ReplyKeyboardRemove())
                bot.send_message(self.userlist[i].id, 'The trump suit is ' + self.trump)
            
            self.currPlayer = self.teams[self.callingTeam][0]
            self.state = 'ROUNDS'
            print(self.trump)
            self.beginRound()
        else: 
            pass
    
    def beginRound(self):
        
        #setting up round
        if(self.roundParams['Turn Count'] == 0):
            self.roundNo += 1
            print('Round starting')
            for i in range(4):
                bot.send_message(self.userlist[i].id, '------------------- ROUND ' + str(self.roundNo) + ' -------------------', reply_markup = ReplyKeyboardRemove()) 
            self.roundParams['First Player'] = self.lastWinner
            self.roundParams['Current Player'] = self.lastWinner
            self.roundParams['Turn Count'] = 1
            self.roundParams['Suit'] = None
            if(self.roundParams['Messages'] != None):
                for m in self.roundParams['Messages']:
                    bot.delete_message(chat_id = m.chat_id, message_id = m.message_id)
            self.roundParams['Messages'] = []
            self.currPlayer = self.userlist[self.lastWinner]
            bot.send_message(self.currPlayer.id, 'You are starting the round. Play a card.', reply_markup = self.currPlayer.getCardKeyboard())
        
        #after all 4 turns
        elif(self.roundParams['Turn Count'] == 5):
            self.lastWinner = self.roundParams['Highest Player']
            self.roundParams['Turn Count'] = 0
            self.scores[self.userlist[self.lastWinner].team] += 1
            for i in range(4):
                bot.send_message(self.userlist[i].id, self.userlist[self.lastWinner].name + ' (Team ' + self.userlist[self.lastWinner].team + ')' +' wins this round', reply_markup = ReplyKeyboardRemove())
                bot.send_message(self.userlist[i].id, 'Team scores\nTeam 1: ' + str(self.scores['1']) + '\nTeam 2: ' + str(self.scores['2']))
            if(self.scores['1'] == 7 or self.scores['2'] == 7):
                winteam = ''
                if(self.scores['1'] == 7):
                    self.gameScores['1'] += 1
                    winteam = 'Team 1'
                else:
                    self.gameScores['2'] += 1
                    winteam = 'Team 2'
                for i in range(4):
                    bot.send_message(self.userlist[i].id, emojize(winteam + ' wins the game! :tada:', use_aliases=True), reply_markup=ReplyKeyboardRemove())
                self.state = 'GAMEOVER'
                yesno = ReplyKeyboardMarkup(keyboard=[['Yes', 'No']], one_time_keyboard = True)
                bot.send_message(self.host.id, 'Do you want to play another game?', reply_markup=yesno)
                self.currPlayer = self.host
                return
            else:
                self.beginRound()
        
        #mid round
        else:
            bot.send_message(self.currPlayer.id, 'It\'s your turn. Play a card', reply_markup = self.currPlayer.getCardKeyboard())



def reset(update, context):
    if(update.message.from_user.id == ADMIN_ID):
        active_games.clear()
        user_game.clear()
        update.message.reply_text('Game list cleared.')
    else:
        update.message.reply_text('Unauthorized.')

def about(update, context):
    update.message.reply_text('Court Piece Bot made by Yash Maniramka and Yashvardhan Jain. Contact @iamyashm7 for reporting bugs, feedback and suggestions.')

def helper(update, context):
    update.message.reply_text("Use /newgame to create a game.\nUse /join <gameid> to join a game.\nUse /gameinfo to get details of current game (scores, trump card, round number, etc)\nUse /endgame to end current game\nUse /about to get info about bot.")

def start(update, context):
    update.message.reply_text("Welcome to Court Piece. Use /help to get a list of available commands.")

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def joingame(update, context):
    if((update.message.from_user.id in user_game) and (update.message.from_user.id != ADMIN_ID)):
        update.message.reply_text('Could not join. Already in a game.')
    else:
        gameid = "".join(context.args)
        if(gameid in active_games):
            if(active_games[gameid].numPlayers < 4):
                newuser = User(update.message.from_user, update.effective_chat, gameid)
                update.message.reply_text('Joined game successfully. Players in room: \n' + active_games[gameid].getUserList(), reply_markup=ReplyKeyboardRemove())
                for x in active_games[gameid].userlist:
                    update.message.bot.send_message(x.chatid, update.message.from_user.name + ' has joined the game')
                active_games[gameid].addUser(newuser)
                user_game[update.message.from_user.id] = gameid
                if(active_games[gameid].numPlayers == 4):
                    active_games[gameid].setTeams(update)
            else:
                update.message.reply_text('Could not join game. Room is full.')
        else:
            update.message.reply_text('Game does not exist. You can create a game using /newgame.')

def newgame(update, context):
    if(len(active_games) > 2):
        update.message.reply_text('Server limit reached. Try again later.')
    else:
        gameid = ''.join(random.choices(string.ascii_uppercase, k=5))
        active_games[gameid] = Game(gameid)
        newuser = User(update.message.from_user, update.effective_chat, gameid)
        active_games[gameid].addUser(newuser)
        user_game[update.message.from_user.id] = gameid
        update.message.reply_text('New game created. Ask your friends to join using \"/join ' + gameid + '\"', reply_markup=ReplyKeyboardRemove())

def respond(update, context):
    if(update.message.from_user.id in user_game):
        gameid = user_game[update.message.from_user.id]
        gm = active_games[gameid]
        gm.respond(update, context)
    else:
        update.message.reply_text('Invalid option. Please create or join a game. Use /help to see a list of commands.')

def gameinfo(update, context):
    if(update.message.from_user.id in user_game):
        gameid = user_game[update.message.from_user.id]
        update.message.reply_text(active_games[gameid].getGameInfo(), reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text('Please create or join a game first.')

def endgame(update, context):
    if(update.message.from_user.id in user_game):
        gameid = user_game[update.message.from_user.id]
        gm = active_games[gameid]
        if(update.message.from_user.id == gm.host.id):
            for u in gm.userlist:
                bot.send_message(u.id, 'The host has ended the game.', reply_markup=ReplyKeyboardRemove())
            del active_games[gameid]
            del user_game[update.message.from_user.id]
        else:
            update.message.reply_text('Unauthorized. Only host can end game.')
    else:
        update.message.reply_text('No active game.')

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('newgame', newgame))
    updater.dispatcher.add_handler(CommandHandler('join', joingame))
    updater.dispatcher.add_handler(CommandHandler('help', helper))
    updater.dispatcher.add_handler(CommandHandler('reset', reset))
    updater.dispatcher.add_handler(CommandHandler('gameinfo', gameinfo))
    updater.dispatcher.add_handler(CommandHandler('endgame', endgame))
    updater.dispatcher.add_handler(CommandHandler('about', about))
    updater.dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), respond))
    updater.dispatcher.add_error_handler(error)

    run(updater)

if __name__ == '__main__':
    main()
