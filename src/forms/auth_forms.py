from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional


class LoginForm(FlaskForm):
    email = EmailField('Correo electrónico', validators=[DataRequired(), Email(message='Ingrese un correo válido.'), Length(max=80)])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=8, max=128)])
    submit = SubmitField('Iniciar Sesión')


class RegisterForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=50)])
    email = EmailField('Correo electrónico', validators=[DataRequired(), Email(message='Ingrese un correo válido.'), Length(max=80)])
    direccion = StringField('Dirección', validators=[DataRequired(), Length(min=3, max=50)])
    celular = StringField('Celular', validators=[DataRequired(), Length(min=7, max=15)])
    telefono = StringField('Teléfono', validators=[Optional(), Length(max=15)])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField('Confirmar contraseña', validators=[DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir.')])
    submit = SubmitField('Crear Cuenta')
