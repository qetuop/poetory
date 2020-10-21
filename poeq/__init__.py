import time
import requests
import json
from time import sleep
import logging
from pathlib import Path


SLEEP = 1.1

league = None
account = None
poesessid = None
cookies = None

'''
limit / per / timeout

x-rate-limit-account: 45:60:60,240:240:900
limit of 45 requests every 60 seconds; 60 second timeout if limit exceeded
limit of 240 requests every 240 seconds; 900 second timeout if limit 
'''
#rateLimit = {'short':[0,0,0], 'long':[0,0,0]}
rateLimit = {'short':{'curr':0, 'per':0, 'timeout':0}, 'long':{'curr':0, 'per':0, 'timeout':0}}


'''
curr / per / timeout

x-rate-limit-account-state: 2:60:0,3:240:0
2 request in the last 60 seconds, no timeout in effect
3 request in the last 240 seconds, no timeout in effect

x-rate-limit-account-state: 0:60:19,84:240:0 = 19sec before another request can be made, counts down

limit example:
x-rate-limit-account-state: 45:60:0,75:240:0 = at max requests, next one will limit you
x-rate-limit-account-state: 46:60:0,76:240:0 = next request - Code 429 returned
x-rate-limit-account-state: 46:60:60,77:240:0 =  3rd request
'''
rateState = {'short':{'curr':0, 'per':0, 'timeout':0}, 'long':{'curr':0, 'per':0, 'timeout':0}}

lastRequest = 0  #

def setup(l, a, p):
    global league, account, poesessid, cookies
    league = l
    account = a
    poesessid = p

    cookies = dict(POESESSID='%s' % poesessid)

# check rate limits a return...sleep value?
def rateLimited():
    sleepVal = 0.0

    #print(rateLimit)
    #print(rateState)

    # if either state value has a timeout just sleep for that amount
    sleepVal = max(rateState['short']['timeout'], rateState['long']['timeout'])

    #print(sleepVal, lastRequest)

    # if not limited yet keep us from soon being so...
    # how
    if sleepVal != 0:
        pass


    return sleepVal

def updateRate(header):
    global rateLimit
    global rateState
    global lastRequest

    limitAcc = header['X-Rate-Limit-Account'].split(',')  # '45:60:60,240:240:900'
    limitState = header['X-Rate-Limit-Account-State'].split(',')  # '1:60:0,1:240:0'

    # these shouldn't change often (ever?) but might as well update with every request...is that bad?
    rateLimit['short']['curr']      = limitAcc[0].split(':')[0]
    rateLimit['short']['per']       = limitAcc[0].split(':')[1]
    rateLimit['short']['timeout']   = limitAcc[0].split(':')[2]
    rateLimit['long']['curr']       = limitAcc[1].split(':')[0]
    rateLimit['long']['per']        = limitAcc[1].split(':')[1]
    rateLimit['long']['timeout']    = limitAcc[1].split(':')[2]

    rateState['short']['curr']      = limitState[0].split(':')[0]
    rateState['short']['per']       = limitState[0].split(':')[1]
    rateState['short']['timeout']   = limitState[0].split(':')[2]
    rateState['long']['curr']       = limitState[1].split(':')[0]
    rateState['long']['per']        = limitState[1].split(':')[1]
    rateState['long']['timeout']    = limitState[1].split(':')[2]

    lastRequest = time.time()

'''
Code	Text	Description
200	OK	The request succeeded.
400	Bad Request	The request was invalid. Check that all arguments are in the correct format.
404	Not Found	The requested resource was not found.
429	Too many requests	You are making too many API requests and have been rate limited.
500	Internal Server Error	We had a problem processing your request. Please try again later or post a bug report.

return "Returns the json-encoded content of a response, if any" --> a list?
'''
def grabData( url ):
    global rateLimit
    global rateState

    wait = SLEEP

    #sleep(wait)
    headers = {
        'User-Agent': 'POE Query (poeq) https://github.com/qetuop/poeQuery'
    }

    if ( rateLimited() == True ):
        sleep(1)

    r = requests.get(url, cookies=cookies, headers=headers)
    while (r.status_code == 429 ):
        print('RATE LIMTED....WAITING %s sec before retrying'%wait)
        r = requests.get(url, cookies=cookies)
        wait = wait*2
        sleep(wait)

    # set curr rate limit data - will be out of date depending on how long between the next request but shouldn't
    # matter that much
    updateRate(r.headers)


    return r.json()


