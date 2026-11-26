from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Post, Comment
from .serializers import PostSerializer, PostCreateSerializer, PostUpdateSerializer, CommentSerializer, CommentCreateSerializer
import jwt
from django.conf import settings

def get_user_from_token(request):
    """Cognito JWT 토큰에서 사용자 정보 추출"""
    print(f"=== get_user_from_token 호출됨 ===")
    
    # request.user가 이미 CognitoJWTAuthentication에서 인증된 경우
    if hasattr(request, 'user') and request.user.is_authenticated:
        print(f"인증된 사용자: {request.user.username}")
        return request.user.id, request.user.username
    
    # fallback: 직접 토큰 디코딩
    auth_header = request.headers.get('Authorization')
    print(f"Authorization 헤더: {auth_header}")
    
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        print(f"토큰 추출됨: {token[:20]}...")
        try:
            from .cognito_auth import decode_cognito_jwt
            payload = decode_cognito_jwt(token)
            print(f"Cognito JWT 디코딩 성공: {payload}")
            user_id = payload.get('sub')
            username = payload.get('cognito:username')
            print(f"추출된 정보: user_id={user_id}, username={username}")
            return user_id, username
        except Exception as e:
            print(f"Cognito JWT 디코딩 실패: {e}")
            return None, None
    else:
        print("Authorization 헤더가 없거나 Bearer 형식이 아님")
    return None, None

