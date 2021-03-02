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
affixTupleList = []
affixDict = {}
fullItems = {}
'''
{
    "ritual": {
        "characters": {
            "RitToxRayne" : [],
            "RitErekD" : []
        },
        "stash": {
            "1" : [],
            "2" : [],
        }
    }
}
'''

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

    '''
    result = 9 entries
    affixDict=
    {
      "result": [
                    {
                      "label": "Pseudo",
                      "entries": [
                        {
                          "id": "pseudo.pseudo_total_cold_resistance",
                          "text": "+#% total to Cold Resistance",
                          "type": "pseudo"
                        },
                    }
                ]
    }
        '''

    affixList = []
    tupleDict = {}
    reverseTupleDict = {}
    affixFile = os.path.join(Config.DATA_DIR, 'stats.json')
    with open(affixFile, 'r') as file:
        affixDict = json.load(file)
        for result in affixDict["result"]:
            for entry in result["entries"]:
                affixList.append(entry['text'])
                affixTupleList.append( (entry['type'],entry['text'],entry['id']))
                tupleDict[(entry['text'], entry['type'])] = entry['id']
                reverseTupleDict[entry['id']] = (entry['text'], entry['type'])

    print(f"{len(affixList)} affixes found")

    keyList = list(tupleDict.keys()) #.sort() #(key=lambda tup: tup[1]
    keyList.sort()
    path = Path.cwd() / 'data' / 'affixlist.csv'
    with open(path, 'w') as file:
        for affix in keyList:
            file.write(f"\"{affix[0]}\", \"{affix[1]}\", \"{tupleDict[(affix[0],affix[1])]}\"\n")

    path = Path.cwd() / 'data' / 'affixTupleList.csv'
    with open(path, 'w') as file:
        for affix in affixTupleList:
            file.write(f"\"{affix[0]}\", \"{affix[1]}\", \"{affix[2]}\"\n")

    # affixList = ['name','# to maximum Energy Shield']

@app.route('/verify', methods=['POST'])
def verify():
    print("VERIFY")

    config = json.loads(open('config.json').read())

    config['account'] = request.form['account']
    config['league'] = request.form['league']
    config['poesessid'] = request.form['poesessid']
    #config['character'] = request.form['character']

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
    characters = poeq.getCharacterNames(account,league)

    form = LoginForm()
    form.account.data = account
    form.poesessid.data = poesessid
    form.league.choices = [(league, league) for league in leagues]
    form.league.data = league
    form.character.choices = [(char,char) for char in characters]
    form.character.data = character

    setup()

    verified = poeq.verify()
    '''
    #print(affixDict["result"])
    for item in affixDict["result"]:
        #print(item) # {'label': 'Pseudo', 'entries': [{'id': 'pseudo.pseudo_total_cold_resistance', ....
        type = item['label']  # new option, pseudo, crafted, etc
        print(type)
        entries = item['entries']
        print(entries)
        for entry in entries:
            #print(entry['id'])
            print(f"{entry['type']}:{entry['text']}:{entry['id']}")
    '''

    return render_template('index.html', verified=verified, form=form)



def typeLookup(frameType):
    return frameType

@app.route('/filter', methods=['GET'])
def filter():
    print('FILTER:', len(affixList))

@app.route('/items', methods=['GET'])
def items():
    print('ITEMS:', len(affixList))


    return render_template('items.html')

@app.route('/items2', methods=['GET'])
def items2():
    global affixList
    global affixTupleList
    global affixDict

    print('ITEMS2:', len(affixList))

    return render_template('items2.html', data=affixDict)

# query a set of stash tabs/chars based on a CONFIG/FILTER
# this will create the pool of data to further filter upon (afixes/types/etc)
@app.route('/getdata', methods=['POST'])
def getdata():
    global fullItems

    # TODO: temp until a gui input is created
    sourceConfig = dict(ritual = {'characters' : ['RitToxRayne', 'RitErekD'], 'stash' : [1,2]})
    with open("sourceConfig.json", "w") as write_file:
        json.dump(sourceConfig, write_file, indent=4)
    '''
    {
        "ritual": {
            "characters": [
                "RitToxRayne",
                "RitErekD"
            ],
            "stash": [
                1,
                2
            ]
        }
    }
    '''
    itemList = []

    sourceConfig = json.loads(open('sourceConfig.json').read())
    print('sourceConfig:',sourceConfig)

    # only one league at this time.  TODO: allow multiple league configs?
    league = list(sourceConfig.keys())[0] # TODO: how to access iterable view?
    fullItems[league] = {'characters':{},'stash':{}}


    for character in sourceConfig['ritual']['characters']:
        inventory = poeq.getCharacterInventory(character)
        itemList.extend(inventory['items'])
        fullItems['ritual']['characters'][character] = inventory

    for stashNum in sourceConfig['ritual']['stash']:
        tab = poeq.getStashTab(league, stashNum)
        print(tab)
        fullItems['ritual']['stash'][stashNum] = tab

    print('fullItems:',fullItems)
    with open("jsonData/fullItems.json", "w") as write_file:
        json.dump(fullItems, write_file, indent=4)


    return render_template('items.html')

