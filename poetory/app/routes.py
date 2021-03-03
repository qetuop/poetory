import re
import os
import sys
from pathlib import Path

from collections import OrderedDict
import json
from flask import render_template, request, flash, redirect, url_for
from rapidfuzz import fuzz
from rapidfuzz import process

from app import app
import poeq
#import poed
#from poem import CharacterInfo
from app.forms import LoginForm, ItemForm, CharacterForm
from config import Config

# GLOBALS
statsDict = {} # dict object created directly from stats.json - used in filter dropdown
affixList = []  # TODO: not used?
affixDict = {}
reverseAffixDict = {}
dataDict = {}
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


# src = Adds 3 to 6 Physical Damage to Attacks, tgt = Adds # to # Physical Damage
# diff = [3,6]....at least it should
def findDiff(src,tgt):

    diff = []
    tgtSplit = tgt.split(" ")
    for y in src.split(" "):
        if y not in tgtSplit:
            diff.append(y)
    #print(f"\tFind Diff: src = {src}, tgt = {tgt}, diff = {diff}")
    return diff

'''
SETUP
call once on startup

Build the *complete* Affix list/?dict? - there will be 1000s of entries

https://pathofexile.gamepedia.com/Modifiers

stats.json comes from https://www.pathofexile.com/api/trade/data/stats
it ?should? contain all affixes for the various types: Pseudo, Explicit, Implicit, Fractured, Enchant, Crafted, Veiled, Monster, Delve

affixes.txt came from https://spidermari.github.io/ and ?up to date? NOT USED at this time

there is also https://raw.githubusercontent.com/brather1ng/RePoE/master/RePoE/data/stat_translations.json, not sure how to use it at this time

entry={"id":"pseudo.pseudo_increased_spell_damage", "text": "#% increased Spell Damage",  type:"pseudo",

the number portion of the id value will be the same for all types EX:
# Chaos Damage taken, explicit, explicit.stat_496011033
# Chaos Damage taken, implicit, implicit.stat_496011033
annnnnnd it won't always be a number ex: "pseudo.pseudo_number_of_crafted_mods" or "pseudo.pseudo_number_of_empty_affix_mods"
i'm sure GGG has reasons....
'''
def setup():
    global statsDict
    global affixList
    global affixDict
    global reverseAffixDict

    print("SETUP")

    '''
    result = 9 entries
    stats.json=
    {
      "result": [
                    {
                      "label": "Pseudo",
                      "entries": [
                        {
                          "id": "pseudo.pseudo_total_cold_resistance",
                          "text": "+#% total to Cold Resistance",
                          "type": "pseudo"
                        },....
                       ]
                    },....
                ]
    }
    '''

    # used for development - easy to read csv of all affix data  TODO: might use for filter builder
    path = Path.cwd() / 'data' / 'affixTupleList.csv'
    affixTupleFile = open(path, 'w')

    statsFile = os.path.join(Config.DATA_DIR, 'stats.json')
    with open(statsFile, 'r') as file:
        statsDict = json.load(file)
        for result in statsDict["result"]:
            for entry in result["entries"]:
                affixList.append(entry['text'])
                affixDict[entry['id']] = (entry['type'], entry['text'])
                reverseAffixDict[(entry['type'], entry['text'])] = entry['id']
                affixTupleFile.write(f"\"{entry['type']}\", \"{entry['text']}\", \"{entry['id']}\"\n")

    affixTupleFile.close()

    print(f"{len(affixList)} affixes found")

@app.route('/verify', methods=['POST'])
def verify():
    print(f"verify: {request.method}")

    # set the config data for account/SID to be read when index is loaded
    config = json.loads(open('config.json').read())
    config['account'] = request.form['account']
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
    poesessid = config['poesessid']

    # setup the query data - account and sid should not change during the lifetime of this app.  I guess if people
    # have multiple accounts...
    # TODO: move to verify?  doesn't need to be done often
    poeq.setup(account, poesessid)

    # populate the fields with config data - blank on initial run, after filling in and hitting verify
    # the config.json will be filled in and this page reloaded with that data, actally verify below
    # --> verify from json file not directly from form (TODO: is this a bad method?)
    form = LoginForm()
    form.account.data = account
    form.poesessid.data = poesessid

    verified = poeq.verify()

    return render_template('index.html', verified=verified, form=form)


def typeLookup(frameType):
    return frameType

@app.route('/filter', methods=['GET'])
def filter():
    print('FILTER:', len(affixList))

@app.route('/items', methods=['GET'])
def items():
    print('ITEMS:', len(affixList))
    return render_template('items.html', data=statsDict)


def processItem(item, league, stashInfo, char=None):
    # NAME
    name = item['name']
    if name == "":  # certain items don't fill this out
        item['name'] = item['typeLine']

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
        location = char  # character

    location += " x:%d y:%d" % (int(item['x']) + 1, int(item['y']) + 1)
    item['location'] = location

    # TYPE
    item['type'] = typeLookup(item['frameType'])

    return item