def checkForError(jresp):
    error = None
    print(jresp)
    if ( 'error' in jresp ):
        return(jresp['error']['code'], jresp['error']['message'])

'''
    [{"id":"Standard","realm":"pc","description":"The default game mode.","registerAt":"2019-09-06T19:00:00Z",
    "url":"http:\/\/pathofexile.com\/forum\/view-thread\/71278","startAt":"2013-01-23T21:00:00Z","endAt":null,
    "delveEvent":true,"rules":[]},...]
    '''
def getLeagues():
    r = requests.get('https://www.pathofexile.com/api/leagues')
    url = 'https://www.pathofexile.com/api/leagues'
    out = grabData(url)
    return out

# ["Standard", "Hardcore",...]
def getLeagueNames():
    allLeagues = getLeagues()

    leagues = []
    for league in allLeagues:
        leagues.append(league['id'])

    return leagues


def getNumTabs(league):
    url = 'https://pathofexile.com/character-window/get-stash-items?league=%s&accountName=%s' %(league,account)

    #cookies = dict(POESESSID='de4c695e9a693a94b563a1727233c7b7')
    #cookies = dict(POESESSID='d')  # error
    #print(url)
    r = requests.get(url, cookies=cookies)

    # checkForError(r.json())
    tabs = None
    try:
        tabs = r.json()['numTabs']
    except:
        tabs = 'error'

    #return (r.status_code, r.json()) #tabs
    return tabs

'''
    [{"name": "StrummBrand", "league": "Standard", "classId": 5, "ascendancyClass": 1, "class": "Inquisitor",
      "level": 94, "experience": 2660312216}, ... ]
      '''
def getCharacters(account):
    # can't do by league, at least don't know how
    url = ('http://pathofexile.com/character-window/get-characters?accountName=%s' %account) # requests.Response
    out = grabData(url)
    dumpToFile('characters.json', out)
    return out

'''
{"items":[{"verified":false,
...
"inventoryId":"MainInventory"}],
"character":{"name":"SalWrendMkII","league":"Blight","classId":6,"ascendancyClass":2,"class":"Trickster","level":91,"experience":2119008055,"lastActive":true}}
'''
def getCharacterInventory(charName):
    url = 'https://pathofexile.com/character-window/get-items?character=%s'%charName
    out = grabData(url)
    print(out)
    dumpToFile('%s.json' % charName, out)
    return out

def getAllCharacterInventory(account):
    out = []
    chars = getCharacters(account)
    for char in (map(lambda x: x['name'], chars)):
        out.append(getCharacterInventory(char))

    return out


def getStashTab(league, tabNum):
    url = 'https://pathofexile.com/character-window/get-stash-items?league=%s&accountName=%s&tabIndex=%s' \
          % (league, account, tabNum)
    out = grabData(url)
    print(tabNum,out)
    return out

def getStash(league):
    stash = []
    for i in range(0,getNumTabs(league)):
        stash.append(getStashTab(league, i))

    dumpToFile('%s.json' % league, stash)
    return stash

def getLeague(account, league):
    leagueDict = {'name': league, 'characters': [], 'stash': []}

    # only want the ones for this league
    chars = getCharacters(account)
    filteredChars = list(filter(lambda x: (x['league']==league), chars))
    for char in (map(lambda x: x['name'], filteredChars)):
        charDict = {}
        #print(char)
        charInv = getCharacterInventory(char)
        charDict[char] = charInv
        leagueDict['characters'].append(charDict)

    #print(leagueDict['characters'][1])

    # get all stash
    leagueDict['stash'] = getStash(league)
    return leagueDict



def getAccount(account):
    accountDict = {'account' : account, 'leagues' : []}

    leagues = getLeagues()
    for league in (map(lambda x: x['id'], leagues)):
        print(league)
        accountDict['leagues'].append(getLeague(account, league))

    dumpToFile('%s.json' % account, accountDict)
    return accountDict



def dumpToFile(fileName, data):
    p = Path('jsonData')
    p.mkdir(exist_ok=True)
    path = Path.cwd() / 'jsonData' / fileName

    with open(path, 'w') as file:
        json.dump(data, file, sort_keys=True, indent=4)

def readFromFile(fileName):
    path = Path.cwd() / 'jsonData' / (fileName +'.json')

    with open(path, 'r') as file:
        return json.load(file)
