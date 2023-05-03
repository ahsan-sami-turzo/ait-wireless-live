from django.shortcuts import redirect
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import reverse


def unauthenticated_user(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('nf.index')
        else:
            return view_func(request, *args, **kwargs)

    return wrapper_func
