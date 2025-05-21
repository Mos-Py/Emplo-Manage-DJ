import os,json,logging
from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO

from django.conf import settings
from django.db.models import Sum
from django.http import JsonResponse, Http404 ,HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from openpyxl import load_workbook

from django.contrib.auth.decorators import login_required
from myapp.access_control import role_required, admin_required
from myapp.utils import log_activity
from myapp.models import Person, WorkDay, SalaryRecord, Fee
from myapp.views_salary.convert_excel_pdf import convert_excel_to_pdf
from myapp.views_salary.view_excel import export_person_salary_excel
from myapp.views_salary.view_pdf import export_person_salary_pdf
from myapp.views_salary.view_merge import export_all_salary_excel

logger = logging.getLogger(__name__)

@property
def thai_display_name(self):
    # แปลงคำนำหน้าภาษาอังกฤษเป็นภาษาไทย
    title_mapping = {
        'Mr': 'นาย',
        'Mrs': 'นาง',
        'Ms': 'นางสาว'
    }
    
    # ใช้คำนำหน้าภาษาไทยถ้ามีในแมปปิง มิฉะนั้นใช้ค่าเดิม
    thai_title = title_mapping.get(self.title, self.title)
    
    # สร้างชื่อแสดงผลใหม่ด้วยคำนำหน้าภาษาไทย
    return f"{thai_title} {self.first_name} {self.last_name}"

