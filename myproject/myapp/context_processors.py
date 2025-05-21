def user_role(request):
    context = {
        'is_accountant': False,
        'has_admin_rights': False,
        'is_superuser': False,  # เพิ่มตัวแปรนี้
    }
    
    if request.user.is_authenticated:
        # ตรวจสอบสิทธิ์ superuser
        if request.user.is_superuser:
            context['has_admin_rights'] = True
            context['is_superuser'] = True  # กำหนดค่าตัวแปรใหม่
        
        # เพิ่มการตรวจสอบกลุ่ม Admin และ is_staff
        if request.user.groups.filter(name='Admin').exists() or request.user.is_staff:
            context['has_admin_rights'] = True
        
        # ตรวจสอบบทบาทจากโมเดล Person
        try:
            from myapp.models import Person
            person = Person.objects.get(user=request.user)
            if person.Role == 'Accountant':
                context['is_accountant'] = True
                context['has_admin_rights'] = True
        except:
            pass
    
    return context