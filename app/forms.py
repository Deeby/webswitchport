from wtforms import SelectField, SubmitField, StringField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Length
from flask_wtf import FlaskForm


class DeviceSelectForm(FlaskForm):
    device = SelectField('Device')
    ports = SelectField('Port', choices=[])
    vlans = SelectField('Vlan', choices=[])
    save = SubmitField('Save')
    text = TextAreaField('text')


class LoginForm(FlaskForm):
    login_fld = StringField('Login', validators=[DataRequired(), Length(min=3, max=30)])
    pass_fld = PasswordField('Pass', [DataRequired()])
    login_btn = SubmitField('Sign in')
