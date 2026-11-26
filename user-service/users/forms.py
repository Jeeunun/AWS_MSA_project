from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from .models import User

# ✅ 공용 팀 선택지 (회원가입/프로필 수정에서 함께 사용)
TEAM_CHOICES = [
    ('', '선택 안함'),
    ('LG', 'LG'), ('한화', '한화'), ('롯데', '롯데'), ('KIA', 'KIA'), ('SSG', 'SSG'),
    ('KT', 'KT'), ('NC', 'NC'), ('삼성', '삼성'), ('두산', '두산'), ('키움', '키움'),
]


class SignupForm(UserCreationForm):
    last_name = forms.CharField(
        label="성",
        max_length=1,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': '예: 김'})
    )
    first_name = forms.CharField(
        label="이름",
        max_length=2,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': '예: 지수'})
    )

    username = forms.CharField(label="아이디")
    email = forms.EmailField(label="이메일", required=True)
    tel = forms.CharField(
        label="전화번호",
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': '예: 01012345678',
            'pattern': '[0-9]+',   # 숫자만 허용
            'title': '숫자만 입력 가능합니다.'
        })
    )


    birth = forms.CharField(
        label="주민번호 앞 6자리",
        required=True,
        max_length=6,
        widget=forms.TextInput(attrs={'maxlength': '6'}),
        help_text="예: 990101 - 1"
    )
    gender_code = forms.CharField(
        label="뒷 첫자리",
        required=True,
        max_length=1,
        widget=forms.TextInput(attrs={'maxlength': '1'}),
        help_text="1, 2, 3, 4 중 하나"
    )

    # ⬇️ 드롭다운 선택
    team = forms.ChoiceField(label="응원팀", choices=TEAM_CHOICES, required=False)

    class Meta:
        model = User
        fields = (
            'last_name', 'first_name', 'username', 'password1', 'password2',
            'email', 'tel', 'birth', 'gender_code', 'team'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 비밀번호 조건 문구 한글로
        self.fields['password1'].help_text = (
            "비밀번호는 최소 8자 이상이어야 하며, 숫자나 문자를 포함해야 합니다."
        )
        self.fields['password2'].help_text = "위와 동일한 비밀번호를 입력해주세요."

    def clean_gender_code(self):
        code = self.cleaned_data.get("gender_code")
        if code not in ['1', '2', '3', '4']:
            raise forms.ValidationError("성별 코드는 1, 2, 3, 4 중 하나여야 합니다.")
        return code

    def save(self, commit=True):
        user = super().save(commit=False)

        # 성별 자동 설정
        gender_code = self.cleaned_data.get("gender_code")
        if gender_code in ['1', '3']:
            user.gender = '남'
        elif gender_code in ['2', '4']:
            user.gender = '여'

        if commit:
            user.save()
        return user


# ✅ 로그인 에러 메시지를 한글로 바꾸는 커스텀 로그인 폼
class CustomLoginForm(AuthenticationForm):
    error_messages = {
        'invalid_login': "아이디 또는 비밀번호가 올바르지 않습니다.",
        'inactive': "이 계정은 비활성화 상태입니다.",
    }


# ✅ 내 정보 수정 폼 (응원팀 드롭다운 선택)
class ProfileForm(forms.ModelForm):
    team = forms.ChoiceField(label="응원팀", choices=TEAM_CHOICES, required=False)

    class Meta:
        model = User
        # username은 보통 수정 금지, birth/gender는 주민번호 파생값이라 수정 제외
        fields = ['name', 'email', 'tel', 'team']
        labels = {
            'name': '이름',
            'email': '이메일',
            'tel': '전화번호',
            'team': '응원팀',
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 새 비밀번호 조건 한글로
        self.fields['new_password1'].help_text = "비밀번호는 최소 8자 이상이어야 하며, 숫자나 문자를 포함해야 합니다."
        self.fields['new_password2'].help_text = "위와 동일한 비밀번호를 입력해주세요."
