from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseForbidden
from myapp.models import Person
from django import forms

from myapp.utils import log_activity

# สร้าง PersonForm ในไฟล์นี้เลย
class PersonForm(forms.ModelForm):
    """
    ฟอร์มสำหรับเพิ่ม/แก้ไขข้อมูลพนักงาน
    """
    # ฟิลด์สำหรับสร้างผู้ใช้ (แสดงเมื่อเพิ่มพนักงานใหม่)
    username = forms.CharField(
        label="ชื่อผู้ใช้",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label="รหัสผ่าน",
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Person
        fields = [
            'title', 'gender', 'date_of_birth',
            'first_name', 'last_name', 'id_card_number',
            'nationality', 'address', 'Role',
            'concrete_mixer_numbers', 'salary', 'status'
        ]
        widgets = {
            'title': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'id_card_number': forms.TextInput(attrs={'class': 'form-control'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'Role': forms.Select(attrs={'class': 'form-select'}),
            'concrete_mixer_numbers': forms.TextInput(attrs={'class': 'form-control'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'title': 'คำนำหน้า',
            'gender': 'เพศ',
            'date_of_birth': 'วันเกิด',
            'first_name': 'ชื่อ',
            'last_name': 'นามสกุล',
            'id_card_number': 'เลขบัตรประชาชน',
            'nationality': 'สัญชาติ',
            'address': 'ที่อยู่',
            'Role': 'ตำแหน่ง',
            'concrete_mixer_numbers': 'เลขประจำรถโม่',
            'salary': 'ค่าจ้าง',
            'status': 'สถานะ',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # กำหนดค่าเริ่มต้นสำหรับเพิ่มพนักงานใหม่
        if not self.instance.pk:  # ถ้าเป็นการเพิ่มใหม่
            self.fields['nationality'].initial = 'ไทย'
            self.fields['status'].initial = 1  # กำหนดค่าเริ่มต้นเป็น "ทำงาน"
            self.fields['username'].required = True
            self.fields['password'].required = True
        else:
            # ไม่แสดงฟิลด์ username และ password เมื่อแก้ไข
            self.fields['username'].widget = forms.HiddenInput()
            self.fields['password'].widget = forms.HiddenInput()
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        
        # ตรวจสอบชื่อผู้ใช้ซ้ำเมื่อเพิ่มพนักงานใหม่
        if not self.instance.pk and username:
            if User.objects.filter(username=username).exists():
                self.add_error('username', 'ชื่อผู้ใช้นี้มีอยู่ในระบบแล้ว')
        
        return cleaned_data

# ฟังก์ชั่นตรวจสอบสิทธิ์แบบรวม - เพิ่มใหม่เพื่อให้ตรงกันทั้งระบบ
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

def is_superuser(user):
    """
    ตรวจสอบว่าผู้ใช้เป็น superuser หรือไม่
    """
    return user.is_superuser

def can_edit_employee(user):
    """
    ตรวจสอบว่าผู้ใช้สามารถแก้ไขข้อมูลพนักงานได้หรือไม่
    - superuser สามารถแก้ไขได้ทุกอย่าง
    - ผู้ใช้ที่อยู่ในกลุ่ม Admin สามารถแก้ไขได้
    - ผู้ใช้ที่เป็น staff สามารถแก้ไขได้
    - ผู้ใช้ที่เป็นตำแหน่ง Accountant สามารถแก้ไขได้
    """
    # ใช้ฟังก์ชั่นตรวจสอบร่วม
    return check_admin_rights(user)

@login_required
def employee_list(request):
    """
    แสดงรายชื่อพนักงานทั้งหมด (สำหรับ admin)
    """
    # ตรวจสอบสิทธิ์ - เฉพาะ admin และ superuser เท่านั้น
    has_admin_rights = check_admin_rights(request.user)
    is_super = request.user.is_superuser

    if not has_admin_rights:
        return HttpResponseForbidden("ไม่มีสิทธิ์เข้าใช้งานส่วนนี้")
    
    # บันทึกการเข้าหน้ารายการพนักงาน
    log_activity(request, 'employee', 'เข้าหน้ารายการพนักงาน')
    
    # ดึงค่าการค้นหา (ถ้ามี)
    search_query = request.GET.get('q', '')
    
    # ดึงข้อมูลพนักงานทั้งหมด
    if search_query:
        # ค้นหาตามชื่อ นามสกุล หรือเลขบัตรประชาชน
        persons = Person.objects.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query) |
            Q(id_card_number__icontains=search_query)
        ).order_by('first_name')
        
        # บันทึกการค้นหาพนักงาน
        log_activity(request, 'employee', 'ค้นหาพนักงาน', f'คำค้น: {search_query}')
    else:
        persons = Person.objects.all().order_by('first_name')
    
    # ส่งค่าเพิ่มเติมเกี่ยวกับสิทธิ์ผู้ใช้
    context = {
        'persons': persons,
        'search_query': search_query,
        'is_superuser': is_super,
        'has_admin_rights': has_admin_rights
    }
    
    return render(request, 'employee_list.html', context)

@login_required
def employee_form(request, person_id=None, is_profile_edit=False):
    """
    แสดงฟอร์มเพิ่ม/แก้ไขข้อมูลพนักงาน
    is_profile_edit - ถ้าเป็น True แสดงว่าเป็นการแก้ไขข้อมูลส่วนตัว (ข้ามการตรวจสอบสิทธิ์บางอย่าง)
    """
    # ตรวจสอบสิทธิ์การเข้าถึง - ใช้ฟังก์ชั่นตรวจสอบร่วม
    is_super = request.user.is_superuser
    
    # ตรวจสอบการเป็น admin โดยอิงจากกลุ่มและตำแหน่ง Accountant
    is_admin = request.user.groups.filter(name='Admin').exists() or request.user.is_staff
    
    # ตรวจสอบตำแหน่ง Accountant
    is_accountant = False
    try:
        person_obj = Person.objects.get(user=request.user)
        if person_obj.Role == 'Accountant':
            is_accountant = True
    except Person.DoesNotExist:
        pass
    
    # กำหนดสิทธิ์ admin รวม
    has_admin_rights = is_super or is_admin or is_accountant
    is_regular_user = not has_admin_rights
    
    # ถ้าเป็นการแก้ไขโปรไฟล์ส่วนตัวของผู้ใช้
    if is_profile_edit:
        try:
            logged_in_person = Person.objects.get(user=request.user)
            if person_id is not None and int(person_id) != logged_in_person.id:
                return HttpResponseForbidden("ไม่มีสิทธิ์แก้ไขข้อมูลของผู้อื่น")
            # อนุญาตให้แก้ไขข้อมูลของตัวเอง
        except Person.DoesNotExist:
            return HttpResponseForbidden("ไม่พบข้อมูลพนักงาน")
    # ถ้าเป็นผู้ใช้ทั่วไปและไม่ใช่การแก้ไขโปรไฟล์ส่วนตัว
    elif is_regular_user:
        try:
            logged_in_person = Person.objects.get(user=request.user)
            if person_id is not None and int(person_id) != logged_in_person.id:
                return HttpResponseForbidden("ไม่มีสิทธิ์แก้ไขข้อมูลของผู้อื่น")
        except Person.DoesNotExist:
            return HttpResponseForbidden("ไม่พบข้อมูลพนักงาน")
    
    # ถ้าเป็น admin แต่ไม่ใช่ superuser ต้องตรวจสอบสิทธิ์เพิ่มเติม
    if (is_admin or is_accountant) and not is_super and person_id is not None:
        # Admin สามารถแก้ไขข้อมูลพนักงานได้ แต่ไม่สามารถแก้ไขข้อมูล superuser อื่น
        try:
            person_to_edit = Person.objects.get(id=person_id)
            if person_to_edit.user and person_to_edit.user.is_superuser and person_to_edit.user != request.user:
                return HttpResponseForbidden("ไม่มีสิทธิ์แก้ไขข้อมูลของ superuser")
        except Person.DoesNotExist:
            return HttpResponseForbidden("ไม่พบข้อมูลพนักงาน")
    
    # ถ้ามี person_id ให้โหลดข้อมูลพนักงาน มิฉะนั้นสร้างใหม่
    instance = None if person_id is None else get_object_or_404(Person, id=person_id)
    
    # ถ้าเป็นการสร้างใหม่และไม่ใช่ superuser หรือ admin
    if instance is None and not has_admin_rights:
        return HttpResponseForbidden("ไม่มีสิทธิ์เพิ่มพนักงานใหม่")
    
    # บันทึกการเข้าฟอร์มพนักงาน
    if instance:
        log_activity(request, 'employee', 'เข้าหน้าแก้ไขพนักงาน', 
                    f'แก้ไขข้อมูล: {instance.first_name} {instance.last_name}', instance)
    else:
        log_activity(request, 'employee', 'เข้าหน้าเพิ่มพนักงาน')
    
    if request.method == 'POST':
        form = PersonForm(request.POST, instance=instance)
        
        # เก็บค่าเดิมของฟิลด์ที่ไม่อนุญาตให้แก้ไข
        original_values = {}
        if instance:
            if is_regular_user:
                original_values = {
                    'Role': instance.Role,
                    'concrete_mixer_numbers': instance.concrete_mixer_numbers,
                    'salary': instance.salary,
                    'status': instance.status
                }
            elif (is_admin or is_accountant) and not is_super:
                original_values = {
                    'salary': instance.salary
                }
        
        # ตรวจสอบว่าถ้าเป็นการแก้ไขข้อมูลส่วนตัว (profile edit) หรือผู้ใช้ทั่วไป
        # ต้องแน่ใจว่าฟิลด์ที่ไม่ได้รับอนุญาตให้แก้ไขยังคงมีค่าเดิม
        if is_profile_edit or is_regular_user:
            # คัดลอก request.POST เพื่อแก้ไข
            post_copy = request.POST.copy()
            
            # คงค่าเดิมของฟิลด์ที่ไม่อนุญาตให้แก้ไข
            if instance:
                post_copy['Role'] = instance.Role
                post_copy['concrete_mixer_numbers'] = instance.concrete_mixer_numbers
                post_copy['salary'] = instance.salary 
                post_copy['status'] = instance.status
                
            # สร้างฟอร์มใหม่จากข้อมูลที่แก้ไขแล้ว
            form = PersonForm(post_copy, instance=instance)
        
        if form.is_valid():
            person = form.save(commit=False)
            
            # ถ้าเป็นผู้ใช้ธรรมดา คืนค่าเดิมของฟิลด์ที่ไม่อนุญาตให้แก้ไข
            if is_regular_user and instance:
                for field_name, value in original_values.items():
                    setattr(person, field_name, value)
            # ถ้าเป็น admin แต่ไม่ใช่ superuser ไม่สามารถแก้ไขเงินเดือนได้
            elif (is_admin or is_accountant) and not is_super and instance:
                person.salary = original_values.get('salary', instance.salary)
            
            # ถ้าเป็นการเพิ่มพนักงานใหม่
            if not person.id:
                # ตรวจสอบสิทธิ์อีกครั้ง
                if not has_admin_rights:
                    return HttpResponseForbidden("ไม่มีสิทธิ์เพิ่มพนักงานใหม่")
                
                # สร้างบัญชีผู้ใช้
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                
                try:
                    user = User.objects.create_user(
                        username=username,
                        password=password,
                        first_name=person.first_name,
                        last_name=person.last_name
                    )
                    
                    person.user = user
                    
                    # บันทึกข้อมูลพนักงาน
                    person.save()
                    
                    # บันทึก log การเพิ่มพนักงาน
                    log_activity(request, 'employee', 'เพิ่มพนักงาน', 
                                f'เพิ่มพนักงานใหม่: {person.first_name} {person.last_name} ตำแหน่ง: {person.get_thai_role()}', 
                                person)
                    
                    messages.success(request, 'บันทึกข้อมูลพนักงานสำเร็จ')
                except Exception as e:
                    log_activity(request, 'employee', 'ข้อผิดพลาดในการเพิ่มพนักงาน', str(e))
                    messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
            else:
                try:
                    # เก็บข้อมูลเดิมเพื่อเปรียบเทียบการเปลี่ยนแปลง
                    old_data = {
                        'first_name': instance.first_name,
                        'last_name': instance.last_name,
                        'role': instance.get_thai_role(),
                        'salary': instance.salary
                    }
                    
                    # บันทึกข้อมูลพนักงาน
                    person.save()
                    
                    # บันทึก log การแก้ไขพนักงาน
                    changes = []
                    if old_data['first_name'] != person.first_name or old_data['last_name'] != person.last_name:
                        changes.append(f'ชื่อ: {old_data["first_name"]} {old_data["last_name"]} -> {person.first_name} {person.last_name}')
                    
                    if old_data['role'] != person.get_thai_role():
                        changes.append(f'ตำแหน่ง: {old_data["role"]} -> {person.get_thai_role()}')
                    
                    if old_data['salary'] != person.salary:
                        changes.append(f'ค่าจ้าง: {old_data["salary"]} -> {person.salary}')
                    
                    changes_text = ', '.join(changes) if changes else 'ไม่มีการเปลี่ยนแปลงที่สำคัญ'
                    
                    log_activity(request, 'employee', 'แก้ไขพนักงาน', 
                                f'แก้ไขข้อมูล: {person.first_name} {person.last_name}, รายละเอียด: {changes_text}', 
                                person)
                    
                    messages.success(request, 'บันทึกข้อมูลพนักงานสำเร็จ')
                    
                    # ถ้าเป็นการแก้ไขข้อมูลส่วนตัว หรือผู้ใช้ทั่วไป ให้กลับไปที่หน้า dashboard แทน
                    if is_profile_edit or is_regular_user:
                        return redirect('dashboard')
                    
                except Exception as e:
                    log_activity(request, 'employee', 'ข้อผิดพลาดในการแก้ไขพนักงาน', str(e))
                    messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
            
            # กลับไปที่หน้ารายการพนักงาน (เฉพาะ admin/superuser)
            if has_admin_rights and not is_profile_edit:
                return redirect('employee_list')
            else:
                return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'ข้อผิดพลาดในฟิลด์ {field}: {error}')
            
            log_activity(request, 'employee', 'ข้อผิดพลาดในการบันทึกพนักงาน', 
                        f'ข้อผิดพลาดในฟอร์ม: {form.errors}')
    else:
        form = PersonForm(instance=instance)
    
    # ส่งค่าสิทธิ์ไปที่ template
    context = {
        'form': form,
        'is_superuser': is_super,
        'has_admin_rights': has_admin_rights,
        'is_regular_user': is_regular_user,
        'person': instance,
        'debug': is_super,  # เปิด debug เพื่อตรวจสอบค่าตัวแปร (อาจลบออกในเวอร์ชัน production)
    }
    
    return render(request, 'form.html', context)

@login_required
def employee_add(request):
    """
    เพิ่มพนักงานใหม่ (เรียกใช้ employee_form โดยไม่ส่ง person_id)
    """
    # ตรวจสอบสิทธิ์ - เฉพาะ admin และ superuser เท่านั้น
    has_admin_rights = check_admin_rights(request.user)
    
    if not has_admin_rights:
        return HttpResponseForbidden("ไม่มีสิทธิ์เพิ่มพนักงานใหม่")
        
    return employee_form(request)

@login_required
def employee_edit(request, person_id):
    """
    แก้ไขข้อมูลพนักงาน (เรียกใช้ employee_form โดยส่ง person_id)
    """
    # ตรวจสอบว่าผู้ใช้สามารถแก้ไขพนักงานคนนี้ได้หรือไม่
    has_admin_rights = check_admin_rights(request.user)
    
    # ถ้าเป็น admin สามารถแก้ไขได้
    if has_admin_rights:
        return employee_form(request, person_id)
    
    # ถ้าเป็นผู้ใช้ทั่วไป ตรวจสอบว่าเป็นข้อมูลของตัวเองหรือไม่
    try:
        person = Person.objects.get(user=request.user)
        if str(person.id) == str(person_id):
            return employee_form(request, person_id)
    except Person.DoesNotExist:
        pass
    
    # ไม่มีสิทธิ์เข้าถึง
    return HttpResponseForbidden("ไม่มีสิทธิ์แก้ไขข้อมูลของผู้อื่น")

@login_required
def employee_profile_edit(request):
    """
    แก้ไขข้อมูลส่วนตัวของพนักงานที่ล็อกอิน
    """
    try:
        person = Person.objects.get(user=request.user)
        # บันทึกการเข้าแก้ไขข้อมูลส่วนตัว
        log_activity(request, 'employee', 'เข้าหน้าแก้ไขข้อมูลส่วนตัว')
        # ส่งพารามิเตอร์ is_profile_edit=True เพื่อบอกว่านี่คือการแก้ไขโปรไฟล์
        response = employee_form(request, person.id, is_profile_edit=True)
        return response
    except Person.DoesNotExist:
        log_activity(request, 'employee', 'ข้อผิดพลาด', 'ไม่พบข้อมูลพนักงานของผู้ใช้')
        messages.error(request, 'ไม่พบข้อมูลพนักงาน')
        return redirect('dashboard')

@login_required
def employee_delete(request, person_id):
    """
    ลบข้อมูลพนักงาน
    """
    # ตรวจสอบสิทธิ์ - เฉพาะ superuser เท่านั้น
    if not request.user.is_superuser:
        return HttpResponseForbidden("ไม่มีสิทธิ์ลบข้อมูลพนักงาน")
        
    try:
        person = get_object_or_404(Person, id=person_id)
        
        # เก็บข้อมูลชื่อเพื่อแสดงข้อความ
        display_name = f"{person.title} {person.first_name} {person.last_name}"
        position = person.get_thai_role()
        
        # บันทึก log ก่อนลบข้อมูล
        log_activity(request, 'employee', 'ลบพนักงาน', 
                    f'ลบพนักงาน: {display_name}, ตำแหน่ง: {position}')
        
        # ลบบัญชีผู้ใช้ที่เชื่อมโยง (ถ้ามี)
        if person.user:
            user = person.user
            person.user = None
            person.save()
            user.delete()
        
        # ลบข้อมูลพนักงาน
        person.delete()
        
        messages.success(request, f'ลบข้อมูลพนักงาน {display_name} เรียบร้อยแล้ว')
    except Exception as e:
        log_activity(request, 'employee', 'ข้อผิดพลาดในการลบพนักงาน', str(e))
        messages.error(request, f'เกิดข้อผิดพลาดในการลบพนักงาน: {str(e)}')
    
    return redirect('employee_list')