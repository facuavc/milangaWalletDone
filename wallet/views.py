#Se importan las acciones necesarias 
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import authenticate, update_session_auth_hash, logout as logout_user, login as login_user
from django.contrib.auth.decorators import login_required
from django.views.defaults import page_not_found
from django.db.models import Q
from django.urls import reverse

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import json

import random

from itertools import chain

from datetime import datetime, timedelta 

from calendar import month_name

import locale

from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from django.contrib.auth.models import User
from .models import Gasto , Ingreso , InfoUser, Recordatorio

from .forms.forms import UserRegistrationForm, LoginForm, ChangePassForm, GastoForm, IngresoForm, recordatoriosForm, forgotPasswordForm

# Envía el mail de bienvenida (W=Welcome)
def send_W_mail(mail,name):
    

    
    #Se establecen datos para el envio del mensaje de bienvenida, como el nombre, mail remitente y plantilla 
    name = str(name)
    me='milangawallet@gmail.com'
    template = loader.get_template("emailTemplate.html")
    rendered_content = template.render({'nombre': name})
    msg = MIMEMultipart('alternative')

    #Se configuran detalles del correo electronico
    msg['Subject'] = "Bienvenido a Milanga Wallet!!"
    msg['From'] = me
    msg['To'] = mail

    #Se crean dos partes del mensaje: Texto de bienvenida y el HTML. y se adjuntan al mensaje
    part1 = MIMEText("Hola!\nComo estas?\nMilanga Wallet te da la bienvenida!!\nEste es el link a la app:\nhttp://127.0.0.1:8000/login/", 'plain')
    part2 = MIMEText(rendered_content, 'html')
    msg.attach(part1)
    msg.attach(part2)

    try:
        # se envia el mansaje a traves de 'local SMTP server'.
        mail_server = smtplib.SMTP('smtp.gmail.com', 587)
        mail_server.ehlo()
        mail_server.starttls()
        mail_server.login('milangawallet@gmail.com', 'ujfeyzrlyhnsimux')
        mail_server.sendmail(me, mail, msg.as_string())
        mail_server.quit()
        print(f'Email sent')
        return True
    
    except Exception as e:
        print(f"An error occurred: {e}")


#Envía el mail de reminder
@login_required
def send_R_email(request):

    today = datetime.now().date()
    #solo queremos analizar aquellos que no fueron enviados
    reminders = Recordatorio.objects.filter(enviado=False)

    for recordatorio in reminders:
        rDate = recordatorio.dueDate

        #se fija si la diferencia de dias entre hoy y'dueDate' es igual a la seteada por el usuario
        if rDate-today==timedelta(days=recordatorio.daysPrior): 
            #busca la tabla del usuario que se quiere mandar mail
            tUsuario=User.objects.get(username=recordatorio.user)

            #datos importantes
            name = tUsuario.first_name
            mail=tUsuario.email
            me='milangawallet@gmail.com'
            
            #se genera el template
            template = loader.get_template("reminderTemplate.html")
            rendered_content = template.render({'reminder': recordatorio.texto, 'nombre': name, 'dueDate':recordatorio.dueDate})
            
            #se configuran deetalles del correo electronico
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "Recordatorio de Milanga Wallet"
            msg['From'] = me
            msg['To'] = mail

            #se crean las dos partes del mail (una tipo texto y la otra html)
            part1 = MIMEText("Hola!\nComo estas?\nRecuerda que tienes el siguiente recordatorio: {} para dentro de {} dias\nEste es el link a la app:\nhttp://127.0.0.1:8000/login/", 'plain'.format(recordatorio.texto,recordatorio.dueDate))
            part2 = MIMEText(rendered_content, 'html')

            msg.attach(part1)
            msg.attach(part2)

            try:
                # Se intenta enviar mensaje mediante un servidor SMTP.
                mail_server = smtplib.SMTP('smtp.gmail.com', 587)
                mail_server.ehlo()
                mail_server.starttls()
                mail_server.login('milangawallet@gmail.com', 'ujfeyzrlyhnsimux')
                mail_server.sendmail(me, mail, msg.as_string())
                mail_server.quit()
                recordatorio.enviado=True
                recordatorio.save()

                print(f'Email sent to {mail}') #para saber nosotros, que lo vemos en terminal
                return True

            except Exception as e:
                print(f"An error occurred: {e}") #lo mismo
    return(request)


