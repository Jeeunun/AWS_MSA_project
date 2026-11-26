import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import InfoLayout from './InfoLayout';
import '../styles/info-service.css';
import awsConfig from '../config/aws-config';

const TeamList = () => {
  // 상태 관리
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [totalPlayers, setTotalPlayers] = useState(0);
  const [totalManagers, setTotalManagers] = useState(0);
  const [lastUpdate, setLastUpdate] = useState('');



  // 컴포넌트 마운트 시 데이터 로드
  useEffect(() => {
    const fetchTeams = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // 인증이 필요없는 API이므로 토큰 헤더 제거
        const response = await axios.get(`${awsConfig.API_BASE_URL}/api/info/teams/`);
        
        if (response.data.teams) {
          setTeams(response.data.teams);
          setTotalPlayers(response.data.total_players || 0);
          setTotalManagers(response.data.total_managers || 0);
          setLastUpdate(response.data.last_update || new Date().toLocaleDateString('ko-KR'));
        }
      } catch (error) {
        console.error('팀 정보 로드 실패:', error);
        setError('팀 정보를 불러오는데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };

    fetchTeams();
  }, []);

  // 로딩 상태
  if (loading) {
    return (
      <InfoLayout>
        <div className="team-list-container">
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <p>팀 정보를 불러오는 중...</p>
          </div>
        </div>
      </InfoLayout>
    );
  }

  // 에러 상태
  if (error) {
    return (
      <InfoLayout>
        <div className="team-list-container">
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <p style={{ color: '#dc3545' }}>{error}</p>
          </div>
        </div>
      </InfoLayout>
    );
  }

  return (
    <InfoLayout>
      <div className="team-list-container">

                 {/* 팀 카드 그리드 */}
         <div className="teams-grid">
           {teams.map((team) => (
             <div key={team.team_id} className="team-card">
               <div className="team-card-header">
                 <h5 className="team-name">
                   <span className="team-icon">👥</span>
                   {team.team_name}
                 </h5>
               </div>
               <div className="team-card-body">
                 <div className="team-info">
                   <div className="info-row">
                     <span className="info-label">팀 코드:</span>
                     <span className="info-value">{team.team_code}</span>
                   </div>
                   <div className="info-row">
                     <span className="info-label">감독:</span>
                     <span className="info-value">{team.manager_name || '미정'}</span>
                   </div>
                   <div className="info-row">
                     <span className="info-label">등록 선수:</span>
                     <span className="info-value">{team.player_count}명</span>
                   </div>
                 </div>
               </div>
               <div className="team-card-footer">
                 <Link to={`/info/team/${team.team_code}`} className="is-btn is-btn-outline-primary">
                   팀 상세보기
                 </Link>
               </div>
             </div>
           ))}
         </div>

        {/* 통계 요약 */}
        <div className="stats-summary">
          <div className="stats-card">
            <div className="stats-header">
              <h5 className="stats-title">
                전체 통계
              </h5>
            </div>
            <div className="stats-body">
              <div className="stats-grid">
                <div className="stat-item">
                  <h3 className="stat-number primary">{teams.length}</h3>
                  <p className="stat-label">등록된 팀</p>
                </div>
                <div className="stat-item">
                  <h3 className="stat-number success">{totalPlayers}</h3>
                  <p className="stat-label">전체 선수</p>
                </div>
                <div className="stat-item">
                  <h3 className="stat-number warning">{totalManagers}</h3>
                  <p className="stat-label">감독</p>
                </div>
                <div className="stat-item">
                  <h3 className="stat-number info">{lastUpdate}</h3>
                  <p className="stat-label">최종 업데이트</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </InfoLayout>
  );
};

export default TeamList;