# add some extra data (location, type) modify some data (name - if empty)
# TODO: type is not working at this time - need to figure out how to get "ring" or "one handed weapon", may have to
# parse a image file name :(
def processData():
    global dataDict

    for league in dataDict.keys():
        print('LEAGUE',league)

        # get stash info for tab names
        stashInfo = poeq.getStashInfo(league)

        for char in dataDict[league]['characters']:
            for i,v in enumerate(dataDict[league]['characters'][char]['items']):
                dataDict[league]['characters'][char]['items'][i] = processItem(v, league, stashInfo, char)

        for tab in dataDict[league]['stash']:
            for i,v in enumerate(dataDict[league]['stash'][tab]['items']):
                dataDict[league]['stash'][tab]['items'][i] = processItem(v, league, stashInfo)

    # TODO: create mapping of affix id : item .... so filterData can quickly find items....but how to linke directly to item
    # 

# query a set of stash tabs/chars based on a CONFIG/FILTER
# this will create the pool of data to further filter upon (afixes/types/etc)
@app.route('/getdata', methods=['GET','POST'])
def getdata():
    global dataDict

    print(f"getdata: {request.method}")

    # TODO: temp until a gui input is created
    sourceConfig = dict(ritual = {'characters' : ['RitToxRayne', 'RitErekD'], 'stash' : [2,3]})
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
    dataDict[league] = {'characters':{}, 'stash':{}}

    # TEMP HACK to not do query every time
    dataDict = json.loads(open('jsonData/dataDict.json').read())

    # TEMP uncomment when need live data
    '''
    for character in sourceConfig['ritual']['characters']:
        inventory = poeq.getCharacterInventory(character)
        print('inventory:',inventory)
        itemList.extend(inventory['items'])
        dataDict['ritual']['characters'][character] = inventory

    for stashNum in sourceConfig['ritual']['stash']:
        tab = poeq.getStashTab(league, stashNum)
        print('tab:',tab)
        dataDict['ritual']['stash'][stashNum] = tab
    '''

    # PROCESS Data
    processData()

    print('dataDict:',dataDict)
    with open("jsonData/dataDict.json", "w") as write_file:
        json.dump(dataDict, write_file, indent=4)

    #return render_template('items.html')
    return redirect(url_for('items'))

# called when items table is loaded
@app.route('/filterdata', methods=['GET'])
def filterdata():
    print(f"filterdata: {request.method}")
    global affixList
    global foo
    global dataDict

    items = []
    cnt = 0

    if len(dataDict) == 0:
        out = {"items": items}
        out["visible"] = []
        out["visible"].insert(0, "type")
        out["visible"].insert(0, "name")
        out["visible"].insert(0, "location")
        return out

    # get stash info for tab names
    league = list(dataDict.keys())[0]  # TODO: how to access iterable view?
    stashInfo = poeq.getStashInfo(league)
    print('filter data, league=',league)

    # temp file to test match logic
    path = Path.cwd() / 'data' / 'matchedMods.csv'
    matchedModsFile = open(path, 'w')


    # datatable js i'm using expects each item to have *all* columns even if value is empty, create superset of all found mods
    # add empty value mods to items that don't contain them.  TODO: can this be done a different way?
    foundMods = []

    # Add all items (char inv and stash) to one single list of items
    fullItemsList = []
    for char in dataDict[league]['characters']:
        fullItemsList.extend((dataDict[league]['characters'][char]['items']))
    for tab in dataDict[league]['stash']:
        fullItemsList.extend((dataDict[league]['stash'][tab]['items']))

    print('fullItemsList:',fullItemsList)

    # TODO : temp hack
    if len(fullItemsList) == 0:
        return {"items": items}

    for item in fullItemsList:
        # #print(f"ITEM:\n {item}")
        #
        # #if item['frameType'] == 5 or 'Flask' in item['typeLine']:  # 5=currency
        # #    continue
        #
        # tmp = {}
        #
        # # NAME
        # tmp["name"] = item['name']
        # if tmp["name"] == "":  # certain items don't fill this out
        #     tmp["name"] = item['typeLine']
        #
        # # LOCATION
        # '''
        # tmp['x']+1 : tmp[y]+1
        # inventoryId: Stash1...StashN (1 indexed, split and subtract 1) ---> index into stashInfo -->  # or name?
        # or 'MainInventory, 'Ring', Ring2, <slot> for character -->
        # '''
        # location = item['inventoryId']
        #
        # if 'Stash' in location:
        #     stashNum = int(location.replace('Stash', '')) - 1
        #     location = stashInfo[stashNum]['n']
        # else:
        #     location = 'TODO' # character
        #
        # location += " x:%d y:%d"%(int(item['x'])+1, int(item['y'])+1)
        # tmp['location'] = location
        #
        # # TYPE
        # tmp['type'] = typeLookup(item['frameType'])

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
            valList = findDiff(mod, genericMod)#[0] // get the value or values for this mode (ex:  # to # -->  5 to 10)

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
#
#
# @app.route('/characters', methods=['GET', 'POST'])
# def characters():
#     print(request.method)
#     config = json.loads(open('config.json').read())
#
#     account = config['account']
#
#     #print('characters: ' + account) # account = <input id="account" name="account" type="text" value="qetuop"> only *after* submit pressed
#
#     updateCharacters(account)
#
#     form = CharacterForm()
#     entries = CharacterInfo.query.all()
#     return render_template('characters.html', form=form, entries=entries)