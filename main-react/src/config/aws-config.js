const awsConfig = {
  Auth: {
    Cognito: {
      userPoolId: 'ap-northeast-2_7itkLu5S9',
      userPoolClientId: '7v6me3sri92mgdn3fusbntsd1n',
      signUpVerificationMethod: 'code',
      loginWith: {
        email: false,
        phone: false,
        username: true
      }
    }
  }
};

// API Gateway 설정 추가
const apiBaseUrl = import.meta.env.REACT_APP_API_BASE_URL || 'https://ugaabk8k65.execute-api.ap-northeast-2.amazonaws.com/prod';

// S3 버킷 설정 추가
const s3BucketUrl = import.meta.env.REACT_APP_S3_BUCKET_URL || 'https://wjdwlstndlalwl.s3.amazonaws.com';

export const API_CONFIG = {
  API_BASE_URL: apiBaseUrl,
  S3_BUCKET_URL: s3BucketUrl,
}

// awsConfig에 설정 추가
awsConfig.API_BASE_URL = apiBaseUrl;
awsConfig.S3_BUCKET_URL = s3BucketUrl;

// 디버깅용 로그
console.log('awsConfig.API_BASE_URL:', awsConfig.API_BASE_URL);
console.log('import.meta.env.REACT_APP_API_BASE_URL:', import.meta.env.REACT_APP_API_BASE_URL);

export default awsConfig;
