from django.shortcuts import render


# def home(request):
#     data = {
#         'Total users': GeneralVariable.objects.get(name='Users counter').value,
#         'Total rooms': GeneralVariable.objects.get(name='Rooms counter').value,
#         'Total tasks': GeneralVariable.objects.get(name='Own tasks counter').value,
#         'Playing now': get_user_model().objects.count(),
#         'Active rooms': Room.objects.count()
#     }
#     return render(request, 'home.html', context={'data': data})