#Envía el emial de forgot password
def send_fP_mail(password, user, mail):
    #Se establece la direccion de correo electronico remitente y carga la plantilla del mensaje con sus datos necesarios
    me='milangawallet@gmail.com'
    template = loader.get_template("fP_mail.html")
    rendered_content = template.render({'nombre': user, 'password': password})
    msg = MIMEMultipart('alternative')

    #Se configuran detalles del correo electronico
    msg['Subject'] = "Milanga Wallet - Recuperacion de contraseña"
    msg['From'] = me
    msg['To'] = mail

    #Se crean dos partes del mensaje: la contraseña creadad y el HTML. y se adjuntan al mensaje
    part1 = MIMEText("Hola!\nComo estas?\nEsta es tu nueva contraseña: {password}\nEste es el link a la app:\nhttp://127.0.0.1:8000/login/", 'plain')
    part2 = MIMEText(rendered_content, 'html')
    msg.attach(part1)
    msg.attach(part2)

    try:
        # Se intenta enviar mensaje mediante un servidor SMTP.
        mail_server = smtplib.SMTP('smtp.gmail.com', 587)
        mail_server.ehlo()
        mail_server.starttls()
        mail_server.login('milangawallet@gmail.com', 'ujfeyzrlyhnsimux')
        mail_server.sendmail(me, mail, msg.as_string())
        mail_server.quit()
        print(f'Email sent')
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        
        
#Formatea la información las categorías del cuadro de home a partir de la info para cada categoría en
#bruto. Calcula los porcentajes de cada una y les da un color random.
def categoriesToList(original_values):
    # Redondear al entero mas cercano
    rounded_values = {key: round(value) for key, value in original_values.items()}

    #Calcula la diferencia entre la suma redondeada y la deseada 
    rounded_sum = sum(rounded_values.values())
    discrepancy = 100 - rounded_sum

    # Ajustar error a mayor redondeor
    max_error_key = max(original_values, key=lambda key: abs(original_values[key] - rounded_values[key]))
    rounded_values[max_error_key] += discrepancy
    
    color_list=['bg-danger','bg-warning','','bg-info','bg-success']
    #Crear una lista de diccionarios con información de categoría, valor redondeado y clase de color aleatoria
    rounded_values=[{'category':key,'value':value, 'color_class':random.choice(color_list)} for key,value in rounded_values.items()]

    #Ordena por valor decendiente y renderiza 
    rounded_values = sorted(rounded_values, key=lambda x: x['value'], reverse=True)
    return rounded_values


def isAlphabetic(string):
    #Verifica que los caracteres de un 'string' sean letras o espacios 
    return all(char.isalpha() or char.isspace() for char in string)

#Actualiza el valor de saldo para un usuario en particular (tabla infousers)
def updateSaldo(user,value):
    #Se localiza la exitencia de balances previos o genera un histoial al cargo de movimientos de un usuario
    if InfoUser.objects.filter(user_id=user.id).exists():
        userInfo = InfoUser.objects.get(user_id=user.id)
        userInfo.saldo = float(userInfo.saldo) + value 
    else:
        userInfo = InfoUser(user_id=user.id,saldo=value)
    #Devuelve el nuevo balance o saldo total del usuario
    return userInfo
        

    
