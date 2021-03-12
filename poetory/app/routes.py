import re
import os

import os.path
from os import path

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
stashInfo = {} # store resutls from getStash, used for mapping stash names and numbers
statsDict = {} # dict object created directly from stats.json - used in filter dropdown
affixList = []  # used to match the specific item mod to the generic affix mod (+12 to maximum Life --> # to maximum Life)  ----> NOT USED
affixDict = {} #  affixDict[entry['id']] = (entry['type'], entry['text']) - used for getting type/text from id - in filterData logic
affixTypeDict = {}   # {'<type>' : [ 'affixs'....],....} - used to match affixs for specific type (implicit vs explicit)
reverseAffixDict = {}  # { (type, text) : id,....}  - used when evaluating stash item to find affix id --> add to displayItemDict
dataDict = {} # character and stash data queried from POE API
displayItemDict = {}  # quick look up for all "items" that have a given affix
'''
{
    '<affix id>': [ <simpleItem> ],
}
simpleItem = { 'name' : X, 'type' : Y, 'location' : Z, <affix name1> : [val1,val2,..], <affix name1> : [val1,val2,..] } this is what is passed to Datatables
'''

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
    global affixTypeDict

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
    path = Path.cwd() / 'debug' / 'affixTupleList.csv'
    affixTupleFile = open(path, 'w')

    #reverseAffixFile = open(Path.cwd() / 'data' / 'reverseAffixDict.json', 'w')

    # NOTE: there is the potential for multiple affixs of the same type ex:
    # implicit.stat_2067062068 = Projectiles Pierce # additional Targets
    # implicit.stat_2902845638 = Projectiles Pierce # additional Targets --> odd one
    # explicit.stat_2067062068 = ""
    # :( there is also *** 1 *** item in standard with the explicit
    # explicit.stat_3640956958  Projectiles Pierce 2 additional Targets --> the matching logic will match to this vs the above = >.<
    # :_( there is also "Projectiles Pierce an additional Target"  "an" **not** a #    but there is no affix listed as that in stats.json

    #
    # this *may* be due to "updates" not sure if intended.  Old items in Standard have one of these while
    # newer items have the other.  Don't know how to distunguish (besides if item is from standard stash vs new league)
    # may not matter which ID i use, i'll need to only store one for the reverse lookup, the last used will overwrite the ones before it

    # TODO: SHould i scrape this from the site everytime its run?, deliver a version of the file?

    # statsFile = os.path.join(Config.DATA_DIR, 'stats.json')
    # statsURL = "https://www.pathofexile.com/api/trade/data/stats"
    # statsData = poeq.grabData(statsURL)
    # try:
    #     if ( 'error' in statsData.keys() ):
    #         print(f"setup: could not parse stats URL: {statsURL} using cached version if exists.  This may not be a problem")
    #     else:
    #         with open(statsFile, "w") as write_file:
    #             json.dump(statsData, write_file, indent=4)
    # except Exception as e:
    #     print(f"setup: could not grab stats URL: {statsURL} using cached version if exists.  This may not be a problem")
    #     print(e)
    #
    # if os.path.exists(statsFile) == False:
    #     print(f"setup: stats.json could not be found.  Exiting.")
    #     sys.exit(0)


    statsFile = os.path.join(Config.DATA_DIR, 'stats.json')
    with open(statsFile, 'r') as file:
        statsDict = json.load(file)
        for result in statsDict["result"]:
            affixType = result['label'].lower()  # Implicit -> implicit
            affixTypeDict[affixType] = []

            for entry in result["entries"]:
                affixList.append(entry['text'])
                affixTypeDict[affixType].append(entry['text'])
                affixDict[entry['id']] = (entry['type'], entry['text'])
                reverseAffixDict[(entry['type'], entry['text'])] = entry['id']  # see note above
                affixTupleFile.write(f"\"{entry['type']}\", \"{entry['text']}\", \"{entry['id']}\"\n")


    affixTupleFile.close()

    with open(Path.cwd() / 'debug' / 'reverseAffixDict.csv', "w") as write_file:
        for item in reverseAffixDict.items():
            write_file.write(f"\"{item}\n")


    print(f"{len(affixList)} {len(affixDict.keys())} affixes found")

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

