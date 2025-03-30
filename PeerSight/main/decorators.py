from django.shortcuts import redirect
from functools import wraps

def professor_required(view_func):
    
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect('account_login')  # or your login route
        if user.role != 'professor':
            return redirect('permission_denied')  # or wherever you want
        return view_func(request, *args, **kwargs)
        
    return _wrapped_view