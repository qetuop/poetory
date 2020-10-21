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
pip3 install wheel
pip install -r requirements.txt
cd poetory
cp config.json.default config.json
```

set the PATYHON path so packages can be found TODO: how to fix this?

```export PYTHONPATH=$PYTHONPATH:$HOME/PycharmProjects/poetory```

### Configure
edit config.json and set account, league, poessid

### Run
```python3.8 poetory.py``` 
