from wtforms import SelectField, SubmitField, StringField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Length
from flask_wtf import FlaskForm


class DeviceSelectForm(FlaskForm):
    device = SelectField('Устройство')
    ports = SelectField('Порт', choices=[])
    vlans = SelectField('vlan', choices=[])
    save = SubmitField('Сохранить')
    text = TextAreaField('text')


class LoginForm(FlaskForm):
    login_fld = StringField('Логин', validators=[DataRequired(), Length(min=3, max=30)])
    pass_fld = PasswordField('Пароль', [DataRequired()])
    login_btn = SubmitField('Вход')