#VIEWS-----------------------------------------------------------------------
def login(request):
    #Se inicia el formmulario de inicio de sesion y establecen variables de control de proceso
    form = LoginForm()
    account = True
    loginError=''
    
    if request.method == 'POST':
        info = request.POST
        #Se obtienen los datos del formulario y se autentican con una funcion de Django 
        user = authenticate(username=info['username'],password=info['password'])
        if user is not None:
            #Datos autenticados correctamnete 
            login_user(request,user)
            print(str(request.user.username)+' logged in successfully!')
            
        else:
            #Posibles casos de error
            try:
                print('es este',User.objects.get(username=info['username']))
                #No autenticados
                loginError='La contraseña es incorrecta.'
            except:
                print('no tiene cuenta')
                loginError='No existe una cuenta ya registrada con ese nombre de usuario.'
            account = False
         
    #Inicia secion cuando autentica correctamente   
    if request.user.is_authenticated:
        return redirect(home)
    #Envia error cuando no logra autenticar 
    return render(request, "login.html",{'request':request,'form':form,'account':account, 'loginError':loginError})


def register(request):
    #Inicia el form de registro y un diccionario para atrapar errores 
    form = UserRegistrationForm()   
    errors={}
    
    if request.method == 'POST':
        #Conotrol de los datos infresados por el usuario
        form = UserRegistrationForm(request.POST)
        if not (isAlphabetic(request.POST['first_name'])):
            errors['first_name']=['El nombre solo debe tener letras y espacios.']
        elif not isAlphabetic(request.POST['last_name']):
            errors['last_name']=['El apellido solo debe tener letras y espacios.']
        
        elif form.is_valid():
            form.cleaned_data['first_name'] = form.cleaned_data['first_name'].title()
            form.cleaned_data['last_name'] = form.cleaned_data['last_name'].title()
            form.save()
    
            while True:
                userObj = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
                if userObj is not None:
                    login_user(request, userObj)
                    print('Se ha registrado un nuevo usuario: ',userObj.username,', de id=',userObj.id,'!')
                    
                    userInfo = InfoUser(user_id=userObj.pk,saldo=0)
                    userInfo.save()
                    
                    break
            
            mail=request.user.email
            name=request.user.first_name

            send_W_mail(mail,name)
            return redirect('home')
        
        else:
            
            errors=dict(form.errors)
            errors['password']=[]
            
            errores={}
           
            for key, value in errors.items():
                
                if not key in errores:
                    errores[key]=[]
                
                try:
                    value = value[0]
                except:
                    value = value
                
                
                if 'user with that username' in value:
                    value = ['Un usuario con ese nombre de usuario ya existe.']
                elif 'with this Email' in value:
                    value = ['Un usuario con ese email ya existe.']
                elif 'similar' in value:
                    value=['La contraseña es muy similar a alguno de sus otros datos.']
                elif 'common' in value:
                    value=['Esa contraseña es muy común!']
                
                
                if 'password' in key:
                    errors['password']+=value
                
                errores[key]+=value  
            
            errors = errores
              
    return render(request, "register.html",{'request':request,'form':form, 'errors':errors})



