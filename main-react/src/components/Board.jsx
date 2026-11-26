import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import awsConfig from '../config/aws-config';
import '../styles/board-service.css';

const Board = () => {
  const { isAuthenticated } = useAuth();
  const [searchType, setSearchType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentCategory, setCurrentCategory] = useState('');
  const [currentGroup, setCurrentGroup] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

  // 게시글 상태
  const [posts, setPosts] = useState([]);
  const [pinnedPosts, setPinnedPosts] = useState([]);
  const [normalPosts, setNormalPosts] = useState([]);
  
  // 페이징 상태
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // API 호출 함수
  const fetchPosts = async (category = '', search = '', page = 1) => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams();
      if (category) params.append('category', category);
      if (search) params.append('search', search);
      if (page > 1) params.append('page', page);
      
      // JWT 토큰 가져오기
      const token = localStorage.getItem('accessToken');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      
      const response = await axios.get(`${awsConfig.API_BASE_URL}/api/board/posts/?${params}`, { headers });
      
      // Django API의 페이징 응답 구조에 맞게 데이터 파싱
      const pinnedPosts = response.data.results?.pinned_posts || [];
      const normalPosts = response.data.results?.normal_posts || [];
      
      setPinnedPosts(pinnedPosts);
      setNormalPosts(normalPosts);
      setPosts([...pinnedPosts, ...normalPosts]);
      
      // 페이징 정보 설정
      if (response.data.count !== undefined) {
        setTotalCount(response.data.count);
        setTotalPages(Math.ceil(response.data.count / 10));
        setCurrentPage(page);
      }
    } catch (err) {
      console.error('게시글 목록 조회 실패:', err);
      setError('게시글을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // 검색 처리
  const handleSearch = (e) => {
    e.preventDefault();
    setCurrentPage(1); // 검색 시 첫 페이지로
    fetchPosts(currentCategory, searchQuery, 1);
  };

  // 카테고리 클릭 처리
  const handleCategoryClick = (group, category = '') => {
    setCurrentGroup(group);
    setCurrentCategory(category);
    setCurrentPage(1); // 카테고리 변경 시 첫 페이지로
    fetchPosts(category, searchQuery, 1);
  };
  
  // 페이지 변경 처리
  const handlePageChange = (page) => {
    setCurrentPage(page);
    fetchPosts(currentCategory, searchQuery, page);
  };

  // 컴포넌트 마운트 시 게시글 로드
  useEffect(() => {
    fetchPosts();
  }, []);

  // 사이드바 토글 처리
  const [expandedMenus, setExpandedMenus] = useState({});
  const toggleSubMenu = (group) => {
    setExpandedMenus(prev => ({
      ...prev,
      [group]: !prev[group]
    }));
  };

  return (
    <div className="wrap bs-board">
      {/* 게시판 제목 - 헤더 하단에 표시 */}
      <div className="board-page-title">
        <h1>⚾ 야구 커뮤니티</h1>
        <p>야구팬들을 위한 자유로운 소통 공간</p>
      </div>
      
      {/* 검색 섹션과 새글작성 버튼을 한 줄에 배치 */}
      <div className="search-section">
        <div className="search-and-add-container">
          <form onSubmit={handleSearch} className="search-form">
            <div className="search-container">
              <select 
                value={searchType} 
                onChange={(e) => setSearchType(e.target.value)}
                className="search-type"
              >
                <option value="all">전체</option>
                <option value="title">제목</option>
                <option value="content">내용</option>
                <option value="author">작성자</option>
              </select>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="검색어를 입력하세요..."
                className="search-input"
              />
              <button type="submit" className="search-button">🔍 검색</button>
              {searchQuery && (
                <button 
                  type="button" 
                  onClick={() => setSearchQuery('')}
                  className="clear-search"
                >
                  검색 초기화
                </button>
              )}
            </div>
          </form>
          <div className="add-post">
            <Link to="/board/new" className="bs-btn bs-btn-primary">새 글 작성</Link>
          </div>
        </div>
        {/* 검색 결과 메시지 제거됨 */}
      </div>
      
      <div className="bs-main-layout main-layout">
        {/* 사이드바 */}
        <div className="bs-sidebar sidebar">
          <div className="sidebar-section">
            <div className="bs-sidebar-title sidebar-title">📂 카테고리</div>
            <ul className="bs-sidebar-menu sidebar-menu">
              <li className="bs-sidebar-item sidebar-item">
                <Link 
                  to="/board" 
                  className={`sidebar-link ${!currentGroup && !currentCategory ? 'active' : ''}`}
                  onClick={() => handleCategoryClick('', '')}
                >
                  전체
                </Link>
              </li>
              <li className="bs-sidebar-item sidebar-item">
                <button 
                  className={`sidebar-link ${currentGroup === 'common' ? 'active' : ''}`}
                  onClick={() => toggleSubMenu('common')}
                >
                  공통게시판
                </button>
                <ul className={`sub-menu ${expandedMenus.common ? 'show' : ''}`}>
                  {categoryGroups.common.map(cat => (
                    <li key={cat.code} className="sub-item">
                      <Link
                        to={`/board?category=${cat.code}`}
                        className={`sub-link ${currentCategory === cat.code ? 'active' : ''}`}
                        onClick={() => handleCategoryClick('common', cat.code)}
                      >
                        {cat.name}
                      </Link>
                    </li>
                  ))}
                </ul>
              </li>
              <li className="bs-sidebar-item sidebar-item">
                <button 
                  className={`sidebar-link ${currentGroup === 'teams' ? 'active' : ''}`}
                  onClick={() => toggleSubMenu('teams')}
                >
                  구단별 게시판
                </button>
                <ul className={`sub-menu ${expandedMenus.teams ? 'show' : ''}`}>
                  {categoryGroups.teams.map(cat => (
                    <li key={cat.code} className="sub-item">
                      <Link
                        to={`/board?category=${cat.code}`}
                        className={`sub-link ${currentCategory === cat.code ? 'active' : ''}`}
                        onClick={() => handleCategoryClick('teams', cat.code)}
                      >
                        {cat.name}
                      </Link>
                    </li>
                  ))}
                </ul>
              </li>
              <li className="sidebar-item">
                <button 
                  className={`sidebar-link ${currentGroup === 'free' ? 'active' : ''}`}
                  onClick={() => toggleSubMenu('free')}
                >
                  자유게시판
                </button>
                <ul className={`sub-menu ${expandedMenus.free ? 'show' : ''}`}>
                  {categoryGroups.free.map(cat => (
                    <li key={cat.code} className="sub-item">
                      <Link
                        to={`/board?category=${cat.code}`}
                        className={`sub-link ${currentCategory === cat.code ? 'active' : ''}`}
                        onClick={() => handleCategoryClick('free', cat.code)}
                      >
                        {cat.name}
                      </Link>
                    </li>
                  ))}
                </ul>
              </li>
            </ul>
          </div>
        </div>
        
        {/* 메인 콘텐츠 */}
        <div className="bs-main-post main-post-content">
          
          {/* 로딩 상태 */}
          {loading && (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>게시글을 불러오는 중...</p>
            </div>
          )}

          {/* 에러 상태 */}
          {error && (
            <div className="error-message">
              <p>{error}</p>
              <button onClick={() => fetchPosts()} className="bs-btn bs-btn-outline">다시 시도</button>
            </div>
          )}

          {/* 게시글 목록 */}
          {!loading && !error && (
            <div className="bs-post-list post-list">
              <div className="bs-post-header post-header">
                <span>제목</span>
                <span>작성자</span>
                <span>작성일</span>
                <span>조회수</span>
              </div>
              
              {/* 고정된 게시글들 */}
              {pinnedPosts.length > 0 && (
                <div className="bs-pinned-posts pinned-posts">
                  {pinnedPosts.map(post => (
                    <div key={post.id} className="bs-post-item post-item pinned">
                      <div className="post-title">
                        <span className="pin-badge">📌</span>
                        <Link to={`/board/${post.id}`} className="post-link">
                          {post.title}
                        </Link>
                      </div>
                      <div className="post-author">{post.author}</div>
                      <div className="post-date">{new Date(post.created_at).toLocaleDateString('ko-KR')}</div>
                      <div className="post-views">{post.views}</div>
                    </div>
                  ))}
                </div>
              )}
              
              {/* 일반 게시글들 */}
              {normalPosts.length > 0 ? (
                normalPosts.map(post => (
                  <div key={post.id} className="bs-post-item post-item">
                    <div className="post-title">
                      <Link to={`/board/${post.id}`} className="post-link">
                        {post.title}
                      </Link>
                    </div>
                    <div className="post-author">{post.author}</div>
                    <div className="post-date">{new Date(post.created_at).toLocaleDateString('ko-KR')}</div>
                    <div className="post-views">{post.views}</div>
                  </div>
                ))
              ) : (
                <div className="bs-empty-message empty-message">
                  <h3>아직 게시물이 없습니다</h3>
                  <p>첫 번째 게시물을 작성해보세요!</p>
                </div>
              )}
              
              {/* 페이징 UI */}
              {totalPages > 1 && (
                <div className="bs-pagination pagination">
                  <div className="pagination-info">
                    총 {totalCount}개 게시글 • {currentPage} / {totalPages} 페이지
                  </div>
                  <div className="pagination-controls">
                    {/* 이전 페이지 */}
                    {currentPage > 1 && (
                      <button 
                        onClick={() => handlePageChange(currentPage - 1)}
                        className="bs-page-btn page-btn prev"
                      >
                        ← 이전
                      </button>
                    )}
                    
                    {/* 페이지 번호들 */}
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      let pageNum;
                      if (totalPages <= 5) {
                        pageNum = i + 1;
                      } else if (currentPage <= 3) {
                        pageNum = i + 1;
                      } else if (currentPage >= totalPages - 2) {
                        pageNum = totalPages - 4 + i;
                      } else {
                        pageNum = currentPage - 2 + i;
                      }
                      
                      return (
                        <button
                          key={pageNum}
                          onClick={() => handlePageChange(pageNum)}
                          className={`bs-page-btn page-btn ${currentPage === pageNum ? 'active' : ''}`}
                        >
                          {pageNum}
                        </button>
                      );
                    })}
                    
                    {/* 다음 페이지 */}
                    {currentPage < totalPages && (
                      <button 
                        onClick={() => handlePageChange(currentPage + 1)}
                        className="bs-page-btn page-btn next"
                      >
                        다음 →
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      

    </div>
  );
};

export default Board;