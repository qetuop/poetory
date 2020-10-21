import re

import json

from flask import render_template, request, flash, redirect

from app import app, db
import poeq
from poem import CharacterInfo
from app.forms import LoginForm, ItemForm, CharacterForm

def updateCharacters(account):
    print('getting chars for account: ' + account)

    characters = poeq.getCharacters(account)
    print(type(characters), characters)

    pattern = re.compile(r'(?<!^)(?=[A-Z])')

    # convert camel case to snake case for DB, and rename the 'class' to 'class_'
    for charDict in characters:
        charDict2 = {}

        for key in charDict.keys():
            print(key)
            if key == 'class':
                charDict2['class_'] = charDict[key]
            else:
                charDict2[pattern.sub('_', key).lower()] = charDict[key]

        char = CharacterInfo(**charDict2)
        db.session.add(char)
        db.session.commit()

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    print(request.method)

    config = json.loads(open('config.json').read())
    account = config['account']
    getStandard = config['getStandard']
    league = config['league']
    poesessid = config['poesessid']

    form = LoginForm()
    leagues = poeq.getLeagueNames()
    form.league.choices = [(league, league) for league in leagues]
    form.account.data = account
    form.poessid.data = poesessid
    form.league.data = league

    # POST
    if form.validate_on_submit():
        account = form.account.data
        league = form.league.data
        poesessid = form.poessid.data

        poeq.setup(league, account, poesessid)

        numTabs = poeq.getNumTabs(league)  # {'numTabs': 28}  or {'error': {'code': 6, 'message': 'Forbidden'}}
        form.tabs.data = numTabs

        #return render_template('index.html', form=form)
        #characters(account) # doesn't work
        updateCharacters(account)

        form = CharacterForm()
        entries = CharacterInfo.query.all()
        return render_template('characters.html', form=form, entries=entries)


    return render_template('index.html', form=form)

@app.route('/items', methods=['GET', 'POST'])
def items():
    form = ItemForm()
    return render_template('items.html', form=form)

@app.route('/characters/<account>', methods=['GET', 'POST'])
def characters(account):
    print(request.method)

    #print('characters: ' + account) # account = <input id="account" name="account" type="text" value="qetuop"> only *after* submit pressed

    updateCharacters(account)

    form = CharacterForm()
    entries = CharacterInfo.query.all()
    return render_template('characters.html', form=form, entries=entries)