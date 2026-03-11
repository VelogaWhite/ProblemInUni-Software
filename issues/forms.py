from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
import re

class RegisterForm(UserCreationForm):
    email = forms.EmailField(label="Email", required=True, help_text="example: s640101234567@email.kmutnb.ac.th")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # ตรวจสอบรูปแบบอีเมล s[student_id]@email.kmutnb.ac.th
            # s ตามด้วยตัวเลข (student_id)
            pattern = r'^s\d+@email\.kmutnb\.ac\.th$'
            if not re.match(pattern, email):
                raise forms.ValidationError("ต้องใช้อีเมลมหาวิทยาลัยเท่านั้น (s[รหัสนักศึกษา]@email.kmutnb.ac.th)")
            
            # ตรวจสอบว่าอีเมลซ้ำหรือไม่
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("อีเมลนี้มีผู้ใช้งานแล้ว")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # ตรวจสอบรูปแบบ username s[student_id]
            pattern = r'^s\d+$'
            if not re.match(pattern, username):
                raise forms.ValidationError("Username ต้องเป็น s ตามด้วยรหัสนักศึกษา")
        return username

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        email = cleaned_data.get("email")

        if username and email:
            # ตรวจสอบความสอดคล้องระหว่าง Username และ Email
            email_prefix = email.split('@')[0]
            if username != email_prefix:
                raise forms.ValidationError("Username ต้องตรงกับรหัสนักศึกษาในอีเมล")
        
        return cleaned_data