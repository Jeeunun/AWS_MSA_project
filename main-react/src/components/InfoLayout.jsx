import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import '../styles/info-service.css';

const InfoLayout = ({ children }) => {
  const location = useLocation();

  // 현재 경로에 따라 활성 메뉴 결정
  const isActive = (path) => {
    return location.pathname.includes(path);
  };

  return (
    <div className="wrap is-info">
      <div className="info-layout">
        {/* 사이드바 */}
        <aside className="info-sidebar">
          <div className="brand">⚾ KBO Info</div>
          <nav className="nav">
            <Link 
              to="/info" 
              className={`nav-link ${location.pathname === '/info' ? 'active' : ''}`}
            >
              팀 목록
            </Link>
            <Link 
              to="/info/search" 
              className={`nav-link ${isActive('search') ? 'active' : ''}`}
            >
              선수 검색
            </Link>
            <Link 
              to="/info/analysis" 
              className={`nav-link ${isActive('analysis') ? 'active' : ''}`}
            >
              통계 분석
            </Link>
            <Link 
              to="/info/compare" 
              className={`nav-link ${isActive('compare') ? 'active' : ''}`}
            >
              팀 비교
            </Link>
          </nav>
        </aside>

        {/* 메인 콘텐츠 */}
        <main className="info-content">
          {children}
        </main>
      </div>
    </div>
  );
};

export default InfoLayout;