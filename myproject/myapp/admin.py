from django.contrib import admin
from django.utils.html import format_html
from django.forms import ModelForm
from .models import Person, WorkDay, QueueRate, Fee, SalaryRecord, Company

class PersonAdminForm(ModelForm):
    class Meta:
        model = Person
        fields = '__all__'
    
    class Media:
        js = ('js/admin.js',)

class PersonAdmin(admin.ModelAdmin):
    form = PersonAdminForm
    list_display = ('full_name', 'get_thai_role', 'get_daily_wage', 'get_monthly_salary', 'get_status_with_icon')
    list_filter = ('Role', 'status', 'gender')
    search_fields = ('first_name', 'last_name', 'id_card_number')
    list_per_page = 20
    
    fieldsets = (
        ('ข้อมูลพื้นฐาน', {
            'fields': ('user', 'title', 'gender', 'first_name', 'last_name', 'date_of_birth', 'id_card_number', 'nationality')
        }),
        ('ข้อมูลที่อยู่', {
            'fields': ('address',)
        }),
        ('ข้อมูลการทำงาน', {
            'fields': ('Role', 'concrete_mixer_numbers', 'salary', 'status')
        }),
    )
    
    def full_name(self, obj):
        return f"{obj.title} {obj.first_name} {obj.last_name}"
    full_name.short_description = 'ชื่อ-นามสกุล'

    def get_thai_role(self, obj):
        role_text = obj.get_thai_role()
        if obj.Role == 'Concrete Mixer Driver' and obj.concrete_mixer_numbers:
            role_text = f"{role_text} {obj.concrete_mixer_numbers}"
        return role_text
    get_thai_role.short_description = 'ตำแหน่ง'
    
    def get_daily_wage(self, obj):
        return f"{obj.salary:,.2f} บาท"
    get_daily_wage.short_description = 'ค่าจ้างต่อวัน'
    
    def get_monthly_salary(self, obj):
        monthly_salary = obj.get_monthly_salary()
        if monthly_salary:
            return f"{monthly_salary:,.2f} บาท"
        return "-"
    get_monthly_salary.short_description = 'เงินเดือน'
    
    def get_status_with_icon(self, obj):
        if obj.status == 1:
            return format_html('<span style="color:green;"><i class="fas fa-check-circle"></i> ทำงาน</span>')
        else:
            return format_html('<span style="color:red;"><i class="fas fa-times-circle"></i> ไม่ได้ทำงาน</span>')
    get_status_with_icon.short_description = 'สถานะ'
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # ไม่ต้องแสดงฟิลด์ concrete_mixer_numbers เริ่มต้น จะแสดงผ่าน JavaScript เมื่อเลือกตำแหน่งคนขับรถโม่
        if 'concrete_mixer_numbers' in form.base_fields:
            form.base_fields['concrete_mixer_numbers'].widget.attrs.update({'class': 'driver-field', 'style': 'display:none;'})
        return form

class WorkDayAdmin(admin.ModelAdmin):
    list_display = ('date', 'person', 'get_status_display', 'full_day', 'queue_count', 'pay')
    list_filter = ('date', 'status', 'full_day')
    search_fields = ('person__first_name', 'person__last_name', 'note')
    date_hierarchy = 'date'
    list_per_page = 20
    
    def get_status_display(self, obj):
        if obj.status == 1:
            return format_html('<span style="color:green;">ทำงาน</span>')
        else:
            return format_html('<span style="color:red;">หยุด</span>')
    get_status_display.short_description = 'สถานะ'

class QueueRateAdmin(admin.ModelAdmin):
    list_display = ('month', 'min_queue', 'max_queue', 'pay_per_queue')
    list_filter = ('month',)
    list_per_page = 20

class FeeAdmin(admin.ModelAdmin):
    list_display = ('person', 'date', 'get_fee_status', 'amount', 'remaining')
    list_filter = ('fee_status', 'date')
    search_fields = ('person__first_name', 'person__last_name', 'description')
    list_per_page = 20

    def get_fee_status(self, obj):
        if obj.fee_status == 0:
            return format_html('<span style="color:#ff9800;">เบิกเงิน</span>')
        else:
            return format_html('<span style="color:#1976d2;">กู้เงิน</span>')
    get_fee_status.short_description = 'ประเภท'

class SalaryRecordAdmin(admin.ModelAdmin):
    list_display = ('person', 'month', 'base_salary', 'bonus', 'commission', 'withdraw', 'loan_payment', 'total')
    list_filter = ('month',)
    search_fields = ('person__first_name', 'person__last_name')
    date_hierarchy = 'month'
    list_per_page = 20
    
    fieldsets = (
        ('ข้อมูลพื้นฐาน', {
            'fields': ('person', 'month')
        }),
        ('รายรับ', {
            'fields': ('base_salary', 'bonus', 'commission', 'extra_items')
        }),
        ('รายจ่าย', {
            'fields': ('withdraw', 'ss_amount', 'loan_payment', 'extra_expenses')
        }),
        ('สรุป', {
            'fields': ('total', 'recorded_by')
        }),
    )

class CompanyAdmin(admin.ModelAdmin):
    list_display = ('C_name', 'address', 'phone_number', 'email')

# ลงทะเบียนโมเดลกับ Admin
admin.site.register(Person, PersonAdmin)
admin.site.register(WorkDay, WorkDayAdmin)
admin.site.register(QueueRate, QueueRateAdmin)
admin.site.register(Fee, FeeAdmin)
admin.site.register(SalaryRecord, SalaryRecordAdmin)
admin.site.register(Company, CompanyAdmin)

# ปรับแต่งหน้า Admin
admin.site.site_header = 'ระบบจัดการพนักงาน'
admin.site.site_title = 'ระบบจัดการพนักงาน'
admin.site.index_title = 'ยินดีต้อนรับสู่ระบบจัดการพนักงาน'