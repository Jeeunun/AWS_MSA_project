# ⚾ 야구 커뮤니티 게시판

야구팬들을 위한 자유로운 소통 공간입니다. 구단별 게시판, 동행/거래 게시판, 공지사항 등 다양한 카테고리로 구성되어 있습니다.

## 🚀 주요 기능

### 📋 게시판 시스템
- **다층 카테고리 구조**: 공통게시판, 구단별 게시판, 자유게시판
- **14개 세부 카테고리**: 동행, 거래, 공지사항, 자유 + 10개 구단별 게시판
- **실시간 게시글 수 표시**: 각 카테고리별 게시글 개수 확인

### 🔍 검색 기능
- **다중 검색 옵션**: 제목, 내용, 작성자, 전체 검색
- **실시간 검색 결과**: 검색된 게시글 수 표시
- **검색 초기화**: 원클릭으로 검색 조건 해제

### 📌 게시글 고정 시스템
- **전체 공지 고정**: 모든 게시판 상단에 표시
- **카테고리별 고정**: 해당 게시판에만 고정 표시
- **일괄 고정 기능**: 체크박스로 다중 선택 후 일괄 처리
- **고정 해제**: 언제든지 고정 상태 해제 가능

### 🎨 사용자 인터페이스
- **반응형 디자인**: 다양한 화면 크기에 최적화
- **구단별 색상 테마**: 각 구단별 고유 색상 적용
- **컴팩트한 레이아웃**: 효율적인 공간 활용
- **직관적인 네비게이션**: 사이드바 기반 카테고리 필터링

## 🛠 기술 스택

### Backend
- **Django 4.x**: 웹 프레임워크
- **SQLite**: 데이터베이스 (개발용)
- **Python 3.x**: 프로그래밍 언어

### Frontend
- **HTML5/CSS3**: 마크업 및 스타일링
- **JavaScript (ES6+)**: 동적 인터랙션
- **CSS Grid/Flexbox**: 레이아웃 시스템

### 보안
- **CSRF 보호**: 모든 POST 요청에 CSRF 토큰 적용
- **XSS 방지**: Django 템플릿 엔진의 자동 이스케이핑

## 📁 프로젝트 구조

```
board-service/
├── board/                          # 메인 애플리케이션
│   ├── models.py                   # 데이터베이스 모델
│   ├── views.py                    # 뷰 로직
│   ├── forms.py                    # 폼 정의
│   ├── urls.py                     # URL 라우팅
│   ├── templates/board/            # HTML 템플릿
│   │   ├── post_list.html         # 게시글 목록 페이지
│   │   ├── post_detail.html       # 게시글 상세 페이지
│   │   ├── post_form.html         # 게시글 작성/수정 페이지
│   │   └── post_confirm_delete.html # 삭제 확인 페이지
│   └── templatetags/              # 커스텀 템플릿 태그
│       └── board_extras.py        # 템플릿 필터
├── board_service/                  # 프로젝트 설정
│   ├── settings.py                # Django 설정
│   └── urls.py                    # 메인 URL 설정
└── manage.py                      # Django 관리 명령어
```

## 🚀 설치 및 실행

### 1. 환경 설정
```bash
# 가상환경 생성 및 활성화
python -m venv vir_env
source vir_env/bin/activate  # Windows: vir_env\Scripts\activate

# 필요한 패키지 설치
pip install django
```

### 2. 데이터베이스 설정
```bash
# 마이그레이션 생성 및 적용
python manage.py makemigrations
python manage.py migrate
```

### 3. 서버 실행
```bash
# 개발 서버 시작
python manage.py runserver
```

### 4. 접속
브라우저에서 `http://localhost:8000/board/` 접속

## 📊 데이터베이스 모델

### Post 모델
```python
class Post(models.Model):
    title = models.CharField(max_length=200)        # 제목
    content = models.TextField()                    # 내용
    author = models.CharField(max_length=100)       # 작성자
    category = models.CharField(max_length=20)      # 카테고리
    created_at = models.DateTimeField(auto_now_add=True)  # 작성일
    updated_at = models.DateTimeField(auto_now=True)      # 수정일
    views = models.IntegerField(default=0)          # 조회수
    is_pinned = models.BooleanField(default=False)  # 고정 여부
    pin_type = models.CharField(max_length=20)      # 고정 타입
    pin_category = models.CharField(max_length=20)  # 고정 카테고리
```

### 카테고리 구조
- **공통게시판**: 동행, 거래, 공지사항
- **구단별 게시판**: KIA, 삼성, LG, 두산, KT, SSG, 롯데, 한화, NC, 키움
- **자유게시판**: 자유

## 🔧 주요 기능 상세

### 게시글 고정 시스템
1. **개별 고정**: 각 게시글의 고정해제 버튼으로 개별 처리
2. **일괄 고정**: 체크박스로 다중 선택 후 일괄 처리
3. **고정 타입**: 전체 공지 / 카테고리별 고정 선택 가능
4. **시각적 구분**: 고정된 게시글은 노란색 배경으로 표시

### 검색 시스템
1. **검색 타입 선택**: 드롭다운으로 검색 범위 지정
2. **실시간 결과**: 검색된 게시글 수 즉시 표시
3. **검색 조건 유지**: 페이지 이동 시에도 검색 조건 유지
4. **초기화 기능**: 원클릭으로 검색 조건 해제

### 카테고리 필터링
1. **계층적 네비게이션**: 메인 그룹과 서브 카테고리 구조
2. **실시간 카운트**: 각 카테고리별 게시글 수 표시
3. **활성 상태 표시**: 현재 선택된 카테고리 하이라이트
4. **토글 기능**: 서브메뉴 접기/펼치기

## 🎨 UI/UX 특징

### 반응형 디자인
- **Flexbox/Grid**: 현대적인 CSS 레이아웃
- **컴팩트한 여백**: 효율적인 공간 활용
- **일관된 색상**: 구단별 테마 색상 적용

### 사용자 경험
- **직관적인 네비게이션**: 사이드바 기반 카테고리 필터
- **시각적 피드백**: 호버 효과, 활성 상태 표시
- **접근성**: 키보드 네비게이션 지원

## 🔒 보안 기능

### CSRF 보호
- 모든 POST 요청에 CSRF 토큰 적용
- JavaScript를 통한 동적 폼 생성 시에도 토큰 포함
- 악의적인 교차 사이트 요청 위조 공격 방지

### 데이터 검증
- Django 폼을 통한 서버 사이드 검증
- 클라이언트 사이드 JavaScript 검증
- XSS 공격 방지를 위한 자동 이스케이핑

## 📈 향후 개발 계획

### 단기 계획
- [ ] 사용자 인증 시스템 (로그인/회원가입)
- [ ] 게시글 댓글 기능
- [ ] 파일 업로드 기능
- [ ] 게시글 추천/비추천 기능

### 중기 계획
- [ ] 실시간 알림 시스템
- [ ] 모바일 앱 개발
- [ ] 관리자 대시보드
- [ ] 통계 및 분석 기능

### 장기 계획
- [ ] AWS 클라우드 배포
- [ ] 마이크로서비스 아키텍처 전환
- [ ] API Gateway 및 Cognito 연동
- [ ] 컨테이너화 및 오케스트레이션

## 🤝 기여하기

1. 이 저장소를 포크합니다
2. 새로운 기능 브랜치를 생성합니다 (`git checkout -b feature/AmazingFeature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/AmazingFeature`)
5. Pull Request를 생성합니다

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해 주세요.

---

**⚾ 야구 커뮤니티에서 즐거운 소통을 나누세요!** 🎉 