@api_view(['GET'])
@permission_classes([AllowAny])
def post_list_api(request):
    """게시글 목록 API (페이징 적용)"""
    from rest_framework.pagination import PageNumberPagination
    
    category = request.GET.get('category', '')
    search_query = request.GET.get('search', '')
    
    posts = Post.objects.all()
    
    # 카테고리 필터링
    if category:
        posts = posts.filter(category=category)
    
    # 검색 기능
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(author__icontains=search_query)
        )
    
    # 고정된 게시글들 먼저 가져오기 (페이징 제외)
    pinned_posts = posts.filter(is_pinned=True).order_by('-created_at')
    
    # 일반 게시글들에 페이징 적용
    normal_posts = posts.filter(is_pinned=False).order_by('-created_at')
    
    # 페이징 적용
    paginator = PageNumberPagination()
    paginator.page_size = 10
    
    # 고정 게시글은 페이징에서 제외하고, 일반 게시글만 페이징
    paginated_normal_posts = paginator.paginate_queryset(normal_posts, request)
    
    # 시리얼라이징
    pinned_serializer = PostSerializer(pinned_posts, many=True)
    normal_serializer = PostSerializer(paginated_normal_posts, many=True)
    
    return paginator.get_paginated_response({
        'pinned_posts': pinned_serializer.data,
        'normal_posts': normal_serializer.data,
        'total_count': posts.count()
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def post_detail_api(request, pk):
    """게시글 상세 API"""
    post = get_object_or_404(Post, pk=pk)
    
    # 조회수 증가
    post.views = post.views + 1
    post.save()
    
    serializer = PostSerializer(post)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_create_api(request):
    """게시글 작성 API"""
    try:
        print(f"=== 게시글 작성 API 호출됨 ===")
        print(f"요청 메서드: {request.method}")
        print(f"요청 URL: {request.path}")
        print(f"요청 데이터: {request.data}")
        print(f"요청 헤더: {dict(request.headers)}")
        
        # 사용자 정보 가져오기
        user_id, username = get_user_from_token(request)
        print(f"인증된 사용자: {username} (ID: {user_id})")
        
        # 게시글 데이터 검증
        serializer = PostCreateSerializer(data=request.data)
        if not serializer.is_valid():
            print(f"시리얼라이저 검증 실패: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # 게시글 생성
        post = serializer.save(
            author=username,
            user_id=user_id
        )
        
        print(f"게시글 생성 성공: ID={post.id}, 제목={post.title}")
        
        # 생성된 게시글 반환
        return Response(PostSerializer(post).data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f"=== 500 에러 발생: {e} ===")
        import traceback
        traceback.print_exc()
        return Response({'error': f'서버 오류: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def post_update_api(request, pk):
    """게시글 수정 API"""
    post = get_object_or_404(Post, pk=pk)
    user_id, username = get_user_from_token(request)
    
    # 작성자 확인
    if post.user_id != user_id:
        return Response({'error': '수정 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = PostUpdateSerializer(post, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(PostSerializer(post).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def post_delete_api(request, pk):
    """게시글 삭제 API"""
    post = get_object_or_404(Post, pk=pk)
    user_id, username = get_user_from_token(request)
    
    # 작성자 확인
    if post.user_id != user_id:
        return Response({'error': '삭제 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
    
    post.delete()
    return Response({'message': '게시글이 삭제되었습니다.'}, status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def comment_create_api(request, post_pk):
    """댓글 작성 API"""
    try:
        post = get_object_or_404(Post, pk=post_pk)
        
        user_id, username = get_user_from_token(request)
        
        if not user_id or not username:
            print("사용자 정보 없음")
            return Response({'error': '사용자 정보를 가져올 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = CommentCreateSerializer(data=request.data)
        print(f"시리얼라이저 데이터: {serializer.initial_data}")
        
        if serializer.is_valid():
            print("시리얼라이저 검증 성공")
            comment = serializer.save(
                post=post,
                author=username,
                user_id=user_id
            )
            print(f"댓글 생성 성공: ID={comment.id}, 내용={comment.content}")
            return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
        else:
            print(f"시리얼라이저 검증 실패: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        print(f"=== 댓글 작성 500 에러 발생: {e} ===")
        import traceback
        traceback.print_exc()
        return Response({'error': f'서버 오류: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def comment_update_api(request, post_pk, comment_pk):
    """댓글 수정 API"""
    try:
        print(f"=== 댓글 수정 API 호출됨 ===")
        print(f"요청 메서드: {request.method}")
        print(f"요청 URL: {request.path}")
        print(f"요청 데이터: {request.data}")
        
        post = get_object_or_404(Post, pk=post_pk)
        comment = get_object_or_404(Comment, pk=comment_pk, post=post)
        print(f"댓글 찾음: ID={comment.id}, 내용={comment.content}")
        
        user_id, username = get_user_from_token(request)
        print(f"사용자 정보: user_id={user_id}, username={username}")
        
        # 작성자 확인
        if comment.user_id != user_id:
            print("댓글 수정 권한 없음")
            return Response({'error': '댓글 수정 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CommentCreateSerializer(comment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            print(f"댓글 수정 성공: ID={comment.id}")
            return Response(CommentSerializer(comment).data)
        else:
            print(f"시리얼라이저 검증 실패: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        print(f"=== 댓글 수정 500 에러 발생: {e} ===")
        import traceback
        traceback.print_exc()
        return Response({'error': f'서버 오류: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def comment_delete_api(request, post_pk, comment_pk):
    """댓글 삭제 API"""
    try:
        print(f"=== 댓글 삭제 API 호출됨 ===")
        print(f"요청 메서드: {request.method}")
        print(f"요청 URL: {request.path}")
        
        post = get_object_or_404(Post, pk=post_pk)
        comment = get_object_or_404(Comment, pk=comment_pk, post=post)
        print(f"댓글 찾음: ID={comment.id}, 내용={comment.content}")
        
        user_id, username = get_user_from_token(request)
        print(f"사용자 정보: user_id={user_id}, username={username}")
        
        # 작성자 확인
        if comment.user_id != user_id:
            print("댓글 삭제 권한 없음")
            return Response({'error': '댓글 삭제 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        comment.delete()
        print(f"댓글 삭제 성공: ID={comment.id}")
        return Response({'message': '댓글이 삭제되었습니다.'}, status=status.HTTP_204_NO_CONTENT)
        
    except Exception as e:
        print(f"=== 댓글 삭제 500 에러 발생: {e} ===")
        import traceback
        traceback.print_exc()
        return Response({'error': f'서버 오류: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
