import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import '../styles/common.css';

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);


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
      newErrors.username = 'ID를 입력해주세요.';
    } else if (formData.username.length < 4) {
      newErrors.username = 'ID는 4자 이상이어야 합니다.';
    }

    if (!formData.password) {
      newErrors.password = '비밀번호를 입력해주세요.';
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
    
    try {
      const result = await login(formData.username, formData.password);
      if (result.success) {
        // 로그인 성공 시 바로 홈페이지로 이동
        navigate('/');
      }
    } catch (error) {
      console.error('로그인 오류:', error);
      let errorMessage = '로그인에 실패했습니다.';
      
      // Cognito 에러 코드에 따른 메시지
      if (error.code) {
        switch (error.code) {
          case 'UserNotFoundException':
            errorMessage = '등록되지 않은 ID입니다.';
            break;
          case 'NotAuthorizedException':
            errorMessage = 'ID 또는 비밀번호가 올바르지 않습니다.';
            break;
          case 'UserNotConfirmedException':
            errorMessage = '이메일 인증이 필요합니다.';
            break;
          case 'TooManyFailedAttemptsException':
            errorMessage = '로그인 시도가 너무 많습니다. 잠시 후 다시 시도해주세요.';
            break;
          default:
            errorMessage = `로그인 오류: ${error.message || error.code}`;
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
    <div className="login-container">
      <div className="login-form-wrapper">
        <h1>로그인</h1>
        

        
        {/* 에러 메시지 */}
        {errors.submit && (
          <div className="msg err">
            {errors.submit}
          </div>
        )}
        
        <form onSubmit={handleSubmit} id="loginForm" noValidate>
          <div className="form-group">
            <label htmlFor="username">ID</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              autoComplete="username"
              required
              className={errors.username ? 'error' : ''}
            />
            {errors.username && <div className="error-message">{errors.username}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="password">비밀번호</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              autoComplete="current-password"
              required
              className={errors.password ? 'error' : ''}
            />
            {errors.password && <div className="error-message">{errors.password}</div>}
          </div>

          <button 
            type="submit" 
            id="btnSignIn"
            disabled={isSubmitting}
            className="us-submit-btn"
          >
            {isSubmitting ? '로그인 중...' : '로그인'}
          </button>
        </form>

        <div className="sub">
          아직 계정이 없나요? <Link to="/signup">회원가입</Link>
        </div>
      </div>
    </div>
  );
};

export default Login;