@login_required
def home(request):
    #Funcion que construye la pagina principal o home, primero carganto la plantilla y valors que esta necesita 
    template = loader.get_template("home.html")
    datos = {'gastos':0,'ingresos':0,'saldo':float(InfoUser.objects.get(user_id=request.user.id).saldo)}

    send_R_email(request) #agregamos esta linea para que cada vez que un usuario se logee a nuestra plataforma se envien todods los mails de tipo reminder
    
    #Se obtienen las listas de los distintos tipos de movimientod del usuario
    gastos = list(Gasto.objects.filter(user_id=request.user.id,done=True))
    ingresos = list(Ingreso.objects.filter(user_id=request.user.id,done=True))
    
    graficosData=[]
    gastos_cat = {}
    ingresos_cat = {}
    #Se recorren las listas de cada tipo de movimmiento: agregando datos a la lista para graficos, actualizando el total y actualizando las categorias del diccionario 
    for i in ingresos:
        datos['ingresos'] += float(i.value)
        graficosData.append({'type':'ingreso','value':i.value,'date':str(i.date)})
        if not i.type in ingresos_cat:
            ingresos_cat[i.type]=float(i.value)
        else:
            ingresos_cat[i.type]+=float(i.value)
    
    for g in gastos:
        datos['gastos'] += float(g.value)
        graficosData.append({'type':'gasto','value':g.value,'date':str(g.date)})
        if not g.type in gastos_cat:
            gastos_cat[g.type]=float(g.value)
        else:
            gastos_cat[g.type]+=float(g.value)
    
    #Se ordena la lista de datos para graficos por fecha descendiente 
    graficosSortedData = sorted(graficosData, key=lambda x:datetime.strptime(x['date'], '%Y-%m-%d'),reverse=True)
    
    #Se determina la cantidad de años para los que hay ingreso
    if len(gastos)!=0 and len(ingresos)!=0: 
        yearsRange=range(int(graficosSortedData[0]['date'].split('-')[0]),int(graficosSortedData[-1]['date'].split('-')[0])-1,-1)
        print(yearsRange)
        info=True
        
        for key, value in ingresos_cat.items():
            ingresos_cat[key]= round(value*100/datos['ingresos'])
        for key, value in gastos_cat.items():
            gastos_cat[key]= value*100/datos['gastos']
            
        ingresos_cat=categoriesToList(ingresos_cat)    
        gastos_cat=categoriesToList(gastos_cat)
    else:
        yearsRange=range(int(datetime.now().year),int(datetime.now().year)+1)
        info=False
        
    #Se conviete la lista de datos para grafico en JSON para graficar
    graficosData = json.dumps(graficosSortedData)
    
    #Renderiza la planilla y incluye los datos para los graficos en la misma
    return HttpResponse(template.render({'request':request, 
                                         'datos':datos,
                                         'graficosData':graficosData,
                                         'yearsRange':yearsRange,
                                         'info':info,
                                         'ingresosCat':ingresos_cat,
                                         'gastosCat':gastos_cat,
                                         }))



@login_required
def movimientos(request,type):
    #Recupera todos los movimientos de un tipo especifico pertenecientes a un usuario, ademas filtramos que hayan sido ya realizados
    if type == 'gastos':
        data= Gasto.objects.filter(user=request.user, done=True)
    elif type == 'ingresos':
        data= Ingreso.objects.filter(user=request.user, done=True)

    #Se crea un diccionario con la informacion para rederizar la planilla
    context = {
        'request': request,
        'type': type,
        'type_unitary': ''.join(list(type)[:-1]),
        'data': data,  
    }
    
    for i in data:
        i.paymentId = [i.paymentId.split('_')[-1],i.paymentId.split('_')[0]]  
    
    #Se obtiene y renderiza la planilla
    template = loader.get_template("tables.html")
    
    return HttpResponse(template.render(context))



def forgotPassword(request):
    #Se inicia una variable de control y crea una instancia del formulario especifico
    alreadySent = False
    form=forgotPasswordForm()
    error=False
    alreadySent=False
    
    if request.method == 'POST':
        #se crea una instancia del formulario con los datos de la solicitud de cambio
        mutable_post_data = request.POST
        form = forgotPasswordForm(mutable_post_data)
        error=False
        alreadySent=False
         
        if form.is_valid():
            #Si el ingreso es valido se obtienen los datos del formularios y se consulta existencia en base de datos
            user=form.cleaned_data['user']
            mail=form.cleaned_data['mail']

            user_object=User.objects.filter(Q(email=mail)).first()
            if user_object and user_object.username==user:
                #Si los datos de el mail y usuario coinciden en la base de datos de Django, se remplaza la contraseña por una generada de manera aleatoria y se envia en un mail
                new_password = User.objects.make_random_password(20)
                user_object.set_password(new_password)
                user_object.save()
                send_fP_mail(new_password, user, mail)
                error=False
                alreadySent=True
            else:
                #Si no coinciden se notifica al usuario en pantalla   
                error=True
        
        print(form.errors)
    
    return render(request,'forgot-password.html',{'request':request,'form':form,'error':error,'alreadySent':alreadySent})



