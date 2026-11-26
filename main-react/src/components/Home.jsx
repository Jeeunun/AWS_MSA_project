import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';
import awsConfig from '../config/aws-config';
import '../styles/common.css';

const Home = () => {
  const [todayMatch, setTodayMatch] = useState(null);
  const [loading, setLoading] = useState(true);
  const [latestNews, setLatestNews] = useState([]);
  const [newsLoading, setNewsLoading] = useState(true);
  const [latestPosts, setLatestPosts] = useState([]);
  const [postsLoading, setPostsLoading] = useState(true);

  // 오늘의 경기 정보 가져오기
  const fetchTodayMatch = async () => {
    try {
      setLoading(true);
      
      // API_BASE_URL 유효성 검사
      if (!awsConfig.API_BASE_URL || awsConfig.API_BASE_URL === 'undefined') {
        console.error('API_BASE_URL이 설정되지 않았습니다:', awsConfig.API_BASE_URL);
        return;
      }
      
      const today = new Date().toISOString().split('T')[0];
      
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${awsConfig.API_BASE_URL}/api/event/schedules/?date=${today}`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('API 응답 데이터:', data); // 디버깅용
        
        const schedules = data.results?.schedules || [];
        console.log('경기 일정:', schedules); // 디버깅용
        
        // 오늘 경기가 있으면 첫 번째 경기 정보 사용
        if (schedules.length > 0) {
          console.log('오늘의 첫 번째 경기:', schedules[0]); // 디버깅용
          setTodayMatch(schedules[0]);
        } else {
          console.log('오늘 경기가 없습니다.'); // 디버깅용
        }
      } else {
        console.error('API 응답 에러:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('오늘의 경기 정보 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  // 최신 뉴스 정보 가져오기
  const fetchLatestNews = async () => {
    try {
      setNewsLoading(true);
      
      // API_BASE_URL 유효성 검사
      if (!awsConfig.API_BASE_URL || awsConfig.API_BASE_URL === 'undefined') {
        console.error('API_BASE_URL이 설정되지 않았습니다:', awsConfig.API_BASE_URL);
        return;
      }
      
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${awsConfig.API_BASE_URL}/api/news/today/`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('뉴스 API 응답:', data); // 디버깅용
        
        const news = data.results?.news || [];
        // 최신 뉴스 3개만 가져오기
        setLatestNews(news.slice(0, 3));
      } else {
        console.error('뉴스 API 응답 에러:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('최신 뉴스 로드 실패:', error);
    } finally {
      setNewsLoading(false);
    }
  };

  // 최신 게시글 정보 가져오기
  const fetchLatestPosts = async () => {
    try {
      setPostsLoading(true);
      
      // API_BASE_URL 유효성 검사
      if (!awsConfig.API_BASE_URL || awsConfig.API_BASE_URL === 'undefined') {
        console.error('API_BASE_URL이 설정되지 않았습니다:', awsConfig.API_BASE_URL);
        return;
      }
      
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${awsConfig.API_BASE_URL}/api/board/posts/`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('게시글 API 응답:', data); // 디버깅용
        
        const pinnedPosts = data.results?.pinned_posts || [];
        const normalPosts = data.results?.normal_posts || [];
        const allPosts = [...pinnedPosts, ...normalPosts];
        // 최신 게시글 3개만 가져오기
        setLatestPosts(allPosts.slice(0, 3));
      } else {
        console.error('게시글 API 응답 에러:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('최신 게시글 로드 실패:', error);
    } finally {
      setPostsLoading(false);
    }
  };

  useEffect(() => {
    fetchTodayMatch();
    fetchLatestNews();
    fetchLatestPosts();
  }, []);

  return (
    <section id="home-section" className="page-section active">
      <div className="wrap">
        {/* Header는 App.jsx의 CommonHeader로 이동했으므로 제거 */}





        {/* Match Prediction Section */}
        <div className="match-prediction">
          <div className="match-card">
            <div className="prediction-header">
              <h2>오늘의 승부 예측</h2>
              <p className="subtitle">경기 결과를 예측해보세요</p>
              <div className="today-tag">오늘의 경기</div>
            </div>
            
            <div className="match-info">
              {loading ? (
                <div className="loading">경기 정보 로딩 중...</div>
              ) : todayMatch ? (
                <>
                  <div className="team left-team">
                    <h3>{todayMatch.homeTeamName}</h3>
                    <p>홈팀</p>
                  </div>
                  
                  <div className="match-center">
                    <div className="vs">VS</div>
                    <div className="match-time">{todayMatch.startTime || '시간 미정'}</div>
                  </div>
                  
                  <div className="team right-team">
                    <h3>{todayMatch.awayTeamName}</h3>
                    <p>원정팀</p>
                  </div>
                </>
              ) : (
                <div className="no-match">오늘은 경기가 없습니다</div>
              )}
            </div>
            
            <div className="prediction-actions">
              <Link to="/event" className="main-btn main-btn-white">예측하러 가기</Link>
            </div>
          </div>
        </div>

        {/* Information Cards */}
        <div className="info-cards">
          {/* Sports News Card */}
          <div className="info-card">
            <div className="card-header">
              <div className="card-title">
                <h3>스포츠 뉴스</h3>
                <p>당일 최신 야구 뉴스</p>
              </div>
            </div>
            {/* 최신 뉴스 미리보기 */}
            <div className="news-preview">
              {newsLoading ? (
                <div className="loading">뉴스를 불러오는 중...</div>
              ) : latestNews.length > 0 ? (
                latestNews.map((news, index) => (
                  <div key={news.idx || index} className="news-item">
                    <h4 className="news-title">
                      {news.title.length > 30 ? `${news.title.substring(0, 30)}...` : news.title}
                    </h4>
                  </div>
                ))
              ) : (
                <div className="no-news">
                  <p>오늘의 뉴스가 없습니다.</p>
                </div>
              )}
            </div>
            <div className="card-action">
              <Link to="/news" className="btn-card main-btn">더보기</Link>
            </div>
          </div>

          {/* Player & Team Info Card */}
          <div className="info-card">
            <div className="card-header">
              <div className="card-title">
                <h3>선수 & 구단</h3>
                <p>선수 및 구단 정보</p>
              </div>
            </div>
            <div className="card-content">
              <p>KBO 팀, 선수 정보 및 통계 등 다양한 야구 정보를 확인하세요.</p>
            </div>
            <div className="card-action">
              <Link to="/info" className="btn-card main-btn">더보기</Link>
            </div>
          </div>

          {/* Free Bulletin Board Card with Posts Preview */}
          <div className="info-card">
            <div className="card-header">
              <div className="card-title">
                <h3>자유 게시판</h3>
                <p>최신 게시글</p>
              </div>
            </div>
            {/* 최신 게시글 미리보기 */}
            <div className="posts-preview">
              {postsLoading ? (
                <div className="loading">게시글을 불러오는 중...</div>
              ) : latestPosts.length > 0 ? (
                latestPosts.map((post, index) => (
                  <div key={post.id || index} className="post-item">
                    <h4 className="post-title">
                      {post.title.length > 30 ? `${post.title.substring(0, 30)}...` : post.title}
                    </h4>
                    <p className="post-author">{post.author}</p>
                  </div>
                ))
              ) : (
                <div className="no-posts">
                  <p>게시글이 없습니다.</p>
                </div>
              )}
            </div>
            <div className="card-action">
              <Link to="/board" className="btn-card main-btn">더보기</Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Home;