def processMod(simpleItem, item, mod, type):
    global displayItemDict

    result = process.extractOne(mod, affixTypeDict[type], score_cutoff=80, scorer=fuzz.ratio)  # token_sort_ratio

    # this mod could not be found in stats.json, some mods are hidden this will be expected.  This is also to catch
    # items i could not match correctly at this time
    if result is None:
        print(f'*** ERROR MATCHING: type:{type} | mod:{mod} | name:{item["name"]} | frameType:{item["frameType"]} | typeLine:{item["typeLine"]}')
        simpleItem.setdefault('unmatched', []).append(mod)
        return simpleItem

    genericMod = result[0]
    valList = findDiff(mod, genericMod)  # [0] // get the value or values for this mode (ex:  # to # -->  5 to 10)

    with open(Path.cwd() / 'debug' / 'matchedModscsv', "w") as write_file:
        write_file.write(f"\"{mod}\", \"{genericMod}\", \"{valList}\"\n")

    simpleItem[genericMod] = valList

    # add
    try:
        affixId = reverseAffixDict[type,genericMod]
        displayItemDict.setdefault(affixId, []).append(simpleItem) # append this item to the affixId list, first time create empty list
    except Exception as e:
        print("%%% Can't add to displayItemDict", affixId, type, genericMod, simpleItem)
        print(e)

    return simpleItem

def processMods(item):
    # skip this stuff for now
    if item['frameType'] in [4, 5, 6, 8] or 'Flask' in item['typeLine']:  # 4=gem, 5=currency, 6=div, 8=prophecy
        return

    simpleItem = {}
    simpleItem['name']      = item['name']
    simpleItem['type']      = item['type']
    simpleItem['location']  = item['location']
    simpleItem['unmatched'] = []

    if 'implicitMods' in item.keys():  # item['implicitMods'] is not None:
        for mod in item['implicitMods']:
            simpleItem = processMod(simpleItem, item, mod, 'implicit')
    if 'explicitMods' in item.keys():  # item['explicitMods'] is not None:
        for mod in item['explicitMods']:
            simpleItem = processMod(simpleItem, item, mod, 'explicit')
    if 'fracturedMods' in item.keys():
        for mod in item['fracturedMods']:
            simpleItem = processMod(simpleItem, item, mod, 'fractured')
    if 'craftedMods' in item.keys():
        for mod in item['craftedMods']:
            simpleItem = processMod(simpleItem, item, mod, 'crafted')

def processItem(item, league, char=None):
    global stashInfo

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

    processMods(item)

    return item

# add some extra data (location, type) modify some data (name - if empty)
# TODO: type is not working at this time - need to figure out how to get "ring" or "one handed weapon", may have to
# parse a image file name :(
def processData():
    global dataDict
    global displayItemDict
    global stashInfo

    for league in dataDict.keys():
        for char in dataDict[league]['characters']:
            for i,v in enumerate(dataDict[league]['characters'][char]['items']):
                dataDict[league]['characters'][char]['items'][i] = processItem(v, league, char)

        for tab in dataDict[league]['stash']:
            for i,v in enumerate(dataDict[league]['stash'][tab]['items']):
                dataDict[league]['stash'][tab]['items'][i] = processItem(v, league)

    with open("debug/dataDict.json", "w") as write_file:
        json.dump(dataDict, write_file, indent=4)

