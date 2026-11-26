import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { signIn, signUp, confirmSignUp, signOut, getCurrentUser, fetchAuthSession } from 'aws-amplify/auth';
import awsConfig from '../config/aws-config';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  // Django API에서 사용자 정보 가져오기
  const getCurrentUserInfo = async () => {
    try {
      const cognitoUser = await getCurrentUser();
      console.log('Cognito 사용자 객체:', cognitoUser);
      
      // JWT 토큰 가져오기
      const session = await fetchAuthSession();
      const idToken = session.tokens.idToken.toString();
      
      // Django API에 사용자 정보 동기화 요청
      try {
        const response = await fetch(`${awsConfig.API_BASE_URL}/api/user/profile/`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${idToken}`
          }
        });
        
        if (response.ok) {
          const djangoUserInfo = await response.json();
          console.log('Django에서 가져온 사용자 정보:', djangoUserInfo);
          
          // Django에서 가져온 정보를 사용
          const userInfo = {
            id: djangoUserInfo.cognito_sub || cognitoUser.userId,
            username: djangoUserInfo.username,
            email: djangoUserInfo.email,
            name: djangoUserInfo.name,
            tel: djangoUserInfo.tel,
            birth: djangoUserInfo.birth,
            team: djangoUserInfo.team,
            date_joined: djangoUserInfo.date_joined,
            cognito_status: djangoUserInfo.cognito_status // Django에서 가져온 인증 상태
          };
          
          console.log('최종 사용자 정보:', userInfo);
          
          setUser(userInfo);
          setIsAuthenticated(true);
          return userInfo;
        } else {
          console.error('Django API 호출 실패:', response.status);
          // Django API 실패 시 Cognito 정보만 사용
          return await getCognitoUserInfo(cognitoUser);
        }
      } catch (apiError) {
        console.error('Django API 호출 오류:', apiError);
        // Django API 오류 시 Cognito 정보만 사용
        return await getCognitoUserInfo(cognitoUser);
      }
    } catch (error) {
      console.log('인증된 사용자 없음:', error);
      setUser(null);
      setIsAuthenticated(false);
      return null;
    }
  };

  // Cognito에서만 사용자 정보 가져오기 (fallback)
  const getCognitoUserInfo = async (cognitoUser) => {
    try {
      const username = cognitoUser.username;
      const session = await fetchAuthSession();
      
      let email = '';
      let name = '';
      if (session.tokens.idToken) {
        const payload = session.tokens.idToken.payload;
        email = payload.email || '';
        name = payload.name || payload['cognito:username'] || username;
      }
      
      const userInfo = {
        id: cognitoUser.userId || cognitoUser.username,
        username: username,
        email: email,
        name: name || username,
        tel: '',
        birth: '',
        team: '',
        date_joined: '',
        cognito_status: 'UNCONFIRMED' // 기본값
      };
      
      setUser(userInfo);
      setIsAuthenticated(true);
      return userInfo;
    } catch (error) {
      console.error('Cognito 정보 가져오기 실패:', error);
      setUser(null);
      setIsAuthenticated(false);
      return null;
    }
  };

  // 토큰 검증 및 사용자 정보 가져오기
  const verifyToken = useCallback(async () => {
    try {
      setLoading(true);
      const userInfo = await getCurrentUserInfo();
      if (userInfo) {
        // JWT 토큰 가져오기
        const session = await fetchAuthSession();
        const idToken = session.tokens.idToken.toString();
        localStorage.setItem('accessToken', idToken);
        
        // 인증 상태 업데이트
        setUser(userInfo);
        setIsAuthenticated(true);
      } else {
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error('토큰 검증 실패:', error);
      setUser(null);
      setIsAuthenticated(false);
      localStorage.removeItem('accessToken');
    } finally {
      setLoading(false);
    }
  }, []);

  // 로그인
  const login = async (username, password) => {
    try {
      console.log('Cognito 로그인 시도:', username);
      const cognitoUser = await signIn({ username, password });
      
      console.log('로그인 성공:', cognitoUser);
      
      // 사용자 정보 설정
      const userInfo = await getCurrentUserInfo();
      
      // JWT 토큰 가져오기
      const session = await fetchAuthSession();
      const idToken = session.tokens.idToken.toString();
      localStorage.setItem('accessToken', idToken);
      
      // Django API에 사용자 정보 동기화 요청
      try {
        const response = await fetch(`${awsConfig.API_BASE_URL}/api/user/profile/`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${idToken}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (response.ok) {
          console.log('Django API 사용자 정보 동기화 성공');
          
          // Django에서 사용자 정보 가져와서 React 상태 업데이트
          const djangoUserData = await response.json();
          console.log('Django 사용자 데이터:', djangoUserData);
          
          // React 사용자 정보에 Django 데이터 병합
          if (djangoUserData) {
            const updatedUserInfo = {
              ...userInfo,
              tel: djangoUserData.tel || userInfo.tel || '',
              birth: djangoUserData.birth || userInfo.birth || '',
              team: djangoUserData.team || userInfo.team || '',
              name: djangoUserData.name || userInfo.name || '',
              email: djangoUserData.email || userInfo.email || '',
              date_joined: djangoUserData.date_joined || userInfo.date_joined || ''
            };
            setUser(updatedUserInfo);
            console.log('업데이트된 사용자 정보:', updatedUserInfo);
            console.log('React 상태 업데이트 완료');
            
            // 인증 상태 업데이트
            setIsAuthenticated(true);
            return { success: true, user: updatedUserInfo };
          }
        } else {
          console.log('Django API 사용자 정보 동기화 실패:', response.status);
        }
      } catch (apiError) {
        console.log('Django API 호출 실패:', apiError);
      }
      
      // Django API 실패 시 기본 사용자 정보로 인증 상태 업데이트
      setUser(userInfo);
      setIsAuthenticated(true);
      
      return { success: true, user: userInfo };
    } catch (error) {
      console.error('로그인 실패:', error);
      throw error;
    }
  };

  // 회원가입
  const signup = async (username, password, email, name, tel, birth, team) => {
    try {
      console.log('Cognito 회원가입 시도:', username);
      
      // 1. Cognito 회원가입 - 구조분해 할당 제거
      const signUpResult = await signUp({
        username: username,
        password: password,
        options: {
          userAttributes: {
            email: email,
            name: name,
            preferred_username: username,
            phone_number: tel,  // 전화번호
            birthdate: birth,   // 생년월일
            'custom:team': team // 선호하는 팀 (커스텀 속성)
          }
        }
      });
      
      console.log('Cognito 회원가입 성공:', signUpResult);
      console.log('SignUp 결과 전체:', signUpResult);
      console.log('SignUp 결과 키들:', Object.keys(signUpResult));
      
      // user 객체 추출 - 다양한 구조 대응
      let user = null;
      if (signUpResult && signUpResult.user) {
        user = signUpResult.user;
      } else if (signUpResult && signUpResult.userId) {
        user = signUpResult;
      } else if (signUpResult) {
        user = signUpResult;
      }
      
      console.log('추출된 user 객체:', user);
      
      // Cognito sub 값 추출 (사용자 ID) - 안전한 방식으로
      let cognitoSub = '';
      if (user && user.userId) {
        cognitoSub = user.userId;
      } else if (user && user.sub) {
        cognitoSub = user.sub;
      } else if (user && user.username) {
        cognitoSub = user.username; // 임시로 username 사용
      } else {
        cognitoSub = username; // 최후 수단으로 입력받은 username 사용
      }
      
      console.log('Cognito sub 값:', cognitoSub);
      console.log('Cognito sub 값 길이:', cognitoSub.length);
      console.log('Cognito sub 값 타입:', typeof cognitoSub);
      
      // 2. Django User 서비스에 사용자 정보 전송
      try {
        const apiUrl = `${awsConfig.API_BASE_URL}/api/user/signup/`;
        const requestData = {
          username: username,
          password: password,  // 비밀번호 추가
          email: email,
          cognito_sub: cognitoSub,  // Cognito sub 값 추가
          name: name || username,
          tel: tel || '',
          birth: birth || '',
          team: team || ''
        };
        
        console.log('=== DJANGO API 호출 디버깅 ===');
        console.log('API URL:', apiUrl);
        console.log('Request Data:', requestData);
        console.log('awsConfig.API_BASE_URL:', awsConfig.API_BASE_URL);
        
        const response = await fetch(apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestData)
        });
        
        console.log('Response Status:', response.status);
        console.log('Response Headers:', Object.fromEntries(response.headers.entries()));
        
        if (response.ok) {
          const result = await response.json();
          console.log('Django API 사용자 생성 성공:', result);
        } else {
          const errorText = await response.text();
          console.error('Django API 사용자 생성 실패:');
          console.error('Status:', response.status);
          console.error('Status Text:', response.statusText);
          console.error('Response Text:', errorText);
          
          // JSON 파싱 시도
          try {
            const errorData = JSON.parse(errorText);
            console.error('Error Data (JSON):', errorData);
          } catch (parseError) {
            console.error('응답이 JSON 형식이 아님');
          }
        }
      } catch (apiError) {
        console.error('Django API 호출 실패:', apiError);
        console.error('Error details:', {
          message: apiError.message,
          stack: apiError.stack,
          name: apiError.name
        });
      }
      
      return { success: true, user };
    } catch (error) {
      console.error('회원가입 실패:', error);
      throw error;
    }
  };

  // 이메일 확인
  const confirmRegistration = async (username, code) => {
    try {
      console.log('이메일 확인 시도:', username, code);
      await confirmSignUp({ username, confirmationCode: code });
      console.log('이메일 확인 성공');
      return { success: true };
    } catch (error) {
      console.error('이메일 확인 실패:', error);
      throw error;
    }
  };

  // 로그아웃
  const logout = async () => {
    try {
      console.log('Cognito 로그아웃 시도');
      await signOut();
      
      // 로컬 상태 정리
      setUser(null);
      setIsAuthenticated(false);
      localStorage.removeItem('accessToken');
      
      console.log('로그아웃 성공');
    } catch (error) {
      console.error('로그아웃 실패:', error);
      throw error;
    }
  };

  // API 호출용 함수 (기존 코드와의 호환성을 위해)
  const callAPI = async (url, options = {}) => {
    try {
      const session = await fetchAuthSession();
      const idToken = session.tokens.idToken.toString();
      
      const response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${idToken}`,
          'Content-Type': 'application/json',
        },
      });
      
      return response;
    } catch (error) {
      console.error('API 호출 실패:', error);
      throw error;
    }
  };

  // 컴포넌트 마운트 시 사용자 정보 확인
  useEffect(() => {
    verifyToken();
  }, [verifyToken]);

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    signup,
    confirmRegistration,
    logout,
    verifyToken,
    callAPI
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