@login_required
def newMovimiento(request,type):
    #Se establece una variable para verificar el envio y activa el formulario respectivo al tipo de movimiento
    alreadySent = False
    if type=='gastos':
        form = GastoForm()
    elif type=='ingresos':
        form = IngresoForm()
        
    #Verifica que la solicitud es carga de datos
    if request.method == 'POST':
        #Se crea una copia del diccionario para asi poder modificarlos
        mutable_post_data = request.POST.copy()

        user = User.objects.get(username=request.user.username)
        mutable_post_data['user'] = user
        if mutable_post_data['description'] == '':
            mutable_post_data['description'] = '-'
            
        #Se realizan ajustes dependiendo del tipo de movieminto  
        if type=='gastos':
            mutable_post_data['value']=float(mutable_post_data['value'])*(int(mutable_post_data['rate'])+100)/100
            cuotas = int(mutable_post_data.get('nPayments'))
            mutable_post_data['value']/=cuotas
        else:
            mutable_post_data['value']=float(mutable_post_data['value'])
            cuotas = int(mutable_post_data.get('repeat'))

        
        fecha_movimiento = datetime.strptime(mutable_post_data.get('date'),'%Y-%m-%d')
        fechaArr = fecha_movimiento.strftime("%Y-%m-%d").split('-')
        #Se itera sobre las cuotas para dividir el valor en los movimientos pertinentes 
        for i in range(cuotas):
            
            if i>0:
                print('cuota numero: ',i )  
                
                mutable_post_data['paymentId']=mother_id+'_'+str(i+1)

                if int(fechaArr[2])<=28:
                    if int(fechaArr[1])==12:
                        fechaArr[1]='1'
                        fechaArr[0]=str(int(fechaArr[0])+1)  
                    else:
                        fechaArr[1] = str(int(fechaArr[1])+1)
                        
                    fecha_movimiento=datetime.strptime('-'.join(fechaArr),'%Y-%m-%d')
                
                else:
                    fecha_movimiento = (fecha_movimiento + timedelta(days=30))
                
                mutable_post_data['date']=fecha_movimiento.strftime("%Y-%m-%d")
            
            else:
                print('Primera cuota')
                mutable_post_data['paymentId']='1_1'

            
            mutable_post_data['done']=False   
            

            if type=='gastos':
                form = GastoForm(mutable_post_data)
                value=-float(mutable_post_data['value'])
            elif type=='ingresos':
                form = IngresoForm(mutable_post_data)
                value=float(mutable_post_data['value'])
        
            if form.is_valid():
                if i==0:
                    instance = form.save()
                    mother_id=str(instance.id)
                    instance.paymentId = mother_id+'_1'
                    instance.save()
                else:
                    form.save()
                alreadySent = True
                    
            else:
                print(form.errors)
        
    #Se rendza el html dependiendo del tipo de movimiento y actuliza la informacion de los movimietos
    return render(request,'newMovimiento.html',{'request':request,'form':form,'alreadySent':alreadySent, 'type':type})



