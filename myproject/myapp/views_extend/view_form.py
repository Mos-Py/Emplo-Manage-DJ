from django import forms
from django.contrib.auth.models import User
from myapp.models import Person
from myapp.access_control import role_required, admin_required
from myapp.utils import log_activity


@admin_required
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
    
    # กำหนดให้ request เป็นพารามิเตอร์เริ่มต้นที่มีค่าเป็น None
    def __init__(self, *args, request=None, **kwargs):
        # ใช้ super().__init__ ตามปกติ ไม่ต้องทำอะไรกับ request
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