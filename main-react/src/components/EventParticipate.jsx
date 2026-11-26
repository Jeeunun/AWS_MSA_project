import React, { useState, useEffect } from 'react';
import EventLayout from './EventLayout';
import { useAuth } from '../contexts/AuthContext';
import awsConfig from '../config/aws-config';
import '../styles/event-service.css';

const EventParticipate = () => {
  const { isAuthenticated } = useAuth();
  
  // 상태 관리
  const [showVoteModal, setShowVoteModal] = useState(false);
  const [voteMessage, setVoteMessage] = useState('');
  const [isVoting, setIsVoting] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // 데이터 상태
  const [match, setMatch] = useState(null);
  const [aggregation, setAggregation] = useState({ away: 0, home: 0, total: 0 });
  const [history, setHistory] = useState([]);

  // API에서 참여 정보 가져오기
  const fetchParticipateInfo = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${awsConfig.API_BASE_URL}/api/event/participate/`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      
      if (!response.ok) {
        throw new Error('참여 정보를 불러오는데 실패했습니다.');
      }
      
      const data = await response.json();
      setMatch(data.match);
      setAggregation(data.aggregation);
      setHistory(data.history || []);
      
    } catch (err) {
      console.error('참여 정보 로드 실패:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 컴포넌트 마운트 시 데이터 로드
  useEffect(() => {
    fetchParticipateInfo();
  }, []);

  // 투표 처리
  const handleVote = async (choice) => {
    if (!isAuthenticated) {
      setVoteMessage('로그인이 필요합니다.');
      return;
    }

    if (!match) {
      setVoteMessage('참여 가능한 경기가 없습니다.');
      return;
    }

    setIsVoting(true);
    setVoteMessage('전송 중...');

    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${awsConfig.API_BASE_URL}/api/event/vote/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          result_id: match.idx,
          choice: choice
        })
      });
      
      const result = await response.json();
      
      if (result.ok) {
        const choiceText = choice === 'AWAY' ? `원정팀 ${match.awayTeamName}` : `홈팀 ${match.homeTeamName}`;
        setVoteMessage(`${choiceText} 선택 완료!`);
        
        // 1.2초 후 데이터 새로고침
        setTimeout(() => {
          fetchParticipateInfo();
          setShowVoteModal(false);
          setVoteMessage('');
        }, 1200);
      } else {
        setVoteMessage(result.msg || '투표에 실패했습니다.');
      }
      
    } catch (error) {
      console.error('투표 실패:', error);
      setVoteMessage('네트워크 오류: ' + error.message);
    } finally {
      setIsVoting(false);
    }
  };

  // 모달 닫기
  const closeModal = () => {
    setShowVoteModal(false);
    setVoteMessage('');
  };

  return (
    <EventLayout>
      <div className="participate-container">
        <h2>이벤트 참여</h2>

        {/* 로딩 및 에러 상태 */}
        {loading && (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <p>참여 정보를 불러오는 중...</p>
          </div>
        )}

        {error && (
          <div style={{ textAlign: 'center', padding: '20px', color: '#dc3545' }}>
            <p>{error}</p>
            <button className="es-btn" onClick={() => fetchParticipateInfo()}>다시 시도</button>
          </div>
        )}

        {!loading && !error && (
          <>
            {match ? (
              <div className="participate-match-card">
                <div className="muted">{match.match_date}</div>
                <h2 style={{ margin: '6px 0' }}>
                  {match.awayTeamName} vs {match.homeTeamName}
                </h2>
                <div style={{ marginBottom: '10px', color: '#6b7280' }}>
                  {match.match_date} {match.startTime} · {match.fieldname || '-'}
                  <span className="badge" style={{ marginLeft: '8px' }}>
                    {match.gameStatus}
                  </span>
                </div>
                <div style={{ textAlign: 'center', margin: '20px 0' }}>
                  <button 
                    id="btnVote" 
                    className="es-btn"
                    onClick={() => setShowVoteModal(true)}
                    style={{ 
                      display: 'block', 
                      margin: '0 auto',
                      padding: '12px 24px',
                      fontSize: '16px'
                    }}
                  >
                    투표하기
                  </button>
                </div>

                <div style={{ marginTop: '10px' }} className="muted">
                  참여현황: 원정 {aggregation.away} / 홈 {aggregation.home} (총 {aggregation.total})
                </div>

                <input type="hidden" id="matchId" value={match.idx} />
              </div>
            ) : (
              <p className="muted">참여 가능한 '경기전' 경기가 없습니다.</p>
            )}

            {/* 투표 모달 */}
            {showVoteModal && (
              <div 
                id="voteModal" 
                className="vote-modal"
                onClick={(e) => {
                  if (e.target === e.currentTarget) closeModal();
                }}
              >
                <div className="modal-content">
                  <div className="modal-header">
                    <h3>⚾ 누가 이길까요?</h3>
                    <button 
                      className="modal-close-btn"
                      onClick={closeModal}
                    >
                      ✕
                    </button>
                  </div>
                  
                  <div className="modal-body">
                    <div className="match-info-modal">
                      <div className="team-vs">
                        <span className="team away">{match?.awayTeamName}</span>
                        <span className="vs-text">VS</span>
                        <span className="team home">{match?.homeTeamName}</span>
                      </div>
                      <div className="match-details">
                        {match?.match_date} {match?.startTime} · {match?.fieldname}
                      </div>
                    </div>
                    
                    <div className="vote-options">
                      <button 
                        className="vote-btn away-btn"
                        data-choice="AWAY"
                        onClick={() => handleVote('AWAY')}
                        disabled={isVoting}
                      >
                        <span className="btn-icon">🏟️</span>
                        <span className="btn-text">원정팀 {match?.awayTeamName}</span>
                      </button>
                      
                      <button 
                        className="vote-btn home-btn"
                        data-choice="HOME"
                        onClick={() => handleVote('HOME')}
                        disabled={isVoting}
                      >
                        <span className="btn-icon">🏠</span>
                        <span className="btn-text">홈팀 {match?.homeTeamName}</span>
                      </button>
                    </div>
                    
                    {voteMessage && (
                      <div className="vote-message">
                        <span className="message-icon">💬</span>
                        {voteMessage}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            <h2 style={{ marginTop: '24px' }}>내 참여 내역</h2>
            <table>
              <thead>
                <tr>
                  <th>일시</th>
                  <th>구장</th>
                  <th>원정</th>
                  <th>홈</th>
                  <th>예측</th>
                  <th>참여시각</th>
                </tr>
              </thead>
              <tbody>
                {history.length > 0 ? (
                  history.map((p, index) => (
                    <tr key={index}>
                      <td>{p.schedule.match_date}</td>
                      <td>{p.schedule.fieldname || '-'}</td>
                      <td>{p.schedule.awayTeamName}</td>
                      <td>{p.schedule.homeTeamName}</td>
                      <td>
                        {p.predicted === 'AWAY' ? `원정팀 ${p.schedule.awayTeamName}` : 
                         p.predicted === 'HOME' ? `홈팀 ${p.schedule.homeTeamName}` : 
                         p.predicted}
                      </td>
                      <td>{new Date(p.created_at).toLocaleString('ko-KR')}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="6" className="muted">참여 내역이 없습니다.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </>
        )}
      </div>
    </EventLayout>
  );
};

export default EventParticipate;
