from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError
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
            raise ValidationError('El correo ya está registrado')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Correo electrónico', validators=[
        DataRequired(message='Ingresa tu correo electrónico'),
        Email(message='Ingresa un formato de correo válido'),
        Length(max=80)
    ])
    submit = SubmitField('Enviar Enlace de Recuperación')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nueva Contraseña', validators=[
        DataRequired(message='Ingresa tu nueva contraseña'),
        Length(min=6, message='La contraseña debe tener al menos 6 caracteres')
    ])
    confirm = PasswordField('Confirmar Nueva Contraseña', validators=[
        DataRequired(message='Confirma tu nueva contraseña'),
        EqualTo('password', message='Las contraseñas no coinciden')
    ])
    submit = SubmitField('Restablecer Contraseña')

