import re
import os
import sys
from pathlib import Path

from collections import OrderedDict
import json
from flask import render_template, request, flash, redirect, url_for
from rapidfuzz import fuzz
from rapidfuzz import process

from app import app, db
import poeq
import poed
from poem import CharacterInfo
from app.forms import LoginForm, ItemForm, CharacterForm
from config import Config

# GLOBALS
affixList = []
affixDict = {}

foo = True

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
    global affixList
    global affixDict

    config = json.loads(open('config.json').read())

    account     = config['account']
    league      = config['league']
    poesessid   = config['poesessid']
    sleep       = config['sleep']

    poeq.setup(league, account, poesessid, sleep)

    # Build the *complete* Affix list/?dict? - there will be 1000s of entries

    # TODO: move this to....poed?
    # https://pathofexile.gamepedia.com/Modifiers

    # stats.json comes from https://www.pathofexile.com/api/trade/data/stats
    # it ?should? contain all affixes for the various types: Pseudo, Explicit, Implicit, Fractured, Enchant, Crafted, Veiled, Monster, Delve

    # affixes.txt came from https://spidermari.github.io/ and ?up to date? NOT USED at this time

    # there is also https://raw.githubusercontent.com/brather1ng/RePoE/master/RePoE/data/stat_translations.json, not sure how to use it at this time

    # entry={"id":"pseudo.pseudo_increased_spell_damage", "text": "#% increased Spell Damage",  type:"pseudo",

    # the number portion of the id value will be the same for all types EX:
    # # Chaos Damage taken, explicit, explicit.stat_496011033
    # # Chaos Damage taken, implicit, implicit.stat_496011033
    # annnnnnd it won't always be a number ex: "pseudo.pseudo_number_of_crafted_mods" or "pseudo.pseudo_number_of_empty_affix_mods"
    # i'm sure GGG has reasons....

    affixList = []
    tupleDict = {}
    reverseTupleDict = {}
    affixFile = os.path.join(Config.DATA_DIR, 'stats.json')
    with open(affixFile, 'r') as file:
        affixDict = json.load(file)
        for result in affixDict["result"]:
            for entry in result["entries"]:
                affixList.append(entry['text'])
                tupleDict[(entry['text'], entry['type'])] = entry['id']
                reverseTupleDict[entry['id']] = (entry['text'], entry['type'])

    print(f"{len(affixList)} affixes found")

    keyList = list(tupleDict.keys()) #.sort() #(key=lambda tup: tup[1]
    keyList.sort()
    path = Path.cwd() / 'data' / 'affixlist.csv'
    with open(path, 'w') as file:
        for affix in keyList:
            file.write(f"\"{affix[0]}\", \"{affix[1]}\", \"{tupleDict[(affix[0],affix[1])]}\"\n")


    # affixList = ['name','# to maximum Energy Shield']

def shortenedModName(name):
    if name is not None:
        name = name.replace("Strength", "Str").strip()
        name = name.replace("Dexterity", "Dex").strip()
        name = name.replace("Intelligence", "Int").strip()

        name = name.replace("maximum", "max").strip()

        name = name.replace("# to", "").strip()
    print("SHORTEN:", name)
    return name



@app.route('/verify', methods=['POST'])
def verify():
    print("VERIFY")
    print(request)

    print(request.form['account'])


    config = json.loads(open('config.json').read())

    config['account'] = request.form['account']
    config['league'] = request.form['league']
    config['poesessid'] = request.form['poesessid']

    with open("config.json", "w") as write_file:
        json.dump(config, write_file, indent=4)

    return redirect(url_for('index'))

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    print(f"index: {request.method}")

    config = json.loads(open('config.json').read())

    account = config['account']
    league = config['league']
    poesessid = config['poesessid']
    sleep = config['sleep']
    character = config['character']
    getStandard = config['getStandard']

    leagues = poeq.getLeagueNames()

    form = LoginForm()
    form.league.choices = [(league, league) for league in leagues]
    form.account.data = account
    form.poesessid.data = poesessid
    form.league.data = league

    setup()

    verified = poeq.verify()

    return render_template('index.html', verified=verified, form=form)

