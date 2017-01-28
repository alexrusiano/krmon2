#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import os
import datetime
import requests
import re
from bs4 import BeautifulSoup
import telebot
#   my modules
import krAd
import krResultPage
import krDetailsPage
import krDbDriver

# program parameters
DEBUG = False
LOCALDEBUG = False
SEND = True
DBFILE = ""
TOKEN = ""

bot = None

# file routine
def getScriptName() :
    return os.path.realpath(__file__)

# file routine
def getScriptPath() :
    return os.path.dirname(getScriptName())

# reads parameters from config file
# returns True if success
# returns False if failed
def readParameters() :
    global DEBUG
    global SEND
    global DBFILE
    global TOKEN
    #result = False

    # open config file
    try :
        configFile = open(getScriptPath() + "/../config/krmon.config")
    except Exception as ex :
        print("Failed to open config file", ex.args)
        return False
    # read parameters
    for line in configFile :
        if line.startswith("DBFILE") :
            try :
                DBFILE = line.strip().split('=')[1]
            except Exception as ex :
                print("Error while returning DBFILE parameter", ex.args)
                configFile.close()
                return False
        if line.startswith("DEBUG") :
            DEBUG = True
        if line.startswith("LOCALDEBUG") :
            LOCALDEBUG = True
        if line.startswith("SEND") :
            SEND = True
        if line.startswith("TOKEN") :
            try :
                TOKEN = line.strip().split('=')[1]
            except Exception as ex :
                print("Error while returning TOKEN parameter", ex.args)
                configFile.close()
                return False
    configFile.close()
    return True


def checkSite(inBot=None, chatID=None) :
    # creating db object and connecting to the db
    dbs = krDbDriver.dbDriver(DBFILE)
    if not(dbs.connect()) :
        print("Unable to connect the database:", dbs.lastError)
        return False
    elif DEBUG :
        print("Successfully connected to the database")
    # getting urls to parse
    monitoredLinks = None
    monitoredLinks = dbs.getQueriesDB()
    if not(monitoredLinks) :
        print("Could not obtain links to check:", dbs.lastError)
        dbs.conn.close()
        return False
    # processing the links
    for monitoredLink in monitoredLinks :
        if DEBUG :
            print("Starting URL processing:", monitoredLink)
        results = krResultPage.resultPage()
        results.urls.append(monitoredLink)
        results.debug = DEBUG
        # receiving today ads
        if not(results.getTodayAds(monitoredLink)) :
            print("Couldn't obtain results:", results.lastError)
        # checking if list is empty
        if len(results.ads) == 0 :
            if DEBUG :
                print("Nothing to send :(")
            if inBot :
                try :
                    inBot.send_message(chatID, "Nothing to send")
                except Exception as ex :
                    print("Unable to send message:", ex.args)
            else :
                print("Nothing to send :(")
        else :
            # flag to check if nothing was sent
            sentSome = False
            # process each ad
            for ad in results.ads :
                # if ad have been sent already sent today - 
                # skip the iteration
                if dbs.alreadySentAd(ad, inToday=True) :
                    continue
                sentSome = True
                if inBot :
                    try :
                        if dbs.alreadySentAd(ad, inToday=False) :
                            # if ad was sent earlier -send without link
                            inBot.send_message(chatID, ad.toString())
                        else :
                            # if ad was never sent - send it with link
                            inBot.send_message(
                                chatID, ad.toString(includeLink=True))
                        dbs.writeAd(ad)
                        dbs.updateSendDate(ad)
                    except Exception as ex :
                        if DEBUG :
                            print("Unable to send message:", ex.args)
                else :
                    if dbs.alreadySentAd(ad, False) :
                        print(ad.toString())
                    else :
                        print(ad.toString(includeLink=True))
                    if not(dbs.writeAd(ad)) :
                        print(dbs.lastError)
                    if not(dbs.updateSendDate(ad)) :
                        print(dbs.lastError)
    if not(sentSome) :
        inBot.send_message(chatID, "Noting to send :(")
    dbs.conn.close()
    return True
                