@app.route('/filterdata', methods=['GET'])
def filterdata():
    print(f"filterdata: {request.method}")
    global affixList
    global foo
    global fullItems

    #form = ItemForm()
    config = json.loads(open('config.json').read())
    character = config['character']
    league = config['league']
    inventory = poeq.getCharacterInventory(character)
    #fullItems = {}
    #fullItems = poeq.getStashTab(league, 1)
    #fullItems.update(inventory)
    '''
    if foo:
        fullItems = poeq.getCharacterInventory('Mr_Auder')
        foo = False
    else:
        fullItems = poeq.getCharacterInventory('RitToxRayne')
    '''

    # get stash info for tab names
    league = config['league']
    league = list(fullItems.keys())[0]  # TODO: how to access iterable view?
    stashInfo = poeq.getStashInfo(league)


    items = []
    cnt = 0

    # temp file to test match logic
    path = Path.cwd() / 'data' / 'matchedMods.csv'
    matchedModsFile = open(path, 'w')


    # datatable js i'm using expects each item to have *all* columns even if value is empty, create superset of all found mods
    # add empty value mods to items that don't contain them.  TODO: can this be done a different way?
    foundMods = []

    # Add all items (char inv and stash) to one single list of items
    fullItemsList = []
    for char in fullItems[league]['characters']:
        fullItemsList.extend((fullItems[league]['characters'][char]['items']))
    for tab in fullItems[league]['stash']:
        fullItemsList.extend((fullItems[league]['stash'][tab]['items']))

    print('fullItemsList:',fullItemsList)

    # TODO : temp hack
    if len(fullItemsList) == 0:
        return {"items": items}

    for item in fullItemsList:
        #print(f"ITEM:\n {item}")

        #if item['frameType'] == 5 or 'Flask' in item['typeLine']:  # 5=currency
        #    continue

        tmp = {}

        # NAME
        tmp["name"] = item['name']
        if tmp["name"] == "":  # certain items don't fill this out
            tmp["name"] = item['typeLine']

        # LOCATION
        '''
        tmp['x']+1 : tmp[y]+1
        inventoryId: Stash1...StashN (1 indexed, split and subtract 1) ---> index into stashInfo -->  # or name?
        or 'MainInventory, 'Ring', Ring2, <slot> for character --> 
        '''
        location = item['inventoryId']

        if 'Stash' in location:
            stashNum = int(location.replace('Stash', '')) - 1
            location = stashInfo[stashNum]['n']
        else:
            location = 'TODO' # character

        location += " x:%d y:%d"%(int(item['x'])+1, int(item['y'])+1)
        tmp['location'] = location

        # TYPE
        tmp['type'] = typeLookup(item['frameType'])

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

        for mod in modList:
            result = process.extractOne(mod, affixList, score_cutoff=80, scorer=fuzz.ratio) #token_sort_ratio

            if result is None:
                print('***ERROR MATCHING:', mod)
                continue

            genericMod = result[0]
            valList = poed.findDiff(mod, genericMod)#[0] // get the value or values for this mode (ex:  # to # -->  5 to 10)

            matchedModsFile.write(f"\"{mod}\", \"{genericMod}\", \"{valList}\"\n")

            tmp[genericMod] = valList
            # name = Adds # to # Physical Damage, value = Adds 3 to 6 Physical Damage to Attacks
            itemName = tmp["name"]
            #print(f"name = {genericMod}, value = {valList}, item = {itemName}")
            if genericMod not in foundMods:
                foundMods.append(genericMod)

        items.append(tmp)
        cnt += 1
        #if cnt  >= 3: break # TODO: dev hack to cut down on data

    matchedModsFile.close()

    # add empty mods to each item for datatables column req, they all should already have 'name'....
    cnt = 0
    for idx, item in enumerate(items):
        for genericMod in foundMods:

            # TODO: add shortened mod name here
            #genericMod = shortenedModName(genericMod)

            if genericMod not in items[idx].keys():
                items[idx][genericMod] = ""

    out = {"items":items}

    # set visible columns
    #out["visible"] = ["name", "# to Strength"]
    out["visible"] = foundMods
    out["visible"].insert(0, "type")
    out["visible"].insert(0, "name")
    out["visible"].insert(0, "location")

    poeq.dumpToFile('table_data.json',out)

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