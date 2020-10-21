from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Item(db.Model):
    print('Item ctor')
    id = db.Column(db.Integer, primary_key=True)
    verified = db.Column(db.Boolean)
    properties = db.relationship('Property', backref='item', lazy='dynamic')


class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    name = db.Column(db.String(128))

'''
    def __init__(self, ascendancyClass, class_, classId, experience, lastActive, league, level, name):
        self.ascendancyClass = ascendancyClass
        self.class_ = class_   #fck
        self.classId = classId
        self.experience = experience
        self.lastActive = lastActive
        self.league = league
        self.level = level
        self.name = name
        
        {'character': {'ascendancyClass': 2, 'class': 'Trickster', 'classId': 6, 'experience': 2182014614, 'lastActive': True, 'league': 'Blight', 'level': 91, 'name': 'SalWrendMkII'}
        '''
class CharacterInfo(db.Model):
    print('CharacterInfo ctor')
    id = db.Column(db.Integer, primary_key=True)
    ascendancy_class = db.Column(db.String(32))
    class_ = db.Column(db.String(32))
    class_id = db.Column(db.Integer)
    experience = db.Column(db.Integer)
    last_active = db.Column(db.Boolean)
    league = db.Column(db.String(32))
    level = db.Column(db.Integer)
    name = db.Column(db.String(128))




