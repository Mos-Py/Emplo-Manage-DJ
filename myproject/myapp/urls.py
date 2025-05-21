from django.urls import path
from .views import (index, login_view, logout_view, checkin_view, 
                   employee_list)
from .views_extend.view_check import check_view, save_attendance, save_day_off
from .views_extend.view_com_calc import (com_calc_view, save_queue_conditions, 
                                        load_queue_conditions, load_prev_queue_conditions,
                                        delete_all_queue_conditions)
from .views_extend import view_withdraw, view_loan,view_employee
from .views_extend.view_employee import employee_list, employee_add, employee_edit, employee_profile_edit, employee_delete
from .views_extend.view_dashboard import dashboard_view, admin_view_dashboard
from .views_salary.view_salary import (salary_list_view, get_salary_info, get_withdraw_history, 
                                       get_saved_salary, get_loan_summary, get_all_persons, export_person_salary_excel, export_person_salary_pdf,convert_excel_to_pdf)
from .views_salary.view_merge import export_all_salary_excel,export_all_salary_pdf
from .views_extend.view_log import (admin_log_view, dashboard_logs, checkin_logs, 
                                     withdraw_logs, loan_logs, calc_logs, salary_logs, employee_logs)

urlpatterns = [
    path('', index, name='index'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path("checkin/", checkin_view, name="checkin"),
    path("check/", check_view, name="check"),
    path("save_attendance/", save_attendance, name="save_attendance"),
    path("save_day_off/", save_day_off, name="save_day_off"),


    # URL Dashboard - แก้ไขให้ใช้ dashboard_view แทน dashboard
    path("dashboard/", dashboard_view, name="dashboard"),
    # แก้ไขให้ใช้ admin_view_dashboard จาก view_dashboard
    path("employee/<int:person_id>/dashboard/", admin_view_dashboard, name="admin_view_dashboard"),

    # URL สำหรับระบบจัดการพนักงาน
    path("employees/", employee_list, name="employee_list"),
    path("employee/add/", employee_add, name="employee_add"),
    path("employee/<int:person_id>/edit/", employee_edit, name="employee_edit"),
    path("employee/<int:person_id>/delete/", employee_delete, name="employee_delete"),
    path("profile/edit/", employee_profile_edit, name="employee_profile_edit"),
    
    
    # URL สำหรับระบบคำนวณหัวคิว
    path("com_calc/", com_calc_view, name="com_calc"),
    path("save_queue_conditions/", save_queue_conditions, name="save_queue_conditions"),
    path("load_queue_conditions/", load_queue_conditions, name="load_queue_conditions"),
    path("load_prev_queue_conditions/", load_prev_queue_conditions, name="load_prev_queue_conditions"),
    path("delete_all_queue_conditions/", delete_all_queue_conditions, name="delete_all_queue_conditions"),

    # URL สำหรับระบบเบิกเงินและกู้เงิน
    path('withdraw/', view_withdraw.withdraw_form, name='withdraw_form'),
    path('loan/', view_loan.loan_form, name='loan_form'),  
    
    # API สำหรับระบบเบิกเงินและกู้เงิน
    path('save_fee/', view_withdraw.save_fee, name='save_fee'),
    path('api/fee_history/<int:person_id>/', view_withdraw.get_fee_history, name='get_fee_history'),
    path('api/delete_fee/<int:fee_id>/', view_withdraw.delete_fee, name='delete_fee'),
    
    # API สำหรับระบบกู้เงิน
    path('api/loan_history/<int:person_id>/', view_loan.get_loan_history, name='get_loan_history'),
    path('api/delete_loan/<int:loan_id>/', view_loan.delete_loan, name='delete_loan'),
    path('api/delete_all_loans/<int:person_id>/', view_loan.delete_all_loans, name='delete_all_loans'),
    path('api/loan_summary/<int:person_id>/', view_loan.get_loan_summary, name='get_loan_summary'),
    
    # URL สำหรับระบบเงินเดือน
    path('salary/', salary_list_view, name='salary_list'),
    path('api/salary_info/<int:person_id>/', get_salary_info, name='get_salary_info'),
    path('api/withdraw_history/<int:person_id>/', get_withdraw_history, name='get_withdraw_history'),
    path('api/saved_salary/<int:person_id>/', get_saved_salary, name='get_saved_salary'),
    path('api/loan_summary/<int:person_id>/', get_loan_summary, name='get_loan_summary'),
    path('api/get_all_persons/', get_all_persons, name='get_all_persons'),
    path('api/export_person_salary/<int:person_id>/', export_person_salary_excel, name='export_person_salary_excel'),
    path('api/export_person_salary_pdf/<int:person_id>/', export_person_salary_pdf, name='export_person_salary_pdf'),
    path("api/export_all_salary_excel/", export_all_salary_excel, name="export_all_salary_excel"),
    path("api/gen_pdf_v2/", export_all_salary_pdf ,name="generate_pdf_batch"),
    path('api/convert_excel_to_pdf/', convert_excel_to_pdf, name='convert_excel_to_pdf'),

    # เพิ่ม URLs สำหรับระบบดู Logs
    path('admin_log/', admin_log_view, name='admin_log'),
    path('admin_log/dashboard/', dashboard_logs, name='dashboard_logs'),
    path('admin_log/checkin/', checkin_logs, name='checkin_logs'),
    path('admin_log/withdraw/', withdraw_logs, name='withdraw_logs'),
    path('admin_log/loan/', loan_logs, name='loan_logs'),
    path('admin_log/calc/', calc_logs, name='calc_logs'),
    path('admin_log/salary/', salary_logs, name='salary_logs'),
    path('admin_log/employee/', employee_logs, name='employee_logs'),

]