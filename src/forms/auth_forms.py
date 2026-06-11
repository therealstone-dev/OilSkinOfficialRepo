from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from src.models.ModeloUsuario import ModeloUsuario

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Iniciar Sesión')

class RegisterForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=50)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=80)])
    direccion = StringField('Direccion', validators=[DataRequired(), Length(max=100)])
    celular = StringField('Celular', validators=[DataRequired(), Length(max=15)])
    telefono = StringField('Telefono', validators=[Optional(), Length(max=15)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('Confirmar Password', validators=[DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir')])
    submit = SubmitField('Crear Cuenta')

    def validate_email(self, field):
        existing = ModeloUsuario.get_by_email(field.data)
        if existing:
            raise ValueError('El correo ya está registrado')