@login_required
def modifyMovimiento(request,type,id):
    # Modifica el movimiento cuando se lo solicita, el metodo post permite obtener los datos del formulario HTML
    
    gastosTypes=['Alquiler','Servicios publicos','Mantenimiento de hogar',
                 'Transporte publico','Combustible/Gastos fijos del auto',
                 'Compra de Comida','Comida afuera','Supermercado',
                 'Salud','Entretenimiento','Educación','Ropa y calzado',
                 'Cuidado personal','Mascotas','Regalos','Otros']
    ingresosTypes=['Saldo Inicial','Salario','Préstamo',
                   'Actividades secundarias','Pensiones','Otros']
    
    
    if type=='gastos':
        existing_data = get_object_or_404(Gasto, id=id)
        typesArr=gastosTypes
    else:
        existing_data =  get_object_or_404(Ingreso, id=id)
        typesArr=ingresosTypes
    
    
    if request.method == 'POST':
        #Se crea una copia del diccionario para asi poder modificarlos
        mutable_post_data = request.POST.copy()
        
        user = User.objects.get(username=request.user.username)
        mutable_post_data['user'] = user
        

        #Se modifica valores con respecto al interes
        if type=='gastos':
            mutable_post_data['value']=float(mutable_post_data['value'])*(float(mutable_post_data['rate'])+100)/100

        nuevoValor=float(mutable_post_data['value'])
        
        viejoValor=existing_data.value
        
        for key, value in mutable_post_data.items():
            setattr(existing_data, key, value)

        existing_data.save()
        
                    
        #Calculo del saldo
        modificacionSaldo=nuevoValor-viejoValor
        
        if type=='gasto':
            updateSaldo(user,modificacionSaldo).save()
        else:
            updateSaldo(user,-modificacionSaldo).save()
        # Se redirije a la pagina pirncipal    
        return redirect(reverse('movimientos', kwargs={'type': type}))
    if type=='gastos':
        existing_data.value = round(existing_data.value/((100+existing_data.rate)/100),2)
       
    return render(request,'modifyMovimiento.html',{'request':request,'existingData':existing_data, 'type':type,'typesArr':typesArr})



@login_required
def recordatorios(request):
    #Se establece una variable que verifique el envio y abre un formulario para el registro del usurio
    alreadySent = False
    form=recordatoriosForm()
    
    data= Recordatorio.objects.filter(user=request.user)
    
    if request.method == 'POST':
        
        mutable_post_data = request.POST.copy()
        user = User.objects.get(username=request.user.username)
        enviado=False

        mutable_post_data['user'] = user
        mutable_post_data['enviado'] = enviado

        
        if mutable_post_data['texto'] == '':
            mutable_post_data['texto'] = '-'
            
    
        form = recordatoriosForm(mutable_post_data)
        
        
        if form.is_valid():
            form.save()
        
            alreadySent = True
        
        print(form.errors)
    
    return render(request,'recordatorios.html',{'request':request,'form':form,'alreadySent':alreadySent,'data':data})



@login_required
def logout(request):
    #Sale de la cuenta del usuario con una funcion nativa de django y re direcciona a login
    logout_user(request)
    return redirect(login)



@login_required
def userPage(request):
    #Activa la pagina del perfil
    template = loader.get_template("userTemplate.html")
    return HttpResponse(template.render({'request':request}))



@login_required
def changePassword(request):
    #Se crea una instancia de formulario con el ususario solicitante como argumento
    form = ChangePassForm(request.user)
    
    errors={}
    
    if request.method == 'POST':
        form = ChangePassForm(request.user, request.POST)
        if form.is_valid():
            #Si el formulario es valido, se guarda el cambio y re direcciona a la pagina de usuario(perfil)
            form.save()
            update_session_auth_hash(request, request.user)
            return redirect('userPage')
        else:
            errors=dict(form.errors)
            errores={}
            errores['password']=[]
           
            for key, value in errors.items():
                try:
                    value = value[0]
                except:
                    value = value
                
                
                if 'was entered incorrectly' in value:
                    value = ['La contraseña vieja ingresada es incorrecta.']
                elif 'similar' in value:
                    value=['La contraseña es muy similar a alguno de sus otros datos personales.']
                elif 'common' in value:
                    value=['Esa contraseña es muy común!']
                
                errores['password']+=value
                
            errors = errores
            
      #Si el formulario es invalido, el usuario permanece en la pagina del cambio y es advertido 
    return render(request, "changePassword.html",{'request':request,'form':form,'errors':errors})



