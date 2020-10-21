import re
import os

import json
from flask import render_template, request, flash, redirect
from rapidfuzz import fuzz
from rapidfuzz import process

from app import app, db
import poeq
import poed
from poem import CharacterInfo
from app.forms import LoginForm, ItemForm, CharacterForm
from config import Config

def updateCharacters(account):
    print('getting chars for account: ' + account)

    characters = poeq.getCharacters(account)
    #print(type(characters), characters)

    pattern = re.compile(r'(?<!^)(?=[A-Z])')

    # convert camel case to snake case for DB, and rename the 'class' to 'class_'
    for charDict in characters:
        charDict2 = {}

        for key in charDict.keys():
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

        if form.characters.data:
            form = CharacterForm()
            entries = CharacterInfo.query.all()
            return render_template('characters.html', form=form, entries=entries)
        elif form.items.data:
            form = ItemForm()
            char = CharacterInfo.query.first()
            fullItems = poeq.getCharacterInventory(char.name)
            print(f"* {fullItems}")

            # TODO: move this to....poed?
            affixList = []
            affixFile = os.path.join(Config.DATA_DIR,'stats.json')
            with open(affixFile, 'r') as file:
                jdata = json.load(file)
                for result in jdata['result']:
                    for entry in result['entries']:
                        affixList.append(entry['text'])


            items = []
            for item in fullItems['items']:
                print(item)

                if item['frameType'] == 5 or 'Flask' in item['typeLine']:  # 5=currency
                    continue

                tmp = {}
                tmp['id'] = 1
                tmp['name'] = item['name']
                for mod in item['explicitMods']:
                    tgt = process.extractOne(mod, affixList, score_cutoff=95)[0]
                    print(mod, poed.findDiff(mod,tgt))

                items.append(tmp)
            return render_template('items.html', form=form, items=items)


    return render_template('index.html', form=form)

@app.route('/items', methods=['GET', 'POST'])
def items():
    form = ItemForm()
    char = CharacterInfo.query.first()
    items = poeq.getCharacterInventory(char.name)
    return render_template('items.html', form=form)

@app.route('/characters/<account>', methods=['GET', 'POST'])
def characters(account):
    print(request.method)

    #print('characters: ' + account) # account = <input id="account" name="account" type="text" value="qetuop"> only *after* submit pressed

    updateCharacters(account)

    form = CharacterForm()
    entries = CharacterInfo.query.all()
    return render_template('characters.html', form=form, entries=entries)