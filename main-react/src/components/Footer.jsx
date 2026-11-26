import React from 'react';
import { Link } from 'react-router-dom';

const Footer = () => {
  return (
    <footer className="footer">
      <div className="footer-content">
        <div className="footer-column">
          <h4>야구 커뮤니티</h4>
          <p>야구 팬들을 위한 최고의 커뮤니티 플랫폼</p>
        </div>
        <div className="footer-column">
          <h4>서비스</h4>
          <ul>
            <li><Link to="/news">스포츠 뉴스</Link></li>
            <li><Link to="/event">경기 예측</Link></li>
            <li><Link to="/info">선수 정보</Link></li>
            <li><Link to="/board">커뮤니티</Link></li>
          </ul>
        </div>
        <div className="footer-column">
          <h4>고객지원</h4>
          <ul>
            <li><Link to="/user">내 정보</Link></li>
            <li><Link to="/board">문의하기</Link></li>
            <li><Link to="/event">이벤트</Link></li>
          </ul>
        </div>
      </div>
      <div className="footer-bottom">
        <p>&copy; 2024 야구 커뮤니티. All rights reserved.</p>
      </div>
    </footer>
  );
};

export default Footer;
