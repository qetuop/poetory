import re
import os
import sys

from collections import OrderedDict
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

# get ALL characters and place in DB
def updateCharacters(account):
    print('getting chars for account: ' + account)

    characters = poeq.getCharacters(account)
    #print(type(characters), characters)

    # convert camel case to snake case for DB, and rename the 'class' to 'class_'
    pattern = re.compile(r'(?<!^)(?=[A-Z])')
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

def getItems():
    pass#getCharacterInventory

def setup():
    config = json.loads(open('config.json').read())
    account = config['account']
    getStandard = config['getStandard']
    league = config['league']
    poesessid = config['poesessid']
    poeq.setup(league, account, poesessid)

def shortenedModName(name):
    if name is not None:
        name = name.replace("Strength", "Str").strip()
        name = name.replace("Dexterity", "Dex").strip()
        name = name.replace("# to", "").strip()
    print("SHORTEN:", name)
    return name

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    print(f"index: {request.method}")

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

        #numTabs = poeq.getNumTabs(league)  # {'numTabs': 28}  or {'error': {'code': 6, 'message': 'Forbidden'}}
        #form.tabs.data = numTabs

        #return render_template('index.html', form=form)
        #characters(account) # doesn't work

        #updateCharacters(account)
        print(poeq.getNumTabs(league))
        poeq.getStashInfo(league)
        poeq.getStash(league)
        characters = poeq.getCharacters(account)
        print(characters)



        if form.characters.data:
            form = CharacterForm()
            entries = CharacterInfo.query.all()
            print(entries)
            return render_template('characters.html', form=form, entries=entries)

        elif form.items.data:
            #form = ItemForm()
            #char = CharacterInfo.query.first()
            return render_template('items.html')


    return render_template('index.html', form=form)

@app.route('/items', methods=['GET', 'POST'])
def items():
    print(f"items: {request.method}")
    setup()
    form = ItemForm()
    config = json.loads(open('config.json').read())
    #char = CharacterInfo.query.filter_by(name='Mr_Auder').first()
    fullItems = poeq.getCharacterInventory(config['character'])

    print(f"* {fullItems}")

    # TODO: move this to....poed?
    affixList = []
    affixFile = os.path.join(Config.DATA_DIR, 'stats.json')
    with open(affixFile, 'r') as file:
        jdata = json.load(file)
        for result in jdata["result"]:
            for entry in result["entries"]:
                affixList.append(entry['text'])

    #affixList = ['name','# to maximum Energy Shield']

    items = []
    cnt = 0
    foundMods = []  # datatable js i'm using expects each item to have *all* columns even if value is empty
    for item in fullItems['items']:
        print(item)

        if item['frameType'] == 5 or 'Flask' in item['typeLine']:  # 5=currency
            continue

        tmp = {}
        tmp["name"] = item['name']
        if tmp["name"] == "":
            tmp["name"] = item['typeLine']

        modList = []

        if 'implicitMods' in item.keys(): #item['implicitMods'] is not None:
            modList += item['implicitMods']
        if 'explicitMods' in item.keys(): #item['explicitMods'] is not None:
            modList += item['explicitMods']
        print('MOD LIST:', modList)
        for mod in modList:
            if process.extractOne(mod, affixList, score_cutoff=92) == None:
                print('***ERROR MATCHING:', mod)
                continue

            genericMod = process.extractOne(mod, affixList, score_cutoff=92)[0]
            val = poed.findDiff(mod, genericMod)[0]

            # TODO: add shortened mod name here
            genericMod = shortenedModName(genericMod)
            print(genericMod)

            tmp[genericMod] = val
            print(genericMod,mod)
            if genericMod not in foundMods:
                foundMods.append(genericMod)

        items.append(tmp)
        cnt += 1
        #if cnt  >= 3: break

    print('FOUND MOD LIST:', foundMods)

    # add empty mods to each item for datatables column req, they all should already have 'name'....
    cnt = 0
    for idx, item in enumerate(items):
        #print('ITEM:',items[idx])
        for genericMod in foundMods:

            # TODO: add shortened mod name here
            genericMod = shortenedModName(genericMod)

            #print('EXISTS:',mod,mod not in items[idx].keys())
            if genericMod not in items[idx].keys():
                items[idx][genericMod] = ""

    print('ITEMS:',items)
    out = {"data":items}

    # set visible columns
    out["visible"] = ["name", "Str"]

    print(out)
    print (json.dumps(out,indent=4))
    #print(out)

    '''
    # ? each entry must have all columns?
    out = {
        "data": [
            {
                "name": "Tiger Nixon",
                "position": "System Architect"
            },
            {
                "name": "Bob",
                "position": "Jester"
            }
        ]
    }
    print(out)
    print(json.dumps(out,indent=4))
    '''

    # a dict should be ok, recent versions of flask will call jsonify under the hood.
    return out

@app.route('/characters/<account>', methods=['GET', 'POST'])
def characters(account):
    print(request.method)

    #print('characters: ' + account) # account = <input id="account" name="account" type="text" value="qetuop"> only *after* submit pressed

    updateCharacters(account)

    form = CharacterForm()
    entries = CharacterInfo.query.all()
    return render_template('characters.html', form=form, entries=entries)