@login_required
def balance(request):
    #Se fltran gastos e ingresos perteneciente a un usuario y se calcula un balance de cuenta
    gastos = list(Gasto.objects.filter(user_id=request.user.id,done=True)) #Añado estas keys para que solo se muestren los que estan hechos
    ingresos = list(Ingreso.objects.filter(user_id=request.user.id,done=True))
    
    total = list(chain(gastos,ingresos))
    saldo = InfoUser.objects.get(user_id=request.user.id).saldo
    print(total)

    return render(request, "balance.html",{'request':request, 'data':total,'saldo':saldo})



def custom_page_not_found(request, exception='404', template_name='custom_404.html'):
    ## Cuando la pagina no se encuntra entre todas las direcciones disponibles, se envia a la pagina de 404
    # Ver re_path en urls.py
    response = page_not_found(request, exception, template_name=template_name)
    response.status_code = 404  
    return response 



@login_required
def deleteAccount(request):
    #Se encuenta el usuario, elimina la cuenta y redirecciona a login
    cuenta = get_object_or_404(User, username=request.user.username)
    cuenta.delete()
    return redirect('login')



@login_required
def eliminarMovimiento(request,type,id,all,mother):
    # La funcion elimina los movimientos cuando, discrimina si se desean eliminar todos o solo un movimiento





        # Divido las opciones si queiro eliminar todos los gastos relacionados o solo 1
    if all==0:    
        if type== 'gastos':
            # Obtenemos el id del movimiento asociandolo a su modelo y se vuelve a sumar el gasto a el balance
            movimiento= get_object_or_404(Gasto, id=id)
            
            updateSaldo(request.user,movimiento.value).save()
            
            # Borramos el movimiento
            movimiento.delete()
        elif type== 'ingresos':
            #En el caso de asocierlo a ingresos este es retado del balance de la cuenta
            movimiento=get_object_or_404(Ingreso,id=id)
            
            updateSaldo(request.user,-movimiento.value).save()
            
            movimiento.delete()  
        
            
    elif all==1:
        
        if type== 'gastos':
            # Obtengo primeramente informacion del gasto cero, de alli surgio la primera cuota
            
            movimiento_inicial=get_object_or_404(Gasto,id=id)

            nroCuotas= movimiento_inicial.nPayments
            id_inicial=int(mother)
            
            for i in range(int(nroCuotas)):

                try:
                    movimiento = get_object_or_404(Gasto, paymentId  = str(id_inicial)+'_'+str(i+1))
                
                    valor = int(movimiento.value)
                    if bool(movimiento.done):
                        updateSaldo(request.user,+valor).save()
                        
                    movimiento.delete()
                except:
                    
                    continue

        else:

            movimiento_inicial=get_object_or_404(Ingreso,id=id)
            nroRepeat= movimiento_inicial.repeat
            id_inicial=int(mother)
            
            for i in range(int(nroRepeat)):
                try:
                    movimiento = get_object_or_404(Ingreso, paymentId  = str(id_inicial)+'_'+str(i+1))
                
                    valor = int(movimiento.value)
                    if bool(movimiento.done):
                        updateSaldo(request.user,-valor).save()
                    

                    movimiento.delete()
                except:
                    continue


    # Redirigimos a la pagina         
    return redirect(reverse('movimientos', kwargs={'type': type}))


@login_required

    # Insertar descripcion de la funcion
def calendario(request):
    #Obtengo los eventos filtrados del ususario que abra el calendario
    eventos = Recordatorio.objects.filter(user=request.user)

    #Extrae la informacion pertinente a los eventos en forma de diccionario con claves 'titulo' y 'end'
    eventos_json = [{'titulo': evento.texto, 'end': evento.dueDate.isoformat()} for evento in eventos]
    contexto = {'eventos_json': eventos_json}
    #Se crea un diccionario llamado contexto que contiene la lista de diccionarios eventos_json 
    return render(request, 'calendario.html', contexto)


@login_required
def eliminarRecordatorio(request,id):
    #Obtiene el recordario con el id y lo elimina de la tabla redieccionando a recordatorios
    movimiento= get_object_or_404(Recordatorio, id=id)
    movimiento.delete()
    return redirect('recordatorios')


