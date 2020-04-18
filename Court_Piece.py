from Extract_JSON import getJSON
import random

class Court_Piece:

    def __init__(self, uid):
        self.uid = uid
        self.players = dict()
        self.score_count = []
        self.win_count = []
        self.all_cards = getJSON("Cards_Deck")
        self.cards_left = getJSON("Cards_Deck")
        self.trump_suit = ""
        self.rounds = {
            "No" : 0,
            "Team A" : 0,
            "Team B" : 0,
            "suit" : "",
            "cards" : []
        }
        # super().__init__()

    def format_player_card(self, player_id, suit, value):
        data = {
            "player_id" : player_id,
            "card" : {
                "suit" : suit,
                "value" : value
            }
        }
        return data

    def add_player(self, player_id):
        # player_data = dict()
        # player_data["player_id"] = player_id
        # player_data["cards"] = []
        # player_data["winning_hands"] = 0
        # player_data["team"] = ""
        # self.players.append(player_data)
        self.players[player_id] = dict()
        self.players[player_id]["cards"] = []
        self.players[player_id]["winning_hands"] = 0
        self.players[player_id]["team"] = ""

    def set_team(self, player_id, team):
        if team.lower()=="a":
            self.players[player_id]["team"] = "Team A"
        else:
            self.players[player_id]["team"] = "Team B"
    def set_trump_suit(self, suit):
        self.trump_suit = suit

    def random_card(self):
        card = random.randrange(0, len(self.cards_left))
        card = self.cards_left.pop(card)
        return card

    def one_deal(self, player_id, no_of_cards):
        deal = []
        for i in range(no_of_cards):
            card = self.random_card()
            deal.append(card)
            self.players[player_id]["cards"].append(card)
        return deal
    
    def remove_card(self, player_id, card):
        i = -1
        for j in range(len(self.players[player_id]["cards"])):
            if self.players[player_id]["cards"][j]["suit"]==card["suit"] and self.players[player_id]["cards"][j]["value"]==card["value"]:
                i = j
                break
        if i!=-1:
            del self.players[player_id]["cards"][i]
            return True
        else:
            return False


    def check_round(self):
        winner = 0
        for i in range(4):
            if self.rounds["cards"][i]["card"]["suit"]==self.rounds["suit"]:
                if self.rounds["cards"][i]["card"]["value"]>self.rounds["cards"][winner]["card"]["value"]:
                    winner = i
            elif self.rounds["suit"]!=self.trump_suit and self.rounds["cards"][i]["card"]["suit"]==self.trump_suit:
                suit = self.trump_suit
                winner = i
        self.players[self.rounds["cards"][i]["player_id"]]["winning_hands"]+=1
        self.rounds["No"] += 1
        self.rounds[self.players[self.rounds["cards"][i]["player_id"]]["team"]] +=1
        return self.rounds["cards"][i]["player_id"]

    def check_chance(self, player_id, suit, value, first_chance):
        chance_data = self.format_player_card(player_id, suit, value)
        if first_chance:
            self.rounds["suit"] = chance_data["card"]["suit"]
            self.rounds["cards"] = []
            self.rounds["cards"].append(chance_data)
            return self.remove_card(chance_data["player_id"], chance_data["card"])
        else:
            if chance_data["card"]["suit"]!=self.rounds["suit"]:
                for i in self.players[chance_data["player_id"]]["cards"]:
                    if i["suit"]==self.rounds["suit"]:
                        return False
            self.rounds["cards"].append(chance_data)
            return self.remove_card(chance_data["player_id"], chance_data["card"])

    def check_winner(self):
        if self.rounds["Team A"]>=7:
            return "Team A"
        elif self.rounds["Team B"]>=7:
            return "Team B"
        else:
            return False

    def cards_in_hand(self, player_id):
        return self.players[player_id]["cards"]