@login_required
@admin_required
def salary_list_view(request):
    """หน้าจัดการเงินเดือนพนักงาน"""
    
    # บันทึกการเข้าใช้งานระบบเงินเดือน
    log_activity(request, 'salary', 'เข้าหน้าจัดการเงินเดือน')
    
    if request.method == "POST":
        person_id = request.POST.get("person_id")
        month_str = request.POST.get("month") + "-01"
        month_date = datetime.strptime(month_str, "%Y-%m-%d").date()
        extra_items_raw = request.POST.get("extra_items_json", "[]")
        extra_items_raw = request.POST.get("extra_items_json", "[]")
        if not extra_items_raw.strip():
            extra_items_raw = "[]"
        extra_items = json.loads(extra_items_raw)
        extra_expenses = json.loads(request.POST.get("extra_expenses_json") or "[]")
        
        try:
            # ดึงข้อมูลพนักงาน
            person = Person.objects.get(id=person_id)
            
            # รับค่าจากฟอร์ม
            base_salary = float(request.POST.get("base_salary", 0))
            commission = float(request.POST.get("commission", 0))
            bonus = float(request.POST.get("bonus", 0))
            deduction = float(request.POST.get("deduction", 0))
            
            # ค่าปกส. และเงินกู้ถ้ามี
            ss_amount = float(request.POST.get("ss_amount", 0))
            loan_payment = float(request.POST.get("loan_payment", 0))
            
            # คำนวณยอดรวม
            total_salary = base_salary + commission + bonus - deduction - ss_amount - loan_payment
            
            # ตรวจสอบว่าเป็นการสร้างใหม่หรืออัปเดต
            existing_record = SalaryRecord.objects.filter(person=person, month=month_date).exists()
            action_type = 'อัปเดต' if existing_record else 'สร้าง'
            
            # อัปเดตหรือสร้างข้อมูลเงินเดือน
            salary_record, created = SalaryRecord.objects.update_or_create(
                person=person,
                month=month_date,
                defaults={
                    "base_salary": base_salary,
                    "commission": commission,
                    "bonus": bonus,
                    "withdraw": deduction,  # เปลี่ยนชื่อฟิลด์จาก deduction เป็น withdraw
                    "ss_amount": ss_amount,
                    "loan_payment": loan_payment,
                    "total": total_salary,
                    "extra_items": extra_items,
                    "extra_expenses": extra_expenses
                }
            )
            
            # บันทึก log การบันทึกเงินเดือน
            log_activity(request, 'salary', f'{action_type}ข้อมูลเงินเดือน', 
                        f'{action_type}เงินเดือนของ {person.first_name} {person.last_name} เดือน {month_date.strftime("%m/%Y")} ' +
                        f'ยอดรวม: {total_salary} บาท', salary_record)
            
            # ถ้ามีการจ่ายเงินกู้
            if loan_payment > 0 and hasattr(Fee, 'fee_status'):
                active_loans = Fee.objects.filter(
                    person=person, 
                    fee_status=1,  # กู้เงิน
                    remaining__gt=0
                ).order_by('date')
                
                if active_loans.exists():
                    loan = active_loans.first()
                    old_remaining = loan.remaining
                    loan.remaining = max(float(loan.remaining) - loan_payment, 0)
                    loan.save()
                    
                    # บันทึก log การจ่ายเงินกู้
                    log_activity(request, 'loan', 'จ่ายเงินกู้', 
                                f'จ่ายเงินกู้ {loan_payment} บาท ของ {person.first_name} {person.last_name} ' +
                                f'คงเหลือ {loan.remaining} บาท', loan)
        
        except Person.DoesNotExist:
            log_activity(request, 'salary', 'ข้อผิดพลาด', f'ไม่พบพนักงานรหัส {person_id}')
        except Exception as e:
            log_activity(request, 'salary', 'ข้อผิดพลาด', f'เกิดข้อผิดพลาดในการบันทึกเงินเดือน: {str(e)}')
        
        return redirect("salary_list")
    
    # GET request
    selected_month = request.GET.get("month", date.today().strftime('%Y-%m'))
    year, month = map(int, selected_month.split("-"))
    month_date = datetime(year, month, 1).date()
    
    # ดึงข้อมูลพนักงานทั้งหมด
    persons = Person.objects.all().order_by('first_name')
    
    # ดึงข้อมูลเงินเดือนที่บันทึกแล้ว
    salary_records = SalaryRecord.objects.filter(month=month_date)
    
    # สร้าง dictionary ของข้อมูลเงินเดือน
    # ในฟังก์ชัน salary_list_view
    salary_dict = {record.person.id: record for record in salary_records}
    for person in persons:
        person.salary_saved = person.id in salary_dict
        if person.salary_saved:
            person.salary_total = salary_dict[person.id].total

        title_mapping = {
            'Mr': 'นาย',
            'Mrs': 'นาง',
            'Ms': 'นางสาว'
        }

        thai_title = title_mapping.get(person.title, person.title)

        # ✅ ชื่อแบบมีคำนำหน้า
        person.display_name = f"{thai_title} {person.first_name} {person.last_name}"

        # ✅ ตำแหน่งแบบมีเลข (ถ้าเป็นคนขับรถโม่)
        if person.Role == "Concrete Mixer Driver" and person.concrete_mixer_numbers:
            person.display_role = f"{person.get_Role_display()} {person.concrete_mixer_numbers}"
        else:
            person.display_role = person.get_Role_display()
    
    context = {
        "selected_month": selected_month,
        "persons": persons,
        "salary_records": salary_dict
        
    }
    
    return render(request, "salary_list.html", context)

def get_all_persons(request):
    """API สำหรับดึงข้อมูลพนักงานทั้งหมด"""
    # บันทึกการดึงข้อมูลพนักงานทั้งหมด
    log_activity(request, 'salary', 'ดึงข้อมูลพนักงานทั้งหมด')
    
    persons = Person.objects.all().order_by('first_name')
    
    persons_data = [
        {
            "id": person.id,
            "name": f"{person.title} {person.first_name} {person.last_name}",
            "role": person.get_Role_display() if hasattr(person, 'get_Role_display') else 'พนักงาน'
        }
        for person in persons
    ]
    
    return JsonResponse({"status": "success", "data": persons_data})

