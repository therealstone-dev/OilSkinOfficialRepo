from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, EmailField, TelField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError
from src.models.ModeloUsuario import ModeloUsuario

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Iniciar Sesión')

class RegisterForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=50)])
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=80)])
    direccion = StringField('Direccion', validators=[DataRequired(), Length(max=100)])
    celular = TelField('Celular', validators=[DataRequired(), Length(max=15)])
    telefono = TelField('Telefono', validators=[Optional(), Length(max=15)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('Confirmar Password', validators=[DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir')])
    submit = SubmitField('Crear Cuenta')

    def validate_email(self, field):
        existing = ModeloUsuario.get_by_email(field.data)
        if existing:
            raise ValidationError('El correo ya está registrado')
