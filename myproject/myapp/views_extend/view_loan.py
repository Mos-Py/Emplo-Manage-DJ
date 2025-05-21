from django.shortcuts import render, redirect
from myapp.models import Fee, Person
from datetime import date
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from myapp.access_control import role_required, admin_required
from myapp.utils import log_activity

@login_required
@admin_required
def loan_form(request):
    # บันทึกการเข้าใช้งานระบบกู้เงิน
    log_activity(request, 'loan', 'เข้าหน้ากู้เงิน')
    
    persons = Person.objects.all()
    today = date.today()
    return render(request, "loan.html", {"persons": persons, "today": today})

# ใช้ save_fee จาก view_withdraw เพราะมีการตรวจสอบ fee_status อยู่แล้ว

def get_loan_history(request, person_id):
    try:
        person = Person.objects.get(id=person_id)
        
        # บันทึกการดูประวัติการกู้เงิน
        log_activity(request, 'loan', 'ดูประวัติการกู้เงิน', 
                     f'ดูประวัติของ {person.first_name} {person.last_name}', person)
        
        # ดึงข้อมูลเงินกู้ทั้งหมดของคนคนนี้
        loans = Fee.objects.filter(
            person__id=person_id,
            fee_status=1,  # 1 = กู้เงิน
            amount__gt=0   # เฉพาะรายการกู้ (ไม่รวมรายการจ่ายคืน)
        ).order_by('-date')
        
        # รวมยอดกู้ทั้งหมด
        total_loan = sum(float(loan.amount) for loan in loans)
        
        # หาการจ่ายคืนทั้งหมด
        repayments = Fee.objects.filter(
            person__id=person_id,
            fee_status=1,  # 1 = กู้เงิน
            amount__lt=0   # เฉพาะรายการจ่ายคืน (มีค่าเป็นลบ)
        )
        
        total_repaid = abs(sum(float(repay.amount) for repay in repayments))
        
        # คำนวณยอดคงเหลือ
        remaining_balance = total_loan - total_repaid
        
        loan_data = []
        for loan in loans:
            # คำนวณยอดคงเหลือของแต่ละรายการกู้
            payments_for_this_loan = Fee.objects.filter(
                person__id=person_id,
                fee_status=1,
                amount__lt=0,
                date__gt=loan.date
            )
            
            total_paid_for_loan = abs(sum(float(payment.amount) for payment in payments_for_this_loan))
            remaining_for_loan = float(loan.amount) - total_paid_for_loan
            
            # ถ้าจ่ายหมดแล้ว ไม่แสดง
            if remaining_for_loan <= 0:
                continue
                
            loan_data.append({
                "id": loan.id,
                "date": loan.date.strftime("%d/%m/%Y"),
                "amount": float(loan.amount),
                "remaining_amount": max(0, remaining_for_loan),
                "description": loan.description or "-"
            })

        return JsonResponse({
            "status": "success",
            "data": loan_data,
            "total_remaining": max(0, remaining_balance)
        })
        
    except Person.DoesNotExist:
        log_activity(request, 'loan', 'ข้อผิดพลาด', f'ไม่พบพนักงานรหัส {person_id}')
        return JsonResponse({"status": "error", "message": "ไม่พบพนักงาน"}, status=404)
    except Exception as e:
        log_activity(request, 'loan', 'ข้อผิดพลาด', str(e))
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@require_http_methods(["DELETE"])
def delete_loan(request, loan_id):
    try:
        loan = Fee.objects.get(id=loan_id, fee_status=1)  # 1 = กู้เงิน
        loan_amount = loan.amount
        person = loan.person
        
        # บันทึก log การลบรายการเงินกู้
        log_activity(request, 'loan', 'ลบรายการกู้เงิน', 
                    f'ลบรายการกู้เงิน {loan_amount} บาท ของ {person.first_name} {person.last_name} วันที่ {loan.date}', 
                    loan)
        
        # ลบรายการเงินกู้
        loan.delete()
        
        return JsonResponse({
            "status": "success", 
            "message": f"ลบรายการเงินกู้ {loan_amount} บาท เรียบร้อยแล้ว"
        })
    except Fee.DoesNotExist:
        log_activity(request, 'loan', 'ข้อผิดพลาด', f'ไม่พบรายการเงินกู้รหัส {loan_id}')
        return JsonResponse({"status": "error", "message": "ไม่พบรายการเงินกู้"}, status=404)
    except Exception as e:
        log_activity(request, 'loan', 'ข้อผิดพลาด', str(e))
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@require_http_methods(["DELETE"])
def delete_all_loans(request, person_id):
    try:
        person = Person.objects.get(id=person_id)
        
        # ดึงเงินกู้ทั้งหมดของพนักงาน
        loans = Fee.objects.filter(
            person__id=person_id,
            fee_status=1  # 1 = กู้เงิน
        )
        
        if not loans.exists():
            log_activity(request, 'loan', 'ข้อผิดพลาด', f'ไม่พบรายการเงินกู้ของ {person.first_name} {person.last_name}')
            return JsonResponse({"status": "error", "message": "ไม่พบรายการเงินกู้ของพนักงานคนนี้"}, status=404)
        
        loan_count = loans.count()
        total_amount = sum(float(loan.amount) for loan in loans if loan.amount > 0)
        
        # บันทึก log การลบเงินกู้ทั้งหมด
        log_activity(request, 'loan', 'ลบรายการกู้เงินทั้งหมด', 
                     f'ลบรายการกู้เงินทั้งหมด {loan_count} รายการ รวม {total_amount} บาท ของ {person.first_name} {person.last_name}',
                     person)
        
        # ลบเงินกู้ทั้งหมด
        loans.delete()
        
        return JsonResponse({
            "status": "success", 
            "message": f"ลบรายการเงินกู้ทั้งหมด {loan_count} รายการ เรียบร้อยแล้ว",
            "count": loan_count
        })
    except Person.DoesNotExist:
        log_activity(request, 'loan', 'ข้อผิดพลาด', f'ไม่พบพนักงานรหัส {person_id}')
        return JsonResponse({"status": "error", "message": "ไม่พบพนักงาน"}, status=404)
    except Exception as e:
        log_activity(request, 'loan', 'ข้อผิดพลาด', str(e))
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

