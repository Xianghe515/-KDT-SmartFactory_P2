document.addEventListener("DOMContentLoaded", () => {
  const cameraSelect = document.getElementById("cameraSelect");
  const cameraStream = document.getElementById("cameraStream");

  if (cameraSelect && cameraStream) {
    cameraSelect.addEventListener("change", function () {
      const selectedCameraId = this.value;
      cameraStream.src = `/camera/stream/${selectedCameraId}`;
    });

    // 페이지 로드시 초기 카메라 스트림 설정 (첫 번째 옵션 값 사용)
    const initialCameraId = cameraSelect.value;
    cameraStream.src = `/camera/stream/${initialCameraId}`;
  } else {
    console.error(
      "cameraSelect 또는 cameraStream 엘리먼트를 찾을 수 없습니다."
    );
  }

  initializeWebSocket();
});

// ✅ 전역 변수로 선언하여 재사용
let socket;
function initializeWebSocket() {
  // 소켓이 이미 연결되었는지 확인
  if (!socket) {
    socket = io.connect('http://' + document.domain + ':' + location.port);
    console.log('클라이언트가 WebSocket으로 연결되었습니다.')

    // 새로운 로그 수신
    socket.on('new_log', function (data) {
      displayLog(data);
    });

    // 민감도 업데이트 로그
    socket.on('sensitivity_updated', function (data) {
      console.log('검출 민감도 수정:', data.value);
    });
  }

  // 기존 로그 로드
  loadLogs();
}

function updateSensitivity(value) {
  if (!socket) return; // 소켓이 아직 연결되지 않은 경우 예외 처리

  const floatVal = parseFloat(value) / 100;  // 0.0 ~ 1.0 범위로 변환
  socket.emit('sensitivity', { value: floatVal });

  // 👇 HTML 조작은 별도로 이벤트 핸들러에 등록하세요 (초기화 시점에)
  document.getElementById('sensitivityValue').innerText = value + '%';
}

async function loadLogs() {
  try {
    const res = await fetch('/detection/api/logs');
    if (!res.ok) {
      throw new Error('네트워크 오류 발생');
    }
    const logs = await res.json();
    const container = document.getElementById('logContainer');
    if (container) {
        container.innerHTML = ''; // 컨테이너 비우기

        logs.forEach(log => {
          displayLog(log);
        });
    } else {
        console.error("로그 컨테이너 엘리먼트 (logContainer)를 찾을 수 없습니다.");
    }

  } catch (error) {
    console.error('로그 로드 실패:', error);
    alert('로그 로드 중 네트워크 오류가 발생했습니다. 나중에 다시 시도해주세요.');
  }
}

// 전체 화면
document.getElementById("fullscreen-btn").addEventListener("click", function () {
    let videoFrame = document.getElementById("cameraStream");
    if (videoFrame.requestFullscreen) {
        videoFrame.requestFullscreen();
    } else if (videoFrame.mozRequestFullScreen) { // Firefox
        videoFrame.mozRequestFullScreen();
    } else if (videoFrame.webkitRequestFullscreen) { // Chrome, Safari, Opera
        videoFrame.webkitRequestFullscreen();
    } else if (videoFrame.msRequestFullscreen) { // IE/Edge
        videoFrame.msRequestFullscreen();
    }
});

function displayLog(log) {
  const container = document.getElementById('logContainer');
  if (!container) {
      console.error("로그 컨테이너 엘리먼트 (logContainer)를 찾을 수 없어 로그를 표시할 수 없습니다.");
      return; // 컨테이너 없으면 종료
  }

  const logItem = document.createElement('div');
  logItem.className = 'p-4 hover:bg-gray-50 transition-colors border-b last:border-b-0';

  // --- log.annotationUrl 값이 유효한지 먼저 확인 ---
  console.log("Processing log:", log);
  console.log("Annotation URL for this log:", log.annotationUrl);
  // ----------------------------------------------

  // 로그 항목 내용 생성
  logItem.innerHTML = `
    <div class="flex items-start">
      <div class="w-20 h-20 bg-gray-200 rounded overflow-hidden flex-shrink-0">
        <img src="${log.imageUrl || ''}" alt="불량 이미지" class="w-full h-full object-cover" onerror="this.onerror=null;this.src='/static/placeholder.png';" />
      </div>
      <div class="ml-4 flex-1">
        <div class="flex items-center justify-between">
          <h3 class="font-medium text-gray-900">${log.issueType || '알 수 없음'}</h3>
          <span class="bg-${log.severityColor || 'gray'}-100 text-${log.severityColor || 'gray'}-800 text-xs px-2 py-1 rounded-full">${log.severity || '정보'}</span>
        </div>
        <div class="mt-1 text-sm text-gray-600">
          <p>시간: ${log.timestamp || '알 수 없음'}</p>
          <p>카메라: ${log.cameraName || '알 수 없음'}</p>
        </div>
      </div>
    </div>
    <div class="mt-2 flex justify-end">
      <a href="${log.imageUrl || '#'}" class="mx-1 text-xs bg-white border border-gray-300 text-gray-700 px-2 py-1 !rounded-button whitespace-nowrap" download>다운로드</a>
      ${log.annotationUrl ? // annotationUrl 값이 있을 때만 버튼 생성
        `<button class="mx-1 text-xs bg-white border border-gray-300 text-gray-700 px-2 py-1 !rounded-button whitespace-nowrap annotation-button" data-url="${log.annotationUrl}">어노테이션</button>`
        : `<button class="mx-1 text-xs bg-gray-300 text-gray-700 px-2 py-1 !rounded-button whitespace-nowrap" disabled>어노테이션 (URL 없음)</button>` // 없으면 비활성화 버튼
      }
     </div>
  `;

  container.appendChild(logItem);

  // --- 버튼 엘리먼트를 찾아서 이벤트 리스너를 추가 ---
  const annotationButton = logItem.querySelector('.annotation-button');
  if (annotationButton) {
      annotationButton.addEventListener('click', function() {
          const url = this.getAttribute('data-url'); // data-url 속성에서 URL 값 읽기
          if (url) {
              openModal(url);
          } else {
              console.error("Annotation URL not found on button data attribute.", this);
          }
      });
  }
  // -------------------------------------------------
}

// openModal 함수는 인자로 받은 URL 값을 로그로 출력하여 확인합니다.
function openModal(url) {
  console.log("Attempting to open modal with URL:", url); // 여기에 URL 값이 정확히 무엇인지 출력될 것입니다.
  const modal = document.getElementById('annotationModal');
  const iframe = document.getElementById('annotationIframe');

  if (modal && iframe) {
      iframe.src = url;
      modal.classList.remove('hidden');
  } else {
      console.error("Modal or iframe elements not found for annotation.");
  }
}

function closeModal() {
  const modal = document.getElementById('annotationModal');
  const iframe = document.getElementById('annotationIframe');
  if (modal && iframe) {
      iframe.src = '';  // 종료 시 리소스 제거 (iframe 내용 초기화)
      modal.classList.add('hidden');
  }
}