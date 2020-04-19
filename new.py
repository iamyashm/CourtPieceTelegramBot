def dealCards(self):
    random.shuffle(self.availableCards)
    if self.trumpSuit==None:
        for j in range(5):
            self.userlist[0].cards.append(self.availableCards[13*0 + j])
        bot.send_message(self.userlist[0].id, self.userlist[0].getCards(), reply_markup=ReplyKeyboardRemove())
        bot.send_message(self.userlist[0].id, "Enter the Trump Suit or Enter Pass", reply_markup=ReplyKeyboardRemove())
    elif self.trumpSuit=="Pass":
        for i in range(1, 4):
            for j in range(5):
                self.userlist[i].cards.append(self.availableCards[13*i + j])
            bot.send_message(self.userlist[i].id, self.userlist[i].getCards(), reply_markup=ReplyKeyboardRemove())
        bot.send_message(self.userlist[3].id, "Enter the Trump Suit or Select Partner's 7th Card's Suit", reply_markup=ReplyKeyboardRemove())    
    elif self.trumpSuit=="7th":
        for j in range(5):
            self.userlist[0].cards.append(self.availableCards[13*0 + j])
            if j==1:
                self.trumpSuit = self.userlist[0].cards[-1][-1]
        bot.send_message(self.userlist[0].id, self.userlist[0].getCards(), reply_markup=ReplyKeyboardRemove())
        for i in range(4):
            bot.send_message(self.userlist[i].id, "The Trump Suit is " + self.trumpSuit , reply_markup=ReplyKeyboardRemove())
        self.dealCards()
    else:
        for i in range(4):
            random.shuffle(self.availableCards)
            for j in range(13-len(self.userlist[i].cards)):
                self.userlist[i].cards.append(self.availableCards[13*i + j])
            bot.send_message(self.userlist[i].id, self.userlist[i].getCards(), reply_markup=ReplyKeyboardRemove()) 