def get_loan_summary(request, person_id):
    month_str = request.GET.get("month")
    try:
        year, month = map(int, month_str.split("-"))
        person = Person.objects.get(id=person_id)
        
        # บันทึก log การดูสรุปเงินกู้
        log_activity(request, 'loan', 'ดูสรุปเงินกู้', 
                     f'ดูสรุปเงินกู้ของ {person.first_name} {person.last_name} เดือน {month_str}', 
                     person)

        # หารายการกู้ทั้งหมด (เฉพาะรายการที่มีค่าเป็นบวก = การกู้)
        loans = Fee.objects.filter(
            person__id=person_id,
            fee_status=1,  # 1 = กู้เงิน
            amount__gt=0   # เฉพาะการกู้ (ไม่รวมการชำระคืน)
        )
        
        # หารายการจ่ายคืนทั้งหมด (มีค่าเป็นลบ)
        repayments = Fee.objects.filter(
            person__id=person_id,
            fee_status=1,  # 1 = กู้เงิน
            amount__lt=0   # เฉพาะการชำระคืน
        )
        
        # ยอดเงินกู้ทั้งหมด
        total_loan_amount = sum(float(loan.amount) for loan in loans)
        
        # ยอดการชำระคืนทั้งหมด
        total_repaid = abs(sum(float(repay.amount) for repay in repayments))
        
        # ยอดคงเหลือ
        remaining_balance = max(0, total_loan_amount - total_repaid)
        
        # ยอดจ่ายคืนในเดือนนี้
        repayments_this_month = Fee.objects.filter(
            person__id=person_id,
            fee_status=1,
            amount__lt=0,
            date__year=year,
            date__month=month
        )
        loan_paid_this_month = abs(sum(float(payment.amount) for payment in repayments_this_month))

        # ไม่มีค่างวดต่อเดือน (ลบฟิลด์ไปแล้ว)
        monthly_installment = 0

        return JsonResponse({
            "loan_paid_this_month": float(loan_paid_this_month),
            "loan_remaining": float(remaining_balance),
            "monthly_installment": float(monthly_installment),
            "loan_amount": float(total_loan_amount)
        })
        
    except ValueError:
        log_activity(request, 'loan', 'ข้อผิดพลาด', f'รูปแบบเดือนไม่ถูกต้อง: {month_str}')
        return JsonResponse({"error": "เดือนผิดรูปแบบ"}, status=400)
    except Person.DoesNotExist:
        log_activity(request, 'loan', 'ข้อผิดพลาด', f'ไม่พบพนักงานรหัส {person_id}')
        return JsonResponse({"error": "ไม่พบพนักงาน"}, status=404)
    except Exception as e:
        log_activity(request, 'loan', 'ข้อผิดพลาด', str(e))
        return JsonResponse({"error": str(e)}, status=500)