def getPhones(inBot=None, inMessage=None, intID=None) :
    if not(intID) :
        return False
    dbs = krDbDriver.dbDriver(DBFILE)
    phones = dbs.getPhonesFromDB(inID=intID)
    if phones :
        if inBot :
            try :
                inBot.reply_to(inMessage, phones + "\nfrom: db")
            except Exception as ex :
                inBot.reply_to(inMessage, ex.args)
                if DEBUG :
                    print("Unable to send phones:", ex.args)
        else :
            print(phones, "\nfrom: db")
    else :
        if dbs.lastError :
            print(dbs.lastError)
            return False
        details = krDetailsPage.detailsPage()
        details.prepareLoading(details.detailsPrefix + intID)
        if not(details.getPhones()) :
            if inBot :
                inBot.reply_to(inMessage, \
                    "Error while receiving phones from the site")
            else :
                if DEBUG :
                    print("Error while receiving phones:", \
                            details.lastError)
            return False
        else :
            if inBot :
                inBot.reply_to(inMessage, details.phones + "\nfrom: site")
            else :
                print(details.phones, "\nfrom: site")
            if not(dbs.updatePhonesDB(
                    intID=intID, inPhones=details.phones)) :
                print(dbs.lastError)
    return True

def getPhotos(inBot=None, inMessage=None, intID=None) :
    if not(intID) :
        return False
    dbs = krDbDriver.dbDriver(DBFILE)
    photos = dbs.getPhotosFromDB(inID=intID)
    if photos :
        if inBot :
            try :
                print(photos)
                for photo in photos.split('\n') :
                    inBot.reply_to(inMessage, "from: db\n" + photo)
            except Exception as ex :
                    inBot.reply_to(inMessage, ex.args)
                    if DEBUG :
                        print("Unable to send photos:", ex.args)
        else :
            print(photos, "\nfrom: db")
    else :
        if dbs.lastError :
            print(dbs.lastError)
            return False
        details = krDetailsPage.detailsPage()
        details.load(details.detailsPrefix + intID)
        if not(details.getPhotos()) :
            if DEBUG :
                print("Error while receiving photos:", \
                        details.lastError)
                return False
        else :
            if inBot :
                for photo in details.photos :
                    inBot.reply_to(inMessage, "from: site\n" + photo)
            else :
                print(details.photos, "from: site")
            if not(dbs.updatePhotosDB(
                    intID=intID, inPhotos=details.photos)) :
                print(dbs.lastError)
    return True

def main() :
    while True :
        command = input("Enter a command:")
        if command == "check" :
            checkSite()
        if command.startswith("phone") :
            getPhones(intID=command.split(' ')[1])
        if command.startswith("photo") :
            getPhotos(intID=command.split(' ')[1])
        if command == "exit" :
            sys.exit()
    return 0

# reading the parameters
if not(readParameters()) :
    sys.exit()
elif DEBUG :
    print("Started with parameters:\n\tDEBUG: True\n\tLOCALDEBUG:", \
          LOCALDEBUG, "\n\tSEND:", SEND, "\n\tDBFILE:", DBFILE, \
          "\n\tTOKEN:", TOKEN)

if SEND :
    bot = None
    try :
        bot = telebot.TeleBot(TOKEN)
    except Exception as ex :
        print("Error while starting the bot:", ex.args)
        sys.exit()

@bot.message_handler(commands=['check'])
def command_check(message) :
    checkSite(bot, message.chat.id)

@bot.message_handler(commands=['phone'])
def command_phone(message) :
    try :
        intID = re.findall('(\d{8,})', message.reply_to_message.text)[0]
        getPhones(bot, message, intID)
    except Exception as ex :
        bot.reply_to(message, ex.args)

@bot.message_handler(commands=['photo'])
def command_photo(message):
    try :
        intID = re.findall('\d{8,}', message.reply_to_message.text)[0]
        getPhotos(bot, message, intID)
    except Exception as ex :
        bot.reply_to(message, ex.args)


@bot.message_handler(func=lambda message: True)
def default_command(message) :
    bot.reply_to(message, "Try another way")

# starting the bot if needed
if SEND :
    bot.polling(none_stop=True, interval=3)

if __name__ == '__main__' and not(bot):
    main()