# -*- coding: utf-8 -*-
import os
import sqlite3
import datetime

class dbDriver(object) :

    def __init__(self, fileToConnect) :
        self.dbFile = fileToConnect
        self.lastError = None # functions put here their errors
        self.conn = None
        self.cur = None
        self.debug = False

    # returns the path to the script
    def getScriptPath(self) :
        result = os.path.dirname(os.path.realpath(__file__))
        return result
    
    # connect to database
    # returns:
    #     True - if successfully connected
    #     False - if file not exists or connection failed
    # changes:
    #     self.conn - puts the connection
    #     self.cur - puts the cursor for connection
    def connect(self) :
        self.lastError = None
        # make full path if path is relational
        if self.dbFile.startswith('../') :
            try :
                self.dbFile = self.getScriptPath() + "/" + self.dbFile
            except Exception as ex:
                self.lastError = ex.args
                return False
        # check if file exists
        if not(os.path.isfile(self.dbFile)) :
            self.lastError = "No such file:", self.dbFile
            return False
        # trying to connect
        try :
            self.conn = sqlite3.connect(self.dbFile)
            self.cur = self.conn.cursor()
        except Exception as ex :
            self.lastError = ex.args
            return False
        return True

    # returns queries list from db
    def getQueriesDB(self) :
        result = []
        self.lastError = None
        selectQuery = '''select requestLink from tblRequests'''

        try :
            self.cur.execute(selectQuery)
        except Exception as ex :
            self.lastError = ex.args
            return result
        
        rows = self.cur.fetchall()
        for row in rows :
            result.append(row[0])

        return result

    # saves given ad to db
    # returns:
    #     True - if success
    #     False - if failed
    def writeAd(self, inAd) :
        self.lastError = None

        insertQuery = '''INSERT INTO tblAd(intID, title, rooms, owner, 
                                           floor, floors, price, square,
                                           liveSquare, kitchenSquare, 
                                           link, year, desc, district, 
                                           updateDate) VALUES(
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''

        try :
            self.cur.execute(insertQuery, (inAd.intID, inAd.title,
                                           inAd.rooms, inAd.owner,
                                           inAd.floor, inAd.floors,
                                           inAd.price, inAd.square,
                                           inAd.squareLive,
                                           inAd.squareKitchen,
                                           inAd.link, inAd.year,
                                           inAd.desc, inAd.district,
                                           inAd.date))
            self.conn.commit()
        except Exception as ex :
            self.lastError = ex.args
            return False
        return True


    # returns True if ad is already sent with the same price
    # returns False if is not sent
    def alreadySentAd(self, inAd, inToday) :
        self.lastError = None
        selectQuery = '''select count(*) from tblAd 
                         where intID=? and price=?'''
        if inToday :
            selectQuery += ''' and sendDate=?'''
        else :
            selectQuery += ''' and sendDate is not null'''

        try :
            if inToday :
                self.cur.execute(selectQuery, (inAd.intID, inAd.price,
                        datetime.datetime.today().strftime('%Y-%m-%d')))
            else :
                self.cur.execute(selectQuery, (inAd.intID, inAd.price))
            if self.cur.fetchone()[0] > 0 :
                return True
            else :
                return False
        except Exception as ex :
            self.lastError = ex.args
            return False

    # returns True if ad exists in DB (but not sent)
    # returns False in other
    def isAdSaved(self, inAd) :
        self.lastError = None
        selectQuery = '''select count(*) from tblAd 
                         where intID=? and price=? 
                         and updateDate=? and sendDate is null'''
        
        try :
            self.cur.execute(selectQuery,
                        (inAd.intID, inAd.price,
                        datetime.datetime.today().strftime('%Y-%m-%d')))
            if self.cur.fetchone()[0] > 0 :
                return True
            else :
                return False
        except Exception as ex :
            self.lastError = ex.args
            return False


    # updates tblAd.sendDate
    # returns True if success, False if failed
    def updateSendDate(self, inAd) :
        self.lastError = None

        selectQuery = '''select id from tblAd 
                         where intID=? and price=? and updateDate=?
                         order by id desc'''
        updateQuery = '''update tblAd set sendDate=? where id=?'''

        try :
            self.cur.execute(selectQuery, (inAd.intID, inAd.price,
                                           str(inAd.date)))
            rowID = self.cur.fetchone()[0]
            self.cur.execute(updateQuery,
                        (datetime.datetime.today().strftime('%Y-%m-%d'),
                         rowID))
            self.conn.commit()
            return True
        except Exception as ex :
            self.lastError = ex.args
            return False

    # updates tblAd.phones
    # returns True if successfully updated, False if failed
    def updatePhonesDB(self, inAd=None, intID=None, link=None, inPhones=None) :
        self.lastError = None
        updateQuery = '''update tblAd set phones=?'''
        if intID :
            updateQuery += ''' where intID=?'''
        elif link :
            updateQuery += ''' where link=?'''

        try :
            if not(self.conn) :
                self.conn = sqlite3.connect(self.dbFile)
                self.cur = self.conn.cursor()
            if intID :
                self.cur.execute(updateQuery, (inPhones, intID))
            elif link :
                self.cur.execute(updateQuery, (inPhones, link))
            #self.cur.execute(updateQuery, (inPhones, inAd.link))
            self.conn.commit()
            return True
        except Exception as ex :
            self.lastError = ex.args
            return False
    # returns phones from db, if any
    # returns None if no phones
    def getPhonesFromDB(self, inLink=None, inID=None) :
        self.lastError = None
        result = None
        if inLink :
            selectQuery = '''select phones from tblAd 
                             where link=? and phones is not null
                             order by updateDate desc'''
        elif inID :
            selectQuery = '''select phones from tblAd 
                             where intID=? and phones is not null
                             order by updateDate desc'''
        else :
            self.lastError = "No suitable ID to look for phones"
            return None


        try :
            if not(self.conn) :
                self.conn = sqlite3.connect(self.dbFile)
                self.cur = self.conn.cursor()
            if inLink :
                self.cur.execute(selectQuery, (inLink,))
            elif inID :
                self.cur.execute(selectQuery, (inID,))
            result = self.cur.fetchone()
            if not(result is None) :
                result = str(result[0])
            else :
                result = None
            return result
        except Exception as ex :
            self.lastError = ex.args
            return False

    def getPhotosFromDB(self, inLink=None, inID=None) :
        self.lastError = None
        result = None
        if inLink :
            selectQuery = '''select photos from tblAd
                             where link=? and photos is not null
                             order by updateDate desc'''
        elif inID :
            selectQuery = '''select photos from tblAd
                             where intID=? and photos is not null
                             order by id desc'''
        try :
            if not(self.conn) :
                self.conn = sqlite3.connect(self.dbFile)
                self.cur = self.conn.cursor()
            if inLink :
                self.cur.execute(selectQuery, (inLink,))
            elif inID :
                self.cur.execute(selectQuery, (inID,))
            result = self.cur.fetchone()
            if not(result is None) :
                result = str(result[0])
            else :
                result = None
            return result
        except Exception as ex :
            self.lastError = ex.args
            return False
    
    def updatePhotosDB(self, inAd=None, intID=None, link=None, inPhotos=None) :
        self.lastError = None
        updateQuery = '''update tblAd set photos=?'''
        if intID :
            updateQuery += ''' where intID=?'''
        elif link :
            updateQuery += ''' where link=?'''

        photosText = ""
        for photo in inPhotos :
            photosText += photo + "\n"
        photosText = photosText.strip()

        try :
            if not(self.conn) :
                self.conn = sqlite3.connect(self.dbFile)
                self.cur = self.conn.cursor()
            if intID :
                self.cur.execute(updateQuery, (photosText, intID))
            elif link :
                self.cur.execute(updateQuery, (photosText, link))
            self.conn.commit()
            return True
        except Exception as ex :
            self.lastError = ex.args
            return False
