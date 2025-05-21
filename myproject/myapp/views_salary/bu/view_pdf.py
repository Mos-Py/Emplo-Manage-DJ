from datetime import datetime
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote
import re, os, tempfile, time

from django.conf import settings
from django.http import HttpResponse
from django.utils.encoding import smart_str

import xlwings as xw

from myapp.models import SalaryRecord, Fee, Company, WorkDay, Person

THAI_MONTHS = [
    "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
]


def generate_salary_excel_to_file(person_id, month, output_path):

    try:
        # === โหลด Template ===
        template_path = Path(settings.BASE_DIR) / "myapp" / "static" / "templates" / "salary_template.xlsx"
        wb = xw.Book(str(template_path))
        ws = wb.sheets[0]

        # === เตรียมข้อมูลพื้นฐาน ===
        year, month_num = [int(x) for x in month.split("-")]
        person = Person.objects.get(id=person_id)
        salary = SalaryRecord.objects.filter(person=person, month__year=year, month__month=month_num).first()

        if not salary:
            return f"ไม่พบข้อมูล SalaryRecord ของ {person} เดือน {month}"

        workdays = WorkDay.objects.filter(person=person, date__year=year, date__month=month_num, status=1)
        fees = Fee.objects.filter(person=person, date__year=year, date__month=month_num)

        # === สรุปข้อมูล ===
        base_salary = Decimal(str(salary.base_salary or 0))
        bonus = Decimal(str(salary.bonus or 0))
        commission = Decimal(str(salary.commission or 0))
        withdraw = Decimal(str(salary.withdraw or 0))
        loan_payment = Decimal(str(salary.loan_payment or 0))
        ss_amount = Decimal(str(salary.ss_amount or 0))
        raw_queue = Decimal(str(getattr(salary, 'raw_queue', 0) or 0))
        total_income = Decimal(str(salary.total or 0))
        extra_income = salary.extra_items or []
        extra_expense = salary.extra_expenses or []

        work_days_count = workdays.count()
        total_work_pay = sum((wd.pay for wd in workdays), Decimal("0"))

        # === ใส่ชื่อและตำแหน่ง ===
        ws.range("full_name").value = f"{person.title} {person.first_name} {person.last_name}"
        role = person.Role  # แก้จาก role เป็น Role ให้ตรงกับโมเดล
        if role == "Concrete Mixer Driver" and person.concrete_mixer_numbers:
            role += f" {person.concrete_mixer_numbers}"
        ws.range("position").value = role

        # === ใส่รายได้ ===
        ws.range("lary_per_day").value = float(base_salary)
        ws.range("work_days").value = work_days_count
        ws.range("commission").value = float(commission)

        # === รายได้เพิ่มเติม ===
        income_row = ws.range("extra_income_start").row + 1
        for item in extra_income:
            ws.range((income_row, 1)).value = item.get("name", "-")
            ws.range((income_row, 2)).value = item.get("amount", 0)
            ws.range((income_row, 3)).value = "บาท"
            income_row += 1

        # === รายจ่าย (เงินกู้ + พิเศษ) ===
        deduct_anchor = ws.range("extra_deduct_start")
        row_deduct = deduct_anchor.row
        col_name = deduct_anchor.column
        col_amount = col_name + 1
        col_unit = col_name + 2

        if loan_payment > 0:
            ws.range((row_deduct, col_name)).value = "เงินกู้"
            ws.range((row_deduct, col_amount)).value = float(loan_payment)
            ws.range((row_deduct, col_unit)).value = "บาท"
            row_deduct += 1

        for item in extra_expense:
            ws.range((row_deduct, col_name)).value = item.get("name", "-")
            ws.range((row_deduct, col_amount)).value = item.get("amount", 0)
            ws.range((row_deduct, col_unit)).value = "บาท"
            row_deduct += 1

        # === รวมยอด ===
        ws.range("total_income").value = float(total_income)
        ws.range("total_deduct").value = float(withdraw + loan_payment + ss_amount + sum(Decimal(str(i.get("amount", 0))) for i in extra_expense))
        ws.range("net_total").value = float(total_income - (withdraw + loan_payment + ss_amount + sum(Decimal(str(i.get("amount", 0))) for i in extra_expense)))

        # === ประวัติการเบิก (จาก Fee ที่ fee_status = 0) ===
        withdraw_fees = fees.filter(fee_status=0)
        row_fee = ws.range("withdraw_start").row
        for fee in withdraw_fees:
            ws.range((row_fee, 2)).value = fee.date.strftime("%d/%m/%Y")
            ws.range((row_fee, 3)).value = float(fee.amount)
            row_fee += 1

        # === วันที่ปัจจุบัน ===
        ws.range("date_today").value = datetime.now().strftime("%d/%m/%Y")

        # === Save ===
        wb.save(str(output_path))
        wb.close()
        return True

    except Exception as e:
        return f"ERROR: {e}"


def export_person_salary_pdf(request, person_id):
    temp_dir = Path(tempfile.gettempdir())
    excel_path = temp_dir / f"salary_{person_id}_{int(time.time())}.xlsx"

    # 👇 เรียกฟังก์ชันที่เขียนไฟล์จริง
    result = generate_salary_excel_to_file(person_id, request.GET.get("month"), excel_path)
    if result is not True:
        return HttpResponse(result, status=500)

    # แทนที่จะสร้าง PDF ด้วย Excel Automation ซึ่งอาจมีปัญหา
    # เราจะคืนไฟล์ Excel แทน
    
    with open(excel_path, 'rb') as f:
        file_data = f.read()
    
    month = request.GET.get("month")
    year, month_num = [int(x) for x in month.split("-")]
    person = Person.objects.get(id=person_id)
    
    # สร้างชื่อไฟล์
    month_name = THAI_MONTHS[month_num]
    year_thai = year + 543
    filename = f"สลิปเงินเดือน_{month_name}_{year_thai}_{person.first_name}.xlsx"
    encoded_filename = quote(filename)
    
    response = HttpResponse(
        file_data,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
    
    # ลบไฟล์ชั่วคราว
    try:
        os.remove(excel_path)
    except:
        pass
    
    return response