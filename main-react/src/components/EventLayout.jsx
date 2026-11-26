import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import '../styles/event-service.css';

const EventLayout = ({ children }) => {
  const location = useLocation();

  // 현재 경로에 따라 활성 메뉴 결정
  const isActive = (path) => {
    return location.pathname.includes(path);
  };

  return (
    <div className="wrap es-event">
      <div className="event-layout">
        {/* 사이드바 */}
        <aside className="event-sidebar">
          <div className="brand">⚾ KBO Event</div>
          <nav className="nav">
            <Link 
              to="/event/coupons" 
              className={`nav-link ${isActive('coupons') ? 'active' : ''}`}
            >
              내 쿠폰 현황
            </Link>
            <Link 
              to="/event/participate" 
              className={`nav-link ${isActive('participate') ? 'active' : ''}`}
            >
              이벤트 참여하기
            </Link>
            <Link 
              to="/event" 
              className={`nav-link ${location.pathname === '/event' ? 'active' : ''}`}
            >
              경기일정·결과
            </Link>
            <Link 
              to="/event/ranks" 
              className={`nav-link ${isActive('ranks') ? 'active' : ''}`}
            >
              전체순위 공격/수비
            </Link>
          </nav>
          <div className="data-update">
            데이터 갱신: <span className="badge">{new Date().toLocaleString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })}</span>
          </div>
        </aside>

        {/* 메인 콘텐츠 */}
        <main className="event-content">
          {children}
        </main>
      </div>
    </div>
  );
};

export default EventLayout;
