from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

#Establecemos el mail como atributo unico en la base de datos de Django
User._meta.get_field('email')._unique = True
# Cear los modelos aqui ---------------------------------------------------------------------------------------------------------------------------------------------------------

class Gasto(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  #conexion con el usuarion que realizo la peticion
    type = models.CharField(max_length=45)  #tipo de gasto
    value = models.FloatField(default=0)    
    date = models.DateField(default=timezone.now().date())   #Dia de paso
    nPayments = models.IntegerField(default=1) #CUOTAS
    paymentId = models.CharField(max_length=45, default='1_1')   #Codigo de distincion del movimiento 
    rate = models.FloatField(default=0)   #interes
    description = models.CharField(max_length=100, default='-')    
    done = models.BooleanField(default=True)
    
    def get_model_name(self):
        return 'gasto'                    

    class Meta:   #Conecta con la base de datos
        db_table = 'gastos'

class Ingreso(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=45)   #Tipo de ingreso
    value = models.FloatField(default=0)
    date = models.DateField(default=timezone.now().date())   #Dia de ingreso de dinero
    repeat = models.IntegerField(default=1)  #Meses consecutivos donde se quiere acreditar el ingreso
    description = models.CharField(max_length=100, default='-') 
    done = models.BooleanField(default=True)
    paymentId = models.CharField(max_length=45, default='1_1')   #Codigo de distincion del movimiento 
    
    def get_model_name(self):
        return 'ingreso'

    class Meta:
        db_table = 'ingresos'


class InfoUser(models.Model):
    #Se reune la informacion de saldo (balance total) del usuario 
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    saldo = models.DecimalField(max_digits=60, decimal_places=2)

    class Meta:
        db_table = 'infoUsers'
        
class Recordatorio(models.Model):
    #Datos reunidos por un recordatorio 
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    texto = models.CharField(max_length=250)
    dueDate = models.DateField()   #Fecha final
    daysPrior = models.IntegerField(default=1)   #Dia que desea recibir el recordatorio
    enviado = models.BooleanField(default=True)   #Si ya fue enviado el mail de aviso
    
    class Meta:
        db_table = 'recordatorios'
    
    def __str__(self):   #Devuelve el mensaje del recordatorio
        return self.texto
    
#Se usa esta clase como una tabla para llevar el trackeo de quienes cambian su contraseña.
#Además sirve para lugo crear un formulario a partir del modelo que facilite el chequeo de los campos.
class forgotPassword(models.Model):
    #Tabla de usuarios y contraseñas
    user=models.CharField(max_length=150)
    mail=models.CharField(max_length=150)

    class Meta:
        db_table = 'forgotPassword'
