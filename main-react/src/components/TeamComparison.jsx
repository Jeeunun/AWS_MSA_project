import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import InfoLayout from './InfoLayout';
import Chart from 'chart.js/auto';
import '../styles/info-service.css';
import awsConfig from '../config/aws-config';

const TeamComparison = () => {
  // 팀 선택 상태
  const [selectedTeams, setSelectedTeams] = useState({
    team1: '',
    team2: ''
  });

  // 비교 결과 상태
  const [comparisonData, setComparisonData] = useState(null);

  // 팀 목록 상태
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 팀 목록 로드
  useEffect(() => {
    const fetchTeams = async () => {
      try {
        const response = await axios.get(`${awsConfig.API_BASE_URL}/api/info/teams/options/`);
        if (response.data && response.data.teams) {
          setTeams(response.data.teams);
        }
      } catch (error) {
        console.error('팀 목록 로드 실패:', error);
        setError('팀 목록을 불러오는데 실패했습니다.');
      }
    };

    fetchTeams();
  }, []);

  // 팀 선택 변경 핸들러
  const handleTeamChange = (e) => {
    const { name, value } = e.target;
    setSelectedTeams(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // 팀 비교 실행
  const handleComparison = async (e) => {
    e.preventDefault();
    
    if (selectedTeams.team1 === selectedTeams.team2) {
      alert('서로 다른 팀을 선택해주세요.');
      return;
    }

    if (selectedTeams.team1 && selectedTeams.team2) {
      try {
        setLoading(true);
        setError(null);
        
        console.log('=== 팀 비교 API 호출 ===');
        const response = await axios.get(`${awsConfig.API_BASE_URL}/api/info/teams/compare/?team1=${selectedTeams.team1}&team2=${selectedTeams.team2}`);
        
        console.log('팀 비교 응답:', response.data);
        
        if (response.data) {
          setComparisonData(response.data);
        }
      } catch (error) {
        console.error('팀 비교 실패:', error);
        setError('팀 비교 데이터를 불러오는데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    }
  };

  // 차트 렌더링 함수 (useEffect보다 먼저 정의)
  const renderCharts = useCallback(() => {


    // 기존 차트 제거
    const existingCharts = document.querySelectorAll('canvas');
    existingCharts.forEach(canvas => {
      const chart = Chart.getChart(canvas);
      if (chart) {
        chart.destroy();
      }
    });

    // 비교 차트
    const comparisonCtx = document.getElementById('comparisonChart');
    if (comparisonCtx) {
      new Chart(comparisonCtx, {
        type: 'bar',
        data: {
          labels: ['전체 선수', '투수', '야수'],
          datasets: [{
            label: comparisonData.team1.name,
            data: [
              comparisonData.team1.stats.total_players,
              comparisonData.team1.stats.pitchers,
              comparisonData.team1.stats.position_players
            ],
            backgroundColor: '#3b82f6'
          }, {
            label: comparisonData.team2.name,
            data: [
              comparisonData.team2.stats.total_players,
              comparisonData.team2.stats.pitchers,
              comparisonData.team2.stats.position_players
            ],
            backgroundColor: '#10b981'
          }]
        },
        options: {
          responsive: true,
          scales: {
            y: {
              beginAtZero: true
            }
          }
        }
      });
    }

    // 포지션별 분포 비교 차트
    const positionComparisonCtx = document.getElementById('positionComparisonChart');
    if (positionComparisonCtx) {
      new Chart(positionComparisonCtx, {
        type: 'doughnut',
        data: {
          labels: [comparisonData.team1.name, comparisonData.team2.name],
          datasets: [{
            data: [
              comparisonData.team1.stats.total_players,
              comparisonData.team2.stats.total_players
            ],
            backgroundColor: ['#3b82f6', '#10b981']
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: 'bottom'
            }
          }
        }
      });
    }
  }, [comparisonData]);

  // 차트 렌더링을 위한 useEffect
  useEffect(() => {
    if (comparisonData) {
      renderCharts();
    }
  }, [comparisonData, renderCharts]);

  // 차이 계산 함수
  const calculateDifference = (value1, value2) => {
    const diff = value1 - value2;
    if (diff > 0) {
      return { text: `+${diff}명`, className: 'text-success' };
    } else if (diff < 0) {
      return { text: `${diff}명`, className: 'text-danger' };
    } else {
      return { text: '동일', className: 'text-muted' };
    }
  };

  return (
    <InfoLayout>
      <div className="team-comparison-container">
        {/* 페이지 헤더 */}
        <div className="comparison-header">
          <h1 className="comparison-title">
            팀 비교
          </h1>
          <Link to="/info" className="is-btn is-btn-outline-secondary">
            <span className="btn-icon">←</span>
            팀 목록으로
          </Link>
        </div>

        {/* 팀 선택 */}
        <div className="team-selection-card">
          <div className="selection-header primary">
            <h5 className="selection-title">
              비교할 팀 선택
            </h5>
          </div>
          <div className="selection-body">
            <form onSubmit={handleComparison}>
              <div className="team-selection-form">
                <div className="team-select-group">
                  <label htmlFor="team1" className="team-select-label">팀 1</label>
                  <select
                    id="team1"
                    name="team1"
                    value={selectedTeams.team1}
                    onChange={handleTeamChange}
                    className="team-select"
                    required
                  >
                    <option value="">팀을 선택하세요</option>
                    {teams.length > 0 ? (
                      teams.map(team => (
                        <option key={team.team_code} value={team.team_code}>
                          {team.team_name}
                        </option>
                      ))
                    ) : (
                      <option value="" disabled>로딩 중...</option>
                    )}
                  </select>
                </div>
                
                <div className="vs-divider">
                  <span className="vs-text">VS</span>
                </div>
                
                <div className="team-select-group">
                  <label htmlFor="team2" className="team-select-label">팀 2</label>
                  <select
                    id="team2"
                    name="team2"
                    value={selectedTeams.team2}
                    onChange={handleTeamChange}
                    className="team-select"
                    required
                  >
                    <option value="">팀을 선택하세요</option>
                    {teams.length > 0 ? (
                      teams.map(team => (
                        <option key={team.team_code} value={team.team_code}>
                          {team.team_name}
                        </option>
                      ))
                    ) : (
                      <option value="" disabled>로딩 중...</option>
                    )}
                  </select>
                </div>
              </div>
              
              <div className="comparison-actions">
                <button type="submit" className="is-btn is-btn-primary is-btn-lg" disabled={loading}>
                  {loading ? '비교 중...' : '팀 비교하기'}
                </button>
              </div>
              
              {/* 에러 메시지 */}
              {error && (
                <div className="error-message">
                  <span className="error-icon">⚠️</span>
                  {error}
                </div>
              )}
            </form>
          </div>
        </div>

        {/* 비교 결과 */}
        {comparisonData && (
          <>
            {/* 팀 정보 비교 */}
            <div className="teams-comparison">
              {/* 팀 1 정보 */}
              <div className="team-info-card primary">
                <div className="team-info-header">
                  <h5 className="team-info-title">
                    <span className="team-info-icon">👥</span>
                    {comparisonData.team1.name}
                  </h5>
                </div>
                <div className="team-info-body">
                  <div className="team-stats-summary">
                    <div className="stat-item">
                      <h3 className="stat-number primary">{comparisonData.team1.stats.total_players}</h3>
                      <p className="stat-label">전체 선수</p>
                    </div>
                    <div className="stat-item">
                      <h3 className="stat-number success">{comparisonData.team1.stats.pitchers}</h3>
                      <p className="stat-label">투수</p>
                    </div>
                    <div className="stat-item">
                      <h3 className="stat-number warning">{comparisonData.team1.stats.position_players}</h3>
                      <p className="stat-label">야수</p>
                    </div>
                  </div>
                  
                  <hr className="team-divider" />
                  
                  <div className="team-details">
                    <div className="detail-section">
                      <p className="detail-title"><strong>포지션별 분포:</strong></p>
                      <ul className="detail-list">
                        <li>포수: {comparisonData.team1.stats.catchers}명</li>
                        <li>내야수: {comparisonData.team1.stats.infielders}명</li>
                        <li>외야수: {comparisonData.team1.stats.outfielders}명</li>
                      </ul>
                    </div>
                    <div className="detail-section">
                      <p className="detail-title"><strong>투타별 분포:</strong></p>
                      <ul className="detail-list">
                        <li>우타: {comparisonData.team1.stats.right_batters}명</li>
                        <li>좌타: {comparisonData.team1.stats.left_batters}명</li>
                        <li>우투: {comparisonData.team1.stats.right_pitchers}명</li>
                        <li>좌투: {comparisonData.team1.stats.left_pitchers}명</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* 팀 2 정보 */}
              <div className="team-info-card success">
                <div className="team-info-header">
                  <h5 className="team-info-title">
                    <span className="team-info-icon">👥</span>
                    {comparisonData.team2.name}
                  </h5>
                </div>
                <div className="team-info-body">
                  <div className="team-stats-summary">
                    <div className="stat-item">
                      <h3 className="stat-number success">{comparisonData.team2.stats.total_players}</h3>
                      <p className="stat-label">전체 선수</p>
                    </div>
                    <div className="stat-item">
                      <h3 className="stat-number success">{comparisonData.team2.stats.pitchers}</h3>
                      <p className="stat-label">투수</p>
                    </div>
                    <div className="stat-item">
                      <h3 className="stat-number warning">{comparisonData.team2.stats.position_players}</h3>
                      <p className="stat-label">야수</p>
                    </div>
                  </div>
                  
                  <hr className="team-divider" />
                  
                  <div className="team-details">
                    <div className="detail-section">
                      <p className="detail-title"><strong>포지션별 분포:</strong></p>
                      <ul className="detail-list">
                        <li>포수: {comparisonData.team2.stats.catchers}명</li>
                        <li>내야수: {comparisonData.team2.stats.infielders}명</li>
                        <li>외야수: {comparisonData.team2.stats.outfielders}명</li>
                      </ul>
                    </div>
                    <div className="detail-section">
                      <p className="detail-title"><strong>투타별 분포:</strong></p>
                      <ul className="detail-list">
                        <li>우타: {comparisonData.team2.stats.right_batters}명</li>
                        <li>좌타: {comparisonData.team2.stats.left_batters}명</li>
                        <li>우투: {comparisonData.team2.stats.right_pitchers}명</li>
                        <li>좌투: {comparisonData.team2.stats.left_pitchers}명</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* 비교 차트 */}
            <div className="comparison-charts">
              <div className="chart-card">
                <div className="chart-header info">
                  <h5 className="chart-title">
                    <span className="chart-icon">📊</span>
                    선수 수 비교
                  </h5>
                </div>
                <div className="chart-body">
                  <canvas id="comparisonChart" width="400" height="200"></canvas>
                </div>
              </div>
              <div className="chart-card">
                <div className="chart-header warning">
                  <h5 className="chart-title">
                    <span className="chart-icon">🥧</span>
                    포지션별 분포 비교
                  </h5>
                </div>
                <div className="chart-body">
                  <canvas id="positionComparisonChart" width="400" height="200"></canvas>
                </div>
              </div>
            </div>

            {/* 상세 비교 테이블 */}
            <div className="comparison-table-card">
              <div className="table-header secondary">
                <h5 className="table-title">
                  <span className="table-icon">📋</span>
                  상세 비교
                </h5>
              </div>
              <div className="table-body">
                <div className="table-responsive">
                  <table className="comparison-table">
                    <thead>
                      <tr>
                        <th>구분</th>
                        <th>{comparisonData.team1.name}</th>
                        <th>{comparisonData.team2.name}</th>
                        <th>차이</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><strong>전체 선수</strong></td>
                        <td>{comparisonData.team1.stats.total_players}명</td>
                        <td>{comparisonData.team2.stats.total_players}명</td>
                        <td className={calculateDifference(comparisonData.team1.stats.total_players, comparisonData.team2.stats.total_players).className}>
                          {calculateDifference(comparisonData.team1.stats.total_players, comparisonData.team2.stats.total_players).text}
                        </td>
                      </tr>
                      <tr>
                        <td><strong>투수</strong></td>
                        <td>{comparisonData.team1.stats.pitchers}명</td>
                        <td>{comparisonData.team2.stats.pitchers}명</td>
                        <td className={calculateDifference(comparisonData.team1.stats.pitchers, comparisonData.team2.stats.pitchers).className}>
                          {calculateDifference(comparisonData.team1.stats.pitchers, comparisonData.team2.stats.pitchers).text}
                        </td>
                      </tr>
                      <tr>
                        <td><strong>야수</strong></td>
                        <td>{comparisonData.team1.stats.position_players}명</td>
                        <td>{comparisonData.team2.stats.position_players}명</td>
                        <td className={calculateDifference(comparisonData.team1.stats.position_players, comparisonData.team2.stats.position_players).className}>
                          {calculateDifference(comparisonData.team1.stats.position_players, comparisonData.team2.stats.position_players).text}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </InfoLayout>
  );
};

export default TeamComparison;
