from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Person, WorkDay
from datetime import date
from .views_extend.view_check import check_view
from .views_extend.view_dashboard import dashboard_view, admin_view_dashboard
from django.http import HttpResponseForbidden
from functools import wraps
from .access_control import role_required, admin_required
from myapp.utils import log_activity

def is_superuser(user):
    return user.is_superuser


def index(request):
    # บันทึกการเข้าหน้าหลัก
    if request.user.is_authenticated:
        log_activity(request, 'dashboard', 'เข้าหน้าหลัก')
    
    person = None
    return render(request, "index.html", {"person": person})


@login_required
def dashboard(request):
    """
    ฟังก์ชั่น Proxy สำหรับเรียกใช้ฟังก์ชั่น dashboard_view จาก views_extend/view_dashboard.py
    """
    # บันทึก log จะถูกทำในฟังก์ชัน dashboard_view อยู่แล้ว
    return dashboard_view(request)


@login_required
@user_passes_test(is_superuser)
def employee_list(request):
    # บันทึกการเข้าหน้ารายการพนักงาน
    log_activity(request, 'employee', 'เข้าหน้ารายการพนักงาน')
    
    persons = Person.objects.all().order_by('first_name')
    return render(request, "employee_list.html", {"persons": persons})


@login_required
@user_passes_test(is_superuser)
def admin_view_dashboard(request, person_id):
    person = get_object_or_404(Person, id=person_id)
    
    # บันทึกการเข้าดูแดชบอร์ดของพนักงาน
    log_activity(request, 'dashboard', 'ดูแดชบอร์ดของพนักงาน', 
                f'ดูข้อมูลของ: {person.first_name} {person.last_name}', person)
    
    return render(request, "dashboard.html", {"person": person, "is_admin_view": True})


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)

            log_activity(request, 'system', 'เข้าสู่ระบบ', f'ผู้ใช้: {username}')

            return redirect("index")  # ✅ ทุก user ไปหน้า index เสมอ
        else:
            log_activity(request, 'system', 'เข้าสู่ระบบไม่สำเร็จ', f'ผู้ใช้: {username}', None)
            return render(request, "login.html", {"error": "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"})
    return render(request, "login.html")


def logout_view(request):
    # บันทึกการออกจากระบบก่อนที่จะ logout จริง
    if request.user.is_authenticated:
        username = request.user.username
        log_activity(request, 'system', 'ออกจากระบบ', f'ผู้ใช้: {username}')
    
    logout(request)
    return redirect("login")


def checkin_view(request):
    # บันทึก log จะถูกทำในฟังก์ชัน check_view อยู่แล้ว
    return check_view(request)

