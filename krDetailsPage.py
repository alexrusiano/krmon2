# -*- coding: utf-8 -*-
import requests
import re
import datetime
from bs4 import BeautifulSoup
import krAd


class detailsPage(object) :

    def __init__(self) :
        self.intID = ''
        self.phones = '-'
        self.photos = []
        self.pageContent = None
        self.headers = {}
        self.phoneLinkPrefix = 'https://krisha.kz/a/ajaxPhones?id='
        self.detailsPrefix = 'https://krisha.kz/a/show/'
        self.phoneLink = ''
        self.lastError = None
        self.session = None

    def toString(self) :
        result = ""
        result += "ID: " + self.intID + "\n"
        result += "Photos:\n"
        for photo in self.photos :
            result += '\t' + photo + '\n'
        result += self.phones
        return result
        
    def prepareLoading(self, detailsURL) :
        # creating session and setting its parameters
        self.session = requests.Session()
        self.session.headers = {}
        self.session.headers["User-agent"] = \
                    '"Mozilla/5.0 (X11; Linux i686; rv:43.0) Gecko/20100101' \
                    + ' Firefox/43.0 Iceweasel/43.0.4"'

        # get internal ID for compiling phone link
        try :
            self.intID = re.findall('(\d{8})', detailsURL)[0]
        except Exception as ex :
            self.lastError = ex.args
            return False

        # compile phone link
        self.phoneLink = self.phoneLinkPrefix + self.intID
        
        return True

    def getPhotos(self) :
        '''
        INTERNAL FUNCTION
        Checks the self.pageContent for photos links
        output:
        * True - if photo links found
        * False - if photo links not found
        * self.photos - array of links to photos (if True returned)
        * self.photos - empty array (if False returned)
        * self.lastError - last error message
        '''
        
        soup = BeautifulSoup(self.pageContent, 'lxml')
        photoSoup = soup("a", {"class" : "small-thumb"})

        self.photos = []
        if len(photoSoup) == 0 :
            return False

        for photo in photoSoup :
            self.photos.append(photo.get('href').strip())

        return True

    
    def getPhones(self) :
        '''
        INTERNAL FUNCTION
        Compiles the phones link and gets phones
        We can receive phones only by reading response to ajax request
        output:
        * True - if phones successfully loaded
        * False - if error was encountered
        * self.phones - resulted phones string (comma-separated) (if True returned)
        * self.phones - '-' (if False returned)
        '''
        
        self.phones = '-'
        self.session.headers["X-Requested-With"] = "XMLHttpRequest"
        try :
            response = self.session.get(self.phoneLink)
        except Exception as ex :
            self.lastError = ex.args
            return False
        
        for phone in response.json() :
            if self.phones == '-' :
                self.phones = phone
            else :
                self.phones += '\n' + phone

        return True


    
    def load(self, urlToLoad=None, fileToLoad=None) :
        '''
        This function loads the details page and puts its content in self.pageContent
        Then it calls differ procedures to fill the result fields in the object

        For real life situations and debugging purposes 
        it can take both local and internet pages

        input:
        * urlToLoad - string - target url, if None - checking the local file
        * fileToLoad - string - target file name, if None - go away
        output:
        * True - if page was successfuly loaded (from file or internet)
        * False - if errors were encountered
        * self.pageContent - target page content (if True returned)
        * self.lastError - last error message (if False returned)
        '''
        if urlToLoad :
            if not(self.prepareLoading(urlToLoad)) :
                print("There was an error while preparing load:", self.lastError)
            try :
                response = self.session.get(urlToLoad)
            except Exception as ex :
                self.lastError = ex.args
                return False
            self.pageContent = response.text
            #if not(self.getPhotos()) :
            #    return False
            #if not(self.getPhones()) :
            #    return False
        elif fileToLoad :
            try :
                self.pageContent = open(fileToLoad).read()
            except Exception as ex :
                self.lastError = ex.args
                return False
        else :
            return False

        return True
