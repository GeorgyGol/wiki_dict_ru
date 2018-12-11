import requests
import re
from bs4 import BeautifulSoup
import sqlite3
import time
import pandas as pd
from itertools import islice

import make_dict.commons as cmm


class rijech:
    _strUrl=''
    _strName=''
    _main_soup=None
    _work_soup=None
    _soup_of_values=[]
    _info=dict()
    _lst_cases = ['Им.Еч', 'Им.Мч', 'Р.Еч', 'Р.Мч', 'Д.Еч', 'Д.Мч', 'В.Еч', 'В.Мч', 'Тв.Еч', 'Тв.Мч', 'Пр.Еч', 'Пр.Мч']

    _root_suff = re.compile(
            r'(?i)(?:Приставк\w+: (?P<pre>[а-я-]+);)?\s?(?:Кор\w+: (?P<root>-[а-я]+-);?)+\s?(?:суффикс\w?: (?P<suff>[а-я-]+);?)?\s?(?:окончани\w?: (?P<ends>[а-я-]+);?)?')

    def __init__(self, name='', link=''):
        self._strUrl=link
        self._strName=name

    def _get_page_parts(self, soup=None, split_tags=''):
        lst_ret = list()
        lst_tags=list()
        lst_tag_cnt=0

        spl_soup=self._work_soup if soup is None else soup

        if type(split_tags) is str:
            lst_tags=spl_soup.find_all(split_tags)
            lst_tag_cnt=len(lst_tags)
        else:
            lst_tags = split_tags
            lst_tag_cnt = len(lst_tags)

        for i in range(lst_tag_cnt):
            lst_siblings = list(lst_tags[i].next_siblings)

            if i < lst_tag_cnt - 1:
                lst_ret.append(' '.join([str(t) for t in lst_siblings[:lst_siblings.index(lst_tags[i + 1])]]))
            else:
                lst_ret.append(' '.join([str(t) for t in lst_siblings]))
        return lst_ret

    def source_case(self):
        cases=[k for k, v in self._info.items() if k in self._lst_cases and re.search(r'\b{}\b'.format(self._strName), v)]
        return  cases

    def get_page(self, session=None):
        ht = session.get(self._strUrl)
        ht.encoding = ht.apparent_encoding

        self._main_soup = BeautifulSoup(ht.text, 'html.parser')

        h1 = self._main_soup.find('span', class_='mw-headline', id='Русский', text='Русский').parent
        self._work_soup = BeautifulSoup(' '.join([str(t) for t in h1.next_siblings]), 'html.parser')
        h1=self._main_soup.find('h1', class_='firstHeading')
        print(h1.text)

        hs = [h.parent for h in self._work_soup.findAll('span', class_='mw-headline', text=re.compile(h1.text))]
        work_list = None

        if hs:
            self._soup_of_values = [BeautifulSoup(t, 'html.parser') for t in self._get_page_parts(split_tags=hs)]
        else:
            self._soup_of_values = [self._work_soup]

        return ht

    def _get_word_parts(self, strWordParts):
        mtc = self._root_suff.findall(strWordParts)
        dct = dict(zip(['pre', 'root_0', 'suff', 'ends'], mtc[0]))

        for i in range(1, len(mtc)):
            dct.update({'root_' + str(i): mtc[i][1]})

        return dct

    def _get_morfo(self, morfo):
        ps=morfo.find_all('p')
        #print(len(ps)) # always 3
        str0=ps[0].text.strip() # heating and syllabels
        str1=ps[1].text.strip() # type-gender etc
        spl=str0.find('Существительное')
        if spl>0:
            str1=str0[spl:]
            str0=str0[:spl]
        str2=ps[-1].text[:ps[-1].text.find('[')].strip().lower() # root-suff

        dct = {'morf0': str0}
        sklZ = re.search(r'тип склонения (?P<sklz>.+) по классификации', str1)
        dct.update(dict(zip(['type', 'anima', 'gender', 'declen'], str1[:str1.find('(')].split(','))))
        dct.update({'declen_Z': sklZ['sklz']})
        dct.update(self._get_word_parts(str2))

        return {k.strip():v.strip() for k, v in dct.items()}

    def _get_cases(self, morfo):
        def replace_rats(strS):
            return strS.replace('о́', 'о').replace('а́', 'a').replace('у́', 'у').replace('е́', 'е').replace('я́', 'я').replace('ю́', 'ю').replace('и́', 'и').replace('э́', 'э').replace('ы́', 'ы')

        tbl=morfo.find('table')
        tbl= BeautifulSoup(str(tbl).replace(r'<br/>', '; '))
        dct_ret=dict()

        if tbl:
            trs=tbl.findAll('tr')
            for tr in trs:
                tds=tr.findAll('td')
                if tds:
                    dct_ret.update({tds[0].text.strip() +'Еч': replace_rats(tds[1].text.strip()),
                                    tds[0].text.strip()+'Мч': replace_rats(tds[2].text.strip())})
        return dct_ret

    def parse(self):

        for n, sp in enumerate(self._soup_of_values):

            self._info ={'value':n}
            sp3s = [BeautifulSoup(h, 'html.parser') for h in self._get_page_parts(split_tags='h3')]
            #sp3s[0] => morfo
            self._info.update(self._get_morfo(sp3s[0]))
            self._info.update(self._get_cases(sp3s[0]))

            for k, v in self._info.items():
                print('{}:{}'.format(k, v))


def main():
    sess = requests.session()
    sess.headers.update(cmm.req_header)

    #r_test=rijech(link=r'https://ru.wiktionary.org/wiki/%D0%BA%D0%B0%D1%80%D1%82%D0%BE%D1%88%D0%B5%D1%87%D0%BA%D0%B0',
    #                name='картошечка')

    #r_test = rijech(link=r'https://ru.wiktionary.org/wiki/%D0%BA%D0%BE%D1%88%D0%BA%D0%B0', name='кошками')
    #r_test = rijech(link=r'https://ru.wiktionary.org/wiki/%D0%BA%D0%BE%D1%87%D0%B5%D1%82', name='кочет')
    #r_test = rijech(link=r'https://ru.wiktionary.org/wiki/%D1%81%D0%BE%D0%B1%D0%B8%D0%BD%D0%BA%D0%B0', name='собинка')
    r_test = rijech(link=r'https://ru.wiktionary.org/wiki/%D0%BF%D1%80%D0%B8%D0%B2%D0%BE%D1%80%D0%BE%D1%82', name='приворот')

    r_test.get_page(session=sess)

    r_test.parse()
    print(r_test.source_case())
    #pdfn = pd.read_csv('ru_nouns.csv', sep=';', index_col=0)
    #print(pdfn)




if __name__ == "__main__":
    main()