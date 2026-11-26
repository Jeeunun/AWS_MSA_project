import json
import jwt
import requests
from django.conf import settings
from django.core.cache import cache
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

class CognitoJWTAuthentication(BaseAuthentication):
    """AWS Cognito JWT 토큰 인증 클래스"""
    
    def __init__(self):
        self.region = getattr(settings, 'AWS_REGION', 'ap-northeast-2')
        self.user_pool_id = getattr(settings, 'AWS_USER_POOL_ID', 'ap-northeast-2_klXPNN9TV')
        self.user_pool_client_id = getattr(settings, 'AWS_USER_POOL_CLIENT_ID', '31rhkv9td4eq8ba3sqhur2ap0q')
        self.jwks_url = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"
    
    def get_public_keys(self):
        """JWKS에서 공개키 가져오기"""
        cache_key = f"cognito_jwks_{self.user_pool_id}"
        jwks = cache.get(cache_key)
        
        if not jwks:
            try:
                response = requests.get(self.jwks_url, timeout=10)
                response.raise_for_status()
                jwks = response.json()
                # 1시간 동안 캐시
                cache.set(cache_key, jwks, 3600)
            except Exception as e:
                raise AuthenticationFailed(f'JWKS 가져오기 실패: {str(e)}')
        
        return jwks
    
    def decode_cognito_jwt(self, token):
        """Cognito JWT 토큰 디코딩 및 검증"""
        try:
            # 헤더만 디코딩하여 kid 확인
            header = jwt.get_unverified_header(token)
            kid = header.get('kid')
            
            if not kid:
                raise AuthenticationFailed('JWT 헤더에 kid가 없습니다.')
            
            # 공개키 가져오기
            jwks = self.get_public_keys()
            public_key = None
            
            for key in jwks['keys']:
                if key['kid'] == kid:
                    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
                    break
            
            if not public_key:
                raise AuthenticationFailed('일치하는 공개키를 찾을 수 없습니다.')
            
            # 토큰 검증 및 디코딩
            payload = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=self.user_pool_client_id,
                issuer=f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}"
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('JWT 토큰이 만료되었습니다.')
        except jwt.InvalidTokenError as e:
            raise AuthenticationFailed(f'유효하지 않은 JWT 토큰: {str(e)}')
        except Exception as e:
            raise AuthenticationFailed(f'JWT 디코딩 실패: {str(e)}')
    
    def authenticate(self, request):
        """인증 처리"""
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header:
            return None
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = self.decode_cognito_jwt(token)
            cognito_user_id = payload.get('sub')
            username = payload.get('cognito:username')
            email = payload.get('email')
            name = payload.get('name')
            
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
            
            user = AuthenticatedUser(username, username, email or '', name or username)
            return (user, token)
            
        except AuthenticationFailed as auth_error:
            raise
        except Exception as e:
            raise AuthenticationFailed(f'인증 처리 실패: {str(e)}')

