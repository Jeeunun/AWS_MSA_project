import React, { useState, useEffect } from 'react';
import '../styles/news-service.css';
import axios from 'axios';
import awsConfig from '../config/aws-config';

const News = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredNews, setFilteredNews] = useState([]);
  const [categories, setCategories] = useState([]);
  
  // 실제 API 호출로 대체할 상태 (크롤링된 뉴스 데이터)
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 뉴스 데이터 로드 (Django News Service API 호출)
  useEffect(() => {
    const fetchNews = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // JWT 토큰 가져오기
        const token = localStorage.getItem('accessToken');
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
        
        // Django News Service API 호출 (토큰과 함께)
        const response = await axios.get(`${awsConfig.API_BASE_URL}/api/news/`, { headers });
        
        // API 응답 구조에 맞게 데이터 설정 (Django 페이지네이션 구조 반영)
        let newsData = [];
        
        if (response.data.results && response.data.results.news) {
          // Django 페이지네이션 + 커스텀 구조: {results: {news: [...], filters: {}}}
          newsData = response.data.results.news;
        } else if (response.data.results && Array.isArray(response.data.results)) {
          // Django 페이지네이션: {results: [...]}
          newsData = response.data.results;
        } else if (response.data.news && Array.isArray(response.data.news)) {
          // 직접 뉴스 배열: {news: [...]}
          newsData = response.data.news;
        } else if (Array.isArray(response.data)) {
          // 루트가 배열
          newsData = response.data;
        }
        
        setNews(newsData);
        setFilteredNews(newsData);
        
        console.log('=== API 응답 분석 ===');
        console.log('API 응답 전체 구조:', response.data);
        console.log('response.data 타입:', typeof response.data);
        console.log('response.data 키들:', Object.keys(response.data));
        console.log('response.data.results:', response.data.results);
        console.log('response.data.news:', response.data.news);
        console.log('newsData:', newsData);
        console.log('newsData 타입:', typeof newsData);
        console.log('newsData 길이:', newsData ? newsData.length : 'undefined');
        console.log('newsData 첫 번째 항목:', newsData && newsData.length > 0 ? newsData[0] : 'undefined');
        console.log('첫 번째 뉴스의 link 필드:', newsData && newsData.length > 0 ? newsData[0].link : 'undefined');
        console.log('사용된 토큰:', token ? '있음' : '없음');
      } catch (error) {
        console.error('뉴스 API 호출 실패:', error);
        setError('뉴스를 불러오는데 실패했습니다. 잠시 후 다시 시도해주세요.');
      } finally {
        setLoading(false);
      }
    };

    fetchNews();
    
    // 카테고리 목록도 함께 로드
    const fetchCategories = async () => {
      try {
        const token = localStorage.getItem('accessToken');
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
        
        const response = await axios.get(`${awsConfig.API_BASE_URL}/api/news/categories/`, { headers });
        setCategories(response.data.categories || []);
      } catch (error) {
        console.error('카테고리 로드 실패:', error);
      }
    };
    
    fetchCategories();
  }, []);

  // 검색어 변경 시 API 호출 또는 로컬 필터링
  useEffect(() => {
    console.log('검색어 변경됨:', searchQuery);
    
    if (!searchQuery.trim()) {
      // 검색어가 없으면 전체 뉴스 표시
      console.log('검색어 없음, 전체 뉴스 표시');
      setFilteredNews(news);
      return;
    }

    // 검색어가 있으면 Django Search API 호출
    const searchNews = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('accessToken');
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
        
        const response = await axios.get(`${awsConfig.API_BASE_URL}/api/news/search/?q=${encodeURIComponent(searchQuery)}`, { headers });
        
        // Django API 응답 구조에 맞게 수정
        let searchResults = [];
        if (response.data.results && response.data.results.news) {
          searchResults = response.data.results.news;
        } else if (response.data.news) {
          searchResults = response.data.news;
        } else if (Array.isArray(response.data)) {
          searchResults = response.data;
        }
        
        setFilteredNews(searchResults);
        
        console.log('검색 API 응답:', response.data);
        console.log('검색 결과:', searchResults);
        console.log('검색 결과 개수:', searchResults.length);
      } catch (error) {
        console.error('검색 API 호출 실패:', error);
        // API 실패 시 로컬 필터링으로 폴백
        const filtered = news.filter(item => {
          const searchText = `${item.title} ${item.keyword}`.toLowerCase();
          return searchText.includes(searchQuery.toLowerCase());
        });
        setFilteredNews(filtered);
      } finally {
        setLoading(false);
      }
    };

    // 검색어 입력 후 500ms 지연 (디바운싱)
    const timeoutId = setTimeout(searchNews, 500);
    return () => clearTimeout(timeoutId);
  }, [searchQuery, news]);

  // 검색어 지우기
  const clearSearch = () => {
    setSearchQuery('');
  };

  // 하이라이트 적용 함수
  const highlightText = (text, query) => {
    if (!query.trim()) return text;
    
    const index = text.toLowerCase().indexOf(query.toLowerCase());
    if (index === -1) return text;
    
    const before = text.slice(0, index);
    const match = text.slice(index, index + query.length);
    const after = text.slice(index + query.length);
    
    return (
      <>
        {before}
        <mark>{match}</mark>
        {after}
      </>
    );
  };

  return (
    <div className="wrap ns-news">
      <div className="container">
        {/* 뉴스 헤더 */}
        <header className="news-header">
          <h1>
            오늘의 KBO 뉴스
            <small className="news-date">
              ({new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' })})
            </small>
          </h1>
          
          {/* 검색 섹션 */}
          <div className="search-wrap" role="search">
            {/* 돋보기 아이콘 */}
            <svg className="search-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79L20 21.5 21.5 20l-6-6zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
            </svg>
            <input
              className="search-input"
              type="text"
              placeholder="안타, 홈런, 선발… 검색어를 입력하세요"
              aria-label="뉴스 검색"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button 
                className="clear-btn" 
                title="지우기" 
                aria-label="검색어 지우기"
                onClick={clearSearch}
              >
                ✕
              </button>
            )}
          </div>
        </header>

        {/* 뉴스 목록 */}
        <main className="news-main">
          
          {loading ? (
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <p>뉴스를 불러오는 중...</p>
            </div>
          ) : error ? (
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <p style={{ color: '#dc3545' }}>{error}</p>
            </div>
          ) : filteredNews.length > 0 ? (
            <ul className="news-list">
              {filteredNews.map((item, index) => (
                <li key={item.id || index} className="news-item">
                  <a 
                    href={item.link} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className="news-link"
                    onClick={() => console.log('뉴스 클릭:', item.title, '링크:', item.link)}
                  >
                    <span className="title">
                      {highlightText(item.title, searchQuery)}
                    </span>
                  </a>
                  <div className="news-meta">
                    <span className="keyword">
                      {item.keywords && item.keywords.length > 0 
                        ? item.keywords.join(', ') 
                        : item.keyword || '키워드 없음'
                      }
                    </span>
                    {item.crawl_date && (
                      <span className="date">
                        {new Date(item.crawl_date).toLocaleDateString('ko-KR')}
                      </span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="empty-state">
              {searchQuery ? '검색 결과가 없습니다. 다른 키워드를 입력해 보세요.' : '아직 뉴스가 없습니다.'}
            </div>
          )}
        </main>
      </div>
      

    </div>
  );
};

export default News;
