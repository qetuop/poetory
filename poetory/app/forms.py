from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, PasswordField, BooleanField, SubmitField, TextField

class LoginForm(FlaskForm):
    account = StringField('Account')
    poessid = StringField('POESSID') # POESESSID de4c695e9a693a94b563a1727233c7b7
    league = SelectField(u'League')
    characters = SubmitField('Characters')  # TODO: temp buttons until i figure out how to use links to submit data
    items = SubmitField('Items')
    tabs = StringField('Verify')

class ItemForm(FlaskForm):
    id = StringField('ID') # DB id
    name = StringField('Name')
    update = SubmitField('Update')

class CharacterForm(FlaskForm):
    id = StringField('ID') # DB id
    name = StringField('Name')
    league = StringField('League')
    class_ = StringField('Class')
    level = StringField('Level')
    ascendancy_class = StringField('Ascendancy')
    update = SubmitField('Update')