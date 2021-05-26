import itertools
import re

from collections import Counter
from typing import Generator, List

import konlpy
import requests

from bs4 import BeautifulSoup

ap_sess = requests.session()
ap_sess.headers['Accept'] = 'application/activity+json'

tagger = konlpy.tag.Okt()


def extract_words(text: str) -> List[str]:
    text = text.replace('\u200b', ' ')
    text = text.replace('\n', ' ')
    pattern = re.compile(r'\B:[a-zA-Z0-9_]+:\B')
    emojis = pattern.findall(text)
    text = pattern.sub('', text)
    return tagger.morphs(text, norm=True) + emojis


def extract_text(html: str) -> str:
    tree = BeautifulSoup(html, features='html.parser')

    for br in tree.find_all('br'):
        br.replace_with('\n')
    for tag in tree.find_all('a', attrs={'class': None}):
        tag.extract()
    for tag in tree.find_all('a', attrs={'class': 'mention'}):
        tag.extract()

    return tree.get_text().strip()


def get_outbox_url(acct: str) -> str:

    if acct.startswith('@'):
        acct = acct[1:]

    domain = acct.split('@')[1]
    fingered = requests.get(
        f'https://{domain}/.well-known/webfinger',
        params={
            'resource': f'acct:{acct}',
        }).json()

    profile_link = next(
        link['href']
        for link in fingered['links']
        if link['type'] == 'application/activity+json' and
        link['rel'] == 'self'
    )

    outbox_url = ap_sess.get(profile_link).json()['outbox']

    return outbox_url


def get_posts(acct: str) -> Generator[str, None, None]:
    outbox_url = get_outbox_url(acct)

    outbox = ap_sess.get(outbox_url).json()

    next_url = outbox['first']
    while next_url:
        try:
            page = ap_sess.get(next_url).json()
            next_url = page['next']
            posts = page['orderedItems']

            for post in posts:
                if post['type'] == 'Announce':
                    continue
                yield extract_text(post['object']['content'])
        except Exception as e:
            print(e)
            return


def generate_words(acct: str) -> Counter:
    posts = get_posts(acct)

    words = itertools.chain.from_iterable(
        extract_words(post)
        for index, post
        in itertools.takewhile(lambda x: x[0] < 100, enumerate(posts))
    )

    return Counter(words)


def generate_report(acct: str) -> str:
    words = generate_words(acct)
    report = '\n'.join(
            f'{word} - {count}'
            for word, count
            in words.most_common(10))

    return report
