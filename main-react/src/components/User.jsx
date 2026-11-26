import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import '../styles/user-service.css';
import awsConfig from '../config/aws-config';

const User = () => {
  const { user, isAuthenticated, loading, logout, verifyToken } = useAuth();
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({});
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [eventHistory, setEventHistory] = useState({ events: [], statistics: {}, pagination: {} });
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [couponHistory, setCouponHistory] = useState({ coupons: [], statistics: {} });
  const [loadingCoupons, setLoadingCoupons] = useState(false);
  const [activeTab, setActiveTab] = useState('profile'); // 'profile', 'events', 'coupons', 'account'
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    if (loading) return;

    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    // 편집 데이터 초기화
    setEditData({
      name: user?.name || '',
      email: user?.email || '',
      tel: user?.tel || '',
      birth: user?.birth || '',
      team: user?.team || ''
    });
  }, [isAuthenticated, user, navigate, loading]);

  const loadEventHistory = async (page = 1) => {
    if (loadingEvents) return;
    
    setLoadingEvents(true);
    try {
      const response = await fetch(`${awsConfig.API_BASE_URL}/api/user/events/?page=${page}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('이벤트 참여내역 로드 성공:', data);
        setEventHistory({
          events: data.events || [],
          statistics: data.statistics || {},
          pagination: data.pagination || {}
        });
        setCurrentPage(page);
      } else {
        console.error('이벤트 참여내역 로드 실패:', response.status);
        setEventHistory({ events: [], statistics: {}, pagination: {} });
      }
    } catch (error) {
      console.error('이벤트 참여내역 로드 오류:', error);
      setEventHistory({ events: [], statistics: {}, pagination: {} });
    } finally {
      setLoadingEvents(false);
    }
  };

  const loadCouponHistory = async () => {
    if (loadingCoupons) return;
    
    setLoadingCoupons(true);
    try {
      const response = await fetch(`${awsConfig.API_BASE_URL}/api/user/coupons/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('쿠폰 현황 로드 성공:', data);
        setCouponHistory({
          coupons: data.coupons || [],
          statistics: data.statistics || {}
        });
      } else {
        console.error('쿠폰 현황 로드 실패:', response.status);
        setCouponHistory({ coupons: [], statistics: {} });
      }
    } catch (error) {
      console.error('쿠폰 현황 로드 오류:', error);
      setCouponHistory({ coupons: [], statistics: {} });
    } finally {
      setLoadingCoupons(false);
    }
  };

  const handleTabChange = (tabName) => {
    setActiveTab(tabName);
    // 탭별 데이터 로드
    if (tabName === 'events' && eventHistory.events.length === 0) {
      loadEventHistory(1);
    } else if (tabName === 'coupons' && couponHistory.coupons.length === 0) {
      loadCouponHistory();
    }
  };

  const handlePageChange = (page) => {
    loadEventHistory(page);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setEditData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSave = async () => {
    try {
      // 이메일을 제외한 데이터만 전송
      const { email, ...updateData } = editData;
      
      const response = await fetch(`${awsConfig.API_BASE_URL}/api/user/update/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        },
        body: JSON.stringify(updateData)
      });

      if (response.ok) {
        alert('정보가 성공적으로 수정되었습니다.');
        await verifyToken();
        setIsEditing(false);
      } else {
        alert('정보 수정에 실패했습니다.');
      }
    } catch (error) {
      console.error('정보 수정 오류:', error);
      alert('정보 수정 중 오류가 발생했습니다.');
    }
  };

  const handleDeleteAccount = () => {
    setShowDeleteModal(true);
  };

  const handleDeleteConfirm = async () => {
    if (deleteConfirmText !== '계정삭제') {
      alert('정확히 "계정삭제"를 입력해주세요.');
      return;
    }

    try {
      const response = await fetch(`${awsConfig.API_BASE_URL}/api/user/delete/`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        }
      });

      if (response.ok) {
        alert('계정이 성공적으로 삭제되었습니다.');
        logout();
        navigate('/');
      } else {
        const data = await response.json();
        alert(`계정 삭제 실패: ${data.error || '알 수 없는 오류'}`);
      }
    } catch (error) {
      console.error('계정 삭제 오류:', error);
      alert('계정 삭제 중 오류가 발생했습니다.');
    }
    
    setShowDeleteModal(false);
    setDeleteConfirmText('');
  };

  const handleDeleteCancel = () => {
    setShowDeleteModal(false);
    setDeleteConfirmText('');
  };

  // 프로필 탭 컴포넌트
  const ProfileTab = () => (
    <div className="tab-content">
      <div className="info-card user-info-card">
        <div className="card-header">
          <div className="card-title">
            <h3>👤 회원 정보</h3>
            <p>가입한 회원 정보입니다</p>
          </div>
          <button 
            onClick={() => setIsEditing(!isEditing)} 
            className="us-btn us-btn-outline"
          >
            {isEditing ? '취소' : '수정'}
          </button>
        </div>
        
        <div className="card-content">
          <div className="info-grid">
            <div className="info-item">
              <strong>ID:</strong> 
              <span className="info-value">{user?.username}</span>
            </div>
            
            <div className="info-item">
              <strong>이름:</strong> 
              {isEditing ? (
                <input
                  type="text"
                  name="name"
                  value={editData.name}
                  onChange={handleInputChange}
                  className="edit-input"
                  placeholder="이름을 입력하세요"
                />
              ) : (
                <span className="info-value">{user?.name || '미입력'}</span>
              )}
            </div>
            
            <div className="info-item">
              <strong>이메일:</strong> 
              <span className="info-value">{user?.email}</span>
            </div>
            
            <div className="info-item">
              <strong>전화번호:</strong> 
              {isEditing ? (
                <input
                  type="tel"
                  name="tel"
                  value={editData.tel}
                  onChange={handleInputChange}
                  className="edit-input"
                  placeholder="전화번호를 입력하세요"
                />
              ) : (
                <span className="info-value">{user?.tel || '미입력'}</span>
              )}
            </div>
            
            <div className="info-item">
              <strong>생년월일:</strong> 
              {isEditing ? (
                <input
                  type="date"
                  name="birth"
                  value={editData.birth}
                  onChange={handleInputChange}
                  className="edit-input"
                />
              ) : (
                <span className="info-value">{user?.birth || '미입력'}</span>
              )}
            </div>
            
            <div className="info-item">
              <strong>응원팀:</strong> 
              {isEditing ? (
                <select
                  name="team"
                  value={editData.team}
                  onChange={handleInputChange}
                  className="edit-input"
                >
                  <option value="">선택하세요</option>
                  <option value="두산 베어스">두산 베어스</option>
                  <option value="삼성 라이온즈">삼성 라이온즈</option>
                  <option value="LG 트윈스">LG 트윈스</option>
                  <option value="KT 위즈">KT 위즈</option>
                  <option value="SSG 랜더스">SSG 랜더스</option>
                  <option value="롯데 자이언츠">롯데 자이언츠</option>
                  <option value="한화 이글스">한화 이글스</option>
                  <option value="NC 다이노스">NC 다이노스</option>
                  <option value="기아 타이거즈">기아 타이거즈</option>
                  <option value="키움 히어로즈">키움 히어로즈</option>
                </select>
              ) : (
                <span className="info-value">{user?.team || '미선택'}</span>
              )}
            </div>
            
            <div className="info-item">
              <strong>인증 상태:</strong> 
              <span className={`status-badge ${user?.cognito_status?.toLowerCase() === 'confirmed' ? 'confirmed' : 'pending'}`}>
                {user?.cognito_status?.toLowerCase() === 'confirmed' ? '인증완료' : '인증대기'}
              </span>
            </div>
          </div>
          
          {isEditing && (
            <div className="card-actions">
              <button onClick={handleSave} className="us-btn us-btn-primary">
                저장
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // 보유 쿠폰 현황 탭 컴포넌트
  const CouponsTab = () => (
    <div className="tab-content">
      <div className="info-card coupon-history-card">
        <div className="card-header-with-refresh">
          <div className="card-title">
            <h3>🎫 보유 쿠폰 현황</h3>
            <p>이벤트 참여로 획득한 쿠폰</p>
          </div>
          <button onClick={loadCouponHistory} className="refresh-btn-new" disabled={loadingCoupons}>
            {loadingCoupons ? '로딩중...' : '새로고침'} 🔄
          </button>
        </div>
        
        <div className="card-content">
          {/* 통계 정보 - 작게 */}
          <div className="coupon-statistics-small">
            <div className="stat-item-small">
              <span className="stat-number-small">{couponHistory.statistics.total_coupons || 0}</span>
              <span className="stat-label-small">총 쿠폰</span>
            </div>
            <div className="stat-item-small">
              <span className="stat-number-small">{couponHistory.statistics.available_coupons || 0}</span>
              <span className="stat-label-small">사용가능</span>
            </div>
            <div className="stat-item-small">
              <span className="stat-number-small">{couponHistory.statistics.used_coupons || 0}</span>
              <span className="stat-label-small">사용완료</span>
            </div>
            <div className="stat-item-small">
              <span className="stat-number-small">{couponHistory.statistics.expired_coupons || 0}</span>
              <span className="stat-label-small">기간만료</span>
            </div>
          </div>

          {/* 쿠폰 목록 - 테이블 형태 */}
          <div className="coupon-table-container">
            {loadingCoupons ? (
              <div className="loading-container">
                <div className="loading-spinner"></div>
                <p>쿠폰 현황을 불러오는 중...</p>
              </div>
            ) : couponHistory.coupons.length === 0 ? (
              <div className="empty-state">
                <p>🎫 보유한 쿠폰이 없습니다.</p>
                <p>경기 예측 이벤트에 참여해서 쿠폰을 획득해보세요!</p>
              </div>
            ) : (
              <div className="coupon-table-wrapper">
                <table className="coupon-table">
                  <thead>
                    <tr>
                      <th>쿠폰 코드</th>
                      <th>쿠폰 상태</th>
                      <th>발급일</th>
                      <th>수정일</th>
                      <th>만료일</th>
                    </tr>
                  </thead>
                  <tbody>
                    {couponHistory.coupons.map((coupon, index) => (
                      <tr key={coupon.coupon_id}>
                        <td className="coupon-code-cell">
                          <div className="coupon-code-info">
                            <strong>{coupon.coupon_name}</strong>
                            <span className="coupon-amount-small">
                              {coupon.discount_amount.toLocaleString()}원 할인
                            </span>
                          </div>
                        </td>
                        <td>
                          <span className={`status-badge-table ${coupon.status_class}`}>
                            {coupon.status}
                          </span>
                        </td>
                        <td className="date-cell">
                          {new Date(coupon.created_at).toLocaleDateString('ko-KR')}
                        </td>
                        <td className="date-cell">
                          {coupon.used_at 
                            ? new Date(coupon.used_at).toLocaleDateString('ko-KR')
                            : '-'
                          }
                        </td>
                        <td className="date-cell">
                          {new Date(coupon.expires_at).toLocaleDateString('ko-KR')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  // 이벤트 참여내역 탭 컴포넌트
  const EventsTab = () => (
    <div className="tab-content">
      <div className="info-card event-history-card">
        <div className="card-header-with-refresh">
          <div className="card-title">
            <h3>🎯 이벤트 참여내역</h3>
            <p>경기 예측 참여 기록</p>
          </div>
          <button onClick={() => loadEventHistory(currentPage)} className="refresh-btn-new" disabled={loadingEvents}>
            {loadingEvents ? '로딩중...' : '새로고침'} 🔄
          </button>
        </div>
        
        <div className="card-content">
          {/* 통계 정보 - 작게 */}
          <div className="event-statistics-small">
            <div className="stat-item-small">
              <span className="stat-number-small">{eventHistory.statistics.total_predictions || 0}</span>
              <span className="stat-label-small">총 참여</span>
            </div>
            <div className="stat-item-small">
              <span className="stat-number-small">{eventHistory.statistics.correct_predictions || 0}</span>
              <span className="stat-label-small">맞춘 예측</span>
            </div>
            <div className="stat-item-small">
              <span className="stat-number-small">{eventHistory.statistics.accuracy || 0}%</span>
              <span className="stat-label-small">예측률</span>
            </div>
          </div>

          {/* 참여내역 목록 */}
          <div className="event-history-list">
            {loadingEvents ? (
              <div className="loading-container">
                <div className="loading-spinner"></div>
                <p>참여내역을 불러오는 중...</p>
              </div>
            ) : eventHistory.events.length === 0 ? (
              <div className="empty-state">
                <p>🎯 아직 참여한 이벤트가 없습니다.</p>
                <p>경기 예측 이벤트에 참여해보세요!</p>
              </div>
            ) : (
              eventHistory.events.map((event, index) => (
                <div key={event.predict_id} className="event-history-item">
                  <div className="event-info">
                    <div className="match-info">
                      <span className="teams">
                        {event.schedule.away_team} vs {event.schedule.home_team}
                      </span>
                      <span className="date">
                        {new Date(event.schedule.game_date).toLocaleDateString('ko-KR')}
                      </span>
                    </div>
                    <div className="prediction-info">
                      <span className="predicted">
                        예측: <strong>{event.predicted_winner === 'HOME' ? event.schedule.home_team : event.schedule.away_team}</strong>
                      </span>
                      {event.schedule.gameStatus === 'END' && event.is_correct !== null && (
                        <span className={`result ${event.is_correct ? 'correct' : 'incorrect'}`}>
                          {event.is_correct ? '✅ 정답' : '❌ 오답'}
                        </span>
                      )}
                      {event.schedule.gameStatus === 'END' && event.is_correct === null && (
                        <span className="result completed">🏁 경기 종료</span>
                      )}
                      {event.schedule.gameStatus === 'BEFORE' && (
                        <span className="result pending">⏳ 경기 예정</span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
            
            {/* 페이지네이션 */}
            {eventHistory.pagination && eventHistory.pagination.total_pages > 1 && (
              <div className="pagination-container">
                <div className="pagination">
                  <button 
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={!eventHistory.pagination.has_previous || loadingEvents}
                    className="pagination-btn"
                  >
                    이전
                  </button>
                  
                  <div className="pagination-info">
                    <span>
                      {currentPage} / {eventHistory.pagination.total_pages} 페이지
                    </span>
                    <span className="total-count">
                      (총 {eventHistory.pagination.total_count}개)
                    </span>
                  </div>
                  
                  <button 
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={!eventHistory.pagination.has_next || loadingEvents}
                    className="pagination-btn"
                  >
                    다음
                  </button>
                </div>
              </div>
            )}
            
            <div className="view-more">
              <Link to="/event/participate" className="us-btn">
                이벤트 참여하러 가기
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // 계정 관리 탭 컴포넌트
  const AccountTab = () => (
    <div className="tab-content">
      <div className="info-card account-management-card">
        <div className="card-header">
          <div className="card-title">
            <h3>⚙️ 계정 관리</h3>
            <p>계정 관련 설정</p>
          </div>
        </div>
        
        <div className="card-content">
          <div className="account-actions">
            <div className="action-item">
              <div className="action-info">
                <h4>계정 탈퇴</h4>
                <p>계정을 영구적으로 삭제합니다. 이 작업은 되돌릴 수 없습니다.</p>
              </div>
              <button onClick={handleDeleteAccount} className="us-btn us-btn-danger">
                계정 탈퇴
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="user-container">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>사용자 정보를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="user-container">
      <div className="user-header">
      </div>

      <div className="user-content-sidebar">
        {/* 사이드바 */}
        <div className="sidebar">
          <h3>마이페이지</h3>
          <div className="sidebar-menu">
            <button 
              className={`menu-item ${activeTab === 'profile' ? 'active' : ''}`}
              onClick={() => handleTabChange('profile')}
            >
              <span className="menu-icon">👤</span>
              <span className="menu-text">프로필 보기</span>
            </button>
            <button 
              className={`menu-item ${activeTab === 'events' ? 'active' : ''}`}
              onClick={() => handleTabChange('events')}
            >
              <span className="menu-icon">🎯</span>
              <span className="menu-text">이벤트 참여현황</span>
            </button>
            <button 
              className={`menu-item ${activeTab === 'coupons' ? 'active' : ''}`}
              onClick={() => handleTabChange('coupons')}
            >
              <span className="menu-icon">🎫</span>
              <span className="menu-text">보유 쿠폰 현황</span>
            </button>
            <button 
              className={`menu-item ${activeTab === 'account' ? 'active' : ''}`}
              onClick={() => handleTabChange('account')}
            >
              <span className="menu-icon">⚙️</span>
              <span className="menu-text">계정 관리</span>
            </button>
          </div>
        </div>

        {/* 메인 콘텐츠 */}
        <div className="main-content">
          {activeTab === 'profile' && <ProfileTab />}
          {activeTab === 'events' && <EventsTab />}
          {activeTab === 'coupons' && <CouponsTab />}
          {activeTab === 'account' && <AccountTab />}
        </div>
      </div>

      {/* 계정 삭제 확인 모달 */}
      {showDeleteModal && (
        <div className="modal-overlay">
          <div className="modal-content delete-modal">
            <div className="modal-header">
              <h3>⚠️ 계정 탈퇴</h3>
            </div>
            <div className="modal-body">
              <div className="warning-message">
                <p><strong>주의: 이 작업은 되돌릴 수 없습니다!</strong></p>
                <ul>
                  <li>• 모든 개인 정보가 영구적으로 삭제됩니다</li>
                  <li>• 참여한 이벤트 기록이 모두 사라집니다</li>
                  <li>• 동일한 이메일로 재가입이 어려울 수 있습니다</li>
                </ul>
              </div>
              
              <div className="confirm-section">
                <label>계속하시려면 아래에 <strong>"계정삭제"</strong>를 정확히 입력해주세요:</label>
                <input
                  type="text"
                  value={deleteConfirmText}
                  onChange={(e) => setDeleteConfirmText(e.target.value)}
                  className="confirm-input"
                  placeholder="계정삭제"
                />
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={handleDeleteCancel} className="us-btn us-btn-outline">
                취소
              </button>
              <button 
                onClick={handleDeleteConfirm} 
                className="us-btn us-btn-danger"
                disabled={deleteConfirmText !== '계정삭제'}
              >
                계정 삭제
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default User;