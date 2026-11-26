import React, { useState, useEffect } from 'react';
import EventLayout from './EventLayout';
import awsConfig from '../config/aws-config';
import '../styles/event-service.css';

const EventSchedule = () => {
  const [selectedDate, setSelectedDate] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  // API에서 경기 데이터 가져오기
  const fetchSchedules = async (date = '', page = 1) => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('accessToken');
      const params = new URLSearchParams();
      if (date) params.append('date', date);
      if (page > 1) params.append('page', page);
      
      const response = await fetch(`${awsConfig.API_BASE_URL}/api/event/schedules/?${params}`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      
      if (!response.ok) {
        throw new Error('경기 데이터를 불러오는데 실패했습니다.');
      }
      
      const data = await response.json();
      setSchedules(data.results.schedules || []);
      setTotalCount(data.count || 0);
      setTotalPages(Math.ceil((data.count || 0) / 20));
      
    } catch (err) {
      console.error('경기 데이터 로드 실패:', err);
      setError(err.message);
      setSchedules([]);
    } finally {
      setLoading(false);
    }
  };

  // 컴포넌트 마운트 시 데이터 로드
  useEffect(() => {
    fetchSchedules();
  }, []);

  // 날짜 필터링 처리
  const handleDateFilter = (e) => {
    e.preventDefault();
    setCurrentPage(1);
    fetchSchedules(selectedDate, 1);
  };

  // 필터 초기화
  const resetFilter = () => {
    setSelectedDate('');
    setCurrentPage(1);
    fetchSchedules('', 1);
  };

  // 페이지 변경
  const handlePageChange = (page) => {
    setCurrentPage(page);
    fetchSchedules(selectedDate, page);
  };

  // 오늘 날짜
  const today = new Date().toISOString().split('T')[0];

  // 경기 상태 표시
  const getGameStatusBadge = (status) => {
    switch (status) {
      case 'BEFORE': return <span className="badge">경기전</span>;
      case 'PLAYING': return <span className="badge" style={{backgroundColor: '#10b981'}}>경기중</span>;
      case 'AFTER': return <span className="badge" style={{backgroundColor: '#6b7280'}}>경기종료</span>;
      default: return <span className="badge">{status}</span>;
    }
  };

  return (
    <EventLayout>
      <div className="schedule-container">
        <h2>경기일정·결과</h2>

        {/* 도구 모음 */}
        <form className="toolbar" onSubmit={handleDateFilter}>
          <label>일자 선택</label>
          <input 
            className="input" 
            type="date" 
            name="date" 
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
          />
          <button className="es-btn" type="submit">필터</button>
          <span className="muted today-info">오늘: {today}</span>
          {selectedDate && (
            <button className="es-btn" type="button" onClick={resetFilter} style={{ marginLeft: '8px' }}>
              초기화
            </button>
          )}
        </form>

        {/* 로딩 및 에러 상태 */}
        {loading && (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <p>경기 데이터를 불러오는 중...</p>
          </div>
        )}

        {error && (
          <div style={{ textAlign: 'center', padding: '20px', color: '#dc3545' }}>
            <p>{error}</p>
            <button className="es-btn" onClick={() => fetchSchedules()}>다시 시도</button>
          </div>
        )}

        {/* 경기 테이블 */}
        {!loading && !error && (
          <>
            <table className="schedule-table">
              <thead>
                <tr>
                  <th>날짜</th>
                  <th>시간</th>
                  <th>원정팀</th>
                  <th>홈팀</th>
                  <th>결과</th>
                  <th>구장</th>
                  <th>상태</th>
                </tr>
              </thead>
              <tbody>
                {schedules.length > 0 ? (
                  schedules.map((schedule) => (
                    <tr key={schedule.idx}>
                      <td>{schedule.match_date}</td>
                      <td>{schedule.startTime || '-'}</td>
                      <td className="team-name">{schedule.awayTeamName}</td>
                      <td className="team-name">{schedule.homeTeamName}</td>
                      <td>
                        {schedule.gameStatus === 'END' && schedule.awayResult !== null && schedule.homeResult !== null ? (
                          <span>
                            {schedule.awayResult} : {schedule.homeResult}
                            {schedule.winner && (
                              <small style={{ marginLeft: '4px', color: '#10b981' }}>
                                ({(() => {
                                  const winner = schedule.winner?.toLowerCase();
                                  if (winner === 'away') {
                                    return `${schedule.awayTeamName} 승`;
                                  } else if (winner === 'home') {
                                    return `${schedule.homeTeamName} 승`;
                                  } else if (winner === 'draw') {
                                    return '무승부';
                                  }
                                  return '';
                                })()})
                              </small>
                            )}
                          </span>
                        ) : '-'}
                      </td>
                      <td>{schedule.fieldname || '-'}</td>
                      <td>{getGameStatusBadge(schedule.gameStatus)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="7" style={{ textAlign: 'center', padding: '20px', color: '#6b7280' }}>
                      {selectedDate ? '해당 날짜에 경기가 없습니다.' : '등록된 경기가 없습니다.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>

            {/* 페이지네이션 */}
            {totalPages > 1 && (
              <div className="pagination" style={{ marginTop: '20px', textAlign: 'center' }}>
                <div className="pagination-info" style={{ marginBottom: '10px' }}>
                  총 {totalCount}개 경기 • {currentPage} / {totalPages} 페이지
                </div>
                <div className="pagination-controls">
                  {currentPage > 1 && (
                    <button 
                      onClick={() => handlePageChange(currentPage - 1)}
                      className="es-btn"
                      style={{ margin: '0 4px' }}
                    >
                      ← 이전
                    </button>
                  )}
                  
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
                        className={`es-btn ${currentPage === pageNum ? 'es-btn-primary' : ''}`}
                        style={{ margin: '0 2px' }}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                  
                  {currentPage < totalPages && (
                    <button 
                      onClick={() => handlePageChange(currentPage + 1)}
                      className="es-btn"
                      style={{ margin: '0 4px' }}
                    >
                      다음 →
                    </button>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </EventLayout>
  );
};

export default EventSchedule;