import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import '../styles/common.css';

const Signup = () => {
  const navigate = useNavigate();
  const { signup } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    name: '',
    password: '',
    confirmPassword: '',
    email: '',
    tel: '',
    birth: '',
    team: 'none'
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const teams = [
    { value: 'none', label: '선택 안함' },
    { value: 'LG', label: 'LG' },
    { value: '두산', label: '두산' },
    { value: '키움', label: '키움' },
    { value: 'SSG', label: 'SSG' },
    { value: 'KT', label: 'KT' },
    { value: '한화', label: '한화' },
    { value: 'KIA', label: 'KIA' },
    { value: '롯데', label: '롯데' },
    { value: '삼성', label: '삼성' },
    { value: 'NC', label: 'NC' }
  ];

  // 비밀번호 유효성 검사
  const validatePassword = (password) => {
    const rules = [
      password.length >= 8,
      /[A-Z]/.test(password),
      /[a-z]/.test(password),
      /\d/.test(password),
      /[^A-Za-z0-9]/.test(password)
    ];
    const kinds = [rules[1], rules[2], rules[3], rules[4]].filter(Boolean).length;
    return rules[0] && kinds >= 3;
  };

  // 전화번호 자동 보정 (010 → +8210)
  const formatPhoneNumber = (phone) => {
    const cleaned = phone.replace(/\D+/g, '');
    if (/^0\d{9,10}$/.test(cleaned)) {
      return '+82' + cleaned.slice(1);
    }
    return phone;
  };

  // 생년월일 자동 형식 변환 (YYYYMMDD → YYYY-MM-DD)
  const formatBirthdate = (birthdate) => {
    const cleaned = birthdate.replace(/\D+/g, '');
    if (cleaned.length <= 4) return cleaned;
    if (cleaned.length <= 6) return `${cleaned.slice(0, 4)}-${cleaned.slice(4)}`;
    if (cleaned.length <= 8) return `${cleaned.slice(0, 4)}-${cleaned.slice(4, 6)}-${cleaned.slice(6)}`;
    return `${cleaned.slice(0, 4)}-${cleaned.slice(4, 6)}-${cleaned.slice(6, 8)}`;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    let formattedValue = value;

    // 전화번호 자동 보정
    if (name === 'tel') {
      formattedValue = formatPhoneNumber(value);
    }

    // 생년월일 자동 형식 변환
    if (name === 'birth') {
      formattedValue = formatBirthdate(value);
    }

    setFormData(prev => ({
      ...prev,
      [name]: formattedValue
    }));

    // 에러 초기화
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }

    // 비밀번호 확인 에러 초기화
    if (name === 'password' || name === 'confirmPassword') {
      if (errors.confirmPassword) {
        setErrors(prev => ({
          ...prev,
          confirmPassword: ''
        }));
      }
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.username.trim()) {
      newErrors.username = 'ID를 입력해주세요.';
    } else if (formData.username.length < 4) {
      newErrors.username = 'ID는 4자 이상이어야 합니다.';
    } else if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
      newErrors.username = 'ID는 영문, 숫자, 언더스코어(_)만 사용 가능합니다.';
    }

    if (!formData.name.trim()) {
      newErrors.name = '이름을 입력해주세요.';
    }

    if (!formData.password) {
      newErrors.password = '비밀번호를 입력해주세요.';
    } else if (!validatePassword(formData.password)) {
      newErrors.password = '비밀번호는 8자 이상, 영문/숫자/특수문자 중 3가지 이상 조합이어야 합니다.';
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = '비밀번호 확인을 입력해주세요.';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = '비밀번호가 일치하지 않습니다.';
    }

    if (!formData.email) {
      newErrors.email = '이메일을 입력해주세요.';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = '올바른 이메일 형식을 입력해주세요.';
    }

    if (!formData.tel) {
      newErrors.tel = '전화번호를 입력해주세요.';
    }

    if (!formData.birth) {
      newErrors.birth = '생년월일을 입력해주세요.';
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
    
    try {
      // Cognito 회원가입 - 필수 필드만 전송
      const { ...signupData } = formData;
      const result = await signup(
        signupData.username,
        signupData.password,
        signupData.email,
        signupData.name,
        signupData.tel,
        signupData.birth,
        signupData.team
      );
      
      if (result.success) {
        // 회원가입 성공 시 확인 페이지로 이동 (사용자명 포함)
        navigate(`/confirm?username=${signupData.username}`);
      }
    } catch (error) {
      console.error('회원가입 오류:', error);
      let errorMessage = '회원가입 중 오류가 발생했습니다. 다시 시도해주세요.';
      
      // Cognito 에러 코드에 따른 메시지
      if (error.code) {
        switch (error.code) {
          case 'UsernameExistsException':
            errorMessage = '이미 사용 중인 ID입니다.';
            break;
          case 'InvalidPasswordException':
            errorMessage = '비밀번호가 요구사항을 충족하지 않습니다.';
            break;
          case 'InvalidParameterException':
            errorMessage = '입력 정보가 올바르지 않습니다.';
            break;
          default:
            errorMessage = `회원가입 오류: ${error.message || error.code}`;
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
    <div className="signup-container">
      <div className="signup-form-wrapper">
        <h1>회원가입</h1>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">ID</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              placeholder="사용할 ID를 입력하세요"
              className={errors.username ? 'error' : ''}
            />
            <div className="helptext">4자 이상, 영문/숫자/언더스코어(_)만 사용 가능합니다.</div>
            {errors.username && <div className="error-message">{errors.username}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="name">이름</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              placeholder="홍길동"
              className={errors.name ? 'error' : ''}
            />
            {errors.name && <div className="error-message">{errors.name}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="password">비밀번호</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              required
              minLength="8"
              className={errors.password ? 'error' : ''}
            />
            <div className="helptext" id="pw_help">
              8자 이상, <b>영문 대/소문자</b>, <b>숫자</b>, <b>특수문자</b> 중 <b>3가지 이상</b> 조합을 권장합니다.
            </div>
            {errors.password && <div className="error-message">{errors.password}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">비밀번호 확인</label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleInputChange}
              required
              minLength="8"
              className={errors.confirmPassword ? 'error' : ''}
            />
            {errors.confirmPassword && <div className="error-message">{errors.confirmPassword}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="email">이메일</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              required
              className={errors.email ? 'error' : ''}
            />
            {errors.email && <div className="error-message">{errors.email}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="tel">전화번호</label>
            <input
              type="text"
              id="tel"
              name="tel"
              value={formData.tel}
              onChange={handleInputChange}
              placeholder="+821012345678"
              required
              className={errors.tel ? 'error' : ''}
            />
            <div className="helptext">예: +821012345678 (입력 시 010으로 쓰면 자동으로 +8210으로 보정합니다)</div>
            {errors.tel && <div className="error-message">{errors.tel}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="birth">생년월일</label>
            <input
              type="text"
              id="birth"
              name="birth"
              value={formData.birth}
              onChange={handleInputChange}
              placeholder="YYYY-MM-DD"
              required
              className={errors.birth ? 'error' : ''}
            />
            <div className="helptext">예: 1990-01-01 (숫자만 입력하면 자동으로 형식이 변환됩니다)</div>
            {errors.birth && <div className="error-message">{errors.birth}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="team">응원팀</label>
            <select
              id="team"
              name="team"
              value={formData.team}
              onChange={handleInputChange}
            >
              {teams.map(team => (
                <option key={team.value} value={team.value}>
                  {team.label}
                </option>
              ))}
            </select>
          </div>

          {errors.submit && <div className="error-message submit-error">{errors.submit}</div>}

          <button type="submit" disabled={isSubmitting} className="us-submit-btn">
            {isSubmitting ? '가입 중...' : '가입하기'}
          </button>
        </form>

        <div className="sub">
          이미 계정이 있나요? <Link to="/login">로그인</Link>
        </div>
      </div>
    </div>
  );
};

export default Signup;