# -*- coding: utf-8 -*-
import datetime

class Ad(object) :

    def __init__(self) :
        self.date = datetime.datetime.today().strftime('%Y-%m-%d')
        self.intID = '-'
        self.price = 0.0
        self.floor = 0
        self.floors = 0
        self.district = '-'
        self.link = '-'
        self.title = '-'
        self.owner = '-'
        self.square = 0
        self.squareKitchen = 0
        self.squareLive = 0
        self.rooms = 0
        self.desc = '-'
        self.phones = '-'
        self.photos = '-'

    def toString(self, includeLink=False) :
        result = ""
        #result += self.title + "\n"
        result += str(self.price) + u" млн: " + str(self.rooms) + u"-шка "
        result += str(self.square) + "/" \
                  + str(self.squareLive) + "/" \
                  + str(self.squareKitchen)
        result += "; " + str(self.floor) + "/" + str(self.floors) + "\n"
        for item in self.title.split(', ')[1:] :
            result += item + ", "
        result += self.district + "; " + self.owner + "\n"
        if includeLink :
            result += self.link
        else :
            result += "id:" + self.intID
        return result

