import React, { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import awsConfig from '../config/aws-config';
import '../styles/board-service.css';

const PostEdit = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    category: 'free'
  });
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [post, setPost] = useState(null);


  // 카테고리 그룹 정의
  const categoryGroups = {
    common: [
      { code: 'companion', name: '야구동행' },
      { code: 'trade', name: '티켓거래' },
      { code: 'notice', name: '공지사항' }
    ],
    teams: [
      { code: 'kia', name: 'KIA 타이거즈' },
      { code: 'samsung', name: '삼성 라이온즈' },
      { code: 'lg', name: 'LG 트윈스' },
      { code: 'doosan', name: '두산 베어스' },
      { code: 'kt', name: 'KT 위즈' },
      { code: 'ssg', name: 'SSG 랜더스' },
      { code: 'lotte', name: '롯데 자이언츠' },
      { code: 'hanwha', name: '한화 이글스' },
      { code: 'nc', name: 'NC 다이노스' },
      { code: 'kiwoom', name: '키움 히어로즈' }
    ],
    free: [
      { code: 'free', name: '자유게시판' }
    ]
  };

  // 게시글 데이터 로드
  useEffect(() => {
    const fetchPost = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const token = localStorage.getItem('accessToken');
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
        
        const response = await axios.get(`${awsConfig.API_BASE_URL}/api/board/posts/${id}/`, { headers });
        const postData = response.data;
        
        // 작성자 확인
        if (postData.user_id !== user?.id) {
          setError('수정 권한이 없습니다.');
          return;
        }
        
        setPost(postData);
        setFormData({
          title: postData.title,
          content: postData.content,
          category: postData.category
        });
      } catch (err) {
        console.error('게시글 조회 실패:', err);
        setError('게시글을 불러오는데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };
    
    if (isAuthenticated && user) {
      fetchPost();
    }
  }, [id, isAuthenticated, user]);

  // 폼 입력 처리
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // 폼 제출 처리
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!isAuthenticated) {
      alert('로그인이 필요합니다.');
      navigate('/login');
      return;
    }
    
    if (!formData.title.trim() || !formData.content.trim()) {
      setError('제목과 내용을 모두 입력해주세요.');
      return;
    }
    
    try {
      setLoading(true);
      setError('');
      
      const token = localStorage.getItem('accessToken');
      await axios.put(`${awsConfig.API_BASE_URL}/api/board/posts/${id}/update/`, formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      alert('게시글이 성공적으로 수정되었습니다!');
      navigate(`/board/${id}`);
    } catch (err) {
      console.error('게시글 수정 실패:', err);
      if (err.response?.status === 403) {
        alert('수정 권한이 없습니다.');
      } else {
        setError('게시글 수정에 실패했습니다. 다시 시도해주세요.');
      }
    } finally {
      setLoading(false);
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

  return (
    <div className="wrap">
      <div className="container">
        <div className="form-container">
          <h1>게시글 수정</h1>
          
          {/* 에러 메시지 */}
          {error && (
            <div className="error-message">
              <p>{error}</p>
            </div>
          )}
          
          <form onSubmit={handleSubmit}>
            {/* 카테고리 선택 */}
            <div className="form-group">
              <label htmlFor="category">카테고리</label>
              <select
                id="category"
                name="category"
                value={formData.category}
                onChange={handleInputChange}
                className="form-control"
                required
              >
                {Object.entries(categoryGroups).map(([groupName, categories]) => (
                  <optgroup key={groupName} label={groupName === 'common' ? '공통' : groupName === 'teams' ? '구단별' : '자유'}>
                    {categories.map(cat => (
                      <option key={cat.code} value={cat.code}>
                        {cat.name}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>
            
            {/* 제목 입력 */}
            <div className="form-group">
              <label htmlFor="title">제목</label>
              <input
                type="text"
                id="title"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                className="form-control"
                placeholder="제목을 입력하세요"
                required
              />
            </div>
            
            {/* 내용 입력 */}
            <div className="form-group">
              <label htmlFor="content">내용</label>
              <textarea
                id="content"
                name="content"
                value={formData.content}
                onChange={handleInputChange}
                className="form-control"
                rows="10"
                placeholder="내용을 입력하세요"
                required
              />
            </div>
            
            {/* 버튼 그룹 */}
            <div className="form-actions">
              <button type="submit" className="bs-btn bs-btn-primary" disabled={loading}>
                {loading ? '수정 중...' : '수정하기'}
              </button>
              <Link to={`/board/${id}`} className="bs-btn bs-btn-outline">
                취소
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default PostEdit;


