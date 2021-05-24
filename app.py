import itertools

from collections import Counter
from typing import Generator

import requests

from bs4 import BeautifulSoup

ap_sess = requests.session()
ap_sess.headers['Accept'] = 'application/activity+json'


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
        except Exception:
            return


def generate_words(acct: str):
    posts = get_posts(acct)

    words = itertools.chain.from_iterable(
        post.split()
        for index, post
        in itertools.takewhile(lambda x: x[0] < 100, enumerate(posts))
    )

    return Counter(words)
