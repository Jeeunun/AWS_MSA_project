import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Home from './components/Home';
import Login from './components/Login';
import Signup from './components/Signup';
import Confirm from './components/Confirm';
import Board from './components/Board';
import User from './components/User';
import PostForm from './components/PostForm';
import PostDetail from './components/PostDetail';
import PostEdit from './components/PostEdit';
import News from './components/News';
import EventSchedule from './components/EventSchedule';
import EventRanks from './components/EventRanks';
import EventCoupons from './components/EventCoupons';
import EventParticipate from './components/EventParticipate';
import InfoLayout from './components/InfoLayout';
import TeamList from './components/TeamList';
import TeamDetail from './components/TeamDetail';
import PlayerSearch from './components/PlayerSearch';
import StatsAnalysis from './components/StatsAnalysis';
import TeamComparison from './components/TeamComparison';
import Footer from './components/Footer';
import './App.css';

// AWS Amplify 설정 (임시 비활성화)
import awsConfig from './config/aws-config';
import { Amplify } from 'aws-amplify';

// Amplify 초기화
Amplify.configure(awsConfig);

// 공통 헤더 컴포넌트
const CommonHeader = () => {
  const { user, isAuthenticated, logout } = useAuth();
  
  // 디버깅용 로그
  console.log('CommonHeader - 인증 상태:', { isAuthenticated, user });
  
  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('로그아웃 실패:', error);
    }
  };

  return (
    <div className="main-header">
      <div className="header-left">
        <Link to="/" className="header-title">
          <h1>Dugout</h1>
          <p>Baseball Community Platform</p>
        </Link>
      </div>
      
      <div className="header-right">
        {isAuthenticated ? (
          // 로그인된 상태: 사용자 환영 메시지 + 마이페이지/로그아웃 버튼
          <div className="user-menu">
            <span className="welcome-message">
              환영합니다, {user?.username || user?.email || '사용자'}님!
            </span>
            <Link to="/user" className="btn btn-primary btn-mypage">마이페이지</Link>
            <button onClick={handleLogout} className="refresh-btn-new">로그아웃</button>
          </div>
        ) : (
          // 로그인되지 않은 상태: 기존 로그인/회원가입 버튼
          <>
            <Link to="/signup" className="refresh-btn-new">회원가입</Link>
            <Link to="/login" className="btn btn-primary">로그인</Link>
          </>
        )}
      </div>
    </div>
  );
};

// 서비스 페이지 컴포넌트들
const NewsPage = () => {
  return (
    <div className="service-page">
      <div className="wrap">
        <h1>KBO 뉴스</h1>
        <div className="news-grid">
          <div className="news-card">
            <div className="news-image">📰</div>
            <h3>오늘의 주요 뉴스</h3>
            <p>KBO 리그의 최신 소식과 분석을 확인하세요</p>
            <div className="news-meta">
              <span className="date">2024.01.15</span>
              <span className="category">전체</span>
            </div>
          </div>
          <div className="news-card">
            <div className="news-image">⚾</div>
            <h3>경기 결과</h3>
            <p>어제 경기 결과와 주요 장면을 요약했습니다</p>
            <div className="news-meta">
              <span className="date">2024.01.14</span>
              <span className="category">경기</span>
            </div>
          </div>
          <div className="news-card">
            <div className="news-image">🎯</div>
            <h3>선수 소식</h3>
            <p>FA, 이적, 부상 등 선수 관련 소식을 전합니다</p>
            <div className="news-meta">
              <span className="date">2024.01.13</span>
              <span className="category">선수</span>
            </div>
          </div>
        </div>
        <p className="service-note">Django 백엔드 연동 후 실제 데이터가 표시됩니다.</p>
      </div>
    </div>
  );
};

const EventPage = () => {
  return (
    <div className="service-page">
      <div className="wrap">
        <h1>특별 이벤트</h1>
        <div className="event-grid">
          <div className="event-card featured">
            <div className="event-badge">🔥 인기</div>
            <div className="event-image">🎁</div>
            <h3>신규 가입 이벤트</h3>
            <p>지금 가입하면 특별한 혜택을 드립니다!</p>
            <div className="event-date">~ 2024.02.15</div>
            <button className="btn btn-primary">참여하기</button>
          </div>
          <div className="event-card">
            <div className="event-image">🏆</div>
            <h3>경기 예측 대회</h3>
            <p>정확한 예측으로 상품을 받아가세요</p>
            <div className="event-date">~ 2024.01.31</div>
            <button className="btn btn-secondary">자세히 보기</button>
          </div>
          <div className="event-card">
            <div className="event-image">📱</div>
            <h3>앱 리뷰 이벤트</h3>
            <p>앱스토어 리뷰 작성하고 선물 받기</p>
            <div className="event-date">상시 진행</div>
            <button className="btn btn-secondary">참여하기</button>
          </div>
        </div>
        <p className="service-note">Django 백엔드 연동 후 실제 이벤트가 표시됩니다.</p>
      </div>
    </div>
  );
};

