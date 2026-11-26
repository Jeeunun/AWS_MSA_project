import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import InfoLayout from './InfoLayout';
import Chart from 'chart.js/auto';
import '../styles/info-service.css';
import awsConfig from '../config/aws-config';

const StatsAnalysis = () => {
  // 통계 데이터 상태
  const [statsData, setStatsData] = useState({
    summary: {
      totalTeams: 0,
      totalPlayers: 0,
      totalManagers: 0,
      avgPlayersPerTeam: 0
    },
    positionStats: {
      pitchers: 0,
      catchers: 0,
      infielders: 0,
      outfielders: 0
    },
    teamStats: []
  });

  // 로딩 상태
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 통계 데이터 로드
  useEffect(() => {
    const fetchStatsData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        console.log('=== 통계분석 데이터 로드 시작 ===');
        const response = await axios.get(`${awsConfig.API_BASE_URL}/api/info/stats/analysis/`);
        
        console.log('통계분석 응답:', response.data);
        
        if (response.data) {
          setStatsData(response.data);
          console.log('통계 데이터 설정 완료:', response.data);
        }
      } catch (error) {
        console.error('통계분석 데이터 로드 실패:', error);
        setError('통계 데이터를 불러오는데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };

    fetchStatsData();
  }, []);

  // 차트 렌더링 함수 (useEffect보다 먼저 정의)
  const renderCharts = useCallback(() => {
    console.log('=== renderCharts 함수 실행 ===');
    console.log('statsData:', statsData);
    console.log('teamStats:', statsData.teamStats);
    
    // 기존 차트 제거
    const existingCharts = document.querySelectorAll('canvas');
    existingCharts.forEach(canvas => {
      const chart = Chart.getChart(canvas);
      if (chart) {
        chart.destroy();
      }
    });

    // 포지션별 차트
    const positionCtx = document.getElementById('positionChart');
    if (positionCtx && positionCtx.getContext) {
      console.log('포지션별 차트 데이터 구성:');
      console.log('  - data:', [
        statsData.positionStats.pitchers,
        statsData.positionStats.catchers,
        statsData.positionStats.infielders,
        statsData.positionStats.outfielders
      ]);
      
      new Chart(positionCtx, {
        type: 'pie',
        data: {
          labels: ['투수', '포수', '내야수', '외야수'],
          datasets: [{
            data: [
              statsData.positionStats.pitchers,
              statsData.positionStats.catchers,
              statsData.positionStats.infielders,
              statsData.positionStats.outfielders
            ],
            backgroundColor: [
              '#FF6384',
              '#36A2EB',
              '#FFCE56',
              '#4BC0C0'
            ]
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
      console.log('포지션별 차트 생성 완료');
    } else {
      console.error('positionChart canvas를 찾을 수 없습니다!');
    }

    // 팀별 차트
    const teamCtx = document.getElementById('teamChart');
    if (teamCtx && teamCtx.getContext) {
      console.log('팀별 차트 데이터 구성:');
      console.log('  - labels:', statsData.teamStats.map(team => team.teamName));
      console.log('  - data:', statsData.teamStats.map(team => team.totalPlayers));
      
      new Chart(teamCtx, {
        type: 'bar',
        data: {
          labels: statsData.teamStats.map(team => team.teamName),
          datasets: [{
            label: '선수 수',
            data: statsData.teamStats.map(team => team.totalPlayers),
            backgroundColor: '#36A2EB'
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
      console.log('팀별 차트 생성 완료');
    } else {
      console.error('teamChart canvas를 찾을 수 없습니다!');
    }
  }, [statsData]);

  // 차트 렌더링을 위한 useEffect
  useEffect(() => {
    if (!loading && statsData.teamStats.length > 0) {
      // DOM이 완전히 렌더링된 후 차트를 그리기 위해 약간의 지연
      const timer = setTimeout(() => {
        renderCharts();
      }, 100);

      return () => clearTimeout(timer);
    }
  }, [loading, statsData, renderCharts]);

  return (
    <InfoLayout>
      <div className="stats-analysis-container">
        {/* 페이지 헤더 */}
        <div className="stats-header">
          <h1 className="stats-title">
            <span className="stats-icon">📊</span>
            통계 분석
          </h1>
          <Link to="/info" className="is-btn is-btn-outline-secondary">
            <span className="btn-icon">←</span>
            팀 목록으로
          </Link>
        </div>

        {/* 로딩 상태 */}
        {loading && (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>통계 데이터를 불러오는 중...</p>
          </div>
        )}

        {/* 에러 상태 */}
        {error && (
          <div className="error-container">
            <span className="error-icon">⚠️</span>
            <p>{error}</p>
            <button 
              className="is-btn is-btn-primary"
              onClick={() => window.location.reload()}
            >
              다시 시도
            </button>
          </div>
        )}

        {/* 통계 데이터가 로드된 경우에만 표시 */}
        {!loading && !error && statsData.teamStats.length > 0 && (
          <>
            {/* 통계 요약 */}
        <div className="stats-summary">
          <div className="summary-card">
            <div className="summary-icon primary">🏟️</div>
            <div className="summary-content">
              <h3 className="summary-number">{statsData.summary.totalTeams}</h3>
              <p className="summary-label">등록된 팀</p>
            </div>
          </div>
          <div className="summary-card">
            <div className="summary-icon success">👥</div>
            <div className="summary-content">
              <h3 className="summary-number">{statsData.summary.totalPlayers}</h3>
              <p className="summary-label">전체 선수</p>
            </div>
          </div>
          <div className="summary-card">
            <div className="summary-icon warning">👨‍💼</div>
            <div className="summary-content">
              <h3 className="summary-number">{statsData.summary.totalManagers}</h3>
              <p className="summary-label">감독</p>
            </div>
          </div>
          <div className="summary-card">
            <div className="summary-icon info">📈</div>
            <div className="summary-content">
              <h3 className="summary-number">{statsData.summary.avgPlayersPerTeam}</h3>
              <p className="summary-label">팀당 평균 선수</p>
            </div>
          </div>
        </div>

        {/* 포지션별 통계 */}
        <div className="stats-charts">
          <div className="chart-card">
            <div className="chart-header primary">
              <h5 className="chart-title">
                <span className="chart-icon">🥧</span>
                포지션별 선수 분포
              </h5>
            </div>
            <div className="chart-body">
              <canvas id="positionChart" width="400" height="200"></canvas>
            </div>
          </div>
          <div className="chart-card">
            <div className="chart-header success">
              <h5 className="chart-title">
                <span className="chart-icon">📊</span>
                팀별 선수 수
              </h5>
            </div>
            <div className="chart-body">
              <canvas id="teamChart" width="400" height="200"></canvas>
            </div>
          </div>
        </div>

        {/* 상세 통계 테이블 */}
        <div className="stats-table-card">
          <div className="table-header info">
            <h5 className="table-title">
              <span className="table-icon">📋</span>
              팀별 상세 통계
            </h5>
          </div>
          <div className="table-body">
            <div className="table-responsive">
              <table className="stats-table">
                <thead>
                  <tr>
                    <th>팀명</th>
                    <th>전체 선수</th>
                    <th>투수</th>
                    <th>포수</th>
                    <th>내야수</th>
                    <th>외야수</th>
                    <th>우타</th>
                    <th>좌타</th>
                    <th>우투</th>
                    <th>좌투</th>
                  </tr>
                </thead>
                <tbody>
                  {console.log('테이블 렌더링 - teamStats:', statsData.teamStats)}
                  {statsData.teamStats.map((team, index) => {
                    console.log(`팀 ${index}:`, team);
                    return (
                      <tr key={index}>
                        <td><strong>{team.teamName || '팀명 없음'}</strong></td>
                        <td>{team.totalPlayers || 0}</td>
                        <td>{team.pitchers || 0}</td>
                        <td>{team.catchers || 0}</td>
                        <td>{team.infielders || 0}</td>
                        <td>{team.outfielders || 0}</td>
                        <td>{team.rightBatters || 0}</td>
                        <td>{team.leftBatters || 0}</td>
                        <td>{team.rightPitchers || 0}</td>
                        <td>{team.leftPitchers || 0}</td>
                      </tr>
                    );
                  })}
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

export default StatsAnalysis;
