from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum, Count
from decimal import Decimal
from ..models import Person, WorkDay, Fee, SalaryRecord
import logging
from myapp.access_control import role_required, admin_required
from myapp.utils import log_activity

# Set up logger
logger = logging.getLogger(__name__)

def is_superuser(user):
    return user.is_superuser

# ฟังก์ชั่นตรวจสอบสิทธิ์ admin ที่รวมตำแหน่ง Accountant
def check_admin_rights(user):
    """
    ตรวจสอบสิทธิ์ admin รวม โดยรวมเงื่อนไขของ superuser, staff, กลุ่ม Admin และตำแหน่ง Accountant
    """
    # ตรวจสอบ superuser และกลุ่ม Admin / staff
    is_super = user.is_superuser
    is_admin = user.groups.filter(name='Admin').exists() or user.is_staff
    
    # ตรวจสอบตำแหน่งพนักงาน Accountant
    is_accountant = False
    try:
        person = Person.objects.get(user=user)
        if person.Role == 'Accountant':
            is_accountant = True
    except Person.DoesNotExist:
        pass
    
    return is_super or is_admin or is_accountant

@login_required
def dashboard_view(request):
    """
    แสดงหน้า Dashboard สำหรับผู้ใช้ที่ล็อกอิน
    """
    # บันทึกการเข้าใช้งานแดชบอร์ด
    log_activity(request, 'dashboard', 'เข้าหน้าแดชบอร์ด')
    
    try:
        # ดึงข้อมูลพนักงาน
        person = Person.objects.get(user=request.user)
        
        # บันทึกข้อมูลเพิ่มเติมเมื่อดึงข้อมูลพนักงานสำเร็จ
        log_activity(request, 'dashboard', 'ดูข้อมูลแดชบอร์ด', 
                     f'ดูข้อมูลของตนเอง: {person.first_name} {person.last_name}', person)
        
        # ดึงข้อมูลเพิ่มเติมสำหรับแสดงในหน้า Dashboard
        context = get_dashboard_context(person)
        context['is_admin_view'] = False
        
        return render(request, "dashboard.html", context)
    except Person.DoesNotExist:
        # ถ้าเป็น superuser แต่ไม่มีข้อมูลพนักงาน ให้ไปที่หน้ารายชื่อพนักงาน
        if request.user.is_superuser:
            log_activity(request, 'dashboard', 'ไม่พบข้อมูลพนักงาน', 'เปลี่ยนเส้นทางไปยังรายชื่อพนักงาน')
            return HttpResponseRedirect(reverse('employee_list'))
        # ถ้าไม่ใช่ superuser ให้กลับไปหน้าหลัก
        log_activity(request, 'dashboard', 'ไม่พบข้อมูลพนักงาน', 'เปลี่ยนเส้นทางไปยังหน้าหลัก')
        return HttpResponseRedirect(reverse('index'))
    except Exception as e:
        logger.error(f"Error in dashboard_view: {str(e)}")
        log_activity(request, 'dashboard', 'ข้อผิดพลาดในการแสดงแดชบอร์ด', str(e))
        raise

@login_required
def admin_view_dashboard(request, person_id):
    """
    แสดงหน้า Dashboard ของพนักงานที่เลือกสำหรับผู้ดูแลระบบ
    """
    # ตรวจสอบสิทธิ์ admin โดยรวมตำแหน่ง Accountant
    has_admin_rights = check_admin_rights(request.user)
    if not has_admin_rights:
        return HttpResponseRedirect(reverse('login') + f'?next={request.path}')
    
    person = get_object_or_404(Person, id=person_id)
    
    # บันทึกการเข้าดูแดชบอร์ดของพนักงาน
    log_activity(request, 'dashboard', 'ดูแดชบอร์ดของพนักงาน', 
                 f'ดูข้อมูลของ: {person.first_name} {person.last_name}', person)
    
    # ดึงข้อมูลเพิ่มเติมสำหรับแสดงในหน้า Dashboard
    context = get_dashboard_context(person)
    context['is_admin_view'] = True
    
    return render(request, "dashboard.html", context)

def get_dashboard_context(person):
    """
    ฟังก์ชั่นสำหรับดึงข้อมูลที่ใช้แสดงในหน้า Dashboard
    """
    # กำหนดวันที่ปัจจุบัน
    current_date = timezone.now().date()
    current_month = current_date.replace(day=1)
    
    # คำนวณวันทำงานโดยใช้โค้ดเดียวกับในไฟล์ view_salary.py
    try:
        # ดึง WorkDays ของคนนี้ในเดือนนั้น
        workdays = WorkDay.objects.filter(
            person=person,
            date__year=current_date.year,
            date__month=current_date.month,
            status=1
        )

        # จำนวนวันทำงานแบบรวมเต็ม/ครึ่งวัน
        days_worked = 0
        full_attendance = True
        for w in workdays:
            if w.full_day:
                days_worked += 1
            else:
                days_worked += 0.5
                full_attendance = False
        
        # แปลงเป็นแบบที่ต้องการแสดงผล
        if days_worked == int(days_worked):  # ถ้าเป็นจำนวนเต็ม
            workdays_this_month = str(int(days_worked))
        else:
            workdays_this_month = str(days_worked)
        
        logger.debug(f"Calculated days_worked: {days_worked}, display as: {workdays_this_month}")
    except Exception as e:
        logger.error(f"Error calculating workdays: {str(e)}")
        workdays_this_month = "0"
    
    # 2. การเช็คชื่อล่าสุด
    last_checkin = WorkDay.objects.filter(
        person=person
    ).order_by('-date').first()
    
    # 3. ยอดกู้คงเหลือ
    loan_remaining = 0
    loan_records = Fee.objects.filter(
        person=person,
        fee_status=1  # กู้เงิน
    ).order_by('-date')
    
    if loan_records.exists():
        latest_loan = loan_records.first()
        loan_remaining = latest_loan.remaining if hasattr(latest_loan, 'remaining') else 0
    
    # 4. จำนวนคิวในเดือนปัจจุบัน (สำหรับคนขับรถโม่)
    queue_total = 0
    if person.Role == 'Concrete Mixer Driver':
        queue_total = WorkDay.objects.filter(
            person=person,
            date__year=current_date.year,
            date__month=current_date.month
        ).aggregate(Sum('queue_count'))['queue_count__sum'] or 0
    
    # 5. เงินเดือนล่าสุด
    latest_salary = None
    salary_record = SalaryRecord.objects.filter(
        person=person
    ).order_by('-month').first()
    
    if salary_record:
        latest_salary = salary_record.total
    
    # 6. คำนวณเงินเดือนประมาณการเหมือนในหน้า salary
    try:
        # ใช้ Decimal เพื่อความแม่นยำในการคำนวณ
        daily_salary = Decimal(str(person.salary))
        days = Decimal(str(days_worked))
        estimated_salary = daily_salary * days
    except Exception as e:
        logger.error(f"Error calculating estimated_salary: {str(e)}")
        estimated_salary = 0
    
    # เตรียมข้อมูล debug สำหรับ admin
    workdays_debug = workdays  # แสดงข้อมูล workdays ทั้งหมด
    
    # สร้าง context สำหรับส่งไปยัง template
    context = {
        'person': person,
        'workdays_this_month': workdays_this_month,
        'last_checkin': last_checkin,
        'loan_remaining': loan_remaining,
        'queue_total': queue_total,
        'latest_salary': latest_salary,
        'estimated_salary': estimated_salary,
        'current_month': current_month,
        'workdays_debug': workdays_debug,  # สำหรับ debug panel
    }
    
    return context