def get_salary_info(request, person_id):
    try:
        person = get_object_or_404(Person, id=person_id)
        month_str = request.GET.get("month")
        if not month_str:
            raise ValueError("ไม่พบพารามิเตอร์เดือน")

        # บันทึกการดึงข้อมูลเงินเดือน
        log_activity(request, 'salary', 'ดึงข้อมูลเงินเดือน', 
                    f'ดึงข้อมูลเงินเดือนของ {person.first_name} {person.last_name} เดือน {month_str}', person)

        month_date = datetime.strptime(month_str, "%Y-%m")

        # WorkDays ของคนนี้ในเดือนนั้น
        workdays = WorkDay.objects.filter(
            person=person,
            date__year=month_date.year,
            date__month=month_date.month,
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

        # ตรวจว่ามาครบวันหรือไม่ (เทียบกับวันทำงานของระบบ)
        total_workdays_in_month = WorkDay.objects.filter(
            date__year=month_date.year,
            date__month=month_date.month,
            status=1
        ).values('date').distinct().count()

        full_attendance = days_worked >= total_workdays_in_month

        # รวมค่าหัวคิว
        commission = workdays.aggregate(total=Sum('pay'))['total'] or 0

        # ยอดเบิกในเดือนนี้
        total_withdraw = Fee.objects.filter(
            person=person,
            fee_status=0,
            date__year=month_date.year,
            date__month=month_date.month
        ).aggregate(total=Sum('amount'))['total'] or 0

        # โบนัสถ้ามาทุกวัน = เงินเดือน
        attendance_bonus = Decimal(person.salary) if full_attendance else Decimal("0.00")

        # ตรวจสอบข้อมูล SalaryRecord หากมี loan_payment เก็บไว้
        try:
            salary = SalaryRecord.objects.get(person=person, month=month_date)
            loan_payment = salary.loan_payment or 0
            extra_income = salary.extra_items if hasattr(salary, "extra_items") else []
        except SalaryRecord.DoesNotExist:
            salary = None
            loan_payment = 0
            extra_income = []

        total = (
            Decimal(person.salary) * Decimal(days_worked)
            + Decimal(commission)
            + attendance_bonus
            - Decimal(total_withdraw)
            - Decimal(loan_payment)
        )

        data = {
            "person_id": person.id,
            "name": f"{person.title} {person.first_name} {person.last_name}",
            "role": person.get_Role_display(),
            "base_salary": float(person.salary),
            "bonus": float(attendance_bonus),
            "commission": float(commission),
            "withdraw": float(total_withdraw),
            "ss_amount": 0,
            "loan_payment": float(loan_payment),  # ✅ เพิ่มจุดนี้
            "total": float(total),
            "days_worked": days_worked,
            "full_attendance": full_attendance,
            "attendance_bonus": float(attendance_bonus),
            "extra_income": salary.extra_items if hasattr(salary, "extra_items") else [],
            "extra_expense": salary.extra_expenses if hasattr(salary, "extra_expenses") else []
        }

        return JsonResponse(data)

    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการโหลด salary_info: {e}")
        log_activity(request, 'salary', 'ข้อผิดพลาด', f'เกิดข้อผิดพลาดในการโหลดข้อมูลเงินเดือน: {str(e)}')
        return JsonResponse({"error": f"เกิดข้อผิดพลาด: {str(e)}"}, status=500)

def get_withdraw_history(request, person_id):
    """API ดึงประวัติการเบิกเงิน"""
    
    month_str = request.GET.get("month")
    try:
        person = get_object_or_404(Person, id=person_id)
        year, month = map(int, month_str.split("-"))
        
        # บันทึกการดึงประวัติการเบิกเงิน
        log_activity(request, 'withdraw', 'ดึงประวัติการเบิกเงิน', 
                     f'ดึงประวัติการเบิกเงินของ {person.first_name} {person.last_name} เดือน {month_str}', person)
    except Person.DoesNotExist:
        log_activity(request, 'withdraw', 'ข้อผิดพลาด', f'ไม่พบพนักงานรหัส {person_id}')
        return JsonResponse({"error": "ไม่พบพนักงาน"}, status=404)
    except Exception as e:
        log_activity(request, 'withdraw', 'ข้อผิดพลาด', f'รูปแบบเดือนไม่ถูกต้อง: {str(e)}')
        return JsonResponse({"error": f"รูปแบบเดือนไม่ถูกต้อง: {str(e)}"}, status=400)
    
    try:
        history = []
        
        # ดึงประวัติการเบิกเงิน
        if hasattr(Fee, 'fee_status'):
            withdraws = Fee.objects.filter(
                person_id=person_id,
                fee_status=0,  # เบิกเงิน
                date__year=year,
                date__month=month
            ).values("date", "amount", "description").order_by("date")
            
            history = [
                {
                    "date": withdraw["date"].strftime("%d/%m/%Y"),
                    "amount": float(withdraw["amount"]),
                    "note": withdraw["description"] or "-"
                }
                for withdraw in withdraws
            ]
        
        return JsonResponse({
            "history": history,
            "total_count": len(history),
            "total_amount": float(sum(item["amount"] for item in history)) if history else 0
        })
    except Exception as e:
        log_activity(request, 'withdraw', 'ข้อผิดพลาด', f'เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}')
        return JsonResponse({"error": f"เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}"}, status=500)

def get_saved_salary(request, person_id):
    """API ดึงข้อมูลเงินเดือนที่บันทึกแล้ว"""
    
    month_str = request.GET.get("month")
    try:
        person = get_object_or_404(Person, id=person_id)
        year, month = map(int, month_str.split("-"))
        month_date = datetime(year, month, 1).date()
        
        # บันทึกการดึงข้อมูลเงินเดือนที่บันทึกแล้ว
        log_activity(request, 'salary', 'ดึงข้อมูลเงินเดือนที่บันทึกแล้ว', 
                     f'ดึงข้อมูลเงินเดือนที่บันทึกแล้วของ {person.first_name} {person.last_name} เดือน {month_str}', person)
    except Person.DoesNotExist:
        log_activity(request, 'salary', 'ข้อผิดพลาด', f'ไม่พบพนักงานรหัส {person_id}')
        return JsonResponse({"error": "ไม่พบข้อมูลพนักงาน"}, status=404)
    except Exception as e:
        log_activity(request, 'salary', 'ข้อผิดพลาด', f'รูปแบบเดือนไม่ถูกต้อง: {str(e)}')
        return JsonResponse({"error": f"รูปแบบเดือนไม่ถูกต้อง: {str(e)}"}, status=400)
    
    try:
        salary = SalaryRecord.objects.get(person_id=person_id, month=month_date)
        
        # จำนวนวันทำงาน
        work_days = WorkDay.objects.filter(
            person_id=person_id,
            date__year=year,
            date__month=month
        ).count()
        
        # ข้อมูลเบิกเงิน
        withdraw_amount = 0
        if hasattr(Fee, 'fee_status'):
            withdraws = Fee.objects.filter(
                person_id=person_id,
                fee_status=0,  # เบิกเงิน
                date__year=year,
                date__month=month
            )
            withdraw_amount = withdraws.aggregate(total=Sum("amount"))['total'] or 0
        
        # ข้อมูลจ่ายเงินกู้
        loan_payment = 0
        if hasattr(Fee, 'fee_status'):
            loan_payments = Fee.objects.filter(
                person_id=person_id,
                fee_status=1,  # กู้เงิน
                date__year=year,
                date__month=month,
                amount__lt=0  # จำนวนเงินติดลบ = การจ่ายคืน
            )
            loan_payment = abs(loan_payments.aggregate(total=Sum('amount'))['total'] or 0)
        
        # ตรวจสอบฟิลด์ยอดรวม
        total_field = 'total' if hasattr(salary, 'total') else 'total_salary'
        
        response_data = {
            "name": f"{person.title} {person.first_name} {person.last_name}",
            "salary_per_day": float(person.salary),
            "days": work_days,
            "commission": float(salary.commission),
            "bonus": float(salary.bonus),
            "withdraw": float(withdraw_amount),
            "ss_amount": float(salary.ss_amount) if hasattr(salary, 'ss_amount') else 0,
            "loan_payment": float(salary.loan_payment) if hasattr(salary, 'loan_payment') else loan_payment,
            "total_salary": float(getattr(salary, total_field)),
            "base_salary": float(salary.base_salary),
            "full_attendance": True if salary.bonus >= person.salary else False,
            "extra_income": salary.extra_items if hasattr(salary, "extra_items") else [],
            "extra_expense": salary.extra_expenses if hasattr(salary, "extra_expenses") else [],       
        }
        
        return JsonResponse(response_data)
    except SalaryRecord.DoesNotExist:
        log_activity(request, 'salary', 'ข้อมูลไม่พบ', f'ยังไม่มีข้อมูลเงินเดือนที่บันทึกของ {person.first_name} {person.last_name} เดือน {month_str}')
        return JsonResponse({"error": "ยังไม่มีข้อมูล"}, status=404)
    except Exception as e:
        log_activity(request, 'salary', 'ข้อผิดพลาด', f'เกิดข้อผิดพลาด: {str(e)}')
        return JsonResponse({"error": f"เกิดข้อผิดพลาด: {str(e)}"}, status=500)

def get_loan_summary(request, person_id):
    """API ดึงข้อมูลสรุปเงินกู้"""
    
    month_str = request.GET.get("month")
    try:
        person = get_object_or_404(Person, id=person_id)
        year, month = map(int, month_str.split("-"))
        
        # บันทึกการดึงข้อมูลสรุปเงินกู้
        log_activity(request, 'loan', 'ดึงข้อมูลสรุปเงินกู้', 
                     f'ดึงข้อมูลสรุปเงินกู้ของ {person.first_name} {person.last_name} เดือน {month_str}', person)
    except Person.DoesNotExist:
        log_activity(request, 'loan', 'ข้อผิดพลาด', f'ไม่พบพนักงานรหัส {person_id}')
        return JsonResponse({"error": "ไม่พบพนักงาน"}, status=404)
    except Exception as e:
        log_activity(request, 'loan', 'ข้อผิดพลาด', f'รูปแบบเดือนไม่ถูกต้อง: {str(e)}')
        return JsonResponse({"error": "รูปแบบเดือนไม่ถูกต้อง"}, status=400)
    
    # ถ้าโมเดลมีคลาส Fee
    if hasattr(Fee, 'fee_status'):
        try:
            # ยอดจ่ายเงินกู้ในเดือนนี้
            loan_payments = Fee.objects.filter(
                person_id=person_id,
                fee_status=1,  # กู้เงิน
                date__year=year,
                date__month=month,
                amount__lt=0  # จำนวนเงินติดลบ = การจ่ายคืน
            )
            total_paid = abs(loan_payments.aggregate(total=Sum('amount'))['total'] or 0)
            
            # รายการเงินกู้ทั้งหมด (ยอดบวก = การกู้)
            loans = Fee.objects.filter(
                person_id=person_id,
                fee_status=1,  # กู้เงิน
                amount__gt=0   # เฉพาะยอดกู้ (ไม่รวมการชำระคืน)
            )
            
            # รายการจ่ายคืนทั้งหมด (ยอดลบ = การชำระคืน)
            repayments = Fee.objects.filter(
                person_id=person_id,
                fee_status=1,  # กู้เงิน
                amount__lt=0   # เฉพาะยอดชำระคืน
            )
            
            # ยอดเงินกู้ทั้งหมด
            total_loan = sum(float(loan.amount) for loan in loans)
            
            # ยอดการชำระคืนทั้งหมด
            total_repaid = abs(sum(float(repay.amount) for repay in repayments))
            
            # ยอดคงเหลือ
            loan_remaining = max(0, total_loan - total_repaid)
            
            # เก็บค่างวดต่อเดือน (ถ้ามี)
            monthly_installment = 0
            
            # ส่งข้อมูลกลับ
            response_data = {
                "loan_paid_this_month": float(total_paid),
                "loan_remaining": float(loan_remaining),
                "monthly_installment": float(monthly_installment),
                "loan_amount": float(total_loan)
            }
            
            return JsonResponse(response_data)
        except Exception as e:
            log_activity(request, 'loan', 'ข้อผิดพลาด', f'เกิดข้อผิดพลาดในการดึงข้อมูลเงินกู้: {str(e)}')
            return JsonResponse({"error": f"เกิดข้อผิดพลาด: {str(e)}"}, status=500)
    
    # กรณีไม่มีโมเดล Fee หรือไม่มี fee_status
    return JsonResponse({
        "loan_paid_this_month": 0,
        "loan_remaining": 0,
        "monthly_installment": 0,
        "loan_amount": 0
    })