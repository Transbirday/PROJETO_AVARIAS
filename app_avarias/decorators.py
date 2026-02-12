from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

def group_required(group_names):
    """
    Decorator to check if user belongs to one of the given group names.
    group_names can be a string (single group) or a list of strings.
    Superusers always pass.
    """
    if isinstance(group_names, str):
        group_names = [group_names]

    def in_groups(user):
        if user.is_authenticated:
            if user.is_superuser:
                return True
            return user.groups.filter(name__in=group_names).exists()
        return False

    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if in_groups(request.user):
                return view_func(request, *args, **kwargs)
            
            # If not authenticated, redirect to login
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            
            # If authenticated but no permission, show custom 403 page
            return render(request, 'app_avarias/permission_denied.html', status=403)
            
        return _wrapped_view
    return decorator

def superuser_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
            
        return render(request, 'app_avarias/permission_denied.html', status=403)
    return _wrapped_view
