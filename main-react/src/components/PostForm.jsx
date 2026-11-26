import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import awsConfig from '../config/aws-config';
import '../styles/board-service.css';

const PostForm = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    category: 'free',
    title: '',
    content: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

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
      await axios.post(`${awsConfig.API_BASE_URL}/api/board/posts/create/`, formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      alert('게시글이 성공적으로 작성되었습니다!');
      navigate('/board');
    } catch (err) {
      console.error('게시글 작성 실패:', err);
      if (err.response?.status === 401) {
        alert('로그인이 필요합니다.');
        navigate('/login');
      } else {
        setError('게시글 작성에 실패했습니다. 다시 시도해주세요.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="wrap">
      <div className="form-container">
        <h1>새 글 작성</h1>
        
        {/* 에러 메시지 */}
        {error && (
          <div className="error-message">
            <p>{error}</p>
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          {/* 카테고리 선택 */}
          <div className="category-selection">
            <label htmlFor="category">카테고리</label>
            <select 
              name="category" 
              id="category" 
              className="category-select"
              value={formData.category}
              onChange={handleInputChange}
            >
              <optgroup label="공통게시판">
                {categoryGroups.common.map(cat => (
                  <option key={cat.code} value={cat.code}>
                    {cat.name}
                  </option>
                ))}
              </optgroup>
              <optgroup label="구단별 게시판">
                {categoryGroups.teams.map(cat => (
                  <option key={cat.code} value={cat.code}>
                    {cat.name}
                  </option>
                ))}
              </optgroup>
              <optgroup label="자유게시판">
                {categoryGroups.free.map(cat => (
                  <option key={cat.code} value={cat.code}>
                    {cat.name}
                  </option>
                ))}
              </optgroup>
            </select>
          </div>
          
          {/* 제목 입력 */}
          <div>
            <label htmlFor="title">제목</label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              placeholder="제목을 입력하세요"
              required
            />
          </div>
          
          {/* 내용 입력 */}
          <div>
            <label htmlFor="content">내용</label>
            <textarea
              id="content"
              name="content"
              value={formData.content}
              onChange={handleInputChange}
              placeholder="내용을 입력하세요"
              required
            />
          </div>
          
          <div className="button-group">
            <button type="submit" disabled={loading}>
              {loading ? '작성 중...' : '작성하기'}
            </button>
            <Link to="/board" className="bs-btn bs-btn-primary">목록으로</Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PostForm;
