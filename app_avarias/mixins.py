from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import render

class GroupRequiredMixin(UserPassesTestMixin):
    group_required = None # List or string

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
            
        groups = self.group_required
        if isinstance(groups, str):
            groups = [groups]
            
        return user.groups.filter(name__in=groups).exists()

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(self.request.get_full_path())
            
        return render(self.request, 'app_avarias/permission_denied.html', status=403)

class SuperUserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_superuser

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(self.request.get_full_path())
            
        return render(self.request, 'app_avarias/permission_denied.html', status=403)
