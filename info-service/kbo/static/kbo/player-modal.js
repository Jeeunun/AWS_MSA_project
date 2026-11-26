// 전역 선수 모달 함수
window.openPlayerModal = function(playerId) {
    console.log('openPlayerModal 호출됨, playerId:', playerId);
    
    // 모달 컨테이너 생성 또는 찾기
    let modalContainer = document.getElementById('playerModalContainer');
    if (!modalContainer) {
        modalContainer = document.createElement('div');
        modalContainer.id = 'playerModalContainer';
        document.body.appendChild(modalContainer);
    }
    
    // 로딩 표시
    modalContainer.innerHTML = '<div class="modal-overlay"><div class="modal-content"><div class="modal-body">로딩 중...</div></div></div>';
    modalContainer.style.display = 'block';
    
    // AJAX로 선수 정보 가져오기
    fetch(`/players/player/${playerId}/modal/`)
        .then(response => {
            console.log('AJAX 응답 상태:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            console.log('HTML 응답 받음, 길이:', html.length);
            modalContainer.innerHTML = html;
            
            // 모달 표시
            const playerModal = document.getElementById('playerModal');
            if (playerModal) {
                playerModal.style.display = 'flex';
                console.log('모달 표시됨');
                
                // 모달 닫기 이벤트 리스너 추가
                setupModalCloseEvents();
                
                // 모달 초기화 함수 호출 (player_detail_modal.html에 정의됨)
                // 전역 함수들이 준비될 때까지 대기
                let initRetryCount = 0;
                const maxInitRetries = 20;
                
                function tryInitModal() {
                    console.log(`모달 초기화 시도 ${initRetryCount + 1}/${maxInitRetries}`);
                    
                    if (typeof window.initializeModal === 'function') {
                        console.log('✅ initializeModal 함수 발견, 호출 시작');
                        try {
                            window.initializeModal();
                            console.log('✅ initializeModal 함수 호출 완료');
                        } catch (error) {
                            console.error('❌ initializeModal 함수 호출 중 오류:', error);
                        }
                    } else {
                        initRetryCount++;
                        if (initRetryCount < maxInitRetries) {
                            console.log(`⏳ initializeModal 함수가 아직 준비되지 않음, 50ms 후 재시도...`);
                            setTimeout(tryInitModal, 50);
                        } else {
                            console.error('❌ initializeModal 함수를 찾을 수 없음 (최대 재시도 횟수 초과)');
                        }
                    }
                }
                
                // 초기화 시작
                setTimeout(tryInitModal, 100);
            } else {
                console.error('playerModal 요소를 찾을 수 없음');
            }
        })
        .catch(error => {
            console.error('AJAX 오류:', error);
            modalContainer.innerHTML = '<div class="modal-overlay"><div class="modal-content"><div class="modal-body">오류가 발생했습니다: ' + error.message + '</div></div>';
        });
};

// 전역 선수 간 이동 함수
window.navigateToPlayer = function(playerId) {
    console.log('=== navigateToPlayer 함수 호출 (player-modal.js) ===');
    console.log('전달받은 playerId:', playerId);
    console.log('playerId 타입:', typeof playerId);
    
    if (!playerId || playerId === 'null' || playerId === null) {
        console.log('유효하지 않은 선수 ID:', playerId);
        return;
    }
    
    console.log('선수 이동 시작:', playerId);
    
    // 현재 모달 닫기
    console.log('현재 모달 닫기');
    if (typeof window.closePlayerModal === 'function') {
        window.closePlayerModal();
    }
    
    // 새 선수 모달 열기
    console.log('새 선수 모달 열기 대기 중...');
    setTimeout(() => {
        console.log('=== 새 선수 모달 열기 시도 ===');
        console.log('openPlayerModal 함수 타입:', typeof window.openPlayerModal);
        
        if (typeof window.openPlayerModal === 'function') {
            console.log('openPlayerModal 함수 호출:', playerId);
            try {
                window.openPlayerModal(playerId);
                console.log('openPlayerModal 함수 호출 완료');
            } catch (error) {
                console.error('openPlayerModal 함수 호출 중 오류:', error);
            }
        } else {
            console.error('openPlayerModal 함수를 찾을 수 없습니다');
            // 폴백: 페이지 새로고침으로 이동
            console.log('폴백: 페이지 새로고침으로 이동');
            window.location.href = `/players/player/${playerId}/modal/`;
        }
    }, 100);
};

// 모달 닫기 이벤트 설정 함수
function setupModalCloseEvents() {
    const modal = document.getElementById('playerModal');
    if (!modal) return;
    
    // 닫기 버튼 이벤트
    const closeBtn = modal.querySelector('button[onclick="closePlayerModal()"]');
    if (closeBtn) {
        closeBtn.onclick = function() {
            closePlayerModal();
        };
    }
    
    // ESC 키 이벤트
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            closePlayerModal();
        }
    });
    
    // 모달 외부 클릭 이벤트
    modal.addEventListener('click', function(event) {
        if (event.target === modal) {
            closePlayerModal();
        }
    });
}

// 모달 닫기 함수
function closePlayerModal() {
    const modalContainer = document.getElementById('playerModalContainer');
    if (modalContainer) {
        modalContainer.innerHTML = '';
        modalContainer.style.display = 'none';
        console.log('모달 닫힘');
    }
}

// 이미지 로드 성공 처리 함수
function handleImageLoad(imgElement) {
    console.log('이미지 로드 성공:', imgElement.src);
    
    // 이미지 크기 강제 설정 (300x300 컨테이너에 맞춤)
    imgElement.style.width = '300px';
    imgElement.style.height = '300px';
    imgElement.style.minWidth = '300px';
    imgElement.style.minHeight = '300px';
    imgElement.style.maxWidth = '300px';
    imgElement.style.maxHeight = '300px';
    imgElement.style.objectFit = 'cover';
    imgElement.style.objectPosition = 'center';
    
    // 이미지 표시
    imgElement.style.opacity = '1';
    
    // 로딩 스피너 숨기기
    const loadingElement = imgElement.parentElement.querySelector('.image-loading');
    if (loadingElement) {
        console.log('로딩 스피너 숨김');
        loadingElement.style.display = 'none';
    } else {
        console.log('로딩 스피너 요소를 찾을 수 없음');
    }
}

// 이미지 로드 실패 처리 함수
function handleImageError(imgElement, playerName) {
    console.log('이미지 로드 실패:', playerName);
    
    // 이미지 요소 숨기기
    imgElement.style.display = 'none';
    
    // 로딩 스피너 숨기기
    const loadingElement = imgElement.parentElement.querySelector('.image-loading');
    if (loadingElement) {
        console.log('로딩 스피너 숨김 (에러)');
        loadingElement.style.display = 'none';
    }
    
    // 에러 메시지 표시
    const container = imgElement.parentElement;
    container.innerHTML = `
        <div class="player-image-placeholder">
            <span>${playerName}</span>
            <br><small>이미지를 불러올 수 없습니다</small>
        </div>
    `;
}

// 페이지 로드 시 전역 이벤트 리스너 설정
document.addEventListener('DOMContentLoaded', function() {
    console.log('전역 모달 기능 준비됨');
    
    // 모든 선수 이름 링크에 클릭 이벤트 추가
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('player-name-link')) {
            const playerId = event.target.getAttribute('data-player-id');
            if (playerId) {
                event.preventDefault();
                openPlayerModal(playerId);
            }
        }
    });
}); 