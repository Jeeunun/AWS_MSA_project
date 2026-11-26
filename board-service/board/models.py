from django.db import models

# Create your models here.
from django.utils import timezone # 날짜/시간 필드 사용을 위해 추가

class Post(models.Model):
    CATEGORY_CHOICES = [
        # 공통 게시판
        ('companion', '야구동행'),
        ('trade', '티켓거래'),
        ('notice', '공지사항'),
        
        # KBO 구단별 게시판
        ('kia', 'KIA 타이거즈'),
        ('samsung', '삼성 라이온즈'),
        ('lg', 'LG 트윈스'),
        ('doosan', '두산 베어스'),
        ('kt', 'KT 위즈'),
        ('ssg', 'SSG 랜더스'),
        ('lotte', '롯데 자이언츠'),
        ('hanwha', '한화 이글스'),
        ('nc', 'NC 다이노스'),
        ('kiwoom', '키움 히어로즈'),
        
        # 자유게시판
        ('free', '자유게시판'),
    ]
    
    # 고정 타입 선택
    PIN_TYPE_CHOICES = [
        ('none', '고정 안함'),
        ('global', '전체 공지'),
        ('category', '게시판별 고정'),
    ]
    
    # 카테고리 그룹핑을 위한 헬퍼 메서드
    @classmethod
    def get_category_groups(cls):
        return {
            'common': [
                ('companion', '야구동행'),
                ('trade', '티켓거래'),
                ('notice', '공지사항'),
            ],
            'teams': [
                ('kia', 'KIA 타이거즈'),
                ('samsung', '삼성 라이온즈'),
                ('lg', 'LG 트윈스'),
                ('doosan', '두산 베어스'),
                ('kt', 'KT 위즈'),
                ('ssg', 'SSG 랜더스'),
                ('lotte', '롯데 자이언츠'),
                ('hanwha', '한화 이글스'),
                ('nc', 'NC 다이노스'),
                ('kiwoom', '키움 히어로즈'),
            ],
            'free': [
                ('free', '자유게시판'),
            ]
        }
    
    title = models.CharField(max_length=200, verbose_name="제목")
    content = models.TextField(verbose_name="내용")
    author = models.CharField(max_length=20, verbose_name="작성자")
    # MSA 환경을 위한 사용자 ID 필드 (Cognito User ID)
    user_id = models.CharField(max_length=70, blank=True, null=True, verbose_name="사용자 ID")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='free', verbose_name="카테고리")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="작성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    views = models.IntegerField(default=0, verbose_name="조회수")
    
    # 고정 기능을 위한 필드들
    is_pinned = models.BooleanField(default=False, verbose_name="고정 여부")
    pin_type = models.CharField(max_length=20, choices=PIN_TYPE_CHOICES, default='none', verbose_name="고정 타입")
    pin_category = models.CharField(max_length=20, blank=True, null=True, verbose_name="고정할 카테고리")

    def __str__(self):
        return f'[{self.category}] {self.title}'

    class Meta:
        ordering = ['-is_pinned', '-created_at'] # 고정된 글이 위에, 최신 글이 위에 오도록 정렬
        verbose_name = "게시물"
        verbose_name_plural = "게시물"

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name="게시물")
    author = models.CharField(max_length=20, verbose_name="작성자")
    # MSA 환경을 위한 사용자 ID 필드 (Cognito User ID)
    user_id = models.CharField(max_length=70, blank=True, null=True, verbose_name="사용자 ID")
    content = models.TextField(verbose_name="내용")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="작성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    def __str__(self):
        return f'{self.author}님의 댓글 on "{self.post.title}"'

    class Meta:
        ordering = ['created_at'] # 오래된 댓글이 위에 오도록 정렬
        verbose_name = "댓글"
        verbose_name_plural = "댓글"
