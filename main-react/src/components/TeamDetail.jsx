import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import InfoLayout from './InfoLayout';
import '../styles/info-service.css';
import awsConfig from '../config/aws-config';

const TeamDetail = () => {
  const { teamCode } = useParams();
  const navigate = useNavigate();
  
  // 상태 관리
  const [team, setTeam] = useState(null);
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeFilter, setActiveFilter] = useState('all');
  const [filteredPlayers, setFilteredPlayers] = useState([]);

  // 컴포넌트 마운트 시 데이터 로드
  useEffect(() => {
    const fetchTeamDetail = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // 팀 상세보기는 인증이 필요없는 API이므로 토큰 헤더 제거
        const response = await axios.get(`${awsConfig.API_BASE_URL}/api/info/teams/${teamCode}/`);
        
        console.log('=== React TeamDetail 디버깅 ===');
        console.log('API 응답 전체:', response);
        console.log('response.data:', response.data);
        console.log('response.data.team:', response.data.team);
        console.log('response.data.team?.players:', response.data.team?.players);
        
        if (response.data.team) {
          console.log('팀 데이터 설정 성공');
          console.log('팀 정보:', response.data.team);
          console.log('선수 목록:', response.data.team.players);
          
          // 선수들의 포지션 정보 확인
          if (response.data.team.players && response.data.team.players.length > 0) {
            console.log('=== 선수 포지션 정보 ===');
            response.data.team.players.forEach((player, index) => {
              console.log(`선수 ${index + 1}: ${player.p_name} - 포지션: ${player.p_position} (타입: ${typeof player.p_position})`);
            });
          }
          
          setTeam(response.data.team);
          setPlayers(response.data.team.players || []);
          setFilteredPlayers(response.data.team.players || []);
        } else {
          console.log('팀 데이터가 없습니다!');
          console.log('response.data 구조:', Object.keys(response.data));
        }
      } catch (error) {
        console.error('팀 상세 정보 로드 실패:', error);
        setError('팀 정보를 불러오는데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };

    if (teamCode) {
      fetchTeamDetail();
    }
  }, [teamCode]);

  // 포지션별 필터링
  const filterPlayers = (position) => {
    console.log('=== 필터링 디버깅 ===');
    console.log('선택된 포지션:', position);
    console.log('전체 선수 수:', players.length);
    console.log('현재 필터링된 선수 수:', filteredPlayers.length);
    
    setActiveFilter(position);
    if (position === 'all') {
      console.log('전체 선택 - 모든 선수 표시');
      setFilteredPlayers(players);
    } else {
      // 한국어 포지션을 영어 코드로 매핑
      const positionMapping = {
        'P': ['투수'],
        'C': ['포수'],
        'IF': ['내야수'],
        'OF': ['외야수']
      };
      
      const targetPositions = positionMapping[position] || [];
      console.log(`매핑된 포지션: ${position} -> ${targetPositions}`);
      
      // 포지션 값이 정확히 일치하는지 확인
      const filtered = players.filter(player => {
        const playerPosition = player.p_position;
        const isMatch = targetPositions.includes(playerPosition);
        console.log(`선수 ${player.p_name}의 포지션: "${playerPosition}" -> 매칭: ${isMatch}`);
        return isMatch;
      });
      
      console.log(`${position} 포지션 필터링 결과:`, filtered.length, '명');
      console.log('필터링된 선수들:', filtered);
      setFilteredPlayers(filtered);
    }
  };

  // 포지션별 선수 수 계산
  const getPositionCount = (position) => {
    // 한국어 포지션을 영어 코드로 매핑
    const positionMapping = {
      'P': ['투수'],
      'C': ['포수'],
      'IF': ['내야수'],
      'OF': ['외야수']
    };
    
    const targetPositions = positionMapping[position] || [];
    const count = players.filter(player => targetPositions.includes(player.p_position)).length;
    console.log(`${position} 포지션 선수 수: ${count}명 (매핑: ${targetPositions})`);
    return count;
  };

  // 홈구장 정보 (하드코딩된 정보)
  const getHomeStadium = (teamCode) => {
    const stadiums = {
      'KIA': '광주기아챔피언스필드',
      'LG': '잠실야구장',
      'SSG': '인천SSG랜더스필드',
      'LT': '사직야구장',
      'WO': '고척스카이돔',
      'KT': '수원KT위즈파크',
      'NC': '창원NC파크',
      'DS': '잠실야구장',
      'SS': '대구삼성라이온즈파크',
      'HH': '대전한화생명이글스파크'
    };
    return stadiums[teamCode] || '정보 없음';
  };

  // 로딩 상태
  if (loading) {
    return (
      <InfoLayout>
        <div className="team-detail-container">
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <p>팀 정보를 불러오는 중...</p>
          </div>
        </div>
      </InfoLayout>
    );
  }

  // 에러 상태
  if (error || !team) {
    return (
      <InfoLayout>
        <div className="team-detail-container">
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <p style={{ color: '#dc3545' }}>{error || '팀을 찾을 수 없습니다.'}</p>
            <button 
              className="is-btn is-btn-primary mt-3"
              onClick={() => navigate('/info')}
            >
              팀 목록으로 돌아가기
            </button>
          </div>
        </div>
      </InfoLayout>
    );
  }

  return (
    <InfoLayout>
      <div className="team-detail-container">
        {/* 헤더 */}
        <div className="page-header">
          <div className="page-title">
            <span className="baseball-icon">⚾</span>
            {team.team_name}
          </div>
          <div className="header-actions">
            <Link to="/info" className="is-btn is-btn-outline-secondary">
              <i className="fas fa-arrow-left me-2"></i>팀 목록으로
            </Link>
            <Link to="/info/search" className="is-btn is-btn-primary">
              <i className="fas fa-search me-2"></i>선수 검색
            </Link>
          </div>
        </div>

        {/* 팀 정보 */}
        <div className="team-info-section">
          <div className="team-info-grid">
            <div className="team-info-card">
              <div className="card-header">
                <h5><i className="fas fa-info-circle me-2"></i>팀 기본 정보</h5>
              </div>
              <div className="card-body">
                <div className="info-grid">
                  <div className="info-item">
                    <label>팀 코드</label>
                    <span className="info-value">{team.team_code}</span>
                  </div>
                  <div className="info-item">
                    <label>홈구장</label>
                    <span className="info-value">{getHomeStadium(team.team_code)}</span>
                  </div>
                  <div className="info-item full-width">
                    <label>감독</label>
                    <span className="info-value manager">{team.manager?.m_name || '정보 없음'}</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="team-stats-card">
              <div className="card-header">
                <h5><i className="fas fa-chart-pie me-2"></i>팀 통계</h5>
              </div>
              <div className="card-body">
                <div className="stats-grid">
                  <div className="stat-item">
                    <div className="stat-number">{players.length}</div>
                    <div className="stat-label">전체 선수</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-number">{getPositionCount('P')}</div>
                    <div className="stat-label">투수</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-number">{players.length - getPositionCount('P')}</div>
                    <div className="stat-label">야수</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 선수 목록 */}
        <div className="players-section">
          <div className="card">
            <div className="card-header">
              <h5><i className="fas fa-list me-2"></i>선수 목록 ({players.length}명)</h5>
            </div>
            <div className="card-body">
              {/* 포지션별 필터 */}
              <div className="filter-buttons">
                <button 
                  type="button" 
                  className={`filter-btn ${activeFilter === 'all' ? 'active' : ''}`}
                  onClick={() => filterPlayers('all')}
                >
                  전체
                </button>
                <button 
                  type="button" 
                  className={`filter-btn ${activeFilter === 'P' ? 'active' : ''}`}
                  onClick={() => filterPlayers('P')}
                >
                  투수
                </button>
                <button 
                  type="button" 
                  className={`filter-btn ${activeFilter === 'C' ? 'active' : ''}`}
                  onClick={() => filterPlayers('C')}
                >
                  포수
                </button>
                <button 
                  type="button" 
                  className={`filter-btn ${activeFilter === 'IF' ? 'active' : ''}`}
                  onClick={() => filterPlayers('IF')}
                >
                  내야수
                </button>
                <button 
                  type="button" 
                  className={`filter-btn ${activeFilter === 'OF' ? 'active' : ''}`}
                  onClick={() => filterPlayers('OF')}
                >
                  외야수
                </button>
              </div>

              <div className="table-responsive">
                <table className="players-table">
                  <thead>
                    <tr>
                      <th>번호</th>
                      <th>이름</th>
                      <th>포지션</th>
                      <th>키/몸무게</th>
                      <th>투타</th>
                      <th>생년월일</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredPlayers.length > 0 ? (
                      filteredPlayers.map((player, index) => (
                        <tr key={player.idx} className={index % 2 === 0 ? 'even' : 'odd'}>
                          <td className="player-number">{player.p_number || '-'}</td>
                          <td className="player-name">{player.p_name}</td>
                          <td className="player-position">
                            <span className="position-badge">{player.p_position}</span>
                          </td>
                          <td className="player-physical">
                            {player.height_cm || player.weight_kg ? (
                              `${player.height_cm || '-'} / ${player.weight_kg || '-'}`
                            ) : (
                              '정보 없음'
                            )}
                          </td>
                          <td className="player-info">{player.p_info || '정보 없음'}</td>
                          <td className="player-birth">{player.birth || '정보 없음'}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="6" className="no-data">
                          <i className="fas fa-info-circle me-2"></i>
                          {activeFilter === 'all' ? '등록된 선수가 없습니다.' : '해당 포지션의 선수가 없습니다.'}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </InfoLayout>
  );
};

export default TeamDetail;