const InfoPage = () => {
  return (
    <div className="service-page">
      <div className="wrap">
        <h1>팀 & 선수 정보</h1>
        <div className="info-tabs">
          <div className="tab-buttons">
            <button className="tab-btn active">팀 정보</button>
            <button className="tab-btn">선수 명단</button>
            <button className="tab-btn">시즌 기록</button>
          </div>
          <div className="tab-content">
            <div className="team-grid">
              <div className="team-card">
                <div className="team-logo">🐯</div>
                <h3>KIA 타이거즈</h3>
                <p>창단: 1982년</p>
                <p>연고지: 광주</p>
                <p>홈구장: 광주기아챔피언스필드</p>
              </div>
              <div className="team-card">
                <div className="team-logo">🦁</div>
                <h3>삼성 라이온즈</h3>
                <p>창단: 1982년</p>
                <p>연고지: 대구</p>
                <p>홈구장: 대구삼성라이온즈파크</p>
              </div>
              <div className="team-card">
                <div className="team-logo">🦅</div>
                <h3>두산 베어스</h3>
                <p>창단: 1982년</p>
                <p>연고지: 서울</p>
                <p>홈구장: 잠실야구장</p>
              </div>
            </div>
          </div>
        </div>
        <p className="service-note">Django 백엔드 연동 후 실제 팀 정보가 표시됩니다.</p>
      </div>
    </div>
  );
};

const BoardPage = () => {
  return (
    <div className="service-page">
      <div className="wrap">
        <h1>커뮤니티 게시판</h1>
        <div className="board-list">
          <div className="board-item">
            <div className="board-category">자유게시판</div>
            <div className="board-title">오늘 경기 어떻게 보셨나요?</div>
            <div className="board-meta">
              <span className="author">야구팬123</span>
              <span className="date">2024.01.15</span>
              <span className="views">조회 45</span>
            </div>
          </div>
          <div className="board-item">
            <div className="board-category">팀별게시판</div>
            <div className="board-title">우리팀 새 시즌 전망</div>
            <div className="board-meta">
              <span className="author">팀팬456</span>
              <span className="date">2024.01.14</span>
              <span className="views">조회 78</span>
            </div>
          </div>
          <div className="board-item">
            <div className="board-category">경기후기</div>
            <div className="board-title">어제 경기 하이라이트</div>
            <div className="board-meta">
              <span className="author">경기감상789</span>
              <span className="date">2024.01.13</span>
              <span className="views">조회 123</span>
            </div>
          </div>
        </div>
        <p className="service-note">Django 백엔드 연동 후 실제 게시글이 표시됩니다.</p>
      </div>
    </div>
  );
};



function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          {/* 공통 헤더 - 모든 페이지에서 보임 */}
          <CommonHeader />
          
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/confirm" element={<Confirm />} />
              <Route path="/news" element={<News />} />
              <Route path="/event" element={<EventSchedule />} />
              <Route path="/event/schedule" element={<EventSchedule />} />
              <Route path="/event/ranks" element={<EventRanks />} />
              <Route path="/event/coupons" element={<EventCoupons />} />
              <Route path="/event/participate" element={<EventParticipate />} />
              <Route path="/info" element={<TeamList />} />
              <Route path="/info/team/:teamCode" element={<TeamDetail />} />
              <Route path="/info/search" element={<PlayerSearch />} />
              <Route path="/info/analysis" element={<StatsAnalysis />} />
              <Route path="/info/compare" element={<TeamComparison />} />

              <Route path="/board" element={<Board />} />
              <Route path="/board/new" element={<PostForm />} />
              <Route path="/board/:id" element={<PostDetail />} />
              <Route path="/board/edit/:id" element={<PostEdit />} />
              <Route path="/user" element={<User />} />
            </Routes>
          </main>
          
          {/* 공통 Footer - 모든 페이지에서 보임 */}
          <Footer />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;