from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import *

@login_required
def avaria_detail(request, pk):
    avaria = get_object_or_404(Avaria, pk=pk)
    fotos_ordenadas = avaria.fotos.select_related('criado_por').order_by('criado_por', '-data_upload')
    
    obs_form = AvariaObservacaoForm()
    
    # Forms for actions
    decisao_form = AvariaDecisaoForm()
    devolucao_form = Avaria DevolucaoForm(instance=avaria)
    photo_form = AvariaFotoForm()
    finalizacao_form = AvariaFinalizacaoDevolucaoForm()
    
    if request.method == 'POST':
        # ... rest of POST handling (keeping existing code)
        pass
    
    context = {
        'avaria': avaria,
        'obs_form': obs_form,
        'decisao_form': decisao_form,
        'devolucao_form': devolucao_form,
        'photo_form': photo_form,
        'fotos_ordenadas': fotos_ordenadas,
        'finalizacao_form': finalizacao_form,
    }
    response = render(request, 'app_avarias/avaria_detail.html', context)
    # Force no cache
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response
