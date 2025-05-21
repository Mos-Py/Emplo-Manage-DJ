
import re
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from datetime import datetime
from decimal import Decimal
from django.conf import settings
import xlwings as xw
from urllib.parse import quote
import tempfile
from pathlib import Path
import time
from django.http import FileResponse, HttpResponse
import tempfile
import win32com.client
from django.utils.encoding import smart_str
import os
from decimal import Decimal


from myapp.models import SalaryRecord, Fee, Company, WorkDay,Person

THAI_MONTHS = [
    "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
]

def export_person_salary_excel(request, person_id):

    try:
        month = request.GET.get('month')
        if not month:
            return HttpResponse("Missing month", status=400)
        month_obj = datetime.strptime(month, "%Y-%m")

        salary = get_object_or_404(
            SalaryRecord,
            person_id=person_id,
            month__year=month_obj.year,
            month__month=month_obj.month
        )
        person = salary.person
        company = Company.objects.first()

        workdays = WorkDay.objects.filter(
            person=person,
            date__year=month_obj.year,
            date__month=month_obj.month,
            status=1
        )

        days_worked = sum(0.5 if not w.full_day else 1 for w in workdays)
        salary_per_day = Decimal(person.salary)
        commission = salary.commission or Decimal("0.00")
        bonus = salary.bonus or Decimal("0.00")

        total_income = (salary_per_day * Decimal(days_worked)) + commission + bonus

        withdraws = Fee.objects.filter(
            person=person,
            date__year=month_obj.year,
            date__month=month_obj.month,
            fee_status=0
        )
        withdraw_total = sum((w.amount for w in withdraws), Decimal("0.00"))
        loan = salary.loan_payment or Decimal("0.00")
        ss = salary.ss_amount or Decimal("0.00")

        extra_expenses_total = sum(
            float(item.get("amount") or item.get("value") or 0)
            for item in salary.extra_expenses or []
        )

        total_deduct = withdraw_total + loan + ss + Decimal(str(extra_expenses_total))
        net_total = total_income - total_deduct

        loan_remaining = 0
        active_loans = Fee.objects.filter(person=person, fee_status=1)

        loan_remaining = sum(
            float(f.remaining) for f in active_loans if f.remaining > 0
        )

        data_map = {
            "full_name": f"{person.first_name} {person.last_name}",
            "position": (
                f"คนขับรถโม่ {person.concrete_mixer_numbers}"
                if person.Role == "Concrete Mixer Driver"
                else dict(person._meta.get_field("Role").choices).get(person.Role, person.Role)
            ),
            "salary_per_day": float(salary_per_day),
            "work_days": float(days_worked),
            "commission": float(commission),
            "bonus": float(bonus),
            "total_income": float(total_income),
            "withdraw_total": float(withdraw_total),
            "loan_payment": float(loan),
            "loan_remaining": float(loan_remaining),
            "ss_amount": float(ss),
            "total_deduct": float(total_deduct),
            "net_total": float(net_total),
            "date_today": datetime.now().strftime("%d/%m/%Y"),
            "company_name": company.C_name,
            "company_address": company.address,
            "total_deduct": float(total_deduct),
        }

        template_path = Path(settings.BASE_DIR) / "myapp" / "static" / "templates" / "salary_template.xlsx"
        if not template_path.exists():
            return HttpResponse("ไม่พบไฟล์ salary_template.xlsx", status=500)

        app = xw.App(visible=False)
        wb = app.books.open(str(template_path))
        ws = wb.sheets[0]

        try:
            target_cell = ws.range("total_deduct_cell")
            row = target_cell.row - 1
            col = target_cell.column

            print(">>> ตรวจตำแหน่ง Named Range: row =", row, "col =", col)
            print(">>> loan_remaining =", data_map["loan_remaining"])

            if data_map["loan_remaining"] > 0:
                ws.range((row, col - 2)).value = "เงินกู้คงเหลือ"
                ws.range((row, col)).value = data_map["loan_remaining"]
                ws.range((row, col + 1)).value = "บาท"
                print(">>> เขียนสำเร็จ")
            else:
                ws.range((row, col - 1), (row, col + 1)).value = None
                print(">>> loan_remaining = 0, ลบช่อง")
        except Exception as e:
            print("⚠️ ไม่พบ named range 'total_deduct_cell' หรือเกิดข้อผิดพลาด:", e)

        pattern = re.compile(r"{{\s*(\w+)\s*}}")
        for cell in ws.range("A1:Z50"):
            if isinstance(cell.value, str):
                matches = pattern.findall(cell.value)
                new_value = cell.value
                for key in matches:
                    if key in data_map:
                        new_value = new_value.replace(f"{{{{ {key} }}}}", str(data_map[key]))
                        new_value = new_value.replace(f"{{{{{key}}}}}", str(data_map[key]))
                cell.value = new_value

        try:
            start_cell = ws.range("withdraw_start")
            start_row = start_cell.row
            for i, item in enumerate(withdraws):
                ws.range((start_row + i, start_cell.column)).value = item.date.strftime("%d/%m/%Y")
                ws.range((start_row + i, start_cell.column + 1)).value = float(item.amount)
        except Exception as e:
            print("⚠️ ไม่พบ named range 'withdraw_start' หรือเกิดข้อผิดพลาด:", e)

        try:
            extra_items = salary.extra_items or []
            print(">>> DEBUG: salary.extra_items =", salary.extra_items)
            print(">>> DEBUG: type =", type(salary.extra_items))

            # รวมชื่อที่ซ้ำกัน
            merged_items = {}
            for item in extra_items:
                name = item.get("name") or item.get("label", "").strip()
                amount = float(item.get("amount") or item.get("value") or 0)
                if not name:
                    continue
                merged_items[name] = merged_items.get(name, 0) + amount

            # ใช้ Named Range เป็น anchor
            income_anchor = ws.range("extra_income_start")
            print(">>> income_anchor type:", type(income_anchor))
            print(">>> income_anchor row/col =", income_anchor.row, income_anchor.column)

            income_row = income_anchor.row + 1  # เขียนถัดจากค่าหัวคิว
            col_name = income_anchor.column
            col_amount = col_name + 1
            col_unit = col_name + 2

            # 🧪 LOG ตรวจหา "รวมรายได้"
            print(">>> LOG: ws type =", type(ws))
            print(">>> LOG: ws.cells type =", type(ws.cells))
            print(">>> LOG: เริ่มค้นหา 'รวมรายได้'")
            total_income_row = None
            for row in range(1, 100):  # ตรวจแถว 1 ถึง 99
                value = ws.range(f"A{row}").value
                if value and str(value).strip() == "รวมรายได้":
                    total_income_row = row
                    break

            if not total_income_row:
                raise Exception("ไม่พบคำว่า 'รวมรายได้'")

            required_lines = len(merged_items)
            available_lines = total_income_row - income_row
            if required_lines > available_lines:
                rows_to_insert = required_lines - available_lines
                for _ in range(rows_to_insert):
                    ws.api.Rows(total_income_row).Insert(Shift=-4121)
                print(f">>> แทรกเพิ่ม {rows_to_insert} แถวที่ {total_income_row}")

            for name, amount in merged_items.items():
                print(f">>> เขียนรายการ: {name} - {amount}")
                ws.range((income_row, col_name)).value = name
                ws.range((income_row, col_amount)).value = amount
                ws.range((income_row, col_unit)).value = "บาท"
                income_row += 1

        except Exception as e:
            print("⚠️ เขียน extra_items ไม่สำเร็จ:", e)

        try:
            extra_expenses = salary.extra_expenses or []
            print(">>> DEBUG: salary.extra_expenses =", extra_expenses)

            merged_expenses = {}
            for item in extra_expenses:
                name = (item.get("name") or item.get("label") or "").strip()
                amount = float(item.get("amount") or item.get("value") or 0)
                if not name:
                    continue
                merged_expenses[name] = merged_expenses.get(name, 0) + amount

            # ✅ กำหนดตำแหน่ง anchor + column
            deduct_anchor = ws.range("extra_deduct_start")
            col_name = deduct_anchor.column      # D
            col_amount = col_name + 1           # E
            col_unit = col_name + 2             # F

            print(">>> salary.loan_payment =", salary.loan_payment)
            print(">>> type =", type(salary.loan_payment))

            # ✅ แสดง "เงินกู้" แยกก่อน (ไม่ขึ้นกับมี extra_expenses หรือไม่)
            if float(salary.loan_payment or 0) > 0:
                ws.range((deduct_anchor.row, col_name)).value = "เงินกู้"
                ws.range((deduct_anchor.row, col_amount)).value = float(salary.loan_payment)
                ws.range((deduct_anchor.row, col_unit)).value = "บาท"
            else:
                ws.range((deduct_anchor.row, col_name), (deduct_anchor.row, col_unit)).value = None
            

            if merged_expenses:
                # ✅ หาแถวของ "เบิกเงิน"
                withdraw_row = None
                for r in range(1, 100):
                    val = ws.range(f"D{r}").value
                    if val and str(val).strip() == "เบิกเงิน":
                        withdraw_row = r
                        break

                # ✅ ถ้าไม่มีเงินกู้และเจอเบิกเงิน → แทรกแถวว่าง
                if float(salary.loan_payment or 0) == 0 and withdraw_row:
                    ws.api.Rows(withdraw_row + 1).Insert(Shift=-4121)
                    print(f">>> แทรกแถวว่างหลังเบิกเงิน ที่แถว {withdraw_row + 1}")

                # ✅ เริ่มเขียนรายการหลังจากเบิกเงิน หรือ anchor
                if float(salary.loan_payment or 0) > 0:
                    start_row = deduct_anchor.row + 1  # เขียนต่อจากเงินกู้
                else:
                    start_row = withdraw_row + 1 if withdraw_row else deduct_anchor.row
                print(f">>> เริ่มเขียน extra_expenses ที่แถว {start_row}")

                for name, amount in merged_expenses.items():
                    ws.range((start_row, col_name)).value = name or "-"
                    ws.range((start_row, col_amount)).value = amount
                    ws.range((start_row, col_unit)).value = "บาท"
                    print(f">>> เขียนรายจ่าย: '{name}' - {amount}")
                    start_row += 1
            

        except Exception as e:
            print("⚠️ เขียน extra_expenses ไม่สำเร็จ:", e)

        # === save ลงไฟล์ temp ===
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            temp_file_path = tmp.name
            cell_value = ws.range("D7").value
            print(f">>> FINAL D7 VALUE BEFORE SAVE: '{cell_value}'")
        wb.save(temp_file_path)
        wb.close()
        app.quit()

        with open(temp_file_path, "rb") as f:
            file_data = f.read()

        # === สร้างชื่อไฟล์ดาวน์โหลด ===
        month_name = THAI_MONTHS[month_obj.month]
        year = month_obj.year
        full_name = f"{person.title}{person.first_name} {person.last_name}"
        filename = f"สลิปเงินเดือน {month_name} {year} {full_name}.xlsx"
        encoded_filename = quote(filename)

        response = HttpResponse(
            file_data,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
        return response

    except Exception as e:
        import traceback
        return HttpResponse(f"เกิดข้อผิดพลาด:\n{e}\n\n{traceback.format_exc()}", status=500)


def export_person_salary_excel_to_file(person_id, month_str, output_path):
    request = type('FakeRequest', (), {'GET': {'month': month_str}})
    response = export_person_salary_excel(request, person_id)
    if response.status_code != 200:
        return False, f"Export failed: {response.status_code}"
    
    with open(output_path, "wb") as f:
        f.write(response.content)

    return True, "OK"

def export_person_salary_excel_to_file(person_id, month_str, output_path):
    request = type('FakeRequest', (), {'GET': {'month': month_str}})
    response = export_person_salary_excel(request, person_id)
    if response.status_code != 200:
        return False, f"Export failed: {response.status_code}"
    
    with open(output_path, "wb") as f:
        f.write(response.content)

    return True, "OK"