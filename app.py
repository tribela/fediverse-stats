from urllib.parse import urlencode

from flask import Flask, redirect, render_template, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

from utils import generate_report

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)


@app.get('/')
def index():
    return render_template('index.html')


@app.get('/<acct>')
def report(acct: str):
    try:
        if acct.startswith('@'):
            acct = acct[1:]

        domain = acct.split('@')[1]

        report = generate_report(acct)

        params = {
            'title': '내가 가장 많이 사용한 단어',
            'text': f'\n{report}\n#내가_가장_많이_사용한_단어',
            'url': url_for('index', _external=True)
        }

        share_url = f'https://{domain}/share?' + urlencode(params)
        return redirect(share_url)
    except Exception:
        return '', 500
