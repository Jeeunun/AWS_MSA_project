import React, { useState, useEffect, useCallback } from 'react';
import EventLayout from './EventLayout';
import { useAuth } from '../contexts/AuthContext';
import awsConfig from '../config/aws-config';
import '../styles/event-service.css';

const EventCoupons = () => {
  const { isAuthenticated } = useAuth();
  
  // 상태 관리
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // 쿠폰 데이터 상태
  const [coupons, setCoupons] = useState([]);
  const [displayName, setDisplayName] = useState('사용자');
  const [totalCount, setTotalCount] = useState(0);
  const [userId, setUserId] = useState('');

  // API에서 쿠폰 데이터 가져오기
  const fetchCoupons = useCallback(async () => {
    if (!isAuthenticated) {
      setError('로그인이 필요합니다.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${awsConfig.API_BASE_URL}/api/event/coupons/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('쿠폰 데이터를 불러오는데 실패했습니다.');
      }
      
      const data = await response.json();
      setCoupons(data.coupons || []);
      setDisplayName(data.display_name || '사용자');
      setTotalCount(data.total_count || 0);
      setUserId(data.user_id || '');
      
    } catch (err) {
      console.error('쿠폰 데이터 로드 실패:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  // 컴포넌트 마운트 시 데이터 로드
  useEffect(() => {
    fetchCoupons();
  }, [isAuthenticated, fetchCoupons]);

  // 현재 시간 (만료 여부 판단용)
  const now = new Date();

  // 쿠폰 상태에 따른 클래스와 배지 결정
  const getCouponStatus = (coupon) => {
    const isExpired = new Date(coupon.expire_at) <= now;
    
    if (coupon.coupon_status === 2 && !isExpired) {
      return { badge: '미사용', className: 'ok' };
    } else if (coupon.coupon_status === 1) {
      return { badge: '사용', className: '' };
    } else {
      return { badge: '만료', className: '' };
    }
  };

  // 쿠폰 행의 클래스 결정
  const getRowClassName = (coupon) => {
    const isExpired = new Date(coupon.expire_at) <= now;
    return (coupon.coupon_status !== 2 || isExpired) ? 'dimmed' : '';
  };

  return (
    <EventLayout>
      <div className="coupons-container">
        <h2>쿠폰 현황</h2>

        {/* 로딩 및 에러 상태 */}
        {loading && (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <p>쿠폰 데이터를 불러오는 중...</p>
          </div>
        )}

        {error && (
          <div style={{ textAlign: 'center', padding: '20px', color: '#dc3545' }}>
            <p>{error}</p>
            {isAuthenticated && (
              <button className="es-btn" onClick={() => fetchCoupons()}>다시 시도</button>
            )}
          </div>
        )}

        {!loading && !error && isAuthenticated && (
          <>
            <p className="muted" style={{ margin: '.25rem 0 1rem' }}>
          <strong>{displayName}</strong>님이 현재 보유한 쿠폰의 개수는
          <strong>{totalCount}</strong>개 입니다.
          <span className="muted" style={{ marginLeft: '.5rem' }}>
            (user: {userId})
          </span>
        </p>

        <table>
          <thead>
            <tr>
              <th style={{ width: '45%' }}>쿠폰 코드</th>
              <th style={{ width: '15%' }}>상태</th>
              <th style={{ width: '20%' }}>발급일</th>
              <th style={{ width: '20%' }}>만료일</th>
            </tr>
          </thead>
          <tbody>
            {coupons.length > 0 ? (
              coupons.map((coupon, index) => {
                const status = getCouponStatus(coupon);
                const rowClass = getRowClassName(coupon);
                
                return (
                  <tr key={index} className={rowClass}>
                    <td style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}>
                      {coupon.code}
                    </td>
                    <td>
                      <span className={`badge ${status.className}`}>
                        {status.badge}
                      </span>
                    </td>
                    <td>{new Date(coupon.created_at).toLocaleString('ko-KR')}</td>
                    <td>{new Date(coupon.expire_at).toLocaleString('ko-KR')}</td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan="4" className="muted">보유한 쿠폰이 없습니다.</td>
              </tr>
            )}
          </tbody>
        </table>
          </>
        )}

        {!isAuthenticated && (
          <div style={{ textAlign: 'center', padding: '20px', color: '#6b7280' }}>
            <p>로그인 후 쿠폰 현황을 확인할 수 있습니다.</p>
          </div>
        )}
      </div>
    </EventLayout>
  );
};

export default EventCoupons;
