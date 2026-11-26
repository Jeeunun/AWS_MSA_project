import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import InfoLayout from './InfoLayout';
import '../styles/info-service.css';
import awsConfig from '../config/aws-config';

const PlayerSearch = () => {
  // 검색 조건 상태
  const [searchForm, setSearchForm] = useState({
    name: '',
    team: '',
    position: '',
    bats: '',
    throws: '',
    min_height: '',
    max_height: '',
    min_weight: ''
  });

  // 검색 결과 상태 (임시 데이터)
  const [searchResults, setSearchResults] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);
  
  // 모달 상태
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  
  // 이미지 로드 상태
  const [imageLoadError, setImageLoadError] = useState(false);

  // S3 선수 이미지 URL 생성 함수
  const getPlayerImageUrl = (player) => {
    if (!player || !player.team_code || !player.p_name || !player.p_position) {
      console.log('[S3 이미지] 필수 데이터 누락:', { 
        team_code: player?.team_code, 
        p_name: player?.p_name, 
        p_position: player?.p_position 
      });
      return null;
    }
    
    // S3 파일명에 사용되는 팀 코드 매핑 (필요시 수정 가능)
    const s3TeamCodeMap = {
      'KIA': 'KIA', // KIA 타이거즈
      'LG': 'LG',   // LG 트윈스
      'SSG': 'SSG', // SSG 랜더스
      'LT': 'LT',   // 롯데 자이언츠
      'DS': 'DS',   // 두산 베어스
      'SS': 'SS',   // 삼성 라이온즈
      'HH': 'HH',   // 한화 이글스
      'NC': 'NC',   // NC 다이노스
      'WO': 'WO',   // 키움 히어로즈
      'KT': 'KT'    // KT 위즈
    };
    
    // S3에서 사용하는 팀 코드
    const s3TeamCode = s3TeamCodeMap[player.team_code] || player.team_code;
    
    // 등번호를 그대로 사용 (0과 00을 구별해야 함)
    const formattedNumber = String(player.p_number || 0);
    
    // S3 실제 파일명 패턴: {팀코드}_{등번호}_{이름}_{포지션}.jpg
    const fileName = `${s3TeamCode}_${formattedNumber}_${player.p_name}_${player.p_position}.jpg`;
    const fullUrl = `${awsConfig.S3_BUCKET_URL}/players/${fileName}`;
    
    // console.log('[S3 이미지] URL 생성 (등번호 원본 유지):', {
    //   player: player.p_name,
    //   original_team_code: player.team_code,
    //   s3_team_code: s3TeamCode,
    //   p_number: player.p_number,
    //   formattedNumber,
    //   p_position: player.p_position,
    //   fileName,
    //   fullUrl,
    //   note: '등번호 0과 00을 구별하여 원본 그대로 사용'
    // });
    
    return fullUrl;
  };

  // 이미지 로드 에러 핸들러
  const handleImageError = (e) => {
    console.log('[S3 이미지] 로드 실패:', {
      src: e.target.src,
      player: selectedPlayer?.p_name
    });
    setImageLoadError(true);
  };

  // 이미지 로드 성공 핸들러
  const handleImageLoad = (e) => {
    console.log('[S3 이미지] 로드 성공:', {
      src: e.target.src,
      player: selectedPlayer?.p_name
    });
    setImageLoadError(false);
  };

  // 팀 목록과 포지션 옵션 상태
  const [teams, setTeams] = useState([]);
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(false);

  // 컴포넌트 마운트 시 옵션 데이터 로드
  useEffect(() => {
    const fetchOptions = async () => {
      try {
        console.log('=== 옵션 데이터 로드 시작 ===');
        
        // 팀 목록 가져오기
        console.log('팀 목록 API 호출 중...');
        const teamsResponse = await axios.get(`${awsConfig.API_BASE_URL}/api/info/teams/options/`);
        console.log('팀 목록 응답:', teamsResponse);
        console.log('팀 목록 데이터:', teamsResponse.data);
        
        if (teamsResponse.data && teamsResponse.data.teams) {
          console.log('팀 목록 설정:', teamsResponse.data.teams);
          setTeams(teamsResponse.data.teams);
        } else {
          console.log('팀 목록 데이터가 없습니다!');
        }
        
        // 포지션 옵션 가져오기
        console.log('포지션 옵션 API 호출 중...');
        const positionsResponse = await axios.get(`${awsConfig.API_BASE_URL}/api/info/positions/options/`);

        console.log('포지션 옵션 응답:', positionsResponse);
        console.log('포지션 옵션 데이터:', positionsResponse.data);
        
        if (positionsResponse.data && positionsResponse.data.positions) {
          console.log('포지션 옵션 설정:', positionsResponse.data.positions);
          setPositions(positionsResponse.data.positions);
        } else {
          console.log('포지션 옵션 데이터가 없습니다!');
        }
        
        console.log('=== 옵션 데이터 로드 완료 ===');
      } catch (error) {
        console.error('옵션 데이터 로드 실패:', error);
        console.error('에러 상세:', error.response?.data || error.message);
      }
    };

    fetchOptions();
  }, []);

  // 타격 옵션
  const batsOptions = [
    { value: '우타', label: '우타' },
    { value: '좌타', label: '좌타' },
    { value: '양타', label: '양타' }
  ];

  // 투구 옵션
  const throwsOptions = [
    { value: '우투', label: '우투' },
    { value: '좌투', label: '좌투' }
  ];

  // 입력 필드 변경 핸들러
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setSearchForm(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // 폼 초기화
  const resetForm = () => {
    setSearchForm({
      name: '',
      team: '',
      position: '',
      bats: '',
      throws: '',
      min_height: '',
      max_height: '',
      min_weight: ''
    });
    setSearchResults([]);
    setHasSearched(false);
  };

  // 검색 실행
  const handleSearch = async (e) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      
      // 검색 파라미터 구성
      const params = new URLSearchParams();
      if (searchForm.name) params.append('name', searchForm.name);
      if (searchForm.team) params.append('team', searchForm.team);
      if (searchForm.position) params.append('position', searchForm.position);
      if (searchForm.bats) params.append('bats', searchForm.bats);
      if (searchForm.throws) params.append('throws', searchForm.throws);
      if (searchForm.min_height) params.append('min_height', searchForm.min_height);
      if (searchForm.max_height) params.append('max_height', searchForm.max_height);
      if (searchForm.min_weight) params.append('min_weight', searchForm.min_weight);
      
      console.log('검색 파라미터:', params.toString());
      
      // Django API 호출
      const response = await axios.get(`${awsConfig.API_BASE_URL}/api/info/players/search/?${params.toString()}`);
      
      console.log('검색 결과:', response.data);
      
      if (response.data && response.data.players) {
        setSearchResults(response.data.players);
      } else {
        setSearchResults([]);
      }
      
      setHasSearched(true);
    } catch (error) {
      console.error('선수 검색 실패:', error);
      setSearchResults([]);
      setHasSearched(true);
    } finally {
      setLoading(false);
    }
  };

  // 모달 열기
  const openPlayerModal = (player) => {
    console.log('[모달 열기] 선수 데이터:', player);
    setSelectedPlayer(player);
    setIsModalOpen(true);
    setImageLoadError(false); // 이미지 로드 상태 초기화
  };

  // 모달 닫기
  const closePlayerModal = () => {
    setIsModalOpen(false);
    setSelectedPlayer(null);
    setImageLoadError(false); // 이미지 로드 상태 초기화
  };

  // 상태 값 디버깅
  // console.log('=== PlayerSearch 렌더링 ===');
  // console.log('teams 상태:', teams);
  // console.log('positions 상태:', positions);
  // console.log('teams.length:', teams.length);
  // console.log('positions.length:', positions.length);

  return (
    <InfoLayout>
      <div className="player-search-container">
        {/* 페이지 헤더 */}
        <div className="search-header">
          <h1 className="search-title">
            선수 검색
          </h1>
          <Link to="/info" className="is-btn is-btn-outline-secondary">
            <span className="btn-icon">←</span>
            팀 목록으로
          </Link>
        </div>

        {/* 검색 폼 */}
        <div className="search-form-card">
          <div className="form-header">
            <h5 className="form-title">
              검색 조건
            </h5>
          </div>
          <div className="form-body">
            <form onSubmit={handleSearch}>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="name">선수명</label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={searchForm.name}
                    onChange={handleInputChange}
                    placeholder="선수명 입력"
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="team">팀</label>
                  <select
                    id="team"
                    name="team"
                    value={searchForm.team}
                    onChange={handleInputChange}
                    className="form-select"
                  >
                                         <option value="">전체 팀</option>
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
                <div className="form-group">
                  <label htmlFor="position">포지션</label>
                  <select
                    id="position"
                    name="position"
                    value={searchForm.position}
                    onChange={handleInputChange}
                    className="form-select"
                  >
                                         <option value="">전체 포지션</option>
                     {positions.length > 0 ? (
                       positions.map(pos => (
                         <option key={pos.value} value={pos.value}>
                           {pos.label}
                         </option>
                       ))
                     ) : (
                       <option value="" disabled>로딩 중...</option>
                     )}
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="bats">타격</label>
                  <select
                    id="bats"
                    name="bats"
                    value={searchForm.bats}
                    onChange={handleInputChange}
                    className="form-select"
                  >
                    <option value="">전체</option>
                    {batsOptions.map(bat => (
                      <option key={bat.value} value={bat.value}>
                        {bat.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="throws">투구</label>
                  <select
                    id="throws"
                    name="throws"
                    value={searchForm.throws}
                    onChange={handleInputChange}
                    className="form-select"
                  >
                    <option value="">전체</option>
                    {throwsOptions.map(throw_ => (
                      <option key={throw_.value} value={throw_.value}>
                        {throw_.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="min_height">최소 키 (cm)</label>
                  <input
                    type="number"
                    id="min_height"
                    name="min_height"
                    value={searchForm.min_height}
                    onChange={handleInputChange}
                    min="150"
                    max="220"
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="max_height">최대 키 (cm)</label>
                  <input
                    type="number"
                    id="max_height"
                    name="max_height"
                    value={searchForm.max_height}
                    onChange={handleInputChange}
                    min="150"
                    max="220"
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="min_weight">최소 몸무게 (kg)</label>
                  <input
                    type="number"
                    id="min_weight"
                    name="min_weight"
                    value={searchForm.min_weight}
                    onChange={handleInputChange}
                    min="50"
                    max="150"
                    className="form-input"
                  />
                </div>
              </div>

              <div className="form-actions">
                <button type="submit" className="is-btn is-btn-primary" disabled={loading}>
                  {loading ? '검색 중...' : '검색'}
                </button>
                <button type="button" className="is-btn is-btn-outline-secondary" onClick={resetForm}>
                  <span className="btn-icon">↺</span>
                  초기화
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* 검색 결과 */}
        {hasSearched && (
          <div className="search-results-card">
            <div className="results-header">
              <h5 className="results-title">
                검색 결과 ({searchResults.length}명)
              </h5>
            </div>
            <div className="results-body">
              {searchResults.length > 0 ? (
                <div className="results-table">
                  <table>
                    <thead>
                      <tr>
                        <th>번호</th>
                        <th>이름</th>
                        <th>팀</th>
                        <th>포지션</th>
                        <th>키/몸무게</th>
                        <th>투타</th>
                        <th>생년월일</th>
                        <th>상세보기</th>
                      </tr>
                    </thead>
                    <tbody>
                      {searchResults.map(player => (
                                                 <tr key={player.idx}>
                           <td>{player.p_number !== null && player.p_number !== undefined ? player.p_number : '-'}</td>
                          <td><strong>{player.p_name}</strong></td>
                          <td>{player.team_name}</td>
                          <td>{player.p_position}</td>
                          <td>
                            {player.height_cm || player.weight_kg ? (
                              `${player.height_cm || '-'} / ${player.weight_kg || '-'}`
                            ) : (
                              '정보 없음'
                            )}
                          </td>
                          <td>
                            {player.p_info || '정보 없음'}
                          </td>
                          <td>{player.birth || '정보 없음'}</td>
                          <td>
                            <button 
                              className="is-btn is-btn-sm is-btn-outline-primary"
                              onClick={() => openPlayerModal(player)}
                            >
                              상세
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="no-results">
                  <span className="no-results-icon">⚠️</span>
                  검색 조건에 맞는 선수를 찾을 수 없습니다.
                </div>
              )}
            </div>
                     </div>
         )}

         {/* 선수 상세 모달 */}
         {isModalOpen && selectedPlayer && (
           <div className="player-modal-overlay" onClick={closePlayerModal}>
             <div className="player-modal" onClick={(e) => e.stopPropagation()}>
               <div className="modal-header">
                 <h5 className="modal-title">선수 상세 정보</h5>
                 <button 
                   type="button" 
                   className="modal-close-btn"
                   onClick={closePlayerModal}
                 >
                   ×
                 </button>
               </div>
               <div className="modal-body">
                 <div className="player-info-grid">
                   {/* 선수 프로필 섹션 */}
                   <div className="player-profile">
                     <div className="player-image">
                       {!imageLoadError && getPlayerImageUrl(selectedPlayer) ? (
                         <img 
                           src={getPlayerImageUrl(selectedPlayer)}
                           alt={`${selectedPlayer.p_name} 선수 사진`}
                           className="player-photo"
                           onError={handleImageError}
                           onLoad={handleImageLoad}
                         />
                       ) : (
                         <div className="player-image-placeholder">
                           <span className="player-icon">👤</span>
                           <span className="no-image-text">이미지 없음</span>
                         </div>
                       )}
                     </div>
                     <h4 className="player-name">{selectedPlayer.p_name}</h4>
                     <p className="player-team">{selectedPlayer.team_name}</p>
                     <span className="position-badge">{selectedPlayer.p_position}</span>
                     {selectedPlayer.p_number !== null && selectedPlayer.p_number !== undefined && (
                       <div className="number-badge">#{selectedPlayer.p_number}</div>
                     )}
                   </div>

                   {/* 기본 정보 섹션 */}
                   <div className="info-section">
                     <h6 className="section-title">
                       <span className="section-icon">ℹ️</span>
                       기본 정보
                     </h6>
                     <div className="info-table">
                       <div className="info-row">
                         <span className="info-label">이름:</span>
                         <span className="info-value">{selectedPlayer.p_name}</span>
                       </div>
                       <div className="info-row">
                         <span className="info-label">팀:</span>
                         <span className="info-value">{selectedPlayer.team_name}</span>
                       </div>
                       <div className="info-row">
                         <span className="info-label">포지션:</span>
                         <span className="info-value">{selectedPlayer.p_position}</span>
                       </div>
                       {selectedPlayer.p_number !== null && selectedPlayer.p_number !== undefined && (
                         <div className="info-row">
                           <span className="info-label">등번호:</span>
                           <span className="info-value">#{selectedPlayer.p_number}</span>
                         </div>
                       )}
                       {selectedPlayer.birth && (
                         <div className="info-row">
                           <span className="info-label">생년월일:</span>
                           <span className="info-value">{selectedPlayer.birth}</span>
                         </div>
                       )}
                     </div>
                   </div>
                 </div>

                                   {/* 신체 정보 섹션 */}
                                     <div className="info-section physical-section">
                     <h6 className="section-title">
                       신체 정보
                     </h6>
                     <div className="physical-info-list">
                       {selectedPlayer.height_cm && (
                         <div className="physical-info-item">
                           <div className="physical-info-content">
                             <div className="physical-info-label">키</div>
                             <div className="physical-info-value">{selectedPlayer.height_cm}</div>
                           </div>
                         </div>
                       )}
                       {selectedPlayer.weight_kg && (
                         <div className="physical-info-item">
                           <div className="physical-info-content">
                             <div className="physical-info-label">몸무게</div>
                             <div className="physical-info-value">{selectedPlayer.weight_kg}</div>
                           </div>
                         </div>
                       )}
                       {selectedPlayer.p_info && (
                         <div className="physical-info-item">
                           <div className="physical-info-content">
                             <div className="physical-info-label">투타 정보</div>
                             <div className="physical-info-value">
                               <span className="badge bats-badge">{selectedPlayer.p_info}</span>
                             </div>
                           </div>
                         </div>
                       )}
                     </div>
                   </div>

                 {/* 모달 하단 버튼 */}
                 <div className="modal-footer">
                   <button 
                     type="button" 
                     className="is-btn is-btn-outline-secondary"
                     onClick={closePlayerModal}
                   >
                     <span className="btn-icon">✕</span>
                     닫기
                   </button>
                 </div>
               </div>
             </div>
           </div>
         )}
       </div>
     </InfoLayout>
   );
 };

export default PlayerSearch;
