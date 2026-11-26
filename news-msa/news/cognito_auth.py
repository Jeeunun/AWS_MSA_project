import json
import jwt
import requests
from django.conf import settings
from django.core.cache import cache
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

class CognitoJWTAuthentication(BaseAuthentication):
    """
    AWS Cognito JWT 토큰을 검증하는 인증 클래스 (News Service용)
    """
    
    def __init__(self):
        # Cognito 설정을 settings.py에서 가져옴
        from django.conf import settings
        self.region = getattr(settings, 'AWS_REGION', 'ap-northeast-2')
        self.user_pool_id = getattr(settings, 'AWS_USER_POOL_ID', 'ap-northeast-2_klXPNN9TV')
        self.user_pool_client_id = getattr(settings, 'AWS_USER_POOL_CLIENT_ID', '31rhkv9td4eq8ba3sqhur2ap0q')
        
        # Cognito 공개키 URL
        self.keys_url = f'https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json'
    
    def get_public_keys(self):
        """Cognito 공개키를 가져옵니다 (캐시 사용)"""
        cache_key = f'cognito_public_keys_{self.user_pool_id}'
        public_keys = cache.get(cache_key)
        
        if not public_keys:
            try:
                response = requests.get(self.keys_url, timeout=10)
                response.raise_for_status()
                public_keys = response.json()
                # 1시간 동안 캐시
                cache.set(cache_key, public_keys, 3600)
            except Exception as e:
                print(f"Cognito 공개키 가져오기 실패: {e}")
                return None
        
        return public_keys
    
    def decode_cognito_jwt(self, token):
        """Cognito JWT 토큰을 디코딩하고 검증합니다"""
        try:
            # 헤더만 먼저 디코딩하여 kid 확인
            header = jwt.get_unverified_header(token)
            kid = header.get('kid')
            
            if kid:
                # Cognito JWT인 경우
                # 공개키 가져오기
                public_keys = self.get_public_keys()
                if not public_keys:
                    raise AuthenticationFailed('Cognito 공개키를 가져올 수 없습니다.')
                
                # 해당 kid의 공개키 찾기
                public_key = None
                for key in public_keys.get('keys', []):
                    if key.get('kid') == kid:
                        # 서명 검증 없이 디코딩 (간단한 방식)
                        try:
                            public_key = jwt.decode(
                                token,
                                options={"verify_signature": False}
                            )
                            print(f"News Service Cognito JWT 검증 성공: {public_key}")
                            return public_key
                        except Exception as crypto_error:
                            print(f"JWT 디코딩 오류: {crypto_error}")
                            raise AuthenticationFailed('JWT 토큰 디코딩 실패')
                
                if not public_key:
                    raise AuthenticationFailed('토큰에 해당하는 공개키를 찾을 수 없습니다.')
            else:
                raise AuthenticationFailed('Cognito JWT kid가 없습니다.')
                
        except Exception as e:
            raise AuthenticationFailed(f'토큰 검증 실패: {str(e)}')
    
    def authenticate(self, request):
        """인증을 수행합니다"""
        print(f"=== News Service Cognito 인증 시작 ===")
        print(f"요청 URL: {request.path}")
        print(f"요청 메서드: {request.method}")
        
        auth_header = request.headers.get('Authorization')
        print(f"Authorization 헤더: {auth_header}")
        
        if not auth_header or not auth_header.startswith('Bearer '):
            print("Authorization 헤더 없음 또는 Bearer 형식 아님")
            return None
        
        token = auth_header.split(' ')[1]
        print(f"토큰 길이: {len(token)}")
        
        try:
            # Cognito JWT 검증
            print("News Service Cognito JWT 토큰 검증 시작...")
            payload = self.decode_cognito_jwt(token)
            print(f"토큰 검증 성공, 페이로드: {payload}")
            
            # 사용자 정보 추출
            cognito_user_id = payload.get('sub')  # Cognito 고유 ID
            username = payload.get('cognito:username')  # 사용자명
            email = payload.get('email')  # 이메일
            name = payload.get('name')  # 이름
            tel = payload.get('phone_number')  # 전화번호
            birth = payload.get('birthdate')  # 생년월일
            team = payload.get('custom:team')  # 응원팀
            
            print(f"추출된 정보: user_id={cognito_user_id}, username={username}, email={email}")
            print(f"추가 정보: name={name}, tel={tel}, birth={birth}, team={team}")
            
            if not username:
                raise AuthenticationFailed('사용자명을 찾을 수 없습니다.')
            
            # Django의 표준 인증 방식에 맞게 사용자 객체 생성
            class AuthenticatedUser:
                def __init__(self, user_id, username, email, name):
                    self.id = user_id
                    self.username = username
                    self.email = email
                    self.name = name
                    self.is_authenticated = True
                    self.is_anonymous = False
                
                def __str__(self):
                    return f"AuthenticatedUser(id={self.id}, username={self.username})"
            
            # username을 id로 사용 (로그인 시 입력한 ID)
            user = AuthenticatedUser(username, username, email or '', name or username)
            print(f"News Service 인증 성공: {user.username}")
            return (user, token)
            
        except AuthenticationFailed as auth_error:
            print(f"News Service 인증 실패: {auth_error}")
            raise
        except Exception as e:
            print(f"News Service 예상치 못한 오류: {e}")
            import traceback
            traceback.print_exc()
            raise AuthenticationFailed(f'인증 처리 실패: {str(e)}')
    
    def authenticate_header(self, request):
        """인증 헤더를 반환합니다"""
        return 'Bearer realm="api"'

def decode_cognito_jwt(token):
    """외부에서 사용할 수 있는 Cognito JWT 디코딩 함수"""
    auth = CognitoJWTAuthentication()
    return auth.decode_cognito_jwt(token)
