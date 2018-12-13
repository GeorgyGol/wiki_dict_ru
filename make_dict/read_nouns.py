import requests
import re
from bs4 import BeautifulSoup
import sqlite3
import time
import pandas as pd
from itertools import islice

import make_dict.commons as cmm
import make_dict.rijec as ru_word

class read_word:
    _base_link = r'https://ru.wiktionary.org/wiki/'

    _word=None

    _strName=''
    _main_soup=None
    _work_soup=None
    _soup_of_values=[]
    _info=dict()
    _part_of_speech=''
    _infinitive=''

    _lst_cases = ['Им.Еч', 'Им.Мч', 'Р.Еч', 'Р.Мч', 'Д.Еч', 'Д.Мч', 'В.Еч', 'В.Мч', 'Тв.Еч', 'Тв.Мч', 'Пр.Еч', 'Пр.Мч']

    _root_suff = re.compile(
            r'(?i)(?:Приставк\w+: (?P<pre>[а-я-]+);)?\s?(?:Кор\w+: (?P<root>-[а-я]+-);?)+\s?(?:суффикс\w?: (?P<suff>[а-я-]+);?)?\s?(?:окончани\w?: (?P<ends>[а-я-]+);?)?')

    _remove_rewrite=re.compile(r'\[.*\]')
    _remove_tag=re.compile((r'<[^>]*>'))

    def _replace_rats(self, strS):
        return strS.replace('о́', 'о').replace('а́', 'a').replace('у́', 'у').replace('е́', 'е').replace('я́', 'я').replace('ю́', 'ю').replace('и́', 'и').replace('э́', 'э').replace('ы́', 'ы')

    def __init__(self, name=''):
        #self._word=ru_word.rijech(name, private=False)
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


    def split_soup(self, soup, tag_list):
        '''split soup by strings between given tags. For exmpl.: between <h1> and <h1>, or <h1> and and of html'''
        def sibling_iterate(start_tag, stop_tag):
            for tag in start_tag.next_siblings:
                if tag == stop_tag:
                    raise StopIteration
                else:
                    yield tag
        ls_ret=list()
        for sbls in [sibling_iterate(i[0], i[1]) for i in cmm.pairwise(tag_list)]:
            t_str=[str(t) for t in sbls]
            ls_ret.append(' '.join(t_str))

        return ls_ret

    def get_lang_htmls(self):
        '''split Item into languages parts'''
        # find languages - split by h1
        lang_parts = self._main_soup.findAll('h1', attrs={'class':None, 'id':None})
        lang_soups = [t for t in
                     self.split_soup(self._main_soup, lang_parts)]

        return dict(zip([self._remove_rewrite.sub('', h1.text) for h1 in lang_parts], lang_soups))

    def get_word_values_htmls(self, soup):
        '''get list of html for each value of the given word'''
        # find values - split by h2
        h2s=soup.find_all('h2')
        if h2s:
            return dict(zip([self._remove_rewrite.sub('', h2.text) for h2 in h2s], [v for v in self.split_soup(self._main_soup, h2s)]))
        else:
            return {self._main_soup.title.text[:self._main_soup.title.text.find('—')].strip(): str(soup)}

    def get_word_properties_htmls(self, soup):
        '''get properties for word in Items - cases, synonims etc'''
        # split on h3
        h3s = soup.find_all('h3')
        #print([h3.text for h3 in h3s])
        if h3s:
            return dict(zip([self._remove_rewrite.sub('', h3.text) for h3 in h3s],
                            [v for v in self.split_soup(self._main_soup, h3s)]))
        else:
            return dict()


    def _solve_part_of_speech(self, str_html):
        strFind=str_html[str_html.find(r'</b>') + 4:].strip()

        mo=re.search(r'(?m)[А-Я]', strFind)
        m_end=re.compile('[,.;]')
        end_pos=m_end.search(strFind, mo.start()).start()
        return self._remove_tag.sub('', strFind[mo.start():end_pos])

    def _solve_infinitive(self, str_html):
        txt=BeautifulSoup(str_html, 'html.parser')
        b=txt.find('b')
        ret=self._replace_rats(b.text)

        if self._strName.find('-')==-1:
            return ret.replace('-', '')
        else:
            return ret

    def _solve_cases(self, morfo):
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

    def _solve_morfems(self, str_html):
        sp=BeautifulSoup(str_html, 'html.parser')
        p=sp.find_all('p')
        strWordParts=p[-1].text
        mtc = self._root_suff.findall(strWordParts)
        if mtc:
            dct = dict(zip(['pre', 'root_0', 'suff', 'ends'], mtc[0]))

            for i in range(1, len(mtc)):
                dct.update({'root_' + str(i): mtc[i][1]})

            return dct
        else:
            return {'pre':'', 'root_0':'', 'suff':'', 'ends':''}

    def make_word(self, dict_html, lang='', link=''):
        wrd=ru_word.rijech(self._strName, private=False)
        wrd.part_of_speech=self._solve_part_of_speech(dict_html['Морфологические и синтаксические свойства'])
        wrd.infinitive=self._solve_infinitive(dict_html['Морфологические и синтаксические свойства'])
        wrd.lang=lang
        wrd.link=link
        wrd.morfems=self._solve_morfems(dict_html['Морфологические и синтаксические свойства'])

        #print(self._solve_cases(BeautifulSoup(dict_html['Морфологические и синтаксические свойства'], 'html.parser')))

        print('{}, {}, {}-{}-{}-{}'.format(wrd.part_of_speech, wrd.infinitive, wrd.prefixes, wrd.roots, wrd.suffixes, wrd.ends))
        #morfo_soup=BeautifulSoup(dict_html['Морфологические и синтаксические свойства'], 'html.parser')


    def get_page(self, session=None):
        ht = session.get(self.link)
        ht.encoding = ht.apparent_encoding

        self._main_soup = BeautifulSoup(ht.text, 'html.parser')

        langs=self.get_lang_htmls()

        t=self.get_word_values_htmls(BeautifulSoup(langs['Русский'], 'html.parser'))

        wp=self.get_word_properties_htmls(BeautifulSoup(t[list(t.keys())[0]], 'html.parser'))

        wrd=self.make_word(wp, lang='Русский', link=ht.url)


        print(len(wp))


    @property
    def link(self):
        return self._base_link + self._strName



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

    #r_test=read_word(link=r'https://ru.wiktionary.org/wiki/%D0%BA%D0%B0%D1%80%D1%82%D0%BE%D1%88%D0%B5%D1%87%D0%BA%D0%B0',
    #                name='картошечка')


    #r_test = read_word(name='кошками')
    #r_test = read_word(name='пылесос')
    r_test = read_word(name='бесперебойный')
    #r_test = read_word(name='бил')
    #r_test = read_word(name='ударил')
    #r_test = read_word(name='кочет')
    #r_test = read_word(name='собинка')
    #r_test = read_word(name='приворот')
    #r_test = read_word(name='бить')
    #r_test = read_word(name='абстрактнее')
    #r_test = read_word(name='девять')
    #r_test = read_word(name='этот')
    #r_test = read_word(name='адаптирующийся')

    r_test.get_page(session=sess)

    #r_test.parse()
    #print(r_test.source_case())

    #pdfn = pd.read_csv('ru_nouns.csv', sep=';', index_col=0)
    #print(pdfn)




if __name__ == "__main__":

    main()
    #lst=list(range(10))

    #print(pairwise(lst))

