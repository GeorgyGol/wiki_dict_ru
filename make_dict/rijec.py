import requests
import re
from bs4 import BeautifulSoup
import sqlite3
import time
import pandas as pd
from itertools import islice

class Error(Exception):
    def __init__(self, message):
        super(Exception, self).__init__('rijec class error -- ' + message)

class PrivateFieldAccess(Error):
    def __init__(self, message):
        super(PrivateFieldAccess, self).__init__(message)


class rijech:
    _infinitive=''
    _base_form=''
    _part_of_speech=''
    _language='Rus'
    _link=''
    _morfems=dict()

    __private=True

    def __check_private(self, message):
        if self.__private: raise PrivateFieldAccess(message)

    def __init__(self, name='', private=True):
        self._base_form=name
        self.__private=private

    @property
    def base_form(self):
        return self._base_form

    @base_form.setter
    def base_form(self, value):
        self.__check_private('setter base_form')
        self._base_form=value

    @property
    def link(self):
        return self._link

    @link.setter
    def link(self, value):
        self.__check_private('setter base_form')
        self._link = value

    @property
    def infinitive(self):
        return self._infinitive

    @infinitive.setter
    def infinitive(self, word):
        self.__check_private('setter infinitive')
        self._infinitive = word

    @property
    def lang(self):
        return self._language
    @lang.setter
    def lang(self, value):
        self.__check_private('setter language')
        self._language=value

    @property
    def morfems(self):
        return self._morfems

    @morfems.setter
    def morfems(self, value):
        self.__check_private('setter language')
        self._morfems = value

    @property
    def roots(self):
        return [v.replace('-', '') for k, v in self._morfems.items() if re.search('root', k)]

    @property
    def prefixes(self):
        return list(filter(None, re.split('-', self._morfems['pre'])))

    @property
    def suffixes(self):
        return list(filter(None, re.split('-', self._morfems['suff'])))

    @property
    def ends(self):
        return list(filter(None, re.split('-', self._morfems['ends'])))

def main():
    r=rijech('proba', private=False)
    print(r.base_form)
    r.base_form='bamm!!'


if __name__ == "__main__":
    main()