# query a set of stash tabs/chars based on a CONFIG/FILTER
# this will create the pool of data to further filter upon (afixes/types/etc)
@app.route('/getdata', methods=['GET','POST'])
def getdata():
    global dataDict
    global displayItemDict
    global stashInfo

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

    sourceConfig = json.loads(open('sourceConfig.json').read())
    print('sourceConfig:',sourceConfig)

    # reset data
    displayItemDict = {}
    # only one league at this time.  TODO: allow multiple league configs?
    league = list(sourceConfig.keys())[0] # TODO: how to access iterable view?
    dataDict[league] = {'characters':{}, 'stash':{}}

    # get stash info for tab names
    stashInfo = poeq.getStashInfo(league)

    # TODO: TEMP HACK to not do query every time
    if (1):
        dataDict = json.loads(open('debug/dataDict.json').read())
    else:
        for character in sourceConfig[league]['characters']:
            inventory = poeq.getCharacterInventory(character)
            #print('inventory:',inventory)
            itemList.extend(inventory['items'])
            dataDict[league]['characters'][character] = inventory

        for stashNum in sourceConfig[league]['stash']:
            tab = poeq.getStashTab(league, stashNum)
            #print('tab:',tab)
            dataDict[league]['stash'][stashNum] = tab


    # PROCESS Data
    processData()

    #return render_template('items.html')
    return redirect(url_for('items'))


'''
INPUT:
displayItemDict
{
    '<affix id>': [ <simpleItem> ],
}
simpleItem = { 'name' : X, 'type' : Y, 'location' : Z, <affix name1> : [val1,val2,..], <affix name1> : [val1,val2,..] } this is what is passed to Datatables

?filterList? = []
- passed in from the drop down
- list of affix id string to filter upon, ex "explicit.stat_3032590688"

OUTPUT:
tableData
{
    "items" : []  # simpleItems
    "visible" : []  # col names - generic affixs and name/location/type/etc
}
'''
# called when items table is loaded
@app.route('/filterdata', methods=['GET'])
def filterdata():
    print(f"filterdata: {request.method}")
    global affixList
    global foo
    global dataDict
    global displayItemDict  # simplified dict of all items contained in configured stashes/chars indexed by affix id

    # TODO: tmp - list of all items processed
    with open(Path.cwd() / 'debug' / 'displayItemDict.json', "w") as write_file:
        json.dump(displayItemDict, write_file, indent=4)

    # TODO: this should come from the filter dropdown/request data
    affixIdFilterList = ["explicit.stat_3032590688", "explicit.stat_2144192055", "explicit.stat_3299347043"]  # "Adds # to # Physical Damage to Attacks", "# to Evasion Rating"

    # data passed to the table - which cols are visible and the data to display
    tableData = {"items":[], "visible":[]}

    # don't need to display the same item multiple times for matched affixs - this will keep a list of location - should be unique...
    matchedItemsSet = set()

    # find any item with an affix id contained in the filter list and add to table data
    for affixId in affixIdFilterList:
        (affixType, affixText) = affixDict[affixId]

        simpleItemList = []
        try:
            simpleItemList = displayItemDict[affixId]
        except KeyError:
            pass # likely means no owned items with this affix, not a problem

        for simpleItem in simpleItemList:
            if simpleItem['location'] in matchedItemsSet:
                continue
            else:
                tableData["items"].append(simpleItem)
                matchedItemsSet.add(simpleItem['location'])

        # this column should be visible
        tableData["visible"].append(affixText)

    # TODO: extra data to alawys show for now
    tableData["visible"].insert(0, "type")
    tableData["visible"].insert(0, "name")
    tableData["visible"].insert(0, "location")
    tableData["visible"].append("unmatched")

    # TODO: show cols based on a configurable input --> displayConfig.json - "Life" : ["type", "name", "location", "+# total maximum Life"
    # should it use the affix id?  should it also include the type?

    with open('debug/tableData.json', 'w') as file:
        json.dump(tableData, file, sort_keys=True, indent=4)

    # a dict should be ok, recent versions of flask will call jsonify under the hood.
    return tableData
