from functools import wraps
from django.shortcuts import redirect

def custom_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'user_id' in request.session:
            return view_func(request, *args, **kwargs)
        else:
            print(f"User not authenticated. Redirecting to login.")
            return redirect('login')
    return _wrapped_view

def fm_custom_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'fm_user_id' in request.session:
            return view_func(request, *args, **kwargs)
        else:
            print(f"User not authenticated. Redirecting to fitness manager login.")
            return redirect('fm_login')
    return _wrapped_view

def admin_custom_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'admin_username' in request.session:
            return view_func(request, *args, **kwargs)
        else:
            print(f"User not authenticated. Redirecting to Admin login.")
            return redirect('admin_login')
    return _wrapped_view

def delivery_manager_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('delivery_manager'):
            return redirect('delivery_manager_login')
        return view_func(request, *args, **kwargs)
    return wrapper

