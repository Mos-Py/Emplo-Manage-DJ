from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from myapp.models import ActivityLog
from myapp.utils import log_activity

def is_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def admin_log_view(request):
    """
    แสดงหน้าหลักของระบบดู Log
    """
    # บันทึกการเข้าใช้งานระบบดู Log
    log_activity(request, 'system', 'เข้าหน้าประวัติการใช้งาน')
    
    return render(request, "admin_log.html")

@login_required
@user_passes_test(is_superuser)
def dashboard_logs(request):
    """
    แสดงประวัติการใช้งานระบบแดชบอร์ด
    """
    # บันทึกการเข้าดูประวัติการใช้งานแดชบอร์ด
    log_activity(request, 'system', 'ดูประวัติการใช้งานแดชบอร์ด')
    
    logs = ActivityLog.objects.filter(system='dashboard').order_by('-created_at')[:100]
    
    return render(request, "log_templates/log_list.html", {
        'logs': logs,
        'system_name': 'แดชบอร์ด',
        'system_code': 'dashboard'
    })

@login_required
@user_passes_test(is_superuser)
def checkin_logs(request):
    """
    แสดงประวัติการใช้งานระบบเช็คชื่อ
    """
    # บันทึกการเข้าดูประวัติการใช้งานระบบเช็คชื่อ
    log_activity(request, 'system', 'ดูประวัติการใช้งานระบบเช็คชื่อ')
    
    logs = ActivityLog.objects.filter(system='checkin').order_by('-created_at')[:100]
    
    return render(request, "log_templates/log_list.html", {
        'logs': logs,
        'system_name': 'เช็คชื่อพนักงาน',
        'system_code': 'checkin'
    })

@login_required
@user_passes_test(is_superuser)
def withdraw_logs(request):
    """
    แสดงประวัติการใช้งานระบบเบิกเงิน
    """
    # บันทึกการเข้าดูประวัติการใช้งานระบบเบิกเงิน
    log_activity(request, 'system', 'ดูประวัติการใช้งานระบบเบิกเงิน')
    
    logs = ActivityLog.objects.filter(system='withdraw').order_by('-created_at')[:100]
    
    return render(request, "log_templates/log_list.html", {
        'logs': logs,
        'system_name': 'เบิกเงิน',
        'system_code': 'withdraw'
    })

@login_required
@user_passes_test(is_superuser)
def loan_logs(request):
    """
    แสดงประวัติการใช้งานระบบกู้เงิน
    """
    # บันทึกการเข้าดูประวัติการใช้งานระบบกู้เงิน
    log_activity(request, 'system', 'ดูประวัติการใช้งานระบบกู้เงิน')
    
    logs = ActivityLog.objects.filter(system='loan').order_by('-created_at')[:100]
    
    return render(request, "log_templates/log_list.html", {
        'logs': logs,
        'system_name': 'กู้เงิน',
        'system_code': 'loan'
    })

@login_required
@user_passes_test(is_superuser)
def calc_logs(request):
    """
    แสดงประวัติการใช้งานระบบคำนวณหัวคิว
    """
    # บันทึกการเข้าดูประวัติการใช้งานระบบคำนวณหัวคิว
    log_activity(request, 'system', 'ดูประวัติการใช้งานระบบคำนวณหัวคิว')
    
    logs = ActivityLog.objects.filter(system='calc').order_by('-created_at')[:100]
    
    return render(request, "log_templates/log_list.html", {
        'logs': logs,
        'system_name': 'คำนวณหัวคิว',
        'system_code': 'calc'
    })

@login_required
@user_passes_test(is_superuser)
def salary_logs(request):
    """
    แสดงประวัติการใช้งานระบบเงินเดือน
    """
    # บันทึกการเข้าดูประวัติการใช้งานระบบเงินเดือน
    log_activity(request, 'system', 'ดูประวัติการใช้งานระบบเงินเดือน')
    
    logs = ActivityLog.objects.filter(system='salary').order_by('-created_at')[:100]
    
    return render(request, "log_templates/log_list.html", {
        'logs': logs,
        'system_name': 'เงินเดือน',
        'system_code': 'salary'
    })

@login_required
@user_passes_test(is_superuser)
def employee_logs(request):
    """
    แสดงประวัติการใช้งานระบบจัดการพนักงาน
    """
    # บันทึกการเข้าดูประวัติการใช้งานระบบจัดการพนักงาน
    log_activity(request, 'system', 'ดูประวัติการใช้งานระบบจัดการพนักงาน')
    
    logs = ActivityLog.objects.filter(system='employee').order_by('-created_at')[:100]
    
    return render(request, "log_templates/log_list.html", {
        'logs': logs,
        'system_name': 'จัดการพนักงาน',
        'system_code': 'employee'
    })