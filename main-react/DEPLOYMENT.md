# 자동 배포 설정 가이드

## GitHub Actions를 통한 자동 빌드 및 S3 배포

이 프로젝트는 GitHub Actions를 사용하여 코드 변경 시 자동으로 빌드하고 S3 버킷에 배포합니다.

### 필요한 GitHub Secrets 설정

GitHub 저장소의 Settings > Secrets and variables > Actions에서 다음 환경 변수들을 설정해야 합니다:

#### 1. AWS 인증 정보
- `AWS_ACCESS_KEY_ID`: AWS IAM 사용자의 액세스 키 ID
- `AWS_SECRET_ACCESS_KEY`: AWS IAM 사용자의 시크릿 액세스 키
- `AWS_REGION`: AWS 리전 (예: us-east-1, ap-northeast-2)

#### 2. S3 버킷 정보
- `S3_BUCKET_NAME`: 배포할 S3 버킷 이름

#### 3. CloudFront 배포 정보 (선택사항)
- `CLOUDFRONT_DISTRIBUTION_ID`: CloudFront 배포 ID (캐시 무효화용)

### AWS IAM 사용자 권한 설정

GitHub Actions에서 사용할 IAM 사용자에게 다음 권한이 필요합니다:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::YOUR-BUCKET-NAME",
                "arn:aws:s3:::YOUR-BUCKET-NAME/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudfront:CreateInvalidation"
            ],
            "Resource": "*"
        }
    ]
}
```

### 워크플로우 동작

1. **main 브랜치에 푸시** 또는 **main 브랜치로 PR 생성** 시 자동 실행
2. Node.js 18 환경에서 의존성 설치
3. ESLint를 통한 코드 품질 검사
4. `npm run build` 명령으로 프로덕션 빌드 생성
5. S3 버킷에 빌드 파일 동기화 (기존 파일 삭제 후 새로 업로드)
6. main 브랜치인 경우 CloudFront 캐시 무효화

### 수동 실행

GitHub Actions 탭에서 "Build and Deploy to S3" 워크플로우를 선택하고 "Run workflow" 버튼을 클릭하여 수동으로 실행할 수 있습니다.

### 문제 해결

- **빌드 실패**: package.json의 의존성 문제나 빌드 스크립트 오류 확인
- **S3 업로드 실패**: AWS 인증 정보와 S3 버킷 권한 확인
- **CloudFront 무효화 실패**: CloudFront 배포 ID와 권한 확인
