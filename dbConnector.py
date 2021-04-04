import datetime
import json
import random

import psycopg2
from psycopg2 import sql


class dbConnector:

    def __init__(self, password):
        try:
            self.conn = psycopg2.connect("dbname='pu1se0_bot' user='postgres' host='localhost' password={}".format(password))
            self.conn.autocommit = True
            self.cur = self.conn.cursor()
        except Exception as e:
            print("Error: {}".format(e))

        # self.createUserTable()
        # self.addNewUser("magicarm22")
        # self.getAllUsers()
        # self.addStream("TEST123", datetime.datetime.now())
        # self.setStreamEnd('7bbbfccd-d898-4604-9347-570a481b08d2')
        # self.getStreamTimeFrom('2020-10-28 22:19:07.166287')
        # self.insertAllBots()
        # self.createCategotyItemTable()
        # self.insertCategoryItem()
        # self.insertItems()
        # self.insertRaids()
        # self.insertLevels()

    def createUserTable(self):
        self.cur.execute("""
        create table "User"
        (
            id uuid default uuid_generate_v4() not null
            nickname      text,
            "lastMessage" timestamp
        );
        """
                         )
        self.cur.execute("""
        create unique index user_id_uindex
        	on "User" (id);
        """)

        self.cur.execute("""
        create unique index user_nickname_uindex
        	on "User" (nickname);
        """)

        self.cur.execute("""
        alter table "User"
        	add constraint user_pk
        		primary key (id);
        """)

        self.cur.execute("""
        alter table "User"
	    add "lastTimeIn" timestamp;
            """)
        self.cur.execute("""
        alter table "User"
            add "timeCount" int;
        """)
        self.cur.execute("""
        comment on column "User"."timeCount" is 'in minutes';
        """)

        self.cur.execute("""
        alter table "User" alter column "timeCount" set default 0;
        """)

        self.cur.execute("""
        alter table "User"
            add pills double precision;
        """)
        self.cur.execute("""
            Comment on column "User".pills is 'Количество таблеток';
        """)
        self.cur.execute("""
            alter table "User" alter column pills set default 15;
        """)

        self.cur.execute("""
            alter table "User" alter column "messagesCount" set default 0;
        """)

        self.cur.execute("""
        alter table "User"
            add "energy" int default 0 not null;
        """)

        self.cur.execute("""
        alter table "User"
            add "isHealthZero" bool default False;
        """)

        self.cur.execute("""
        alter table "User"
            add "countRaids" int default 0;
        """)
        self.cur.execute("""
        alter table "User"
            add "countCert" int default 0;
        """)

        self.cur.execute("""
            alter table "User"
                add pz int default 0;       
        """)
        self.cur.execute("""
            alter table "User"
                add pa int default 0;
        """)
        self.cur.execute("""
            alter table "User"
                add py int default 0;
        """)
        self.conn.commit()

    def createStreamTable(self):
        self.cur.execute('''
        create table "Streams"
        (
            id uuid default uuid_generate_v4() not null,
            "streamName" text,
            "startedAt" timestamp,
            "endedAt" timestamp
        );''')

        self.cur.execute('''
        create unique index streams_id_uindex
        	on "Streams" (id);
        ''')

        self.cur.execute("""
            alter table "Streams"
	add constraint streams_pk
		primary key (id);
        
        """)
        self.conn.commit()

    def createInjectionTable(self):
        self.cur.execute("""
        create table "Injection"
        (
            id uuid default uuid_generate_v4() not null,
            "userId" uuid not null
                constraint injection_user_id_fk
                    references "User"
                        on update cascade on delete cascade,
            "countTimes" int default 0,
            "lastInjectionTime" timestamp not null
        );
        """)

        self.cur.execute("""
            create unique index injection_id_uindex
                on "Injection" (id);
            """)

        self.cur.execute("""
            create unique index injection_userid_uindex
                on "Injection" ("userId");
        """)
        self.cur.execute("""
            alter table "Injection"
                add constraint injection_pk
                    primary key (id);
        """)

        self.cur.execute("""
        alter table "Injection"
        	add "endInjectionTime" timestamp;
        """)

        self.conn.commit()

    def createBotsTable(self):
        self.cur.execute("""
        create table "Bots"
        (
            id uuid default uuid_generate_v4() not null,
            "botName" text not null
        );
        """)
        self.cur.execute("""
            create unique index bots_id_uindex
                on "Bots" (id);
            """)
        self.cur.execute("""
            alter table "Bots"
                add constraint bots_pk
                    primary key (id);

        """)

        self.conn.commit()

    def createCategoryItemTable(self):
        self.cur.execute("""
        create table "CategoryItem"
        (
            id serial not null,
            "categoryName" text not null
        );
        """)
        self.cur.execute("""
        create unique index category_id_uindex
            on "CategoryItem" (id);
        """)
        self.cur.execute("""
        alter table "CategoryItem"
            add constraint category_pk
                primary key (id);
        """)
        self.cur.execute("""
        alter table "CategoryItem" rename column "categoryName" to "mainCategoryName";
        """)
        self.cur.execute("""
        alter table "CategoryItem"
            add "subCategoryName" text;
        
        """)
        self.cur.execute("""
        alter table "CategoryItem"
        add "itemsCanBeUsed" int;
        """)
        self.conn.commit()

    def createItemsTable(self):
        self.cur.execute("""
        create table "Items"
        (
            id serial not null,
            "itemName" text not null,
            category_id int not null
                constraint items_categoryitem_id_fk
                    references "CategoryItem"
                        on update cascade on delete cascade,
            PZ int default 0 not null,
            PA int default 0 not null,
            PY int default 0 not null
        );
        """)
        self.cur.execute("""
            create unique index items_id_uindex
                on "Items" (id);
        """)
        self.cur.execute("""
            alter table "Items"
                add constraint items_pk
                    primary key (id);
            """)
        self.cur.execute("""
                alter table "Inventory"
            add "inUse" bool default False not null;
        """)
        self.cur.execute("""
        alter table "Items"
            add cost int default 0;
        """)
        self.cur.execute("""
                alter table "Items"
                    add "shopChance" double precision default 0;
                """)
        self.cur.execute("""
                alter table "Items"
                    add "fragility" int default 1;
                """)
        self.conn.commit()

    def createInventoryTable(self):
        self.cur.execute("""
        create table "Inventory"
        (
            id serial not null,
            "userId" uuid not null
                constraint inventory_user_id_fk
                    references "User"
                        on update cascade on delete cascade,
            "itemId" int not null
                constraint inventory_items_id_fk
                    references "Items"
                        on update cascade on delete cascade,
            count int default 1 not null
        );
        """)
        self.cur.execute("""
        create unique index inventory_id_uindex
            on "Inventory" (id);
        """)

        self.cur.execute("""
        alter table "Inventory"
            add constraint inventory_pk
                primary key (id);
        """)

        self.cur.execute("""
        alter table "Inventory"
            add "currentFragility" int;
        """)

        self.conn.commit()

    def createRaidsTable(self):
        self.cur.execute("""
        create table "Raids"
        (
            id serial not null,
            "locationName" text not null,
            PZ int not null,
            PA int not null,
            loot json
        );
        """)
        self.cur.execute("""
        create unique index raids_id_uindex
            on "Raids" (id);
        """)
        self.cur.execute("""
        alter table "Raids"
            add constraint raids_pk
                primary key (id);
        """)
        self.cur.execute("""
        alter table "Raids"
        add time int not null;
        """)
        self.cur.execute("""
        comment on column "Raids".time is 'in minutes';
        """)
        self.cur.execute("""
        alter table "Raids"
            add "minUserPA" int default 0;
        """)

        self.cur.execute("""
        alter table "Raids"
            add "minPills" int default 0;
        """)

        self.cur.execute("""
        alter table "Raids"
            add "maxPills" int default 0;
        """)
        self.cur.execute("""
        alter table "Raids"
            add "tierCert" int default 0;        
        """)

        self.conn.commit()

    def createRaidPartyTable(self):
        self.cur.execute("""
        create table "RaidParty"
        (
            id serial not null,
            player1 uuid,
            player2 uuid,
            player3 uuid,
            player4 uuid,
            "countPlayer" int default 1,
            "partyCreated" timestamp,
            "raidId" int
                constraint raidparty_raids_id_fk
                    references "Raids"
                        on update cascade on delete cascade
        );
        """)

        self.cur.execute("""
        create unique index raidparty_id_uindex
            on "RaidParty" (id);
        """)

        self.cur.execute("""
        alter table "RaidParty"
            add constraint raidparty_pk
                primary key (id);
        """)
        self.cur.execute("""
        
            alter table "RaidParty"
        add constraint raidparty_user_id_fk
            foreign key (player1) references "User"
                on update cascade on delete cascade;
        """)
        self.cur.execute("""
            alter table "RaidParty"
                add constraint raidparty_user_id_fk_2
                    foreign key (player2) references "User"
                        on update cascade on delete cascade;
            """)
        self.cur.execute("""
            alter table "RaidParty"
                add constraint raidparty_user_id_fk_3
                    foreign key (player3) references "User"
                        on update cascade on delete cascade;
            """)
        self.cur.execute("""
            alter table "RaidParty"
                add constraint raidparty_user_id_fk_4
                    foreign key (player4) references "User"
                        on update cascade on delete cascade;
            """)

        self.cur.execute("""
        alter table "RaidParty"
            add "isRaidStarted" bool default False;
        """)
        self.cur.execute("""
        alter table "RaidParty"
            add "raidEnded" timestamp;        
        """)
        self.conn.commit()

    def createLevelsTable(self):
        self.cur.execute("""
        create table "Levels"
        (
            id serial not null,
            "levelName" text not null,
            "minEnergy" int not null,
            "maxEnergy" int not null
        );
        """)
        self.cur.execute("""
        create unique index levels_id_uindex
            on "Levels" (id);
        """)
        self.cur.execute("""
        alter table "Levels"
            add constraint levels_pk
                primary key (id);
        """)
        self.conn.commit()

    def createShopTable(self):
        self.cur.execute("""
            create table "Shop"
            (
                id serial not null
                    constraint shop_pk
                        primary key,
                "lastChanges" timestamp not null,
                "currentItem1" integer
                    constraint shop_items_id_fk
                        references "Items"
                            on delete set null,
                "currentItem2" integer
                    constraint shop_items_id_fk_2
                        references "Items"
                            on delete set null,
                "currentItem3" integer
                    constraint shop_items_id_fk_3
                        references "Items"
                            on delete set null,
                "currentItem4" integer
                    constraint shop_items_id_fk_4
                        references "Items"
                            on delete set null,
                "currentItem5" integer
                    constraint shop_items_id_fk_5
                        references "Items"
                            on delete set null
            );
            """)
        self.cur.execute("""
            alter table "Shop" owner to postgres;
        """)
        self.cur.execute("""
        create unique index shop_id_uindex
            on "Shop" (id);
        """)
        self.conn.commit()

    def createTradeTable(self):
        self.cur.execute("""
        create table "Trade"
        (
            id serial not null,
            "fromUser" uuid not null
                constraint trade_user_id_fk
                    references "User"
                        on update cascade on delete cascade,
            "toUser" uuid not null
                constraint trade_user_id_fk_2
                    references "User"
                        on update cascade on delete cascade,
            item int not null
                constraint trade_items_id_fk
                    references "Items"
                        on update cascade on delete cascade,
            price int not null,
            "tradeTime" timestamp not null
        );
        """)
        self.cur.execute("""
        create unique index trade_id_uindex
            on "Trade" (id);
        """)
        self.conn.commit()

    def createRaidTimeTable(self):
        self.cur.execute("""
        create table "RaidTime"
        (
            id serial not null,
            "lastRaidsTime" timestamp not null
        );
        """)
        self.cur.execute("""
        alter table "RaidTime"
            add "isRaidTime" bool default False;
        """)
        self.conn.commit()

    def insertRaids(self):
        self.cur.execute("""
        Insert Into "Raids" ("locationName", "pz", "pa", "loot", "time") values 
        ('Кладовая', 2, 0, '{"Швабра": 0.58, "Мебельный гвоздь": 8.7, "Стул": 2.9, "Веревка": 5.8, "Простыня": 43.5, "Кепка": 37.7 }', 10)
        """)

    def createFeedbacksTable(self):
        self.cur.execute("""
        create table "Feedbacks"
        (
            id serial not null,
            feedback text,
            author uuid,
            "timeCreated" timestamp
        );
        """)
        self.cur.execute("""
        create unique index feedbacks_id_uindex
            on "Feedbacks" (id);
        """)

        self.cur.execute("""
        alter table "Feedbacks"
            add constraint feedbacks_pk
                primary key (id);
        """)

        self.cur.execute("""
        alter table "Feedbacks"
            add constraint feedbacks_user_id_fk
                foreign key (author) references "User"
                    on update cascade;        
        """)
        self.conn.commit()

    def insertItems(self):
        #TODO: Прописать цены предметам
        self.cur.execute("""
        Insert Into "Items" ("itemName", "category_id", "pz", "pa", "py", "cost") values 
        ('Мебельный гвоздь', 1, 0, 3, 0, 10), ('Стул', 2, 2, 6, 0, 40), 
        ('Вилка', 1, 0, 3, 0, 10), ('Ложка', 1, 0, 1, 0, 5), 
        ('Веревка', 2, 0, 4, 0, 15), ('Нож', 1, 0, 8, 0, 50), 
        ('Ключ', 1, 0, 2, 0, 7), ('Шприц', 1, 0, 5, 1,), 
        ('Ручка', 1, 0, 2, 0), ('Душка от кровати', 2, 2, 7, 0),
        ('Швабра', 2, 2, 6, 0, 40) 
        """)  # Оружие

        self.cur.execute("""
        Insert Into "Items" ("itemName", "category_id", "pz", "pa", "py") values
        ('Бинты на руки', 4, 2, 0, 0), ('Перчатки медицинские', 4, 3, 0, 1),
        ('Порванная на лоскуты простыня', 4, 1, 0, 0), ('Упаковка из-под еды', 4, 1, 0, 0),
        ('Бинты на ноги', 5, 2, 0, 0), ('Бахилы медицинские', 5, 1, 0, 1),
        ('Простыня', 5, 1, 0, 0), ('Большая упаковка из-под еды', 5, 1, 0, 0),
        ('Штаны врача', 6, 5, 0, 2), ('Шорты', 6, 2, 0, 0),
        ('Смирительная рубашка', 7, 6, -2, 1), ('Халат', 7, 3, 0, 1),
        ('Футболка', 7, 2, 0, 0), ('Комбинезон', 7, 4, 0, 0),
        ('Медицинская шапка', 8, 1, 0, 1), ('Кепка', 8, 2, 0, 0),
        ('Шапка из бинтов', 8, 1, 0, 0), ('Дуршлаг', 8, 3, 1, 0)        
        """)
        self.conn.commit()

    def insertCategoryItem(self):
        self.cur.execute("""
        Insert Into "CategoryItem" ("mainCategoryName", "subCategoryName", "itemsCanBeUsed") values
        ('Оружие','Одноручное', 2), ('Оружие', 'Двуручное', 1), ('Оружие', 'Метательное', 1),
        ('Одежда', 'Руки', 1), ('Одежда', 'Обувь', 1), ('Одежда', 'Ноги', 1), ('Одежда', 'Тело', 1), 
        ('Одежда', 'Голова', 1)
        """)
        self.conn.commit()

    def insertLevels(self):
        self.cur.execute("""
        Insert Into "Levels" ("levelName", "class", "minEnergy", "maxEnergy") Values 
        ('Паническое расстройство', 'Пассивный', -100, -90),
        ('Обсессивно-компульсивное расстройство', 'Пассивный', -100, -75),
        ('Депрессия', 'Пассивный', -100, -50),
        ('Эпилепсия', 'Пассивный', -100, -30),
        ('Биполярное аффективное расстройство', 'Пассивный', -100, -15),
        ('Навящивые мысли', 'Пассивный', -100, -1),
        ('Сомнамбулизм', 'Неопределившийся', 0, 60),
        ('Неврастения', 'Неопределившийся', 10, 70),
        ('Клиническая депрессия', 'Неопределившийся', 20, 80),
        ('Синдром деперсонализации', 'Неопределившийся', 30, 90),
        ('Трихотилломания', 'Неопределившийся', 40, 100),
        ('Аутофагия', 'Неопределившийся', 50, 110),
        ('Диссоциативное расстройство личности', 'Активный', 50, 110),
        ('Шизофрения', 'Активный', 50, 110),
        ('Эмоциональная неустойчивость', 'Активный', 50, 110),
        ('Пиромания', 'Активный', 50, 110),
        ('Посттравматическое стрессовое расстройство', 'Активный', 50, 110),
        ('Кататонический синдром', 'Активный', 50, 110)
        """)

    def addNewUser(self, nickname):
        self.cur.execute("""
        INSERT INTO "User" (nickname, "lastMessage") values (%s, %s)
        """, (nickname, datetime.datetime.now()))
        self.conn.commit()

    def addStream(self, streamName, startedAt):
        try:
            self.cur.execute("""
            INSERT INTO "Streams" ("streamName", "startedAt", "endedAt") values
            (%s, %s, NULL)
            """, (streamName, startedAt))
            self.conn.commit()
            self.cur.execute("""
            Select id from "Streams" Where "startedAt" = %s """, [startedAt])
            id = self.cur.fetchone()[0]
            return id
        except Exception as e:
            print(e)

    def setStreamEnd(self, id):
        self.cur.execute("""
        update "Streams" SET "endedAt" = %s Where id = %s;
        """, (datetime.datetime.now(), id))
        self.conn.commit()
        pass

    def getLastStream(self):
        self.cur.execute("""
        select "id" from "Streams" where "endedAt" is NULL
        """)
        id = self.cur.fetchone()[0]
        return id

    def getStreamTimeFrom(self, time):
        self.cur.execute("""
        SELECT "startedAt", "endedAt" From "Streams" Where "endedAt" > %s Or "endedAt" is NULL Order by "startedAt" """, [time])
        res = self.cur.fetchall()
        return res

    def getUserIdByNickname(self, nick):
        self.cur.execute("""
        Select id from "User" Where nickname = %s
        """, [nick])
        id = self.cur.fetchone()
        if id is None:
            return None
        return id[0]

    def getNicknameByUserId(self, user_id):
        self.cur.execute("""
        Select nickname from "User" Where id = %s
        """, [user_id])
        id = self.cur.fetchone()
        if id is None:
            return None
        return id[0]

    def addNewInjection(self, id):
        self.cur.execute("""
        Insert into "Injection" ("userId", "beforeLastInjectionTime") values
        (%s, %s)
        """, (id, datetime.datetime.now()))
        self.conn.commit()

    def getInjectionTime(self, user_id):
        self.cur.execute("""
        select "lastInjectionTime" from "Injection" Where "userId" = %s
        """, [user_id])
        injectionTime = self.cur.fetchone()[0]
        return injectionTime

    def getBeforeLastInjectionTime(self, user_id):
        self.cur.execute("""
        select "beforeLastInjectionTime" from "Injection" Where "userId" = %s
        """, [user_id])
        beforeLastInjectionTime = self.cur.fetchone()[0]
        return beforeLastInjectionTime

    def setBeforeLastInjectionTime(self, user_id, time):
        self.cur.execute("""
        Update "Injection" Set "beforeLastInjectionTime" = %s Where "userId" = %s
        """, [time, user_id])
        self.conn.commit()

    def setInjectionTime(self, user_id, time):
        self.cur.execute("""
        Update "Injection" Set "lastInjectionTime" = %s Where "userId" = %s
        """, (time, user_id))
        self.conn.commit()

    def setEndInjectionTime(self, user_id, time):
        self.cur.execute("""
        Update "Injection" Set "endInjectionTime" = %s Where "userId" = %s
        """, [time, user_id])
        self.conn.commit()

    def stopInjection(self, user_id, endInjectionTime):
        self.cur.execute("""
        Update "Injection" Set "beforeLastInjectionTime" = %s, "lastInjectionTime" = null, "endInjectionTime" = null Where "userId" = %s
        """, (endInjectionTime, user_id))
        self.conn.commit()

    # def getInjectionCount(self, user_id):
    #     self.cur.execute("""
    #     select "countTimes" from "Injection" Where "userId" = %s
    #     """, [user_id])
    #     return self.cur.fetchone()[0]

    def getEndInjectionTime(self, user_id):
        self.cur.execute("""
        select "endInjectionTime" from "Injection" Where "userId" = %s
        """, [user_id])
        return self.cur.fetchone()[0]

    def increaceInjectionCount(self, userId):
        self.cur.execute("""
        select "countTimes" from "Injection" Where "userId" = %s
        """, [userId])
        countTimes = int(self.cur.fetchone()[0]) + 1
        self.cur.execute("""
        Update "Injection" Set "countTimes" = %s Where "userId" = %s
        """, (countTimes, userId))
        self.conn.commit()

    def getBots(self):
        self.cur.execute("""
        SELECT "botName" FROM "Bots" 
        """)
        res = self.cur.fetchall()
        return [i[0] for i in res]

    def insertAllBots(self):
        stringValues = ""
        with open("res\\bots.json", "r") as file:
            res = json.loads(file.read())
            for bot in res['bots']:
                stringValues += f"(\'{bot[0]}\'), "
            stringValues = stringValues[:-2]
        self.cur.execute(f"""
        INSERT INTO "Bots" ("botName") VALUES {stringValues}
        """)
        self.conn.commit()

    def getLastTimeIn(self, nickname):
        self.cur.execute("""
        Select "lastTimeIn" From "User" Where "nickname" = %s
        """, [nickname])
        lastTimeIn = self.cur.fetchone()[0]
        return lastTimeIn

    def getLastTimeOut(self, nickname):
        self.cur.execute("""
        Select "lastTimeOut" From "User" Where "nickname" = %s
        """, [nickname])
        lastTimeOut = self.cur.fetchone()[0]
        return lastTimeOut

    def getTimeCount(self, nickname):
        self.cur.execute("""
        Select "timeCount" From "User" Where "nickname" = %s
        """, [nickname])
        timeCount = int(self.cur.fetchone()[0])
        return timeCount

    def isUserNew(self, nickname):
        self.cur.execute("""
        select "nickname" from "User" where "nickname" = %s""", [nickname])
        user = self.cur.fetchone()
        return user is None

    def setLastTimeIn(self, nickname, lastTimeIn):
        if lastTimeIn is not None:
            self.cur.execute("""
            Update "User" Set "lastTimeIn" = %s Where "nickname" = %s
            """, (lastTimeIn, nickname))
        else:
            self.cur.execute("""
            Update "User" Set "lastTimeIn" = null Where "nickname" = %s
            """, [nickname])
        self.conn.commit()

    def setTimeCount(self, nickname, timeCount):
        self.cur.execute("""
        Update "User" Set "timeCount" = %s Where "nickname" = %s
        """, (timeCount, nickname))
        self.conn.commit()

    def getTimeInStream(self, nickname):
        self.cur.execute("""
        Select "lastTimeIn", "timeCount" from "User" where "nickname" = %s
        """, [nickname])
        res = self.cur.fetchone()
        return res

    def getAllLeftPersons(self, viewers):
        if len(viewers) != 0:
            self.cur.execute(f"""
            Select nickname From "User" Where "lastTimeIn" is not NULL and "nickname" not in ({str(viewers)[1:-1]})
            """)
        else:
            self.cur.execute(f"""
            Select nickname From "User" Where "lastTimeIn" is not NULL
            """)
        res = self.cur.fetchall()
        return res

    def getUserItems(self, user_id):
        self.cur.execute("""
        Select "Items".id, "mainCategoryName", "subCategoryName", "Items"."itemName", "Inventory"."currentFragility", "Items"."fragility", "Inventory"."inUse" From "Inventory"
        Join "Items" ON "Inventory"."itemId" = "Items".id
        Join "CategoryItem" ON "CategoryItem".id = "Items"."category_id"
        Where "Inventory"."userId" = %s
        """, [user_id])
        res = self.cur.fetchall()
        return res

    def getInformationAboutItem(self, item_id):
        self.cur.execute("""
        Select "Items"."itemName", "CategoryItem"."mainCategoryName",
                "CategoryItem"."subCategoryName", "Items"."pz", 
                "Items"."pa", "Items"."py", "Items"."fragility" From "Items" 
        Join "CategoryItem" On "Items"."category_id" = "CategoryItem".id
        Where "Items".id = %s
        """, [item_id])
        res = self.cur.fetchone()
        print(res)
        if res is None:
            return None
        return res

    def getItemIdByItemName(self, itemName):
        self.cur.execute("""
        Select "Items"."id" from "Items" Where "itemName" = %s
        """, [itemName])
        res = self.cur.fetchone()
        if res is None:
            return None
        return res[0]

    def giveItemToUser(self, user_id, item_id, count):
        self.cur.execute("""
        Select "fragility" from "Items" where id = %s
        """, [item_id])
        res = self.cur.fetchone()
        if res is None:
            return
        self.cur.execute("""
        Insert Into "Inventory" ("userId", "itemId", "count", "currentFragility") values
        (%s, %s, %s, %s)
        """, (user_id, item_id, count, res[0]))
        self.conn.commit()

    def useItem(self, user_id, item_id):
        self.cur.execute("""
        Update "Inventory" Set "inUse" = True Where id in (
            Select id From "Inventory" Where
                "userId" = %s and "itemId" = %s and "inUse" = False limit 1
            )
        """, [user_id, item_id])
        self.conn.commit()

    def unuseItem(self, user_id, item_id):
        self.cur.execute("""
        Update "Inventory" Set "inUse" = False Where id in (
            Select id From "Inventory" Where
                "userId" = %s and "itemId" = %s and "inUse" = True limit 1
            )
        """, [user_id, item_id])
        self.conn.commit()

    def isItemInUserInventory(self, user_id, item_id):
        self.cur.execute("""
        Select id from "Inventory" Where "userId" = %s and "itemId" = %s 
        """, [user_id, item_id])
        res = self.cur.fetchone()
        if res is None:
            return False
        return True

    def isUsableItemsExist(self, userId, itemId, isUse):
        self.cur.execute("""
        Select id from "Inventory" Where "userId" = %s and "itemId" = %s and "inUse" = %s
        """, [userId, itemId, isUse])
        res = self.cur.fetchone()
        if res is None:
            return False
        return True

    def getUsableItemsFeatures(self, user_id):
        self.cur.execute("""
            Select "Items".pz, "Items".pa, "Items".py from "Inventory" 
            Join "Items" On "Inventory"."itemId" = "Items".id 
            Where "Inventory"."inUse" = True and "Inventory"."userId" = %s
        """, [user_id])
        res = self.cur.fetchall()
        return res

    def getMaximumItemsInCategory(self, item_id):
        self.cur.execute("""
        select "CategoryItem"."itemsCanBeUsed" from "Items" 
        Join "CategoryItem" On "Items"."category_id" = "CategoryItem".id
        Where "Items".id = %s
        """, [item_id])
        res = self.cur.fetchone()
        if res is None:
            return None
        return res[0]

    def getCountItemsInCategory(self, user_id, item_id):
        self.cur.execute("""
        select count(*) from "Inventory"
        join "Items" On "Items".id = "Inventory"."itemId"
        Join "CategoryItem" On "Items"."category_id" = "CategoryItem".id
        Where category_id = (Select category_id from "Items" where id = %s) and "Inventory"."inUse" = True and "Inventory"."userId" = %s
        """, [item_id, user_id])
        res = self.cur.fetchone()
        return res[0]

    def isItemWeapon(self, item_id):
        self.cur.execute("""
            select "CategoryItem"."mainCategoryName" from "Items" 
            Join "CategoryItem" On "Items"."category_id" = "CategoryItem".id
            Where "Items".id = %s
        """, [item_id])
        res = self.cur.fetchone()
        if res is None or res[0] != 'Оружие':
            return False
        return True

    def getItemById(self, item_id):
        self.cur.execute("""
        Select "Items"."itemName", "CategoryItem"."mainCategoryName",
                "CategoryItem"."subCategoryName", "Items"."pz", 
                "Items"."pa", "Items"."py" From "Items"  
        Join "CategoryItem" On "Items"."category_id" = "CategoryItem".id
        Where "Items".id = %s
        """, [item_id])
        res = self.cur.fetchone()
        if res is None:
            return None
        return res

    def deleteItemFromInventory(self, user_id, item_id):
        self.cur.execute("""
        Delete From "Inventory" Where id in (
        select id from "Inventory" Where "userId" = %s and "itemId" = %s order by "currentFragility" limit 1)
        """, (user_id, item_id))
        self.conn.commit()

    def getAllRaids(self):
        self.cur.execute("""
        Select "locationName" From "Raids"
        """)
        res = self.cur.fetchall()
        return res

    def getRaidIdByLocationName(self, locationName):
        self.cur.execute("""
        Select id From "Raids" Where "locationName" = %s
        """, [locationName])
        res = self.cur.fetchone()
        if res is None:
            return None
        return res[0]

    def createNewRaidParty(self, user_id, raid_id):
        self.cur.execute("""
        Insert Into "RaidParty" ("player1", "partyCreated", "raidId") values (%s, %s, %s)
        """, (user_id, datetime.datetime.now(), raid_id))

    def isUserInRaidParty(self, user_id):
        self.cur.execute("""
        Select id from "RaidParty" Where player1 = %s or player2 = %s or player3 = %s or player4 = %s;
        """, [user_id, user_id, user_id, user_id])
        if self.cur.fetchone() is not None:
            return True
        return False
        pass

    def getIdPartyByUserId(self, user_id):
        self.cur.execute("""
            Select id from "RaidParty" Where player1 = %s or player2 = %s or player3 = %s or player4 = %s;
            """, [user_id, user_id, user_id, user_id])
        res = self.cur.fetchone()
        print(res)
        if res is None:
            return None
        return res[0]

    def getCountPlayersInRaidParty(self, party_id):
        self.cur.execute("""
            Select "countPlayer" from "RaidParty" Where id = %s;
            """, [party_id])
        count = self.cur.fetchone()
        print(count)
        return count[0]

    def joinRaidParty(self, party_id, user_id):
        count = self.getCountPlayersInRaidParty(party_id)
        var = f"player{count + 1}"
        print(var)
        print(user_id, party_id)
        query = sql.SQL("Update \"RaidParty\" Set {} = %s, \"countPlayer\" = %s where id = %s;")
        self.cur.execute(query.format(sql.Identifier(var)), [user_id, count + 1, party_id])
        self.conn.commit()

    def getRaidIdInParty(self, party_id):
        self.cur.execute("""
            Select "raidId" from "RaidParty" Where id = %s;
        """, [party_id])
        res = self.cur.fetchone()
        print(res)
        if res is None:
            return None
        return res[0]

    def getRaidInformation(self, raid_id):
        self.cur.execute("""
        select "locationName", "pz", "pa", loot, "time", "minUserPA" From "Raids" where id = %s
        """, [raid_id])
        res = self.cur.fetchone()
        if res is None:
            return None
        return res
        pass

    def getRaidPartyInformation(self, party_id):
        self.cur.execute("""
        Select id, player1, player2, player3, player4, "countPlayer", "partyCreated", "raidId"
        From "RaidParty"
        Where id = %s
        """, [party_id])
        res = self.cur.fetchone()
        if res == 0:
            return None
        return res

    def exitFromPartyRaid(self, party_id, user_id):
        count = self.getCountPlayersInRaidParty(party_id)
        if count == 1:
            self.deleteRaidParty(party_id)
            return
        info = self.getRaidPartyInformation(party_id)
        if user_id == info[1]: # player1
            self.cur.execute("""
            Update "RaidParty" Set player1 = %s, player2 = %s, player3 = %s, player4 = %s, "countPlayer" = %s where id = %s;
            """, [info[2], info[3], info[4], None, count - 1, party_id])
            self.conn.commit()
        elif user_id == info[2]:  # player2
            self.cur.execute("""
                            Update "RaidParty" Set player2 = %s, player3 = %s, player4 = %s, "countPlayer" = %s where id = %s;
                            """, [info[3], info[4], None, count - 1, party_id])
            self.conn.commit()
        elif user_id == info[3]: # player2
            self.cur.execute("""
                        Update "RaidParty" Set player3 = %s, player4 = %s, "countPlayer" = %s where id = %s;
                        """, [info[4], None, count - 1, party_id])
            self.conn.commit()
        elif user_id == info[4]: # player2
            self.cur.execute("""
                        Update "RaidParty" Set player4 = %s, "countPlayer" = %s where id = %s;
                        """, [None, count - 1, party_id])
            self.conn.commit()

    def deleteRaidParty(self, party_id):
        self.cur.execute("""
        Delete from "RaidParty" where id = %s
        """, [party_id])
        self.conn.commit()
        pass

    def setRaidStarted(self, party_id):
        self.cur.execute("""
        Update "RaidParty" Set "isRaidStarted" = True where id = %s
        """, [party_id])
        self.conn.commit()

    def setRaidEnded(self, party_id):
        partyInfo = self.getRaidPartyInformation(party_id)
        raidInfo = self.getRaidInformation(partyInfo[7])
        self.cur.execute("""
        Update "RaidParty" Set "raidEnded" = %s where id = %s;
        """, [datetime.datetime.now() + datetime.timedelta(minutes=raidInfo[4]), party_id])
        self.conn.commit()

    def getEndedRaids(self):
        self.cur.execute("""
        Select id from "RaidParty" Where "raidEnded" < %s;
        """, [datetime.datetime.now()])
        res = self.cur.fetchall()
        return res

    def getStreamTimeBefore(self, time):
        self.cur.execute("""
        SELECT "startedAt", "endedAt" From "Streams" Where "startedAt" < %s Order by "startedAt" Desc Limit 36;
        """, [time])
        res = self.cur.fetchall()
        return res

    def getPills(self, nickname):
        self.cur.execute("""
        Select pills from "User" where nickname = %s
        """, [nickname])
        res = self.cur.fetchone()
        if res is None:
            return None
        return res[0]

        pass

    def setPills(self, nickname, pills):
        self.cur.execute("""
        Update "User" Set pills = %s Where nickname = %s
        """, [pills, nickname])
        self.conn.commit()

    def increaseMessagesCount(self, name):
        self.cur.execute("""
        Select "messagesCount" From "User" Where nickname = %s
        """, [name])
        res = self.cur.fetchone()
        if res is None:
            return
        print(res[0])
        self.cur.execute("""
            Update "User" Set "messagesCount" = %s Where nickname = %s;
        """, [res[0] + 1, name])
        self.conn.commit()

        pass

    def getMessagesCount(self, name):
        self.cur.execute("""
        Select "messagesCount" From "User" Where nickname = %s
        """, [name])
        res = self.cur.fetchone()
        if res is None:
            return
        return res[0]
        pass

    def addEnergy(self, name, count):
        self.cur.execute("""
        Select "energy" From "User" Where nickname = %s
        """, [name])
        res = self.cur.fetchone()
        if res is None:
            return
        if res[0] + count > 200:
            energy = 200
        elif res[0] + count < -100:
            energy = -100
        else:
            energy = res[0] + count
        self.cur.execute("""
            Update "User" Set "energy" = %s Where nickname = %s;
        """, [energy, name])
        self.conn.commit()
        pass

    def setEnergy(self, name, count):
        self.cur.execute("""
            Update "User" Set "energy" = %s Where nickname = %s;
        """, [count, name])
        self.conn.commit()
        pass

    def getSilenceUsers(self, minutes):
        curTime = datetime.datetime.now()
        delta = datetime.timedelta(minutes=minutes)
        self.cur.execute("""
        Select "nickname" From "User" Where
        ("lastMessage" + %s * interval '1 minute') < %s
        and "lastTimeIn" is not NULL
        """, [minutes, curTime])
        res = self.cur.fetchall()
        return res

    def setLastMessage(self, nickname, time):
        self.cur.execute("""
        Update "User" Set "lastMessage" = %s Where nickname = %s 
        """, [time, nickname])
        self.conn.commit()

    def getCurrentLevel(self, user_id):
        self.cur.execute("""
        Select energy From "User" Where id = %s
        """, [user_id])
        res = self.cur.fetchone()
        if res is None:
            return
        self.cur.execute("""
        Select "levelName", "class" From "Levels" Where "minEnergy" <= %s and "maxEnergy" >= %s
        """, [res[0], res[0]])
        res = self.cur.fetchall()
        return res
        pass

    def setZeroHealth(self, name, value):
        self.cur.execute("""
        Update "User" Set "isHealthZero" = %s Where nickname = %s 
        """, [value, name])
        pass

    def isHealthZero(self, name):
        self.cur.execute("""
        Select "isHealthZero" From "User" Where nickname = %s
        """, [name])
        res = self.cur.fetchone()
        if res is None:
            return None
        return res[0]
        pass

    def getShop(self):
        self.cur.execute("""
        Select * from "Shop";
        """)
        res = self.cur.fetchone()
        if res is None:
            return None
        return res[1:]
        pass

    def getAllItems(self):
        self.cur.execute("""
        Select * from "Items"
        """)
        res = self.cur.fetchall()
        if res is None:
            return None
        return res

    def addShop(self, shopItems):
        self.cur.execute("""
        Insert Into "Shop" ("lastChanges", "currentItem1", "currentItem2", "currentItem3", "currentItem4", "currentItem5")
        Values (%s, %s, %s, %s, %s, %s)
        """, [datetime.datetime.now(), shopItems[0], shopItems[1], shopItems[2], shopItems[3], shopItems[4]])
        self.conn.commit()
        pass

    def getLastChangesTime(self):
        self.cur.execute("""
        Select "lastChanges" From "Shop";
        """)
        res = self.cur.fetchone()
        if res is None:
            return None
        return res[0]

    def shopExist(self):
        self.cur.execute("""
        Select id From "Shop"
        """)
        res = self.cur.fetchone()
        if res is None:
            return False
        return True

    def getPricesForItems(self, items):
        print(items)
        cost = []
        for i in range(0, len(items)):
            self.cur.execute("""
            Select cost From "Items" where "id" = %s;
            """, [items[i]])
            res = self.cur.fetchone()
            if res is None:
                cost.append(0)
            else:
                for item in res:
                    cost.append(item)
        return cost

    def getItemNameByItemId(self, item_id):
        self.cur.execute("""
        Select "itemName" From "Items" Where id = %s
        """, [item_id])
        res = self.cur.fetchone()
        if res is None:
            return None
        return res[0]
        pass

    def isItemSelling(self, item_id):
        self.cur.execute("""
        select id from "Shop" where "currentItem1" = %s or "currentItem2" = %s or "currentItem3" = %s or 
                                    "currentItem4" = %s or "currentItem5" = %s
        """, [item_id, item_id, item_id, item_id, item_id])
        res = self.cur.fetchone()
        if res is None:
            return False
        return True
        pass

    def setItemSelled(self, item_id):
        pos = 0
        shop = self.getShop()
        print(shop, item_id)
        for i in range(1, 6):
            if shop[i] == item_id:
                pos = i
                break
        var = f"currentItem{pos}"
        query = sql.SQL("Update \"Shop\" Set {} = null;")
        self.cur.execute(query.format(sql.Identifier(var)))
        self.conn.commit()
        pass

    def isUserTraiding(self, user_id):
        self.cur.execute("""
        Select id from "Trade" Where "fromUser" = %s
        """, [user_id])
        res = self.cur.fetchone()
        if res is None:
            return False
        return True

    def createTrade(self, fromUserId, toUserId, itemId, price):
        self.cur.execute("""
        Insert Into "Trade" ("fromUser", "toUser", item, price, "tradeTime") values
        (%s, %s, %s, %s, %s)
        """, [fromUserId, toUserId, itemId, price, datetime.datetime.now()])
        self.conn.commit()

    def deleteTrade(self, fromUserId):
        self.cur.execute("""
        Delete From "Trade" Where "fromUser" = %s
        """, [fromUserId])
        self.conn.commit()
        pass

    def isUserTradeingWithUser(self, fromUserId, toUserId):
        self.cur.execute("""
                Select id from "Trade" Where "fromUser" = %s and "toUser" = %s
                """, [fromUserId, toUserId])
        res = self.cur.fetchone()
        if res is None:
            return False
        return True
        pass

    def getTradeIdByUserFrom(self, fromUserId):
        self.cur.execute("""
        Select id from "Trade" Where "fromUser" = %s
        """, [fromUserId])
        res = self.cur.fetchone()
        if res is None:
            return None
        return res[0]

    def getItemIdFromTrade(self, tradeId):
        self.cur.execute("""
            Select item from "Trade" Where id = %s
            """, [tradeId])
        res = self.cur.fetchone()
        if res is None:
            return None
        return res[0]
        pass

    def getPriceFromTrade(self, tradeId):
        self.cur.execute("""
            Select price from "Trade" Where id = %s
            """, [tradeId])
        res = self.cur.fetchone()
        if res is None:
            return None
        return res[0]
        pass

    def deleteOldTrades(self, minutes):
        self.cur.execute("""
        Delete From "Trade" Where "tradeTime" < %s
        """, [datetime.datetime.now() - datetime.timedelta(minutes=minutes)])
        self.conn.commit()

        pass

    def getTrade(self, tradeId):
        self.cur.execute("""
        Select "fromUser", "toUser", "item", price, "tradeTime" From "Trade" where id = %s
        """, [tradeId])
        res = self.cur.fetchone()
        return res

    def getCountRaids(self, userId):
        self.cur.execute("""
        Select "countRaids" from "User" where id = %s
        """, [userId])
        res = self.cur.fetchone()
        if res is None:
            return None
        return res[0]

    def increaseRaids(self, userId):
        raids = self.getCountRaids(userId)
        self.cur.execute("""
        Update "User" Set "countRaids" = %s Where id = %s
        """, [raids + 1, userId])
        self.conn.commit()

    def getCountCert(self, userId):
        self.cur.execute("""
        Select "countCert" from "User" where id = %s
        """, [userId])
        res = self.cur.fetchone()
        if res is None:
            return None
        return res[0]

    def increaseCerts(self, userId):
        certs = self.getCountCert(userId)
        self.cur.execute("""
        Update "User" Set "countCert" = %s where id = %s
        """, [certs + 1, userId])
        self.conn.commit()

    def setUserIndexes(self, userId, pz, pa, py):
        self.cur.execute("""
        Update "User" Set pz = %s, pa = %s, py = %s Where id = %s
        """, [pz, pa, py, userId])
        self.conn.commit()

        pass

    def getUserIndexes(self, userId):
        self.cur.execute("""
        select "pz", "pa", "py" from "User" where id = %s
        """, [userId])
        res = self.cur.fetchone()
        if res is None:
            return None
        return res

    def insertFeedback(self, message, author):
        self.cur.execute("""
        Insert Into "Feedbacks" ("feedback", "author", "timeCreated") values 
        (%s, %s, %s)
        """, [message, author, datetime.datetime.now()])

    def isTimeChangeShop(self, minutes):
        self.cur.execute("""
        Select id From "Shop" Where "lastChanges" < %s;
        """, [datetime.datetime.now() - datetime.timedelta(minutes=minutes)])
        res = self.cur.fetchone()
        if res is None:
            return False
        return True
        pass

    def deleteShop(self):
        self.cur.execute("""
        Delete From "Shop"
        """)
        self.conn.commit()
        pass

    def getUsableItems(self, userId):
        self.cur.execute("""
        Select "itemId", "count", "currentFragility" from "Inventory" where "userId" = %s and "inUse" = True
        """, [userId])
        res = self.cur.fetchall()
        return res

    def setCurrentFragility(self, userId, itemId, fragility):
        self.cur.execute("""
        Update "Inventory" Set "currentFragility" = %s Where "userId" = %s and "itemId" = %s and "inUse" = True
        """, [fragility, userId, itemId])
        pass

    def deleteItemFromInventoryByFragility(self, userId, itemId):
        self.cur.execute("""
        Delete From "Inventory" Where id in (
        select id from "Inventory" Where "userId" = %s and "itemId" = %s and "currentFragility" = 1 limit 1)
        """, (userId, itemId))
        self.conn.commit()
        pass

    def isItemUsable(self, userId, itemId):
        self.cur.execute("""
        Select id From "Inventory" WHERE "userId" = %s and "itemId" = %s and "inUse" = True
        """, [userId, itemId])
        res = self.cur.fetchone()
        if res is None:
            return False
        return True
        pass

    def getPossibleRaids(self, currentPa, certCount):
        self.cur.execute("""
        Select "locationName" From "Raids" where "minUserPA" <= %s and "tierCert" = %s 
        """, [currentPa, certCount])
        res = self.cur.fetchall()
        return res

    def getMinUserPA(self, raidId):
        self.cur.execute("""
        Select "minUserPA" From "Raids" Where id = %s
        """, [raidId])
        res = self.cur.fetchone()
        if res is None:
            return None
        return res[0]
        pass

    def getPillsFromRaid(self, raidId):
        self.cur.execute("""
        Select "minPills", "maxPills" From "Raids" Where id = %s
        """, [raidId])
        res = self.cur.fetchone()
        return res
        pass

    def getTopByTime(self, topCount):
        self.cur.execute("""
        Select id, 
        coalesce("timeCount" + EXTRACT(EPOCH FROM (%s - "lastTimeIn")) / 60, "timeCount") as t 
        From "User" Where nickname != 'pu1se0' order by t DESC LIMIT %s;
        """, [datetime.datetime.now(), topCount])
        return self.cur.fetchall()
        pass

    def getCurrentPositionInTimeTop(self, userId):
        self.cur.execute("""
        WITH summary AS (
            Select id,
                   ROW_NUMBER()
                   OVER (order by coalesce("timeCount" + EXTRACT(EPOCH FROM (%s - "lastTimeIn")) / 60,
                                           "timeCount") DESC) as t
            From "User"
            order by t DESC
        )
        Select s.t From summary s Where id = %s;
        """, [datetime.datetime.now(), userId])
        res = self.cur.fetchone()
        if res is None:
            return None
        return res[0]

    def getTopByPills(self, topCount):
        self.cur.execute("""
        Select id, 
        coalesce("pills" + (EXTRACT(EPOCH FROM (%s - "lastTimeIn")) / 60)::int / 20, "pills") as t 
        From "User" Where nickname != 'pu1se0' order by t DESC LIMIT %s;
        """, [datetime.datetime.now(), topCount])
        return self.cur.fetchall()
        pass

    def getCurrentPositionInPillsTop(self, userId):
        self.cur.execute("""
        WITH summary AS (
            Select id,
                   ROW_NUMBER()
                   OVER (order by coalesce("pills" + (EXTRACT(EPOCH FROM (%s - "lastTimeIn")) / 60)::int / 20, "pills") DESC) as t
            From "User"
            order by t DESC
        )
        Select s.t From summary s Where id = %s;
        """, [datetime.datetime.now(), userId])
        res = self.cur.fetchone()
        if res is None:
            return None
        return res[0]

    def getTopByRaids(self, topCount):
        self.cur.execute("""
        Select id, 
        "countRaids" as t 
        From "User" Where nickname != 'pu1se0' order by t DESC LIMIT %s;
        """, [topCount])
        return self.cur.fetchall()
        pass

    def getCurrentPositionInRaidsTop(self, userId):
        self.cur.execute("""
        WITH summary AS (
            Select id,
                   ROW_NUMBER()
                   OVER (order by "countRaids" DESC) as t
            From "User"
            order by t DESC
        )
        Select s.t From summary s Where id = %s;
        """, [userId])
        res = self.cur.fetchone()
        if res is None:
            return None
        return res[0]

    def getTopByCerts(self, topCount):
        self.cur.execute("""
        Select id, 
        "countCert" as t 
        From "User" Where nickname != 'pu1se0' order by t DESC LIMIT %s;
        """, [topCount])
        return self.cur.fetchall()
        pass

    def getCurrentPositionInCertsTop(self, userId):
        self.cur.execute("""
        WITH summary AS (
            Select id,
                   ROW_NUMBER()
                   OVER (order by "countCert" DESC) as t
            From "User"
            order by t DESC
        )
        Select s.t From summary s Where id = %s;
        """, [userId])
        res = self.cur.fetchone()
        if res is None:
            return None
        return res[0]

    def getTierCert(self, raidId):
        self.cur.execute("""
        Select "tierCert" From "Raids" Where id = %s
        """, [raidId])
        res = self.cur.fetchone()
        if res is None:
            return None
        return res[0]

    def getEnergy(self, userId):
        self.cur.execute("""
        Select energy from "User" where id = %s
        """, [userId])
        res = self.cur.fetchone()
        if res is None:
            return None
        return res[0]

    def isRaidLastInTierCert(self, raidId):
        tier = self.getTierCert(raidId)
        self.cur.execute("""
        Select id from "Raids" where "tierCert" = %s Order By "minUserPA" DESC
        """, [tier])
        res = self.cur.fetchall()
        print(res)
        if res[0][0] == raidId:
            return True
        return False
        pass

    def createRaidTime(self):
        self.cur.execute("""
        Insert Into "RaidTime" ("lastRaidsTime", "isRaidTime") values 
        (%s, %s)
        """, [datetime.datetime.now(), False])
        self.conn.commit()

    def getLastRaidsTime(self):
        self.cur.execute("""
        Select "lastRaidsTime" from "RaidTime"
        """)
        res = self.cur.fetchone()
        if res is None:
            return None
        return res[0]

    def isRaidTime(self):
        self.cur.execute("""
            Select "isRaidTime" from "RaidTime"
            """)
        res = self.cur.fetchone()
        if res is None:
            return None
        return res[0]

    def setRaidsTime(self, status):
        self.cur.execute("""
        Update "RaidTime" Set "lastRaidsTime" = %s, "isRaidTime" = %s
        """, [datetime.datetime.now(), status])

    def deleteNotReadyParties(self):
        self.cur.execute("""
            Delete From "RaidParty" Where "isRaidStarted" = FALSE 
        """)
        self.conn.commit()
        pass

    def isRaidStarted(self, partyId):
        self.cur.execute("""
        Select "isRaidStarted" from "RaidParty" where id = %s 
        """, [partyId])
        res = self.cur.fetchone()
        if res is None:
            return False
        return res[0]
        pass