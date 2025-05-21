# myapp/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden


def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # superuser มีสิทธิ์เข้าถึงทุกส่วน
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            try:
                from myapp.models import Person
                person = Person.objects.get(user=request.user)
                if person.Role in allowed_roles:
                    return view_func(request, *args, **kwargs)
            except:
                pass
            
            # ไม่มีสิทธิ์เข้าถึง
            return HttpResponseForbidden("ไม่มีสิทธิ์เข้าใช้งานส่วนนี้")
            
        return _wrapped_view
    return decorator

def admin_required(view_func):
    """decorator สำหรับจำกัดเฉพาะ admin และ superuser"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # อนุญาตเฉพาะ superuser
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        # ตรวจสอบตำแหน่ง Accountant (ถือว่าเป็น admin)
        try:
            from myapp.models import Person
            person = Person.objects.get(user=request.user)
            if person.Role == 'Accountant':
                return view_func(request, *args, **kwargs)
        except:
            pass
        
        # ไม่มีสิทธิ์เข้าถึง
        return HttpResponseForbidden("ไม่มีสิทธิ์เข้าใช้งานส่วนนี้")
        
    return _wrapped_view