@login_required
def reporte(request):
  # Obtengo el nombre del usuario
  usuario = request.user.username
  Usuario = usuario.capitalize()

  # Obtengo la fecha actual
  fecha = datetime.now()
  ano = fecha.year
  mes_numero = fecha.month
  
  # Establece la configuracion regional a español
  locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

  mes_nombre = month_name[mes_numero]

  # Obtengo los gastos e ingresos segun el mes actual y el usuario
  gastos = list(Gasto.objects.filter(date__year=ano, date__month=mes_numero, user=request.user.id, done=True))
  ingresos = list(Ingreso.objects.filter(date__year=ano, date__month=mes_numero, user=request.user.id, done=True))

  reporte_data=[]

  for gasto in gastos:
      reporte_data.append({'Mov':'Gasto','type': gasto.type,'description': gasto.description, 'value': gasto.value, 'date': gasto.date})
  
  for ingreso in ingresos:
      reporte_data.append({'Mov':'Ingreso','type': ingreso.type,'description': ingreso.description, 'value': ingreso.value, 'date': ingreso.date})

  reporte = sorted(reporte_data, key=lambda x: x['date'])  

  # Creacion del Http con el pdf
  response = HttpResponse(content_type='application/pdf')
  response['Content-Disposition']='attachment; filename = Reporte_{}.pdf'.format(Usuario)

  # Crea el objeto pdf, con el objeto BytesIO como file
  buffer = BytesIO() 
  # El buffer ayudan con las diferencias en las velocidades de procesamiento o de entrada/salida entre dos componentes de un sistema
  # Almacena datos de manera temporal antes de ser procesados o transferidos a otro lugar. 

  # Encabezado
  # Establece el ancho de la linea
  c = canvas.Canvas(buffer, pagesize=A4)
  c.setLineWidth(.3)
  c.setFont('Times-Italic',16)
  c.drawString(25,800,'Reporte de {}'.format(Usuario))
  c.setFont('Times-Italic',12)
  c.drawString(25,780,'{} del {} '.format(mes_nombre.capitalize(),ano))
  c.line(10,770,585,770)
  
  # Tabla - Encabezado
  styles = getSampleStyleSheet()
  styleBH = styles['Normal']
  styleBH.alignment = TA_CENTER
  styleBH.fontSize = 10
  
  # Titulos del encabezado 
  Tipo = Paragraph('''<b>Tipo de Movimiento</b>''',styleBH)
  Fecha = Paragraph('''<b>Fecha</b>''',styleBH)
  Categoria = Paragraph('''<b>Categoria</b>''',styleBH)
  Descripcion = Paragraph('''<b>Descripción</b>''',styleBH)
  Monto = Paragraph('''<b>Monto</b>''',styleBH)

  data = []
  data.append([Tipo, Fecha, Categoria, Descripcion, Monto])

  # Tabla - cuerpo
  styles = getSampleStyleSheet()
  styleN = styles["BodyText"]
  styleN.alignment = TA_CENTER
  styleN.fontSize = 7

  high = 730

  for reporte in reporte:
    movimiento = [reporte['Mov'],reporte['date'].strftime('%Y-%m-%d'),reporte['type'], reporte['description'],round(reporte['value'],2)]
    data.append(movimiento)
    high = high - 18

  # Tamano de la Tabla
  width, height = A4
  table = Table(data, colWidths=[3.9*cm,2.5*cm,4.5*cm,6.5*cm,2.5*cm])
  table.setStyle(TableStyle([
      ('INNERGRID',(0,0),(-1,-1),0.25, colors.black),
      ('BOX',(0,0),(-1,-1),0.25, colors.black),]))
  
  table.wrapOn(c,width,height)
  table.drawOn(c,17,high)
  c.showPage()

  c.save()

  pdf=buffer.getvalue()
  buffer.close()

  response.write(pdf)
  
  return response


    



##-----------------------------------------END-----------------------------------------------##  return response