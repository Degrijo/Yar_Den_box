import requests
import re
from bs4 import BeautifulSoup
from config.settings.common import BASE_DIR


SITE_URL = r'https://baza-otvetov.ru'


r = requests.get(SITE_URL + r'/crosswords')
soup = BeautifulSoup(r.text, 'html.parser')
jokes = soup.find_all('h3', {'class': 'crossword-list__group-title'})
with open('../../questions.txt', 'w', encoding='utf-8') as file:
    for tag in jokes:
        category = tag.text
        for cross in tag.nextSibling.findChildren(recursive=False):
            href = cross.findChild().get('href')
            new_r = requests.get(SITE_URL + href)
            new_soap = BeautifulSoup(new_r.text, 'html.parser')
            for q in new_soap.find_all('div', {'class': 'cw-q__row'}):  # may be get only sentences with ?
                question = re.sub(r' \(.*\)', '', q.contents[1])
                file.write(question + '\n')
