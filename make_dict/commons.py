import re

strNounURL = r'https://ru.wiktionary.org/wiki/%D0%9A%D0%B0%D1%82%D0%B5%D0%B3%D0%BE%D1%80%D0%B8%D1%8F:%D0%A0%D1%83%D1%81%D1%81%D0%BA%D0%B8%D0%B5_%D1%81%D1%83%D1%89%D0%B5%D1%81%D1%82%D0%B2%D0%B8%D1%82%D0%B5%D0%BB%D1%8C%D0%BD%D1%8B%D0%B5'
strUrlBase = r'https://ru.wiktionary.org'

req_header = {'accept': r'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
              'accept-encoding': 'gzip, deflate, sdch', 'accept-language': 'ru,en-US;q=0.8,en;q=0.6,sr;q=0.4,hr;q=0.2',
              'user-agent': r'Mozilla/5.0 (Windows NT 5.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36}'}



def main():
    str1='Корень: -кош-; суффикс: -к; окончание: -а. '.lower()
    str2='Приставки: бес-при-; корень: -да-; суффиксы: -н-ниц; окончание: -а '
    str3 = 'Корень: -пыл-; интерфикс: -е-; корень: -сос- '

    r_s=re.compile(r'(?i)(?:Приставк\w+: (?P<pre>[а-я-]+);)?\s?(?:Кор\w+: (?P<root>-[а-я]+-);?)+\s?(?:суффикс\w?: (?P<suff>[а-я-]+);?)?\s?(?:окончани\w?: (?P<ends>[а-я-]+);?)?')

    mtc=r_s.findall(str3)
    dct=dict(zip(['pre', 'root_0', 'suff', 'ends'], mtc[0]))

    for i in range(1, len(mtc)):
        dct.update({'root_'+str(i):mtc[i][1]})

    print(dct)
    #print('root = {}, pre = {}, suff = {}, ends = {}'.format(mtc['root'], mtc['pre'], mtc['suff'], mtc['ends']))


if __name__ == "__main__":
    main()