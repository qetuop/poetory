# poetory
Grab, Display, Search your personal Path of Exile inventory

### Setup
Test with Python 3.8, might work with earlier versions.  
Ensure all system packages are installed for the right version ex:
```
sudo apt-get install python3.8-venv
sudo apt-get install python3.8-dev
```

### Build
```
git clone https://github.com/qetuop/poetory.git
cd poetory
python3.8 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd poetory
cp config.json.default config.json
```

set the PATYHON path so packages can be found TODO: how to fix this?

```export PYTHONPATH=$PYTHONPATH:$HOME/PycharmProjects/poetory```

### Configure
~~edit config.json and set account, league, poessid~~

edit poetory/filter/source.json and add any character/stash # to grab, surround character names with double quotes and comma seperate. ex:

{
    "standard": {
        "characters": [
            "BOB",
            "Joe"
        ],
        "stash": [
            1,
            2,
            3,
            4
        ]
    }
}

### Run
```python3.8 poetory.py``` 

open url 

```http://127.0.0.1:5000/```