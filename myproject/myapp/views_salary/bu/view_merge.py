import os, time, tempfile
import xlwings as xw
from django.http import HttpResponse
from django.conf import settings
from pathlib import Path
from datetime import datetime
from myapp.models import SalaryRecord
from .view_excel import export_person_salary_excel_to_file

def merge_excels_to_one(file_paths, output_path):
    app = xw.App(visible=False)
    final_wb = app.books.add()
    final_ws = final_wb.sheets[0]
    current_row = 1

    for idx, path in enumerate(file_paths):
        wb = app.books.open(path)
        ws = wb.sheets[0]

        used_range = ws.used_range
        row_count = used_range.last_cell.row
        col_count = used_range.last_cell.column

        ws.range((1, 1), (row_count, col_count)).copy(final_ws.range((current_row, 1)))

        for r in range(1, row_count + 1):
            final_ws.range((current_row + r - 1, 1)).row_height = ws.range((r, 1)).row_height

        if idx == 0:
            for c in range(1, col_count + 1):
                final_ws.range((1, c)).column_width = ws.range((1, c)).column_width

        current_row += row_count + 2
        wb.close()

    final_wb.save(str(output_path))
    final_wb.close()
    app.quit()
    return output_path

def export_all_salary_excel(request):
    month_str = request.GET.get("month")
    if not month_str:
        return HttpResponse("Missing month", status=400)

    month_date = datetime.strptime(month_str, "%Y-%m").date()
    salary_records = SalaryRecord.objects.filter(month=month_date)
    if not salary_records.exists():
        return HttpResponse("ไม่พบพนักงานที่บันทึกเงินเดือนในเดือนนี้", status=404)

    temp_files = []
    for sr in salary_records:
        temp_path = Path(tempfile.gettempdir()) / f"slip_{sr.person.id}_{int(time.time())}.xlsx"
        success, result = export_person_salary_excel_to_file(sr.person.id, month_str, temp_path)
        if success:
            temp_files.append(temp_path)

    merged_path = Path(tempfile.gettempdir()) / f"merge_salary_all_{int(time.time())}.xlsx"
    merge_excels_to_one(temp_files, merged_path)

    with open(merged_path, "rb") as f:
        file_data = f.read()

    response = HttpResponse(file_data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="รวมสลิปเงินเดือน_{month_str}.xlsx"'
    return response
