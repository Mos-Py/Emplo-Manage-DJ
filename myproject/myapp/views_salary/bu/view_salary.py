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

from myapp.models import Person, WorkDay, SalaryRecord, Fee
from myapp.views_salary.convert_excel_pdf import convert_excel_to_pdf
from myapp.views_salary.view_excel import export_person_salary_excel
from myapp.views_salary.view_pdf import export_person_salary_pdf
from myapp.views_salary.view_merge import export_all_salary_excel

logger = logging.getLogger(__name__)

def salary_list_view(request):
    """หน้าจัดการเงินเดือนพนักงาน"""
    
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
                "total": base_salary + commission + bonus - deduction - ss_amount - loan_payment,
                "extra_items": extra_items,
                "extra_expenses": extra_expenses
            }
        )
        
        # ถ้ามีการจ่ายเงินกู้
        if loan_payment > 0 and hasattr(Fee, 'fee_status'):
            all_loans = Fee.objects.filter(
                person=person, 
                fee_status=1
            ).order_by('date')

            active_loans = [loan for loan in all_loans if loan.remaining > 0]

            if active_loans:
                loan = active_loans[0]
                loan.remaining = max(float(loan.remaining) - loan_payment, 0)
                loan.save()
        
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

        # ✅ ชื่อแบบมีคำนำหน้า
        person.display_name = f"{person.title} {person.first_name} {person.last_name}"

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
        return JsonResponse({"error": f"เกิดข้อผิดพลาด: {str(e)}"}, status=500)

def get_withdraw_history(request, person_id):
    """API ดึงประวัติการเบิกเงิน"""
    
    month_str = request.GET.get("month")
    try:
        year, month = map(int, month_str.split("-"))
    except Exception as e:
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
        return JsonResponse({"error": f"เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}"}, status=500)

def get_saved_salary(request, person_id):
    """API ดึงข้อมูลเงินเดือนที่บันทึกแล้ว"""
    
    month_str = request.GET.get("month")
    try:
        year, month = map(int, month_str.split("-"))
        month_date = datetime(year, month, 1).date()
    except Exception as e:
        return JsonResponse({"error": f"รูปแบบเดือนไม่ถูกต้อง: {str(e)}"}, status=400)
    
    try:
        salary = SalaryRecord.objects.get(person_id=person_id, month=month_date)
        person = Person.objects.get(id=person_id)
        
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
        return JsonResponse({"error": "ยังไม่มีข้อมูล"}, status=404)
    except Person.DoesNotExist:
        return JsonResponse({"error": "ไม่พบข้อมูลพนักงาน"}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"เกิดข้อผิดพลาด: {str(e)}"}, status=500)

def get_loan_summary(request, person_id):
    """API ดึงข้อมูลสรุปเงินกู้"""
    
    month_str = request.GET.get("month")
    try:
        year, month = map(int, month_str.split("-"))
    except Exception:
        return JsonResponse({"error": "รูปแบบเดือนไม่ถูกต้อง"}, status=400)
    
    # เตรียมค่าเริ่มต้น
    response_data = {
        "loan_paid_this_month": 0,
        "loan_remaining": 0,
        "monthly_installment": 0,
        "loan_amount": 0
    }
    
    # ถ้าโมเดลมีคลาส Fee
    if hasattr(Fee, 'fee_status'):
        # ยอดจ่ายเงินกู้ในเดือนนี้
        loan_payments = Fee.objects.filter(
            person_id=person_id,
            fee_status=1,  # กู้เงิน
            date__year=year,
            date__month=month,
            amount__lt=0  # จำนวนเงินติดลบ = การจ่ายคืน
        )
        total_paid = abs(loan_payments.aggregate(total=Sum('amount'))['total'] or 0)
        
        # เงินกู้ทั้งหมด
        loans = Fee.objects.filter(
            person_id=person_id,
            fee_status=1  # กู้เงิน
        )
        
        # ถ้ามีฟิลด์ remaining
        if hasattr(Fee, 'remaining'):
            active_loans = [loan for loan in loans if float(loan.remaining) > 0]
            loan_remaining = sum(float(loan.remaining) for loan in active_loans)
            
            # ค่างวดต่อเดือน
            monthly_installment = 0
            if hasattr(Fee, 'installment_amount'):
                monthly_installment = sum(
                    float(loan.installment_amount or 0) 
                    for loan in active_loans 
                    if loan.installment_amount
                )
            
            # ยอดเงินกู้รวม
            loan_amount = sum(float(loan.amount) for loan in active_loans)
            
            response_data.update({
                "loan_paid_this_month": float(total_paid),
                "loan_remaining": float(loan_remaining),
                "monthly_installment": float(monthly_installment),
                "loan_amount": float(loan_amount)
            })
    
    return JsonResponse(response_data)

