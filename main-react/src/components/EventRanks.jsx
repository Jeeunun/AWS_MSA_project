import React, { useState, useEffect } from 'react';
import EventLayout from './EventLayout';
import awsConfig from '../config/aws-config';
import '../styles/event-service.css';

const EventRanks = () => {
  // 상태 관리
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // 순위 데이터 상태
  const [totalRanks, setTotalRanks] = useState([]);
  const [attackRanks, setAttackRanks] = useState([]);
  const [defendRanks, setDefendRanks] = useState([]);

  // API에서 순위 데이터 가져오기
  const fetchRanks = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${awsConfig.API_BASE_URL}/api/event/ranks/`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      
      if (!response.ok) {
        throw new Error('순위 데이터를 불러오는데 실패했습니다.');
      }
      
      const data = await response.json();
      setTotalRanks(data.total || []);
      setAttackRanks(data.attack || []);
      setDefendRanks(data.defense || []);
      
    } catch (err) {
      console.error('순위 데이터 로드 실패:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 컴포넌트 마운트 시 데이터 로드
  useEffect(() => {
    fetchRanks();
  }, []);

  return (
    <EventLayout>
      <div className="ranks-container">

        {/* 로딩 및 에러 상태 */}
        {loading && (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <p>순위 데이터를 불러오는 중...</p>
          </div>
        )}

        {error && (
          <div style={{ textAlign: 'center', padding: '20px', color: '#dc3545' }}>
            <p>{error}</p>
            <button className="es-btn" onClick={() => fetchRanks()}>다시 시도</button>
          </div>
        )}

        {!loading && !error && (
          <>
            <h2>📊 종합 순위</h2>
        <div className="table-container">
          <table className="ranks-table">
            <thead>
              <tr>
                <th>순위</th>
                <th>팀</th>
                <th>경기</th>
                <th>승</th>
                <th>무</th>
                <th>패</th>
                <th>승률</th>
                <th>게임차</th>
                <th>연속</th>
              </tr>
            </thead>
            <tbody>
              {totalRanks.map((row) => (
                <tr key={`${row.rank}-${row.team}`}>
                  <td>{row.rank}</td>
                  <td className="team-name">{row.team}</td>
                  <td>{row.game}</td>
                  <td>{row.win}</td>
                  <td>{row.draw}</td>
                  <td>{row.loss}</td>
                  <td>{row.wpct}</td>
                  <td>{row.gb}</td>
                  <td className={`streak ${row.streak.startsWith('W') ? 'win' : 'loss'}`}>
                    {row.streak}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h2>🔥 공격 순위</h2>
        <div className="table-container">
          <table className="ranks-table">
            <thead>
              <tr>
                <th>순위</th>
                <th>팀</th>
                <th>타수</th>
                <th>안타</th>
                <th>2루타</th>
                <th>3루타</th>
                <th>홈런</th>
                <th>타점</th>
                <th>득점</th>
                <th>도루</th>
                <th>사구</th>
                <th>삼진</th>
                <th>병살</th>
                <th>타율</th>
                <th>출루율</th>
                <th>장타율</th>
                <th>OPS</th>
              </tr>
            </thead>
            <tbody>
              {attackRanks.map((row) => (
                <tr key={`${row.rank}-${row.team}`}>
                  <td>{row.rank}</td>
                  <td className="team-name">{row.team}</td>
                  <td>{row.batAb}</td>
                  <td>{row.batH}</td>
                  <td>{row.bat2b}</td>
                  <td>{row.bat3b}</td>
                  <td>{row.batHr}</td>
                  <td>{row.batRbi}</td>
                  <td>{row.batR}</td>
                  <td>{row.batSb}</td>
                  <td>{row.batBbhp}</td>
                  <td>{row.batSo}</td>
                  <td>{row.batGdp}</td>
                  <td>{row.batAvg}</td>
                  <td>{row.batObp}</td>
                  <td>{row.batSlg}</td>
                  <td>{row.batOps}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h2>🛡 수비 순위</h2>
        <div className="table-container">
          <table className="ranks-table">
            <thead>
              <tr>
                <th>순위</th>
                <th>팀</th>
                <th>이닝</th>
                <th>피안타</th>
                <th>피홈런</th>
                <th>실점</th>
                <th>자책</th>
                <th>사사구</th>
                <th>탈삼진</th>
                <th>평균자책</th>
                <th>실책</th>
                <th>WHIP</th>
                <th>QS</th>
                <th>홀드</th>
                <th>세이브</th>
              </tr>
            </thead>
            <tbody>
              {defendRanks.map((row) => (
                <tr key={`${row.rank}-${row.team}`}>
                  <td>{row.rank}</td>
                  <td className="team-name">{row.team}</td>
                  <td>{row.pitIp}</td>
                  <td>{row.pitH}</td>
                  <td>{row.pitHr}</td>
                  <td>{row.pitR}</td>
                  <td>{row.pitEr}</td>
                  <td>{row.pitBbhp}</td>
                  <td>{row.pitSo}</td>
                  <td>{row.pitEra}</td>
                  <td>{row.fldErr}</td>
                  <td>{row.pitWhip}</td>
                  <td>{row.pitQs}</td>
                  <td>{row.pitHld}</td>
                  <td>{row.pitSv}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
          </>
        )}
      </div>
    </EventLayout>
  );
};

export default EventRanks;
