import numpy as np
import random
import warnings

import discord
import time
import random
from discord.ext import tasks
client = discord.Client()

games_en_cours = {}



with open("token.txt","r") as f:
    token = f.readline().replace("\n","")


class Puissance4():
    def __init__(self, shape=(6, 7)):
        self.grille = np.zeros(shape)

    def get_plateau(self):
        return self.grille

    def get_column(self, nb_column):
        column = []
        for ligne in self.grille:
            column.append(ligne[nb_column])
        return column

    def get_all_diag(self):
        diagonales = []
        for x in range(0 - self.grille.shape[0] + 1, self.grille.shape[1]):
            diagonales.append(np.diag(self.grille, k=x))
            diagonales.append(np.diag(np.fliplr(self.grille), k=x))
        return diagonales

    def get_all_columns(self):
        columns = []
        for x in range(self.grille.shape[1]):
            columns.append(self.get_column( x))
        return columns

    def insert_column(self, nb_column, value):
        a = 0
        for ligne in self.grille:
            ligne[nb_column] = value[a]
            self.grille[a] = ligne
            a += 1

    def check_victory(self):
        list_combinaison = self.get_all_columns()

        for s in self.get_all_diag():
            list_combinaison.append(s)
        for s in self.grille:
            list_combinaison.append(s)
        for liste in list_combinaison:
            last_val = 0
            nb = 1
            for val in liste:
                if last_val == val and val != 0:
                    nb += 1
                else:
                    nb = 1
                if nb >= 4:
                    return True, last_val
                last_val = int(val)
        return False, 0

    def add_pion(self, nb_column, pion_value=1):
        base_column = self.get_column(nb_column)
        out_column = np.copy(base_column)
        if base_column[-1] == 0: #si c'est le premier pion
            out_column[-1] = pion_value
            self.insert_column(nb_column, out_column)
            return True
        if base_column[0] != 0:
            return False
        for index, value in enumerate(base_column):
            if value != 0:
                if index == 0:
                    return False
                else:
                    out_column[index - 1] = pion_value
                    break
        self.insert_column(nb_column, out_column)
        return True


class Game():
    def __init__(self, playersID, shape=(6, 7), name="base"):
        self.playersID = playersID
        self.game = Puissance4(shape)
        self.shape = shape
        self.name = name
        self.last_played = 0

    def get_game(self):
        return self.game.get_plateau()

    def jouer(self, id, column):
        if id not in self.playersID:
            return "Tu N'est pas inscris dans cette partie"

        if id != self.playersID[self.last_played]:
            return "Ce n'est pas ton tour, le tour de <@{}>".format(self.playersID[self.last_played])

        pion_value = 0
        for n, pID in enumerate(self.playersID):
            if pID == id:
                pion_value = n + 1
        if self.game.add_pion(column, pion_value):
            if len(self.playersID)-1 == self.last_played:
                self.last_played = 0
            else:
                self.last_played +=1
            return ""
        else:
            return "<@{}> La colone est pleine, rejout".format(self.playersID[self.last_played])
    def check_winner(self):
        r = self.game.check_victory()
        vainqueur = "A <@{}>".format(self.playersID[self.last_played])
        if r[0]:
            vainqueur = self.playersID[r[1]-1]
        return r[0], vainqueur



def get_mention_in_text(text):
    list_mention = []
    open = 0
    taille = len(text)
    for index, lettre in enumerate(text):
        if lettre == "<" and open == 0:
            if index != taille:
                if text[index + 1] == "@" and text[index + 2] == "!":
                    open = index + 3
        if lettre == ">" and open > 0:
            list_mention.append(int(text[open:index]))
            open = 0
    return list_mention

def supprime_game(nom):
    try:
        del games_en_cours[nom]
        return True
    except:
        return False


async def affiche_game(chanel, game):
    couleurs = "⚪🔵🔴🟢🟣🟡🟤⚫"
    jeux_z = np.array(game.get_game()).reshape(game.shape[0]*game.shape[1]).astype(int)
    result_array = jeux_z.copy().astype(str)
    for x in enumerate(couleurs):
        result_array = np.where(jeux_z == int(x[0]), x[1], result_array)
    result_array= result_array.reshape(game.shape[0],game.shape[1])
    result_text = ""
    for ligne in result_array:
        result_text += "".join(ligne.tolist())
        result_text +="\n"
    result_text += "1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣"
    await chanel.send(result_text)




import time

last_leaderboard = 1




@client.event
async def on_message(message):
    if message.author.bot:
        return
    if len(message.content) == 2:
        return
    global games_en_cours
    split_message = message.content.split()
    mention = get_mention_in_text(message.content)
    joueur = message.author.id
    responce = " "
    repondre = True

    if split_message[0] == "*newx4":
        # Cree une game
        name_game = split_message[1]
        nom_free = True
        try:
            games_en_cours[name_game]
            nom_free = False
            responce += " Le nom n'est pas disponible "
        except:
            pass

        if nom_free and len(mention) > 1:
            game = Game(mention)
            games_en_cours[name_game] = game
            responce += " Game créé sous le nom de {} avec {} joueurs ".format(
                name_game, len(mention))
            await affiche_game(message.channel, game)

    elif split_message[0] == "*play":
        # jouer sur une game en cours
        nom_bon = True
        name_game = split_message[1]
        columns_bon = True
        try:
            game = games_en_cours[name_game]
        except:
            nom_bon = False
            responce += " Le nom de la Game est incorrect "
        try:
            columns_to_play = int(split_message[2])-1
            if columns_to_play-1 > game.shape[1]:
                columns_bon = False
        except:
            columns_bon = False
            responce += " La column rentrée est incorrect "

        if nom_bon + columns_bon == 2:
            messageE = game.jouer(joueur, columns_to_play)
            await affiche_game(message.channel, game)

            responce += messageE
            e = game.check_winner()
            if e[0]:
                responce += "Gagnant <@{}> !!  \n".format(str(e[1]))
                if supprime_game( name_game):
                    responce += "Game supprimée"


    elif split_message[0] == "*resume":
        nom_bon = True
        name_game = split_message[1]
        try:
            game = games_en_cours[name_game]
        except:
            nom_bon = False
            responce += " Le nom de la Game est incorrect "

        if nom_bon:
            await affiche_game(message.channel, game)

    elif split_message[0] == "*destroy":
        nom_bon = True
        name_game = split_message[1]
        try:
            game = games_en_cours[name_game]
        except:
            nom_bon = False
            responce += " Le nom de la Game est incorrect "

        if nom_bon:
            if supprime_game( name_game):
                responce += "Game supprimée"

    else:
        repondre = False
    if repondre:
        if len(responce)> 1:
            await message.channel.send(responce)




a = np.array([1,3,4,3,5])
b = np.array([1,4,2,3,6])
a ==b
sum(a == b)





@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run(token)
#
