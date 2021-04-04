import asyncio
import datetime
import json
import logging
import os
import random
from dotenv import load_dotenv
import pymorphy2 as pymorphy2
import requests
from pip._vendor import requests
from twitchio import WebhookMode
from twitchio.ext import commands
from twitchio.webhook import StreamChanged

from dbConnector import dbConnector

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(module)s %(name)s.%(funcName)s +%(lineno)s: %(levelname)-8s [%(process)d] '
                           '%(message)s',
                    )


class Bot(commands.Bot):
    def __init__(self, irc_token, nick, client_id='test', client_secret='', api_key='', bearer='', initial_channels=None,
                 external_host="",
                 port=4040,
                 webhook_server=False,
                 callback=""
                 ):
        self.bearer = bearer
        self.token = irc_token
        self.client_id = client_id
        if initial_channels is None:
            initial_channels = []
        self.external_host = external_host
        self.callback = callback
        params = {
            'irc_token': irc_token,
            'client_id': client_id,
            'api_token': api_key,
            'client_secret': client_secret,
            'nick': nick,
            'prefix': '!',
            'initial_channels': ['#pu1se0'],
            # 'local_host': "http://localhost:9",
            'external_host': self.external_host,
            'port': port,
            'webhook_server': True,
            'callback': callback
        }
        super().__init__(**params)
        db_password = os.getenv('DB_PASSWORD')
        self.db = dbConnector(db_password)
        nicknames = self.db.getAllLeftPersons([])
        for nickname in nicknames:
            self.calcTimeCount(nickname[0])
            self.calcPills(nickname[0])
            self.db.setLastTimeIn(nickname, None)
        self.log = logging
        self.streamLive = False
        self.streamInfo = None
        self.streamId = None
        self.bots = self.db.getBots()
        self.morph = pymorphy2.MorphAnalyzer()

    async def userTime(self, channel, ws):
        while True:
            if self.streamLive:
                try:
                    r = requests.get(f"http://tmi.twitch.tv/group/user/{channel}/chatters")
                    res = json.loads(r.text)
                    chatters = res['chatters']
                    logging.info(res)
                    allViewers = chatters['vips'] + chatters['moderators'] + chatters['viewers'] + chatters[
                        'broadcaster']
                    # print(allViewers)
                    for person in allViewers:
                        if person not in self.bots:
                            if self.db.isUserNew(person):
                                self.createNewUser(person)
                                await ws.send_privmsg(os.environ['CHANNEL'],
                                                      f"Привет, {person}! Мы рады, что ты наш больной! "
                                                      f"Используй команду !help, чтобы познакомиться с нами поближе.")
                            timeIn = self.db.getLastTimeIn(person)
                            if timeIn is None:
                                self.db.setLastTimeIn(person, datetime.datetime.now())
                    leftUsers = self.db.getAllLeftPersons(allViewers)
                    for user in leftUsers:
                        nickname = user[0]
                        self.calcTimeCount(nickname)
                        self.calcPills(nickname)
                        self.db.setLastTimeIn(nickname, None)
                except Exception as e:
                    logging.critical(f"Ошибка получения списка пользователей: {str(e)}")
                silenceUsers = self.db.getSilenceUsers(20)
                for user in silenceUsers:
                    self.db.addEnergy(user, -1)
                    self.db.setLastMessage(user, datetime.datetime.now())
                self.db.deleteOldTrades(10)
                if self.db.isTimeChangeShop(15):
                    self.changeShop()
                lastRaidsTime = self.db.getLastRaidsTime()
                if lastRaidsTime is None:
                    self.db.createRaidTime()
                else:
                    streamTime = self.getStreamTime(lastRaidsTime, datetime.datetime.now()).total_seconds()
                    if self.db.isRaidTime():
                        if streamTime / 60 >= 30:
                            self.db.setRaidsTime(False)
                            self.db.deleteNotReadyParties()
                            await ws.send_privmsg(os.environ['CHANNEL'], "/me Наступило утро, и снова началась "
                                                                         "размеренная жизнь. Команда !raid заблокированна, "
                                                                         "все не отправленные группы расформированны.")
                    else:
                        if streamTime / 60 >= 60:
                            self.db.setRaidsTime(True)
                            await ws.send_privmsg(os.environ['CHANNEL'], "/me Наступила ночь! "
                                                                         "Самое время немного подебоширить! "
                                                                         "Используй команду !raid, чтобы начать")
            await asyncio.sleep(60)

    def calcTimeCount(self, nickname):
        timeCount = self.db.getTimeCount(nickname)  # in minutes
        timeIn = self.db.getLastTimeIn(nickname)  # datetime
        timeOut = datetime.datetime.now()  # datetime
        diff = timeOut - timeIn
        minutes = int(diff.total_seconds() / 60)
        timeCount += minutes
        self.db.setTimeCount(nickname, timeCount)

    def calcPills(self, nickname):
        pills = self.getPills(nickname)
        print(pills)
        self.db.setPills(nickname, pills)

    async def event_ready(self):
        await self.modify_webhook_subscription(
            callback=self.external_host + '/' + self.callback,
            mode=WebhookMode.subscribe,
            topic=StreamChanged(user_id=81294161),
            lease_seconds=60 * 60 * 24,
        )
        headers = {'Authorization': "Bearer " + str(self.bearer), 'Client-ID': self.client_id}
        r = requests.get('https://api.twitch.tv/helix/webhooks/subscriptions',
                         headers=headers)
        print(r.text)
        ws = bot._ws

        await asyncio.gather(*[self.userTime(initial_channels[0][1:], ws), self.raidTime(ws)])

    async def raidTime(self, ws):
        while True:
            endedRaids = self.db.getEndedRaids()
            print("Законченные рейды:", endedRaids)
            if endedRaids is not None:
                for partyId in endedRaids:
                    await self.calculateRaidResult(partyId[0], ws)
            await asyncio.sleep(60)

    async def calculateRaidResult(self, partyId, ws):
        partyInfo = list(self.db.getRaidPartyInformation(partyId))
        raidInfo = self.db.getRaidInformation(partyInfo[7])
        playersStats = []
        for i in range(1, 5):
            if partyInfo[i] is None:
                break
            playerInfo = [partyInfo[i]] + list(self.calculateUserStats(partyInfo[i]))
            playersStats.append(playerInfo)
        teamPA = 0
        for player in playersStats:
            teamPA += player[2]
        # if teamPA >= raidInfo[2] - 1:
        if raidInfo[2] == 1 and teamPA == 0:
            prop = 0.5
        else:
            prop = teamPA / ((raidInfo[2]) * 2)
        res = random.choices([False, True], [1 - prop, prop])[0]
        if not res:
            await self.loseRaid(ws, partyInfo, raidInfo, playersStats)
        else:
            await self.winRaid(ws, partyInfo, raidInfo, playersStats)
        self.db.addEnergy(partyInfo[1], 5)
        for i in range(2, 5):
            if partyInfo[i] is None:
                break
            self.db.addEnergy(partyInfo[i], 3)
        for i in range(1, 5):
            if partyInfo[i] is None:
                break
            self.db.increaseRaids(partyInfo[i])
        # else:
        #     await self.loseRaid(ws, partyInfo, raidInfo, playersStats)
        self.changeCurrentFragility(partyInfo)

    async def loseRaid(self, ws, partyInfo, raidInfo, playersStats):
        playerNames = ["" for i in range(0, 4)]
        for i in range(1, 5):
            playerNames[i - 1] = self.db.getNicknameByUserId(partyInfo[i])
        if partyInfo[5] == 4:
            message = f"C возвращением, {playerNames[0]}, {playerNames[1]}, {playerNames[2]} и {playerNames[3]}!" \
                      f" Слава богу, что вы успели унести оттуда ноги." \
                      f" Вы ничего не успели прихватить из локации {raidInfo[0]}." \
                      f" Пора посидеть и немного подлатать раны."
        elif partyInfo[5] == 3:
            message = f"C возвращением, {playerNames[0]}, {playerNames[1]} и {playerNames[2]}!" \
                      f" Слава богу, что вы успели унести оттуда ноги." \
                      f" Вы ничего не успели прихватить из локации {raidInfo[0]}." \
                      f" Пора посидеть и немного подлатать раны."
        elif partyInfo[5] == 2:
            message = f"C возвращением, {playerNames[0]} и {playerNames[1]}!" \
                      f" Слава богу, что вы успели унести оттуда ноги." \
                      f" Вы ничего не успели прихватить из локации {raidInfo[0]}." \
                      f" Пора посидеть и немного подлатать раны."
        else:
            message = f"C возвращением, {playerNames[0]}! Слава богу, что ты успел унести оттуда ноги. " \
                      f"Ты ничего не успел прихватить из локации {raidInfo[0]}." \
                      f" Пора посидеть и немного подлатать раны."
        for player in playersStats:
            self.calculateHpLost(player, raidInfo)
        self.db.deleteRaidParty(partyInfo[0])
        await ws.send_privmsg(os.environ['CHANNEL'], f"/me {message}")

    async def winRaid(self, ws, partyInfo, raidInfo, playersStats):
        playerNames = ["" for i in range(0, 4)]
        for i in range(1, 5):
            playerNames[i - 1] = self.db.getNicknameByUserId(partyInfo[i])
        if partyInfo[5] == 4:
            message = f"C возвращением, {playerNames[0]}, {playerNames[1]}, {playerNames[2]} и {playerNames[3]}!" \
                      f" Вы успешно зачистили локацию \"{raidInfo[0]}\"!" \
                      f" Все вещи, что вы нашли, вы попрятали в свои карманы и нычки." \
                      f" Советую вам перевязать свои раны и снова отправиться в рейды"
        elif partyInfo[5] == 3:
            message = f"C возвращением, {playerNames[0]}, {playerNames[1]} и {playerNames[2]}!" \
                      f" Вы успешно зачистили локацию \"{raidInfo[0]}\"!" \
                      f" Все вещи, что вы нашли, вы попрятали в свои карманы и нычки." \
                      f" Советую вам перевязать свои раны и снова отправиться в рейды"
        elif partyInfo[5] == 2:
            message = f"C возвращением, {playerNames[0]} и {playerNames[1]}!" \
                      f" Вы успешно зачистили локацию \"{raidInfo[0]}\"!" \
                      f" Все вещи, что вы нашли, вы попрятали в свои карманы и нычки." \
                      f" Советую вам перевязать свои раны и снова отправиться в рейды"
        else:
            message = f"C возвращением, {playerNames[0]}!" \
                      f" Ты успешно в одиночку зачистил локацию \"{raidInfo[0]}\"!" \
                      f" Все вещи, что ты нашел, ты уже спрятал в свои карманы и нычки." \
                      f" Советую тебе немного отдохнуть и снова отправиться в рейды"
        for player in playersStats:
            self.calculateHpLost(player, raidInfo)
            # for i in range(0, 10):
            self.calculateLoot(player, raidInfo, partyInfo)
        self.db.deleteRaidParty(partyInfo[0])
        await ws.send_privmsg(os.environ['CHANNEL'], f"/me {message}")
        for player in playersStats:
            if self.db.isRaidLastInTierCert(partyInfo[7]) and self.db.getEnergy(player[0]) >= 200:
                if random.choices([True, False], [0.2, 0.8])[0]:
                    if not self.db.isItemInUserInventory(player[0], 100):
                        self.db.giveItemToUser(player[0], 100, 1)
                        self.db.increaseCerts(player[0])
                        await ws.send_privmsg(os.environ['CHANNEL'], f"/me Поздравляю, {self.db.getNicknameByUserId(player[0])}, "
                                                                     f"Ты получил справку о выздоровлении! "
                                                                     f"Ты настолько всех достал, что тебя хотят выписать! "
                                                                     f"Чтобы выписаться, используй команду !reset")

    def calculateHpLost(self, player, raidInfo):
        prop = int(player[1] / (raidInfo[1] * 2) * 100)
        if prop >= 100:
            return
        minHp = 100 - prop - 15 if 100 - prop - 15 > 0 else 0
        maxHp = 100 - prop + 15 if 100 - prop + 15 < 100 else 100
        hp = random.randint(minHp, maxHp)
        curHp = self.getCurrentHealth(player[0])
        newHp = curHp - hp if curHp - hp > 0 else 0
        self.getTimeWithHp(player[0], newHp)
        # print(hp, curHp, newHp)

    def calculateLoot(self, player, raidInfo, partyInfo):
        countItems = random.choices([0, 1, 2, 3, 4, 5], [0.1, 0.65, 0.2, 0.04, 0.0085, 0.0015])[0]
        raidItems = raidInfo[3]
        items = []
        props = []
        for name, prop in raidItems.items():
            items.append(name)
            props.append(prop)
        summ = 0
        for i in range(0, len(props)):
            if props[i] < 5:
                props[i] *= (player[3] + 1)
            summ += props[i]
        coef = 100/summ
        error = 100
        for i in range(0, len(props)):
            props[i] *= coef
            error -= props[i]
        props[int(len(props) / 2)] += error
        for i in range(0, countItems):
            itemName = random.choices(items, props)[0]
            itemId = self.db.getItemIdByItemName(itemName)
            self.db.giveItemToUser(player[0], itemId, 1)
        pills = self.db.getPillsFromRaid(partyInfo[7])
        username = self.db.getNicknameByUserId(player[0])
        userPills = self.db.getPills(username)
        foundedPills = random.randint(pills[0], pills[1])
        print(userPills, foundedPills)
        self.db.setPills(username, userPills + foundedPills)

    async def event_webhook(self, data):
        try:
            print(data)
            if not data['data'] and self.streamLive:
                self.streamLive = False
                print("STREAM STOPPED")
                self.streamInfo = None
                if self.streamId is not None:
                    self.db.setStreamEnd(self.streamId)
                    self.streamId = None
                else:
                    self.streamId = self.db.getLastStream()
                    self.db.setStreamEnd(self.streamId)
                    self.streamId = None
                nicknames = self.db.getAllLeftPersons([])
                for nickname in nicknames:
                    self.calcTimeCount(nickname[0])
                    self.calcPills(nickname[0])
                    self.db.setLastTimeIn(nickname, None)
            elif data['data'] and not self.streamLive:
                self.streamInfo = data['data'][0]
                print("STREAM STARTED")
                print(data['data'][0]['type'])
                if data['data'][0]['type'] == 'live':
                    self.streamLive = True
                    print(self.streamInfo, self.streamInfo['title'], self.streamInfo['started_at'])
                    hours_added = datetime.timedelta(hours=3)
                    started_at = datetime.datetime.strptime(self.streamInfo['started_at'], '%Y-%m-%dT%H:%M:%SZ')
                    self.streamId = self.db.addStream(self.streamInfo['title'], started_at + hours_added)
                    print(self.streamId)
        except Exception as e:
            print("event_webhook error: " + str(e))

    # bot.py, below bot object
    # async def event_ready(self):
    #     'Called once when the bot goes online.'
    #     print(f"{os.environ['BOT_NICK']} is online!")
    #     ws = bot._ws  # this is only needed to send messages within event_ready
    #     # await ws.send_privmsg(os.environ['CHANNEL'], f"/me has landed!")

    async def event_message(self, ctx):
        commandList = ['!help', '!stats', '!health', '!inj', '!raid', '!startRaid', '!infoRaid',
                       '!exitRaid', '!joinRaid', '!map', '!inv', '!trade', '!cancelTrade',
                       '!shop', '!buy', '!top', '!use', '!unuse', '!drop', '!giveItem', '!weapons',
                       '!clothes', '!info', '!reset', '!authors', '!feedback']
        if ctx.author.name not in self.bots:
            if self.db.isUserNew(ctx.author.name):
                self.createNewUser(ctx.author.name)
                await ctx.channel.send(f"Привет, {ctx.author.name}! Мы рады, что ты наш больной! "
                                       f"Используй команду !help, чтобы познакомиться с нами поближе.")
            self.db.setLastMessage(ctx.author.name, datetime.datetime.now())
            if any(command in ctx.content for command in commandList):
                if self.streamLive: #TODO: Не забыть поменять на обратное значение
                    await self.handle_commands(ctx)
                else:
                    await ctx.channel.send(f'/me Вы почему еще не спите! А ну бегом в кровать, марш!')
                return
            else:
                if self.streamLive:
                    self.db.increaseMessagesCount(ctx.author.name)
                    messagesCount = self.db.getMessagesCount(ctx.author.name)
                    if messagesCount % 20 == 0:
                        self.db.addEnergy(ctx.author.name, 1)

    @commands.command(name='help')
    async def my_command(self, ctx):
        await ctx.send(f'/me Привет, {ctx.author.name}!'
                       f' Инструкция: https://drive.google.com/file/d/1TsY16oeR-SieVjFO8gaz8Kq1Pb0QNgHC/view?usp=sharing |'
                       f' Список основных команд на последних двух страницах инструкции')

    @commands.command(name='health')
    async def command_health(self, ctx):
        try:
            userId = self.db.getUserIdByNickname(ctx.author.name)
            health = self.getCurrentHealth(userId)
            if health == 0.0 and not self.db.isHealthZero(ctx.author.name):
                self.db.addEnergy(ctx.author.name, -3)
                self.db.setZeroHealth(ctx.author.name, True)
            await ctx.send(f'/me {ctx.author.name}, ваш уровень здоровья - {round(health, 1)}')
        except Exception as e:
            await ctx.channel.send("/me Кажется, мне не хорошо...")
            logging.critical(f"{ctx.content} | {str(e)}")
        # else:
        #     await ctx.send(f'/me Вы почему еще не спите! А ну бегом в кровать, марш!')

    @commands.command(name='inj')
    async def getInjection(self, ctx):
        try:
            userId = self.db.getUserIdByNickname(ctx.author.name)
            health = self.getCurrentHealth(userId)
            if self.db.getEndInjectionTime(userId):
                minutes = int((100 - health) / 4.0) + 1
                await ctx.send(f"/me {ctx.author.name}, вы уже на уколах! Вы восстановитесь через {minutes} минут")
                return
            if health == 0.0 and not self.db.isHealthZero(ctx.author.name):
                self.db.addEnergy(ctx.author.name, -3)
                self.db.setZeroHealth(ctx.author.name, True)
            if health < 50:
                minutes = int((100 - health) / 4.0) + 1
                self.useInjection(userId, datetime.datetime.now() + datetime.timedelta(minutes=minutes))
                self.db.setZeroHealth(ctx.author.name, False)
                await ctx.send(
                    f'/me Больной {ctx.author.name} отправляется на уколы. Он будет восстанавливаться {minutes} минут')
            else:
                await ctx.send(f'/me {ctx.author.name}, вы принимали таблетки совсем недавно!')
        except Exception as e:
            await ctx.channel.send("/me Кажется, мне не хорошо...")
            logging.critical(f"{ctx.content} | {str(e)}")

    def useInjection(self, userId, endTime):
        self.db.setInjectionTime(userId, datetime.datetime.now())
        self.db.setEndInjectionTime(userId, endTime)
        self.db.increaceInjectionCount(userId)

    @commands.command(name='giveItem')
    async def giveItem(self, ctx, userName="", *itemName):
        try:
            itemName = ' '.join(map(str, itemName))
            print(itemName)
            if not self.isUserModerator(ctx.author.name):
                await ctx.send(f"/me {ctx.author.name}, только модераторы могут использовать эту команду!")
                return
            if userName == '' or itemName == '':
                await ctx.send(f"/me {ctx.author.name}, требуется ввести !giveItem <Кому> <Что>")
                return
            itemName = itemName.capitalize()
            userName = userName.lower().replace("@", "")
            userId = self.db.getUserIdByNickname(userName)
            if userId is None:
                await ctx.send(f'/me {ctx.author.name}, такой никнейм не найден, проверьте правильность написания')
                return
            itemId = self.db.getItemIdByItemName(itemName)
            if itemId is None:
                await ctx.send(f'/me {ctx.author.name}, такой предмет не найден, проверьте правильность написания')
                return
            self.db.giveItemToUser(userId, itemId, 1)
            await ctx.send(f'/me Неожиданно {userName} получает {itemName}')
        except Exception as e:
            await ctx.channel.send("/me Кажется, мне не хорошо...")
            logging.critical(f"{ctx.content} | {str(e)}")

    @commands.command(name='inv')
    async def getInventory(self, ctx):
        try:
            userId = self.db.getUserIdByNickname(ctx.author.name)
            inventory = self.db.getUserItems(userId)
            resultStr = f"{ctx.author.name}, твои предметы: "
            tmpStr = resultStr
            for i in range(0, len(inventory)):
                item = inventory[i]
                tmpStr += f" {i + 1}. [{item[3]} ({item[4]}/{item[5]})]"
                if len(tmpStr) > 500:
                    await ctx.send(f'/me {resultStr}')
                    resultStr = ""
                    tmpStr = ""
                resultStr += f" {i + 1}. [{item[3]} ({item[4]}/{item[5]})]"
                # print(len(resultStr))
            await ctx.send(f'/me {resultStr}')
        except Exception as e:
            await ctx.channel.send("/me Кажется, мне не хорошо...")
            logging.critical(f"{ctx.content} | {str(e)}")

    @commands.command(name='info')
    async def getInformationAboutItem(self, ctx, itemName=""):
        try:
            if itemName == '':
                await ctx.send(f"/me {ctx.author.name}, требуется ввести !info <Название предмета>")
                return
            itemName = itemName.capitalize()
            # userId = self.db.getUserIdByNickname(ctx.author.name)
            itemId = self.db.getItemIdByItemName(itemName)
            # if not self.db.isItemInUserInventory(userId, itemId) or itemId is None:
            if itemId is None:
                await ctx.send(f"/me {ctx.author.name}, у вас нет информации по данному предмету")
                return
            info = self.db.getInformationAboutItem(itemId)
            print(info)
            resultStr = f"{info[0]}; Класс: {info[1]}, Подкласс: {info[2]};" \
                        f" ПЗ: {info[3]}, ПА: {info[4]}, ПУ: {info[5]}; Стойкость: {info[6]}"
            await ctx.send(f"/me {resultStr}")
        except Exception as e:
            await ctx.channel.send("/me Кажется, мне не хорошо...")
            logging.critical(f"{ctx.content} | {str(e)}")

    @commands.command(name='drop')
    async def dropItem(self, ctx, *itemName):
        try:
            itemName = " ".join(map(str, itemName)).capitalize()
            if itemName == '':
                await ctx.send("/me {ctx.author.name}, требуется ввести !drop <Название предмета>")
                return
            itemName = itemName.capitalize()
            itemId = self.db.getItemIdByItemName(itemName)
            userId = self.db.getUserIdByNickname(ctx.author.name)
            if itemId is None or not self.db.isItemInUserInventory(userId, itemId):
                await ctx.send("/me {ctx.author.name}, у вас нет данного предмета")
                return
            self.db.deleteItemFromInventory(userId, itemId)
            await ctx.send(f"/me {ctx.author.name}, {itemName} успешно выброшен в окно")
        except Exception as e:
            await ctx.channel.send("/me Кажется, мне не хорошо...")
            logging.critical(f"{ctx.content} | {str(e)}")

    @commands.command(name='weapons')
    async def getWeapons(self, ctx):
        try:
            userId = self.db.getUserIdByNickname(ctx.author.name)
            inventory = self.db.getUserItems(userId)
            weapons = []
            for item in inventory:
                if item[1] == 'Оружие' and item[-1]:
                    weapons.append(item)
            if len(weapons) == 2:
                message = f"{ctx.author.name}, в бою вы используете следующие оружия: {weapons[0][3]} и {weapons[1][3]}"
            elif len(weapons) == 1:
                message = f"{ctx.author.name}, в бою вы используете следующее оружие: {weapons[0][3]}"
            else:
                message = f"{ctx.author.name}, вы не используете оружие"
            await ctx.send(f"/me {message}")
        except Exception as e:
            await ctx.channel.send("/me Кажется, мне не хорошо...")
            logging.critical(f"{ctx.content} | {str(e)}")

    @commands.command(name='clothes')
    async def getClothes(self, ctx):
        try:
            userId = self.db.getUserIdByNickname(ctx.author.name)
            inventory = self.db.getUserItems(userId)
            print(inventory)
            clothes = []
            for item in inventory:
                if item[1] == 'Одежда' and item[-1]:
                    clothes.append(item)
            message = f"{ctx.author.name}, на вас надето: "
            for i in range(0, len(clothes) - 2):
                message += f"{clothes[i][3]}, "
            if message == f"{ctx.author.name}, на вас надето: ":
                if len(clothes) == 2:
                    message = f"{ctx.author.name}, на вас надето: {clothes[0][3]} и {clothes[1][3]}"
                elif len(clothes) == 1:
                    message = f"{ctx.author.name}, на вас надето: {clothes[0][3]}"
                else:
                    message = f"{ctx.author.name}, на вас ничего не надето"
            else:
                message += f"{clothes[-2][3]} и {clothes[-1][3]}"
            await ctx.send(f"/me {message}")
        except Exception as e:
            await ctx.channel.send("/me Кажется, мне не хорошо...")
            logging.critical(f"{ctx.content} | {str(e)}")

    @commands.command(name='raid')
    async def createRaid(self, ctx, *locationName):
        try:
            locationName = " ".join(map(str, locationName)).capitalize()
            print(locationName)
            if not self.db.isRaidTime():
                minutes = int(60 - self.getStreamTime(self.db.getLastRaidsTime(), datetime.datetime.now()).total_seconds() / 60)
                # minutes = int((datetime.timedelta(hours=1) - (datetime.datetime.now() - self.db.getLastRaidsTime())).total_seconds() / 60)
                await ctx.send(f"/me {ctx.author.name}, на дворе день, вас сразу же заметят! Рейды можно проводить только ночью. "
                               f"До ночи осталось {minutes} минут")
                return
            if not locationName:
                await ctx.send(f"/me {ctx.author.name}, вам нужно указать локацию для рейда")
                return
            userId = self.db.getUserIdByNickname(ctx.author.name)
            if self.getCurrentHealth(userId) < 25:
                await ctx.send(f"/me {ctx.author.name}, у вас слишком мало здоровья, чтобы отправляться в рейды")
                return
            raidId = self.db.getRaidIdByLocationName(locationName)
            if raidId is None:
                await ctx.send(f"/me {ctx.author.name}, извините, такой локации не существует")
                return
            if self.db.isUserInRaidParty(userId):
                await ctx.send(f"/me {ctx.author.name}, вы уже находитесь в составе рейда. Пожалуйста, покиньте его!")
                return
            pz, pa, py = self.calculateUserStats(userId)
            if pa < self.db.getMinUserPA(raidId):
                await ctx.send(f"/me {ctx.author.name}, вы недостаточно сильны, чтобы участвовать в данном рейде")
                return
            if self.db.getCountCert(userId) != self.db.getTierCert(raidId):
                await ctx.send(f"/me {ctx.author.name}, эта локация для вас недоступна")
                return
            self.db.createNewRaidParty(userId, raidId)
            await ctx.send(f"/me Внимание! {ctx.author.name} собирается в рейд на {locationName}! "
                           f"Чтобы присоедниться, воспользуйтесь командой !joinRaid {ctx.author.name}")
        except Exception as e:
            await ctx.channel.send("/me Кажется, мне не хорошо...")
            logging.critical(f"{ctx.content} | {str(e)}")

    @commands.command(name='joinRaid')
    async def joinRaid(self, ctx, nickname=''):
        try:
            if nickname == '':
                await ctx.send(f"/me {ctx.author.name}, требуется указать, к какому игроку вы хотите присоединиться")
                return
            nickname = nickname.lower().replace("@", "")
            if ctx.author.name == nickname:
                await ctx.send(f"/me {ctx.author.name}, вы не можете пригласить самого себя в рейд")
                return
            userId = self.db.getUserIdByNickname(ctx.author.name)
            nicknameId = self.db.getUserIdByNickname(nickname)
            if self.db.isUserInRaidParty(userId):
                await ctx.send(f"/me {ctx.author.name}, вы уже находитесь в составе рейда. Пожалуйста, покиньте его!")
                return
            if not self.db.isUserInRaidParty(nicknameId):
                await ctx.send(f"/me {ctx.author.name}, {nickname} не находится в рейде.")
                return
            partyId = self.db.getIdPartyByUserId(nicknameId)
            if self.db.isRaidStarted(partyId):
                await ctx.send(f"/me {ctx.author.name}, этот участник уже ушел в рейд, присоединиться не получится.")
                return
            raidId = self.db.getRaidIdInParty(partyId)
            pz, pa, py = self.calculateUserStats(userId)
            if pa < self.db.getMinUserPA(raidId):
                await ctx.send(f"/me {ctx.author.name}, вы недостаточно сильны, чтобы участвовать в данном рейде")
                return
            if self.db.getCountCert(userId) != self.db.getTierCert(raidId):
                await ctx.send(f"/me {ctx.author.name}, эта локация для вас недоступна")
                return
            if self.getCurrentHealth(userId) < 25:
                await ctx.send(f"/me {ctx.author.name}, у вас слишком мало здоровья, чтобы отправляться в рейды")
                return
            if self.db.getCountPlayersInRaidParty(partyId) >= 4:
                await ctx.send(f"/me {ctx.author.name}, в данном рейде уже участвует максимальное количество людей")
                return
            self.db.joinRaidParty(partyId, userId)
            raidId = self.db.getRaidIdInParty(partyId)
            raidInfo = self.db.getRaidInformation(raidId)
            await ctx.send(f"/me {ctx.author.name}, вы успешно вступили в рейд на локацию '{raidInfo[0]}'")
        except Exception as e:
            await ctx.channel.send("/me Кажется, мне не хорошо...")
            logging.critical(f"{ctx.content} | {str(e)}")

    @commands.command(name="startRaid")
    async def startRaid(self, ctx):
        try:
            userId = self.db.getUserIdByNickname(ctx.author.name)
            partyId = self.db.getIdPartyByUserId(userId)
            if partyId is None:
                await ctx.send(f"/me {ctx.author.name}, вы не состоите в рейде")
                return
            raidPartyInfo = list(self.db.getRaidPartyInformation(partyId))
            if userId != raidPartyInfo[1]:
                await ctx.send(f"/me {ctx.author.name}, вы не капитан данной группы. Только капитан может запускать рейд.")
                return
            self.db.setRaidStarted(partyId)
            self.db.setRaidEnded(partyId)
            raidPartyInfo = list(self.db.getRaidPartyInformation(partyId))
            raidInfo = self.db.getRaidInformation(raidPartyInfo[7])
            for i in range(1, 5):
                raidPartyInfo[i] = self.db.getNicknameByUserId(raidPartyInfo[i])
            if raidPartyInfo[5] == 4:
                message = f"Бравые войны {raidPartyInfo[1]}, {raidPartyInfo[2]}, {raidPartyInfo[3]} и {raidPartyInfo[4]}" \
                          f" отправились в рейд на локацию '{raidInfo[0]}'. Пожелаем им удачи!"
            elif raidPartyInfo[5] == 3:
                message = f"Бравые войны {raidPartyInfo[1]}, {raidPartyInfo[2]} и {raidPartyInfo[3]}" \
                          f" отправились в рейд на локацию '{raidInfo[0]}'. Пожелаем им удачи!"
            elif raidPartyInfo[5] == 2:
                message = f"Бравые войны {raidPartyInfo[1]} и {raidPartyInfo[2]} отправились в рейд на локацию" \
                          f" '{raidInfo[0]}'. Пожелаем им удачи!"
            else:
                message = f"Бравый войн {raidPartyInfo[1]} отправился в рейд на локацию '{raidInfo[0]}'." \
                          f" Пожелаем ему удачи!"
            await ctx.send(f"/me {message}")
        except Exception as e:
            await ctx.channel.send("/me Кажется, мне не хорошо...")
            logging.critical(f"{ctx.content} | {str(e)}")

    @commands.command(name="exitRaid")
    async def exitRaid(self, ctx):
        try:
            userId = self.db.getUserIdByNickname(ctx.author.name)
            partyId = self.db.getIdPartyByUserId(userId)
            if partyId is None:
                await ctx.send(f"/me {ctx.author.name}, вы не состоите в рейде")
                return
            info = self.db.getRaidPartyInformation(partyId)
            self.db.exitFromPartyRaid(partyId, userId)
            if userId == info[1] and info[5] > 1:
                nickname = self.db.getNicknameByUserId(info[2])
                await ctx.send(f"/me {ctx.author.name}, вы успешно вышли из группы. Теперь {nickname} - капитан рейда")
            elif info[5] == 1:
                await ctx.send("/me {ctx.author.name}, вы успешно вышли из группы. Рейд расформирован")
            else:
                await ctx.send("/me {ctx.author.name}, вы успешно вышли из группы.")
        except Exception as e:
            await ctx.channel.send("/me Кажется, мне не хорошо...")
            logging.critical(f"{ctx.content} | {str(e)}")

    @commands.command(name='infoRaid')
    async def getRaidInformation(self, ctx):
        try:
            userId = self.db.getUserIdByNickname(ctx.author.name)
            partyId = self.db.getIdPartyByUserId(userId)
            if partyId is None:
                await ctx.send(f"/me {ctx.author.name}, вы не состоите в рейде")
                return
            raidPartyInfo = list(self.db.getRaidPartyInformation(partyId))
            raidInfo = self.db.getRaidInformation(raidPartyInfo[7])
            for i in range(1, 5):
                raidPartyInfo[i] = self.db.getNicknameByUserId(raidPartyInfo[i])
            if raidPartyInfo[5] == 4:
                players = f"{raidPartyInfo[1]}, {raidPartyInfo[2]}, {raidPartyInfo[3]} и {raidPartyInfo[4]}"
            elif raidPartyInfo[5] == 3:
                players = f"{raidPartyInfo[1]}, {raidPartyInfo[2]} и {raidPartyInfo[3]}"
            elif raidPartyInfo[5] == 2:
                players = f"{raidPartyInfo[1]} и {raidPartyInfo[2]}"
            else:
                players = f"{raidPartyInfo[1]}"
            await ctx.send(f"/me {ctx.author.name}, локация: [{raidInfo[0]}], Участники: [{players}]")
        except Exception as e:
            await ctx.channel.send("/me Кажется, мне не хорошо...")
            logging.critical(f"{ctx.content} | {str(e)}")

    @commands.command(name='map')
    async def getMap(self, ctx):
        try:
            userId = self.db.getUserIdByNickname(ctx.author.name)
            certCount = self.db.getCountCert(userId)
            pz, pa, py = self.calculateUserStats(userId)
            raids = self.db.getPossibleRaids(pa, certCount)
            message = f"/me {ctx.author.name}, для рейда (!raid) вам доступны следующие локации:"
            for i in range(0, len(raids)):
                message += f" {i + 1}. [{raids[i][0]}]"
            await ctx.send(message)
        except Exception as e:
            await ctx.channel.send("/me Кажется, мне не хорошо...")
            logging.critical(f"{ctx.content} | {str(e)}")

    @commands.command(name='use')
    async def useItem(self, ctx, *itemName):
        try:
            itemName = " ".join(map(str, itemName)).capitalize()
            if itemName == '':
                await ctx.send(f"/me {ctx.author.name}, требуется указать название используемого предмета")
                return
            itemName = itemName.capitalize()
            userId = self.db.getUserIdByNickname(ctx.author.name)
            itemId = self.db.getItemIdByItemName(itemName)
            if itemId is None or not self.db.isItemInUserInventory(userId, itemId):
                await ctx.send(f"/me {ctx.author.name}, у вас нет данного предмета")
                return
            isWeapon = self.db.isItemWeapon(itemId)
            if not self.db.isUsableItemsExist(userId, itemId, False):
                if isWeapon:
                    await ctx.send(f"/me {ctx.author.name}, {itemName} уже в ваших руках")
                else:
                    await ctx.send(f"/me {ctx.author.name}, предмет '{itemName}' уже надет на вас")
                return
            maxCount = self.db.getMaximumItemsInCategory(itemId)
            count = self.db.getCountItemsInCategory(userId, itemId)
            if count + 1 > maxCount:
                if isWeapon:
                    await ctx.send(f'/me {ctx.author.name}, ты не можешь удержать столько оружия. Сначала убери то, что у тебя в руках')
                else:
                    await ctx.send(f'/me {ctx.author.name}, на тебе уже надет другой предмет из этого класса. Сними его')
                return
            userItems = self.db.getUserItems(userId)
            weapons = []
            for item in userItems:
                itemInfo = self.db.getInformationAboutItem(item[0])
                isInUse = self.db.isItemUsable(userId, item[0])
                if itemInfo[1] == 'Оружие' and isInUse:
                    weapons.append(itemInfo)
            newItem = self.db.getItemById(itemId)
            if isWeapon and len(weapons) != 0 and weapons[0][2] != newItem[2]:
                await ctx.send(f'/me {ctx.author.name}, нельзя использовать оружие другого класса. Сначала убери старое оружие')
                return
            self.db.useItem(userId, itemId)
            if isWeapon:
                await ctx.send(f'/me {ctx.author.name} берет {itemName} в руки')
            else:
                await ctx.send(f'/me {ctx.author.name} надевает {itemName} на себя')
        except Exception as e:
            await ctx.channel.send("/me Кажется, мне не хорошо...")
            logging.critical(f"{ctx.content} | {str(e)}")

    @commands.command(name='unuse')
    async def unuseItem(self, ctx, *itemName):
        try:
            itemName = " ".join(map(str, itemName)).capitalize()
            if itemName == "":
                await ctx.send(f"/me {ctx.author.name}, чтобы снять предмет, требуется указать его имя")
            itemName = itemName.capitalize()
            userId = self.db.getUserIdByNickname(ctx.author.name)
            itemId = self.db.getItemIdByItemName(itemName)
            if itemId is None or not self.db.isItemInUserInventory(userId, itemId):
                await ctx.send(f"/me {ctx.author.name}, у вас нет данного предмета")
                return
            isWeapon = self.db.isItemWeapon(itemId)
            if not self.db.isUsableItemsExist(userId, itemId, True):
                if isWeapon:
                    await ctx.send(f"/me {ctx.author.name}, это оружие у вас не в руках")
                else:
                    await ctx.send(f"/me {ctx.author.name}, вы не носите этот предмет")
                return
            self.db.unuseItem(userId, itemId)
            if isWeapon:
                await ctx.send(f'/me {ctx.author.name} убирает {itemName} ')
            else:
                await ctx.send(f'/me {ctx.author.name} снимает {itemName} с себя')
        except Exception as e:
            await ctx.channel.send("/me Кажется, мне не хорошо...")
            logging.critical(f"{ctx.content} | {str(e)}")

    @commands.command(name='stats')
    async def getStats(self, ctx):
        try:
            userId = self.db.getUserIdByNickname(ctx.author.name)
            health = self.getCurrentHealth(userId)
            if health == 0.0 and not self.db.isHealthZero(ctx.author.name):
                self.db.addEnergy(ctx.author.name, -3)
                self.db.setZeroHealth(ctx.author.name, True)
            levelInfo = self.db.getCurrentLevel(userId)
            print(levelInfo)
            illnesses = ""
            for level in levelInfo:
                illnesses += level[0] + ', '
            # injectionCount = self.db.getInjectionCount(userId)
            info = self.db.getTimeInStream(ctx.author.name)
            if info[0] is None:
                streamTime = info[1]
            else:
                streamTime = info[1] + int((datetime.datetime.now() - info[0]).total_seconds() / 60)
            countRaid = self.db.getCountRaids(userId)
            pills = self.getPills(ctx.author.name)
            strStreamTime = self.formatStreamTime(streamTime)
            pz, pa, py = self.calculateUserStats(userId)
            certs = self.db.getCountCert(userId)
            await ctx.send(f'/me Имя: {ctx.author.name} | Класс: {levelInfo[0][1]} '
                           f'| Болезни: {illnesses[:-2]} '
                           f'| Таблеток: {pills} '
                           f'| Количество рейдов: {countRaid} '
                           f'| ПЗ: {pz}, ПА: {pa}, ПУ: {py} '
                           f'| Количество справок: {certs} '
                           f'| Время, проведенное на стриме: {strStreamTime} |')
        except Exception as e:
            await ctx.channel.send("/me Кажется, мне не хорошо...")
            logging.critical(f"{ctx.content} | {str(e)}")

    @commands.command(name="shop")
    async def getShop(self, ctx):
        shop = self.db.getShop()
        if shop is None:
            self.createShop()
            shop = self.db.getShop()
        prices = self.db.getPricesForItems(shop[1:6])
        print(prices)
        resultStr = self.formatShopStr(shop[1:6], prices)
        await ctx.send(f"/me {ctx.author.name}, добро пожаловать в магазин! Сегодня в продаже: {resultStr}")

    @commands.command(name='buy')
    async def buyNewItem(self, ctx, *itemName):
        itemName = " ".join(map(str, itemName)).capitalize()
        if itemName == "":
            await ctx.send(f"/me {ctx.author.name}, нужно сказать, что ты хочешь купить")
            return
        itemId = self.db.getItemIdByItemName(itemName)
        if itemId is None:
            await ctx.send(f"/me {ctx.author.name}, я не знаю такого предмета!")
            return
        if not self.db.isItemSelling(itemId):
            await ctx.send(f"/me {ctx.author.name}, вы можете купить только тот предмет, что продается (!shop)")
            return
        userId = self.db.getUserIdByNickname(ctx.author.name)
        price = self.db.getPricesForItems([itemId])[0]
        pills = self.getPills(ctx.author.name)
        if pills - price < 0:
            await ctx.send(f"/me {ctx.author.name}, у вас недостаточно средств!")
            return

        self.db.setItemSelled(itemId)
        savedPills = self.db.getPills(ctx.author.name)
        self.db.setPills(ctx.author.name, savedPills - price)
        self.db.giveItemToUser(userId, itemId, 1)
        await ctx.send(f"/me {ctx.author.name}, вы успешно купили '{itemName}'")

    @commands.command(name='trade')
    async def trade(self, ctx, nickname="", *info):
        try:
            nickname = nickname.lower().replace("@", "")
            itemName = info[0]
            if itemName.capitalize() == "Да" or itemName.capitalize() == "Нет":
                await self.tradeAnswer(ctx, nickname, itemName.capitalize())
            else:
                itemName = " ".join(map(str, info[:-1])).capitalize()
                price = int(info[-1])
                if price >= 0:
                    await self.createTrade(ctx,nickname, itemName, price)
                else:
                    await ctx.send(f"/me {ctx.author.name}, не могу распознать команду. Проверьте правильность введенной команды")
        except Exception as e:
            await ctx.send(f"/me {ctx.author.name}, не могу распознать команду. Проверьте правильность введенной команды")

    @commands.command(name='cancelTrade')
    async def cancelTrade(self, ctx):
        userId = self.db.getUserIdByNickname(ctx.author.name)
        if not self.db.isUserTraiding(userId):
            await ctx.send(f"/me {ctx.author.name}, вы не торгуетесь ни с кем")
            return
        self.db.getTradeIdByUserFrom(userId)
        tradeId = self.db.getTradeIdByUserFrom(userId)
        tradeInfo = self.db.getTrade(tradeId)
        self.db.deleteTrade(userId)
        tuUserName = self.db.getNicknameByUserId(tradeInfo[1])
        await ctx.send(f"/me {ctx.author.name}, обмен c {tuUserName} успешно отменен")

    @commands.command(name='reset')
    async def resetGame(self, ctx):
        userId = self.db.getUserIdByNickname(ctx.author.name)
        if not self.db.isItemInUserInventory(userId, 100):
            await ctx.send(f"/me {ctx.author.name}, у вас нет справки!")
            return
        items = self.db.getUserItems(userId)
        pz, pa, py = self.calculateUserStats(userId)
        self.db.setUserIndexes(userId, pz, pa, py)
        for item in items:
            self.db.deleteItemFromInventory(userId, item[0])
        self.db.setEnergy(ctx.author.name, 0)
        await ctx.send(f"/me {ctx.author.name}, вы успешно выбрались из больницы. Поздравляю! "
                       "Ваши показатели сохранены, все остальное сброшено. "
                       "Удачи в 'Новой игре'!")

    @commands.command(name='authors')
    async def getAuthors(self, ctx):
        await ctx.send("/me Директор больницы: pu1se0 | "
                       "По всем вопросам: magicarm22 в дискорд канале | "
                       "Отдельная благодарность: DokerStim, flynn_meier, sander_sia, zakhozhka")

    @commands.command(name='feedback')
    async def createFeedback(self, ctx, *message):
        message = " ".join(map(str, message))
        if message == "":
            await ctx.send(f"/me {ctx.author.name}, неправильное использование команды. Использование: !feedback \"<Отзыв>\"")
            return
        userId = self.db.getUserIdByNickname(ctx.author.name)
        self.db.insertFeedback(message, userId)
        await ctx.send(f"/me {ctx.author.name}, cпасибо за отзыв! Мы рассмотрим его в ближайшее время.")

    @commands.command(name='top')
    async def getTop(self, ctx, topName):
        topName = str(topName).capitalize()
        if topName == 'Время':
            await self.getTopByTime(ctx)
        elif topName == 'Таблетки':
            await self.getTopByPills(ctx)
        elif topName == 'Рейды':
            await self.getTopByRaids(ctx)
        elif topName == 'Справки':
            await self.getTopByCert(ctx)
        else:
            await ctx.send(f"/me {ctx.author.name}, извините, но я не знаю такого топа")

    def getPills(self, nickname):
        lastTimeIn = self.db.getLastTimeIn(nickname)
        pills = self.db.getPills(nickname)
        if lastTimeIn is None:
            return int(pills)
        curPills = pills + int((datetime.datetime.now() - lastTimeIn).total_seconds() / 60) / 20
        return int(curPills)

    def calculateUserStats(self, userId):
        features = self.db.getUsableItemsFeatures(userId)
        indexes = self.db.getUserIndexes(userId)
        print("ind:", indexes)
        pz = indexes[0]
        pa = indexes[1]
        py = indexes[2]
        print(features)
        for feat in features:
            pz += feat[0]
            pa += feat[1]
            py += feat[2]
        return pz, pa, py

    def formatStreamTime(self, time: int):
        streamTime = datetime.timedelta(seconds=time * 60) + datetime.datetime(1, 1, 1)
        minuteMorph = self.morph.parse("минута")[0]
        hourMorph = self.morph.parse("час")[0]
        if 2 <= (streamTime.day - 1) <= 4 or 22 <= (streamTime.day - 1) <= 24:
            dayName = "дня"
        elif 5 <= (streamTime.day - 1) <= 20 or 25 <= (streamTime.day - 1) <= 30:
            dayName = "дней"
        else:
            dayName = "день"
        if 2 <= (streamTime.month - 1) <= 4:
            monthName = "месяца"
        elif 5 <= (streamTime.month - 1) <= 12:
            monthName = "месяцев"
        else:
            monthName = "месяц"
        if 11 <= (streamTime.year - 1) % 100 <= 14 or (streamTime.year - 1) % 10 >= 5:
            yearName = "лет"
        elif 2 <= (streamTime.year - 1) % 10 <= 4:
            yearName = "года"
        else:
            yearName = "год"
        if streamTime.year - 1 != 0:
            strStreamTime = f"{streamTime.year - 1} {yearName}, {streamTime.month - 1} {monthName}, {streamTime.day - 1} {dayName}, {streamTime.hour} {hourMorph.make_agree_with_number(streamTime.hour).word} и {streamTime.minute} {minuteMorph.make_agree_with_number(streamTime.minute).word}"
        elif streamTime.month - 1 != 0:
            strStreamTime = f"{streamTime.month - 1} {monthName}, {streamTime.day - 1} {dayName}, {streamTime.hour} {hourMorph.make_agree_with_number(streamTime.hour).word} и {streamTime.minute} {minuteMorph.make_agree_with_number(streamTime.minute).word} "
        elif streamTime.day - 1 != 0:
            strStreamTime = f"{streamTime.day - 1} {dayName}, {streamTime.hour} {hourMorph.make_agree_with_number(streamTime.hour).word} и {streamTime.minute} {minuteMorph.make_agree_with_number(streamTime.minute).word}"
        elif streamTime.hour != 0:
            strStreamTime = f"{streamTime.hour} {hourMorph.make_agree_with_number(streamTime.hour).word} и {streamTime.minute} {minuteMorph.make_agree_with_number(streamTime.minute).word}"
        else:
            strStreamTime = f"{streamTime.minute} {minuteMorph.make_agree_with_number(streamTime.minute).word}"
        return strStreamTime

    def createNewUser(self, name):
        self.db.addNewUser(name)
        userId = self.db.getUserIdByNickname(name)
        self.db.addNewInjection(userId)

    def getCurrentHealth(self, userId):
        currentTime = datetime.datetime.now()
        lastInjectionTime = self.db.getInjectionTime(userId)
        beforeLastInjectionTime = self.db.getBeforeLastInjectionTime(userId)
        endInjectionTime = self.db.getEndInjectionTime(userId)
        if lastInjectionTime is None:  # Впервые пришел
            return self.getHealthInTime(beforeLastInjectionTime, currentTime)
        if endInjectionTime is not None and endInjectionTime < currentTime:  # Укол закончен
            self.db.stopInjection(userId, endInjectionTime)
            return self.getHealthInTime(endInjectionTime, currentTime)
        hpInInjection = self.getHealthInTime(beforeLastInjectionTime, lastInjectionTime)
        return hpInInjection + (currentTime - lastInjectionTime).total_seconds() / (  # Во время укола
            (endInjectionTime - lastInjectionTime).total_seconds()) * (100 - hpInInjection)

    def getTimeWithHp(self, userId, hp):
        health = self.getCurrentHealth(userId)
        if hp > health:
            return None
        timeInSeconds = (1 - hp / 100) * 6 * 60.0 * 60.0
        # print(timeInSeconds)
        beforeLastInjectionTime = datetime.datetime.now()
        # print(self.getHealthInTime(beforeLastInjectionTime, datetime.datetime.now() + datetime.timedelta(seconds=timeInSeconds)))
        streams = self.db.getStreamTimeBefore(beforeLastInjectionTime)
        # print(streams)
        if streams[0][1] is not None and beforeLastInjectionTime > streams[0][1]:
            startTime = streams[0][1]
        else:
            startTime = beforeLastInjectionTime
        time = startTime
        times = 0
        for i in range(0, len(streams)):
            times += (time - streams[i][0]).total_seconds()
            # print(times)
            if times > timeInSeconds:
                newBefore = streams[i][0] + datetime.timedelta(seconds=times - timeInSeconds)
                # print("newTime:", newBefore)
                # print("HP:", self.getHealthInTime(newBefore, datetime.datetime.now()))
                self.db.setBeforeLastInjectionTime(userId, newBefore)
                break
            time = streams[i + 1][1]

    def getHealthInTime(self, startTime, time):
        injectionTime = startTime
        times = self.getStreamTime(injectionTime, time)
        health = (1 - (times.total_seconds() / (60.0 * 60.0)) / 6) * 100
        if health < 0.0:
            health = 0.0
        # print(health)
        return health

    def formatShopStr(self, items, prices):
        resultStr = ""
        zipped = zip(items, prices)
        for item in zipped:
            if item[0] is None:
                continue
            itemName = self.db.getItemNameByItemId(item[0])
            resultStr += f"[{itemName} - {item[1]}], "
        return resultStr[:-2]

    async def tradeAnswer(self, ctx, nickname, answer):
        fromUserId = self.db.getUserIdByNickname(nickname)
        toUserId = self.db.getUserIdByNickname(ctx.author.name)
        if not self.db.isUserTradeingWithUser(fromUserId, toUserId):
            await ctx.send("/me Указанный больной не торгует с вами")
            return
        if answer == 'Нет':
            self.db.deleteTrade(fromUserId)
            await ctx.send(f"/me {nickname}, увы, но больной {ctx.author.name} отклонил ваше предложение")
            return
        elif answer == 'Да':
            tradeId = self.db.getTradeIdByUserFrom(fromUserId)
            itemId = self.db.getItemIdFromTrade(tradeId)
            self.db.deleteItemFromInventory(fromUserId, itemId)
            self.db.giveItemToUser(toUserId, itemId, 1)
            price = self.db.getPriceFromTrade(tradeId)
            fromUserPills = self.db.getPills(nickname)
            self.db.setPills(nickname, fromUserPills + price)
            toUserPills = self.db.getPills(ctx.author.name)
            self.db.setPills(ctx.author.name, toUserPills - price)
            self.db.deleteTrade(fromUserId)
            itemName = self.db.getItemNameByItemId(itemId)
            await ctx.send(f"/me Обмен произошел успешно. {ctx.author.name} получил '{itemName}', "
                           f"а {nickname} получил {price} таблеток.")
        pass

    async def createTrade(self, ctx, nickname, itemName, price):
        fromUserId = self.db.getUserIdByNickname(ctx.author.name)
        toUserId = self.db.getUserIdByNickname(nickname)
        if fromUserId == toUserId:
            await ctx.send(f"/me Вы не можете торговать сами с собой. Совсем уже с ума сошли...")
            return
        if price < 0:
            await ctx.send(f"/me Вы не можете задавать отрицательную цену")
            return
        itemId = self.db.getItemIdByItemName(itemName)
        if self.db.isUserTraiding(fromUserId):
            await ctx.send("/me Вы уже торгуйте с другим участником. Чтобы завершить сделку, используйте !cancelTrade")
            return
        if itemId is None or not self.db.isItemInUserInventory(fromUserId, itemId):
            await ctx.send("/me У вас нет такого предмета")
            return
        if toUserId is None:
            await ctx.send("/me Данный пользователь не найден")
            return
        if self.db.getLastTimeIn(nickname) is None:
            await ctx.send("/me Этот пользователь сейчас не в сети")
            return
        toUserPills = self.getPills(nickname)
        if toUserPills - price < 0:
            await ctx.send("/me У пользователя нет столько таблеток, чтобы оплатить товар")
            return
        self.db.createTrade(fromUserId, toUserId, itemId, price)

        await ctx.send(f"/me {nickname}, пользователь {ctx.author.name} предлагает вам сделку."
                       f" За {price} таблеток вы получите прекрасный предмет '{itemName}'."
                       f" Для ответа воспользуйтесь командой !trade {ctx.author.name} <Да/Нет>")

    def createShop(self):
        items = self.db.getAllItems()
        itemsId = []
        itemsChance = []
        for item in items:
            itemsId.append(item[0])
            itemsChance.append(item[7])
        # print(itemsName)
        # print(itemsChance)
        # for i in range(0, 20):
        shopItems = random.choices(itemsId, itemsChance, k=5)
        # if not self.db.shopExist():
        self.db.addShop(shopItems)

    def changeShop(self):
        self.db.deleteShop()
        self.createShop()
        pass

    def changeCurrentFragility(self, partyInfo):
        for i in range(1, 5):
            userId = partyInfo[i]
            if userId is None:
                break
            inventory = self.db.getUsableItems(userId)
            for item in inventory:
                frag = item[2]
                if frag - 1 != 0:
                    self.db.setCurrentFragility(userId, item[0], frag - 1)
                else:
                    self.db.deleteItemFromInventoryByFragility(userId, item[0])

    async def getTopByTime(self, ctx):
        userId = self.db.getUserIdByNickname(ctx.author.name)
        top5 = self.db.getTopByTime(5)
        currentPos = self.db.getCurrentPositionInTimeTop(userId)
        str = ""
        for i in range(1, len(top5) + 1):
            nickname = self.db.getNicknameByUserId(top5[i - 1][0])
            str += f"{i}. [{nickname} - {self.formatStreamTime(top5[i - 1][1])}] "
        if 1 <= currentPos <= 5:
            await ctx.send(f"/me Топ по времени на стриме: {str[:-1]}")
            return
        else:
            info = self.db.getTimeInStream(ctx.author.name)
            if info[0] is None:
                streamTime = info[1]
            else:
                streamTime = info[1] + int((datetime.datetime.now() - info[0]).total_seconds() / 60)
            str += f"... {currentPos}. [{ctx.author.name} - {self.formatStreamTime(streamTime)}]"
            await ctx.send(f"/me Топ по времени на стриме: {str}")
            return
        pass

    async def getTopByPills(self, ctx):
        userId = self.db.getUserIdByNickname(ctx.author.name)
        top5 = self.db.getTopByPills(5)
        currentPos = self.db.getCurrentPositionInPillsTop(userId)
        str = ""
        for i in range(1, len(top5) + 1):
            nickname = self.db.getNicknameByUserId(top5[i - 1][0])
            str += f"{i}. [{nickname} - {int(top5[i - 1][1])}] "
        if 1 <= currentPos <= 5:
            await ctx.send(f"/me Топ по количеству таблеток: {str[:-1]}")
            return
        else:
            pills = self.getPills(ctx.author.name)
            str += f"... {currentPos}. [{ctx.author.name} - {pills}]"
            await ctx.send(f"/me Топ по количеству таблеток: {str}")
            return
        pass

    async def getTopByRaids(self, ctx):
        userId = self.db.getUserIdByNickname(ctx.author.name)
        top5 = self.db.getTopByRaids(5)
        currentPos = self.db.getCurrentPositionInRaidsTop(userId)
        str = ""
        for i in range(1, len(top5) + 1):
            nickname = self.db.getNicknameByUserId(top5[i - 1][0])
            str += f"{i}. [{nickname} - {int(top5[i - 1][1])}] "
        if 1 <= currentPos <= 5:
            await ctx.send(f"/me Топ по количеству рейдов: {str[:-1]}")
            return
        else:
            raids = self.db.getCountRaids(userId)
            str += f"... {currentPos}. [{ctx.author.name} - {raids}]"
            await ctx.send(f"/me Топ по количеству рейдов: {str}")
            return
        pass

    async def getTopByCert(self, ctx):
        userId = self.db.getUserIdByNickname(ctx.author.name)
        top5 = self.db.getTopByCerts(5)
        currentPos = self.db.getCurrentPositionInCertsTop(userId)
        str = ""
        for i in range(1, len(top5) + 1):
            nickname = self.db.getNicknameByUserId(top5[i - 1][0])
            str += f"{i}. [{nickname} - {int(top5[i - 1][1])}] "
        if 1 <= currentPos <= 5:
            await ctx.send(f"/me Топ по количеству справок: {str[:-1]}")
            return
        else:
            certs = self.db.getCountCert(userId)
            str += f"... {currentPos}. [{ctx.author.name} - {certs}]"
            await ctx.send(f"/me Топ по количеству справок: {str}")
            return
        pass

    def getStreamTime(self, fromTime, toTime):
        streams = self.db.getStreamTimeFrom(fromTime)
        # print(streams)
        if fromTime < streams[0][0]:
            startTime = streams[0][0]
        else:
            startTime = fromTime
        if streams[0][1] is None:
            times = toTime - startTime
        else:
            times = streams[0][1] - startTime
            # print(times)
            for i in range(1, len(streams)):
                if streams[i][1] is None:
                    times += toTime - streams[i][0]
                else:
                    times += streams[i][1] - streams[i][0]
        return times

    def isUserModerator(self, nickname):
        r = requests.get(f"http://tmi.twitch.tv/group/user/{initial_channels[0][1:]}/chatters")
        res = json.loads(r.text)
        chatters = res['chatters']
        moderators = chatters['moderators'] + chatters['broadcaster']
        if nickname not in moderators:
            return False
        return True


if __name__ == "__main__":
    load_dotenv(".env")
    irc_token = os.getenv('IRC_TOKEN')
    client_id = os.getenv('CLIENT_ID')
    secret = os.getenv('CLIENT_SECRET')
    api_key = os.getenv('API_TOKEN')
    bearer = os.getenv('BEARER_KEY')
    nick = os.getenv('BOT_NICK')
    prefics = os.getenv('BOT_PREFIX')
    initial_channels = ['#pu1se0']
    bot = Bot(irc_token=irc_token, nick=nick, client_id=client_id,
              client_secret=secret, api_key=api_key, bearer=bearer,
              initial_channels=initial_channels,
              external_host="http://8cba8ebd6160.ngrok.io",
              port=4040,
              webhook_server=True,
              callback="fu138103hdiq89qy0r3y"
              )
    bot.run()
