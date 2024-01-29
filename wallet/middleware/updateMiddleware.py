from django.contrib.auth.decorators import login_required
from wallet.views import updateSaldo
from wallet.models import Gasto , Ingreso , InfoUser
from datetime import datetime

#Un middleware que actualiza todos los datos de la tabla y los saldos dependiendo de la fecha
class updateSaldoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
                
        # Chequea si el usuario está logueado
        if hasattr(request, 'user') and request.user.is_authenticated:
            
            # Crear listas con los movimientos del usuario en cuestion
            gastos = list(Gasto.objects.filter(user_id=request.user.id)) 
            ingresos = list(Ingreso.objects.filter(user_id=request.user.id))
            
            def updateTables(table,gasto=True):
                for i in table:
                    # Iterar la tabla y chequear si la fecha de abono ya paso o es hoy y si ya se hizo el pago (i.done)
                    if i.date<=datetime.now().date() and not i.done:
                        i.done = True
                        if gasto: # Se actualizan los saldos para cada movimiento
                            updateSaldo(request.user,-i.value).save()
                        else:
                            updateSaldo(request.user,i.value).save()
                        i.save() 
                    elif i.date>datetime.now().date() and i.done: # Aqui se contempla el caso de que el pago se haya hecho y no corresponda
                        i.done = False
                        if gasto: # Se modifican los saldos opuestamente
                            updateSaldo(request.user,i.value).save()
                        else:
                            updateSaldo(request.user,-i.value).save()
                        i.save()
            
            updateTables(gastos)
            updateTables(ingresos,False)
                 

        response = self.get_response(request)
        return response