@app.route('/items', methods=['GET'])
def items():
    return render_template('items.html')

@app.route('/itemdata', methods=['GET'])
def itemdata():
    print(f"itemdata: {request.method}")
    global affixList
    global foo


    #form = ItemForm()
    #config = json.loads(open('config.json').read())
    #char = CharacterInfo.query.filter_by(name='Mr_Auder').first()

    if foo:
        fullItems = poeq.getCharacterInventory('Mr_Auder')
        foo = False
    else:
        fullItems = poeq.getCharacterInventory('RitToxRayne')


    print(f"* {fullItems}")



    items = []
    cnt = 0

    # temp file to test match logic
    path = Path.cwd() / 'data' / 'matchedMods.csv'
    matchedModsFile = open(path, 'w')


    # datatable js i'm using expects each item to have *all* columns even if value is empty, create superset of all found mods
    # add empty value mods to items that don't contain them.  TODO: can this be done a different way?
    foundMods = []
    for item in fullItems['items']:
        print(f"ITEM:\n {item}")

        if item['frameType'] == 5 or 'Flask' in item['typeLine']:  # 5=currency
            continue

        tmp = {}
        tmp["name"] = item['name']
        if tmp["name"] == "":
            tmp["name"] = item['typeLine']

        modList = []

        # TODO: change to tuple (name, type) # ("# to Strength", "implicit")
        if 'implicitMods' in item.keys(): #item['implicitMods'] is not None:
            modList += item['implicitMods']
        if 'explicitMods' in item.keys(): #item['explicitMods'] is not None:
            modList += item['explicitMods']
        if 'fracturedMods' in item.keys():
            modList += item['fracturedMods']
        if 'craftedMods' in item.keys():
            modList += item['craftedMods']

        print('MOD LIST:', modList)
        for mod in modList:
            result = process.extractOne(mod, affixList, score_cutoff=80, scorer=fuzz.ratio) #token_sort_ratio

            if result == None:
                print('***ERROR MATCHING:', mod)
                continue

            genericMod = result[0]
            valList = poed.findDiff(mod, genericMod)#[0]

            matchedModsFile.write(f"\"{mod}\", \"{genericMod}\", \"{valList}\"\n")

            # TODO: add shortened mod name here
            #genericMod = shortenedModName(genericMod)
            #print(genericMod)

            tmp[genericMod] = valList
            # name = Adds # to # Physical Damage, value = Adds 3 to 6 Physical Damage to Attacks
            itemName = tmp["name"]
            print(f"name = {genericMod}, value = {valList}, item = {itemName}")
            if genericMod not in foundMods:
                foundMods.append(genericMod)

        items.append(tmp)
        cnt += 1
        #if cnt  >= 3: break

    matchedModsFile.close()

    print('FOUND MOD LIST:', foundMods)

    # add empty mods to each item for datatables column req, they all should already have 'name'....
    cnt = 0
    for idx, item in enumerate(items):
        #print('ITEM:',items[idx])
        for genericMod in foundMods:

            # TODO: add shortened mod name here
            #genericMod = shortenedModName(genericMod)

            #print('EXISTS:',mod,mod not in items[idx].keys())
            if genericMod not in items[idx].keys():
                items[idx][genericMod] = ""

    #print('ITEMS:',items)
    out = {"data":items}
    print(out)

    # set visible columns
    #out["visible"] = ["name", "# to Strength"]
    out["visible"] = foundMods
    out["visible"].insert(0,"name")


    #print(out)
    #print (json.dumps(out,indent=4))
    poeq.dumpToFile('table_data.json',out)
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


@app.route('/characters', methods=['GET', 'POST'])
def characters():
    print(request.method)
    config = json.loads(open('config.json').read())

    account = config['account']

    #print('characters: ' + account) # account = <input id="account" name="account" type="text" value="qetuop"> only *after* submit pressed

    updateCharacters(account)

    form = CharacterForm()
    entries = CharacterInfo.query.all()
    return render_template('characters.html', form=form, entries=entries)