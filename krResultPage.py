# -*- coding: utf-8 -*-
import requests
import datetime
import re
from bs4 import BeautifulSoup
import krAd

class resultPage(object) :
    
    def __init__(self) :
        self.ads = []
        self.urls = []
        self.session = None
        self.pageContent = None
        self.headers = {}
        self.lastError = None
        self.finished = False
        self.pageCount = -1
        self.adsPerPage = 20
        self.debug = False

        
    def prepareLoad(self) :
        self.headers = {}
        # creating session and setting its parameters
        self.session = requests.Session()
        self.session.headers = {}
        self.session.headers["User-agent"] = \
                    '"Mozilla/5.0 (X11; Linux i686; rv:43.0) Gecko/20100101' \
                    + ' Firefox/43.0 Iceweasel/43.0.4"'

        return True

    
    def load(self, urlToLoad=None, fileToLoad=None) :
        if urlToLoad :
            self.urls.append(urlToLoad)
            try :
                pageResponse = self.session.get(urlToLoad)
            except Exception as ex :
                self.lastError = ex.args
                return False
            self.pageContent = pageResponse.text
        elif fileToLoad :
            try :
                self.pageContent = open(fileToLoad).read()
            except Exception as ex :
                self.lastError = ex.args
                return False
        else :
            return False
        return True

    
    def countPages(self) :
        result = 0
        soup = BeautifulSoup(self.pageContent, 'lxml')
        pCountSoup = soup(
            "a", {"class" : re.compile("^btn paginator-page-btn")})
        for pageLink in pCountSoup :
            try :
                pageNumber = int(pageLink.get_text())
            except :
                continue
            if pageNumber > result :
                result = pageNumber
        return result

    def getTodayAds(self, urlToLoad=None, fileToLoad=None) :
        self.prepareLoad()
        self.ads = []
        if urlToLoad :
            if not(self.load(urlToLoad)) :
                return False
        elif fileToLoad :
            if not(self.load(None, fileToLoad)) :
                return False
        self.parse()
        pageCounter = 1
        while not(self.finished) :
            pageCounter += 1
            if self.debug :
                print("Going to page", str(pageCounter))
            self.load(urlToLoad + "&page=" + str(pageCounter))
            self.parse()
            if self.debug :
                print("ADs count:", len(self.ads))
        return True
        

    def getDateByString(self, inStr):
        result = ""
        #   parse date from ad and return formalized value
        months = {u'января' : '01', u'февраля' : '02', u'марта' : '03',
                u'апреля' : '04', u'мая' : '05', u'июня' : '06', 
                u'июля' : '07', u'августа' : '08', u'сентября' : '09',
                u'октября' : '10', u'ноября' : '11', u'декабря' : '12'}
        
        dateset = inStr.split(' ')
        day = dateset[0]
        if day == "19" :
            day = "20"
        if len(day) == 1 :
            day = "0" + day
        month = months[dateset[1]]
        today = datetime.datetime.now()
        alldate = str(today.year) + "-" + month + "-" + day
        result = \
                 datetime.datetime.strptime(alldate, "%Y-%m-%d").strftime('%Y-%m-%d')
        
        return result
        
    def parse(self) :
        #self.ads = []
        # returns array of strings (messages)
        soup = BeautifulSoup(self.pageContent, 'lxml')
        adsSoup = soup.findAll("div", {"id" : re.compile("^id-[0-9]*")})
        for adSoup in adsSoup :
            apt = krAd.Ad()
            # get ad date
            apt.date = adSoup.find(
                "span", {"class" : "a-date status-item"}
            ).get_text().strip()
            apt.date = self.getDateByString(apt.date)
            # check if is today ad
            if apt.date != datetime.datetime.today().strftime('%Y-%m-%d') :
                self.finished = True
                return True
            # get ad id
            apt.intID = adSoup.get("data-id")
            # get ad price
            priceText = adSoup.find(
                "span", {"class" : "a-price-value"}).get_text()
            apt.price = float(re.findall("([0-9\.]+)", priceText)[0])
            # check if 
            subtitle = adSoup.find("div", {"class" : "a-subtitle"}).text
            subtitle = subtitle.split(", ")
            # get floors
            try :
                floors = re.findall('(\d+) .*? (\d+)', subtitle[2])
            except :
                pass
            try :
                apt.floor = int(floors[0][0])
            except :
                pass
            try :
                apt.floors = int(floors[0][1])
            except :
                pass
            # get district
            try :
                apt.district = re.findall('^(.*) ', subtitle[1])[0]
            except :
                pass
            # get square
            try :
                apt.square = int(float(re.findall('(\d+)', subtitle[3])[0]))
            except :
                pass
            # get link
            apt.link = "https://krisha.kz" + adSoup.div.a.get("data-href")
            # get title
            title = adSoup.find("a", {"class" : "link"})
            apt.title = title.get_text()
            # get owner
            owner = adSoup.find("div", {"class" : re.compile("^user-info")})
            owner = owner.get("class")
            if "owner" in owner :
                apt.owner = "Хозяин"
            else :
                apt.owner = "Риэлтор"
            apt.rooms = int(apt.title[0])
            apt.desc = adSoup.find("div", {"class" : "a-text"}).text.strip()
            descArr = apt.desc.split(", ")
            for desc in descArr :
                if u"жил. площадь" in desc :
                    try :
                        apt.squareLive = int(re.findall('(\d+)', desc)[0])
                    except :
                        pass
                if u"кухня" in desc :
                    try :
                        apt.squareKitchen = int(re.findall('(\d+)', desc)[0])
                    except :
                        pass
                if u"г.п." in desc :
                    try :
                        apt.year = int(re.findall('(\d+)', desc)[0])
                    except :
                        pass
            self.ads.append(apt)