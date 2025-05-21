from myapp.models import Person, Fee
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from datetime import date, datetime
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from myapp.access_control import role_required, admin_required
from myapp.utils import log_activity
from django.contrib.auth.decorators import login_required

@login_required
@admin_required
def withdraw_form(request):
    # บันทึกการเข้าใช้งานระบบเบิกเงิน
    log_activity(request, 'withdraw', 'เข้าหน้าเบิกเงิน')
    
    persons = Person.objects.all()
    today = date.today()
    return render(request, "withdraw.html", {"persons": persons, "today": today})


@csrf_exempt
def save_fee(request):
    if request.method == "POST":
        person_id = request.POST.get("person")
        amount = request.POST.get("amount")
        description = request.POST.get("description")
        fee_status = int(request.POST.get("fee_status", 0))  # 0 = เบิกเงิน, 1 = กู้เงิน
        
        # รับค่างวดที่ต้องจ่ายต่อเดือน (เฉพาะกรณีกู้เงิน) - ถ้ามี
        installment_amount = request.POST.get("installment_amount") if fee_status == 1 else None

        try:
            person = Person.objects.get(id=person_id)
            
            fee_date_str = request.POST.get("fee_date") or date.today().isoformat()
            fee_date = datetime.strptime(fee_date_str, "%Y-%m-%d").date()

            # บันทึกรายการเบิกเงินหรือกู้เงิน
            fee = Fee.objects.create(
                person=person,
                fee_status=fee_status,
                amount=amount,
                description=description,
                date=fee_date,
                # เพิ่ม installment_amount ถ้ามีค่า
                installment_amount=installment_amount 
            )
            
            # บันทึก log activity
            action = 'เบิกเงิน' if fee_status == 0 else 'กู้เงิน'
            detail = f'{action} {amount} บาท ให้กับ {person.first_name} {person.last_name} วันที่ {fee_date}'
            log_activity(request, 'withdraw' if fee_status == 0 else 'loan', action, detail, fee)

            # ถ้าเป็นการเบิกเงิน กลับไปหน้าเบิกเงิน, ถ้าเป็นการกู้เงิน กลับไปหน้ากู้เงิน
            if fee_status == 0:
                return redirect("withdraw_form")
            else:
                return redirect("loan_form")
                
        except Person.DoesNotExist:
            log_activity(request, 'withdraw' if fee_status == 0 else 'loan', 'ข้อผิดพลาด', f'ไม่พบพนักงานรหัส {person_id}')
            # ควรเพิ่มการแจ้งเตือนข้อผิดพลาดที่นี่
            if fee_status == 0:
                return redirect("withdraw_form")
            else:
                return redirect("loan_form")
        except Exception as e:
            log_activity(request, 'withdraw' if fee_status == 0 else 'loan', 'ข้อผิดพลาด', str(e))
            # ควรเพิ่มการแจ้งเตือนข้อผิดพลาดที่นี่
            if fee_status == 0:
                return redirect("withdraw_form")
            else:
                return redirect("loan_form")


def get_fee_history(request, person_id):
    month_str = request.GET.get('month')  # รูปแบบ '2025-04'
    fee_status = int(request.GET.get('fee_status', 0))  # 0 = เบิกเงิน, 1 = กู้เงิน

    # บันทึกการดูประวัติการเบิกเงิน/กู้เงิน
    system_name = 'withdraw' if fee_status == 0 else 'loan'
    action_name = 'ดูประวัติการเบิกเงิน' if fee_status == 0 else 'ดูประวัติการกู้เงิน'
    
    try:
        person = Person.objects.get(id=person_id)
        log_activity(request, system_name, action_name, 
                     f'ดูประวัติของ {person.first_name} {person.last_name} เดือน {month_str}', person)
    except Person.DoesNotExist:
        log_activity(request, system_name, 'ข้อผิดพลาด', f'ไม่พบพนักงานรหัส {person_id}')

    if not month_str:
        return JsonResponse({"status": "error", "message": "ไม่พบข้อมูลเดือน"}, status=400)

    try:
        year, month = map(int, month_str.split('-'))
    except ValueError:
        log_activity(request, system_name, 'ข้อผิดพลาด', f'รูปแบบเดือนไม่ถูกต้อง: {month_str}')
        return JsonResponse({"status": "error", "message": "รูปแบบเดือนไม่ถูกต้อง"}, status=400)

    fees = Fee.objects.filter(
        person__id=person_id,
        fee_status=fee_status,
        date__year=year,
        date__month=month
    ).order_by('-date')

    total = sum(float(f.amount) for f in fees)

    data = [
        {
            "id": f.id,
            "date": f.date.strftime("%d/%m/%Y") if f.date else "ไม่ระบุวันที่",
            "amount": float(f.amount),
            "description": f.description or "-"
        }
        for f in fees
    ]

    return JsonResponse({
        "status": "success",
        "data": data,
        "total": float(total)
    })


@require_http_methods(["DELETE"])
def delete_fee(request, fee_id):
    try:
        fee = Fee.objects.get(pk=fee_id)
        fee_status = fee.fee_status
        person = fee.person
        amount = fee.amount
        
        # บันทึก log ก่อนลบข้อมูล
        action = 'ลบรายการเบิกเงิน' if fee_status == 0 else 'ลบรายการกู้เงิน'
        detail = f'{action} จำนวน {amount} บาท ของ {person.first_name} {person.last_name} วันที่ {fee.date}'
        system_name = 'withdraw' if fee_status == 0 else 'loan'
        log_activity(request, system_name, action, detail, fee)
        
        fee.delete()
        return JsonResponse({"status": "success", "fee_status": fee_status})
    except Fee.DoesNotExist:
        log_activity(request, 'withdraw', 'ข้อผิดพลาด', f'ไม่พบรายการเบิกเงิน/กู้เงินรหัส {fee_id}')
        return JsonResponse({"status": "error", "message": "ไม่พบรายการ"}, status=404)
    except Exception as e:
        log_activity(request, 'withdraw', 'ข้อผิดพลาด', str(e))
        return JsonResponse({"status": "error", "message": str(e)}, status=500)