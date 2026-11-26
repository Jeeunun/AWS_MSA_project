import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import '../styles/common.css';

const Confirm = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { confirmRegistration, logout } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    code: ''
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  // URL 파라미터에서 사용자명 가져오기
  useEffect(() => {
    const username = searchParams.get('username');
    if (username) {
      setFormData(prev => ({ ...prev, username }));
    }
  }, [searchParams]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // 에러 초기화
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.username.trim()) {
      newErrors.username = '사용자명을 입력해주세요.';
    }

    if (!formData.code.trim()) {
      newErrors.code = '인증 코드를 입력해주세요.';
    } else if (formData.code.length !== 6) {
      newErrors.code = '인증 코드는 6자리여야 합니다.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setErrors({});
    setSuccessMessage('');
    
    try {
      const result = await confirmRegistration(formData.username, formData.code);
      if (result.success) {
        setSuccessMessage('이메일 인증이 완료되었습니다! 로그인 페이지로 이동합니다.');
        
        // 이메일 인증 완료 후 로그아웃하여 인증 상태 초기화
        try {
          await logout();
        } catch (logoutError) {
          console.log('로그아웃 오류 (무시):', logoutError);
        }
        
        // 잠시 후 로그인 페이지로 이동
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      }
    } catch (error) {
      console.error('인증 오류:', error);
      let errorMessage = '인증에 실패했습니다. 다시 시도해주세요.';
      
      // Cognito 에러 코드에 따른 메시지
      if (error.code) {
        switch (error.code) {
          case 'CodeMismatchException':
            errorMessage = '인증 코드가 올바르지 않습니다.';
            break;
          case 'ExpiredCodeException':
            errorMessage = '인증 코드가 만료되었습니다.';
            break;
          case 'UserNotFoundException':
            errorMessage = '존재하지 않는 사용자입니다.';
            break;
          default:
            errorMessage = `인증 오류: ${error.message || error.code}`;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setErrors({ submit: errorMessage });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="confirm-container">
      <div className="confirm-form-wrapper">
        <h1>이메일 인증</h1>
        
        <div className="info-box">
          <h3>📧 인증 코드 확인 방법</h3>
          <p><strong>이메일</strong>에서 인증 코드를 확인하세요:</p>
          <div className="code-example">
            <code>사용자 {formData.username}에게 인증 코드 XXXXXX 발송</code>
          </div>
          <p>이 <strong>6자리 숫자</strong>를 아래에 입력하세요.</p>
        </div>
        
        {/* 성공 메시지 */}
        {successMessage && (
          <div className="msg ok">
            {successMessage}
          </div>
        )}
        
        {/* 에러 메시지 */}
        {errors.submit && (
          <div className="msg err">
            {errors.submit}
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">사용자명</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              className={errors.username ? 'error' : ''}
              readOnly
            />
            {errors.username && <div className="error-message">{errors.username}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="code">인증 코드</label>
            <input
              type="text"
              id="code"
              name="code"
              value={formData.code}
              onChange={handleInputChange}
              placeholder="6자리 숫자 입력"
              maxLength="6"
              className={errors.code ? 'error' : ''}
            />
            {errors.code && <div className="error-message">{errors.code}</div>}
          </div>

          <button 
            type="submit" 
            disabled={isSubmitting}
            className="us-submit-btn"
          >
            {isSubmitting ? '인증 중...' : '인증하기'}
          </button>
        </form>

        <div className="sub">
          <p>인증 코드가 보이지 않나요?</p>
          <p>이메일 스팸함도 확인해보세요!</p>
        </div>
      </div>
    </div>
  );
};

export default Confirm;
