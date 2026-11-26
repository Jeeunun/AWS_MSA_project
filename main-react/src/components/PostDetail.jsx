import React, { useState, useEffect, useRef } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import awsConfig from '../config/aws-config';
import '../styles/board-service.css';

const PostDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  
  // 중복 호출 방지를 위한 ref
  const hasFetched = useRef(false);
  
  // 게시글 상태
  const [post, setPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [newComment, setNewComment] = useState('');
  const [editingComment, setEditingComment] = useState(null);
  const [editContent, setEditContent] = useState('');

  // 게시글 데이터 로드
  useEffect(() => {
    // 이미 데이터를 가져온 경우 중단
    if (hasFetched.current) {
      return;
    }
    
    hasFetched.current = true;
    
    const fetchPost = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const token = localStorage.getItem('accessToken');
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
        
        const response = await axios.get(`${awsConfig.API_BASE_URL}/api/board/posts/${id}/`, { headers });
        
        setPost(response.data);
        setComments(response.data.comments || []);
      } catch (err) {
        console.error('게시글 조회 실패:', err);
        setError('게시글을 불러오는데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchPost();
  }, [id]);

  // 카테고리 표시명 변환
  const getCategoryDisplay = (category) => {
    const categoryMap = {
      'free': '자유게시판',
      'companion': '야구동행',
      'trade': '티켓거래',
      'notice': '공지사항',
      'kia': 'KIA 타이거즈',
      'samsung': '삼성 라이온즈',
      'lg': 'LG 트윈스',
      'doosan': '두산 베어스',
      'kt': 'KT 위즈',
      'ssg': 'SSG 랜더스',
      'lotte': '롯데 자이언츠',
      'hanwha': '한화 이글스',
      'nc': 'NC 다이노스',
      'kiwoom': '키움 히어로즈'
    };
    return categoryMap[category] || category;
  };

  // 댓글 작성 처리
  const handleCommentSubmit = async (e) => {
    e.preventDefault();
    
    if (!isAuthenticated) {
      alert('로그인이 필요합니다.');
      navigate('/login');
      return;
    }
    
    if (!newComment.trim()) {
      alert('댓글 내용을 입력해주세요.');
      return;
    }

    try {
      const token = localStorage.getItem('accessToken');
      const response = await axios.post(`${awsConfig.API_BASE_URL}/api/board/posts/${id}/comments/`, {
        content: newComment
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      // 새 댓글을 목록에 추가
      setComments(prev => [...prev, response.data]);
      setNewComment('');
      alert('댓글이 작성되었습니다!');
    } catch (err) {
      console.error('댓글 작성 실패:', err);
      if (err.response?.status === 401) {
        alert('로그인이 필요합니다.');
        navigate('/login');
      } else {
        alert('댓글 작성에 실패했습니다.');
      }
    }
  };

  // 댓글 수정 시작
  const startEditComment = (comment) => {
    setEditingComment(comment.id);
    setEditContent(comment.content);
  };

  // 댓글 수정 취소
  const cancelEditComment = () => {
    setEditingComment(null);
    setEditContent('');
  };

  // 댓글 수정 저장
  const saveEditComment = async (commentId) => {
    if (!editContent.trim()) {
      alert('댓글 내용을 입력해주세요.');
      return;
    }

    try {
      const token = localStorage.getItem('accessToken');
      const response = await axios.put(`${awsConfig.API_BASE_URL}/api/board/posts/${id}/comments/${commentId}/`, {
        content: editContent
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      // 댓글 목록 업데이트
      setComments(prev => prev.map(comment => 
        comment.id === commentId 
          ? { ...comment, content: editContent, updated_at: response.data.updated_at }
          : comment
      ));
      
      setEditingComment(null);
      setEditContent('');
      alert('✅ 댓글이 수정되었습니다!');
    } catch (err) {
      // 개발 모드에서만 콘솔 에러 표시
      if (import.meta.env.NODE_ENV === 'development') {
        console.error('댓글 수정 실패:', err);
      }
      
      // 사용자 친화적 에러 메시지
      if (err.response?.status === 403) {
        alert('❌ 권한 없음\n\n본인이 작성한 댓글만 수정할 수 있습니다.');
      } else if (err.response?.status === 404) {
        alert('❌ 댓글을 찾을 수 없습니다.\n\n이미 삭제되었거나 존재하지 않는 댓글입니다.');
      } else if (err.response?.status === 401) {
        alert('❌ 로그인이 필요합니다.\n\n다시 로그인해주세요.');
        navigate('/login');
      } else if (!err.response) {
        alert('❌ 네트워크 오류\n\n인터넷 연결을 확인해주세요.');
      } else {
        alert(`❌ 수정 실패\n\n댓글 수정 중 오류가 발생했습니다.\n(오류 코드: ${err.response?.status || 'Unknown'})`);
      }
    }
  };

  // 게시글 삭제 처리
  const handlePostDelete = async (postId) => {
    if (!window.confirm('정말로 이 게시글을 삭제하시겠습니까?')) {
      return;
    }
    
    try {
      const token = localStorage.getItem('accessToken');
      await axios.delete(`${awsConfig.API_BASE_URL}/api/board/posts/${postId}/delete/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      alert('게시글이 삭제되었습니다.');
      navigate('/board');
    } catch (err) {
      // 개발 모드에서만 콘솔 에러 표시
      if (import.meta.env.NODE_ENV === 'development') {
        console.error('게시글 삭제 실패:', err);
      }
      
      // 사용자 친화적 에러 메시지
      if (err.response?.status === 403) {
        alert('❌ 권한 없음\n\n본인이 작성한 게시글만 삭제할 수 있습니다.');
      } else if (err.response?.status === 404) {
        alert('❌ 게시글을 찾을 수 없습니다.\n\n이미 삭제되었거나 존재하지 않는 게시글입니다.');
      } else if (err.response?.status === 401) {
        alert('❌ 로그인이 필요합니다.\n\n다시 로그인해주세요.');
        navigate('/login');
      } else if (!err.response) {
        alert('❌ 네트워크 오류\n\n인터넷 연결을 확인해주세요.');
      } else {
        alert(`❌ 삭제 실패\n\n게시글 삭제 중 오류가 발생했습니다.\n(오류 코드: ${err.response?.status || 'Unknown'})`);
      }
    }
  };

  // 댓글 삭제 처리
  const handleCommentDelete = async (commentId) => {
    if (!window.confirm('정말로 이 댓글을 삭제하시겠습니까?')) {
      return;
    }

    try {
      const token = localStorage.getItem('accessToken');
      await axios.delete(`${awsConfig.API_BASE_URL}/api/board/posts/${id}/comments/${commentId}/delete/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      // 댓글 목록에서 제거
      setComments(prev => prev.filter(comment => comment.id !== commentId));
      alert('✅ 댓글이 삭제되었습니다!');
    } catch (err) {
      // 개발 모드에서만 콘솔 에러 표시
      if (import.meta.env.NODE_ENV === 'development') {
        console.error('댓글 삭제 실패:', err);
      }
      
      // 사용자 친화적 에러 메시지
      if (err.response?.status === 403) {
        alert('❌ 권한 없음\n\n본인이 작성한 댓글만 삭제할 수 있습니다.');
      } else if (err.response?.status === 404) {
        alert('❌ 댓글을 찾을 수 없습니다.\n\n이미 삭제되었거나 존재하지 않는 댓글입니다.');
      } else if (err.response?.status === 401) {
        alert('❌ 로그인이 필요합니다.\n\n다시 로그인해주세요.');
        navigate('/login');
      } else if (!err.response) {
        alert('❌ 네트워크 오류\n\n인터넷 연결을 확인해주세요.');
      } else {
        alert(`❌ 삭제 실패\n\n댓글 삭제 중 오류가 발생했습니다.\n(오류 코드: ${err.response?.status || 'Unknown'})`);
      }
    }
  };

  // 로딩 중 표시
  if (loading) {
    return (
      <div className="wrap">
        <div className="container">
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <p>게시글을 불러오는 중...</p>
          </div>
        </div>
      </div>
    );
  }

  // 에러 표시
  if (error) {
    return (
      <div className="wrap">
        <div className="container">
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <p style={{ color: '#dc3545' }}>{error}</p>
            <Link to="/board" style={{ color: '#1e40af' }}>목록으로 돌아가기</Link>
          </div>
        </div>
      </div>
    );
  }

  // 게시글이 없는 경우
  if (!post) {
    return (
      <div className="wrap">
        <div className="container">
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <p>게시글을 찾을 수 없습니다.</p>
            <Link to="/board" style={{ color: '#1e40af' }}>목록으로 돌아가기</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="wrap">
      <div className="container">
        {/* 게시물 헤더 */}
        <div className="post-header">
          <div className={`post-category category-${post.category}`}>
            {getCategoryDisplay(post.category)}
          </div>
          <h1 className="post-title">{post.title}</h1>
          <div className="post-meta">
            <div>
              <span className="post-author">👤 {post.author}</span>
              <span className="post-date">📅 {post.created_at}</span>
            </div>
            <span className="post-views">👁️ {post.views}</span>
          </div>
        </div>
        
        {/* 게시물 내용 */}
        <div className="post-content-container">
          <div className="content-header">
            📝 게시물 내용
          </div>
          <div className="post-content">
            {post.content}
          </div>
        </div>
        
        {/* 액션 버튼 */}
        <div className="post-actions">
          <div className="action-buttons">
            {/* 작성자만 수정/삭제 버튼 표시 */}
            {console.log('게시글 권한 확인:', {
              isAuthenticated,
              user: user?.username,
              post_author: post.author,
              isAuthor: post.author === user?.username
            })}
            {isAuthenticated && user && post.author === user.username && (
              <>
                <Link to={`/board/edit/${post.id}`} className="action-button edit-button">수정</Link>
                <button 
                  onClick={() => handlePostDelete(post.id)}
                  className="action-button delete-button"
                >
                  삭제
                </button>
              </>
            )}
            <Link to="/board/new" className="action-button new-post-button">새 글 작성</Link>
          </div>
        </div>
        
        {/* 댓글 섹션 */}
        <div className="comments-section">
          <div className="comments-header">
            💬 댓글 ({comments.length})
          </div>
          <div className="comments-list">
            {comments.length > 0 ? (
              comments.map(comment => (
                <div key={comment.id} className="comment-item" data-comment-id={comment.id}>
                  <div className="comment-author">👤 {comment.author}</div>
                  
                  {editingComment === comment.id ? (
                    // 댓글 수정 폼
                    <div className="comment-edit-form">
                      <textarea
                        className="comment-edit-textarea"
                        value={editContent}
                        onChange={(e) => setEditContent(e.target.value)}
                        placeholder="댓글을 입력하세요"
                        rows="2"
                      />
                      <div className="comment-edit-actions">
                        <button 
                          className="bs-comment-save-btn"
                          onClick={() => saveEditComment(comment.id)}
                        >
                          저장
                        </button>
                        <button 
                          className="bs-comment-cancel-btn"
                          onClick={cancelEditComment}
                        >
                          취소
                        </button>
                      </div>
                    </div>
                  ) : (
                    // 댓글 표시
                    <>
                      <div className="comment-content-row">
                        <div className="comment-content">{comment.content}</div>
                        <div className="comment-actions">
                          {/* 작성자만 수정/삭제 버튼 표시 */}
                          {console.log('댓글 권한 확인:', {
                            isAuthenticated,
                            user: user?.username,
                            comment_author: comment.author,
                            isAuthor: comment.author === user?.username
                          })}
                          {isAuthenticated && user && comment.author === user.username && (
                            <>
                              <button 
                                className="bs-comment-edit-btn"
                                onClick={() => startEditComment(comment)}
                              >
                                수정
                              </button>
                              <button 
                                className="bs-comment-delete-btn"
                                onClick={() => handleCommentDelete(comment.id)}
                              >
                                삭제
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                      <div className="comment-meta">
                        <div className="comment-date">{comment.updated_at}</div>
                      </div>
                    </>
                  )}
                </div>
              ))
            ) : (
              <p style={{ textAlign: 'center', color: '#6c7280', fontStyle: 'italic' }}>
                아직 댓글이 없습니다.
              </p>
            )}
          </div>
          
          <div className="comment-form-container">
            <h3>💬 댓글 작성</h3>
            <form onSubmit={handleCommentSubmit} className="comment-form">
              <div style={{ flex: 1 }}>
                <label htmlFor="comment-content">댓글 내용</label>
                <textarea
                  id="comment-content"
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  placeholder="댓글을 입력하세요"
                  required
                />
              </div>
              <button type="submit">작성</button>
            </form>
          </div>
        </div>
        
        <div className="back-button">
          <Link to="/board">← 목록으로 돌아가기</Link>
        </div>
      </div>
    </div>
  );
};

export default PostDetail;