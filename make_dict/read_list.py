import requests
from bs4 import BeautifulSoup
import time
import pandas as pd

import make_dict.commons as commons

def read_main_list(session, strUrl):
    def find_link(tag):
        return tag.name == 'a' and tag.has_attr('title') and tag.string == tag['title']

    nt = session.get(strUrl)

    nt.encoding = nt.apparent_encoding
    soup = BeautifulSoup(nt.text, 'html.parser')

    next_page = soup.find(text='Следующая страница')
    ret_dict = {a.string: commons.strUrlBase + a['href'] for a in soup.findAll(find_link)}

    print(list(ret_dict.keys())[0], list(ret_dict.keys())[-1])

    #time.sleep(1)

    if next_page and next_page.parent.name == 'a':
        ret_dict.update(read_main_list(session, commons.strUrlBase + next_page.parent['href']))
        print(len(ret_dict))
        return ret_dict
    else:
        print(ret_dict)
        return ret_dict


def get_noun_list(sess, save_to_csv=True):
    # get full list of russ. nouns
    pdf = pd.Series(read_main_list(sess, commons.strNounURL))
    pdf=pdf.sort_index()
    pdf.index.name = 'name'
    pdf.name = 'link'

    if save_to_csv:
        pdf.to_csv('ru_nouns.csv', sep=';')
    return pdf


def main():
    sess = requests.session()
    sess.headers.update(commons.req_header)
    get_noun_list(sess)


if __name__ == "__main__":
    main()