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

function initializeWebSocket() {
  const socket = io.connect('http://' + document.domain + ':' + location.port);

  // 새로운 로그를 수신
  socket.on('new_log', function (data) {
    displayLog(data);
  });

  // 기존 로그 로드
  loadLogs();
}

async function loadLogs() {
  try {
    const res = await fetch('/detection/api/logs');
    if (!res.ok) {
      throw new Error('네트워크 오류 발생');
    }
    const logs = await res.json();
    const container = document.getElementById('logContainer');
    container.innerHTML = '';

    logs.forEach(log => {
      displayLog(log);
    });
  } catch (error) {
    console.error('로그 로드 실패:', error);
    alert('네트워크 오류가 발생했습니다. 나중에 다시 시도해주세요.');
  }
}

function displayLog(log) {
  const container = document.getElementById('logContainer');
  const logItem = document.createElement('div');
  logItem.className = 'p-4 hover:bg-gray-50 transition-colors border-b last:border-b-0';

  // 로그 항목 내용 생성
  logItem.innerHTML = `
    <div class="flex items-start">
      <div class="w-20 h-20 bg-gray-200 rounded overflow-hidden flex-shrink-0">
        <img src="${log.imageUrl}" alt="불량 이미지" class="w-full h-full object-cover" />
      </div>
      <div class="ml-4 flex-1">
        <div class="flex items-center justify-between">
          <h3 class="font-medium text-gray-900">${log.issueType}</h3>
          <span class="bg-${log.severityColor}-100 text-${log.severityColor}-800 text-xs px-2 py-1 rounded-full">${log.severity}</span>
        </div>
        <div class="mt-1 text-sm text-gray-600">
          <p>시간: ${log.timestamp}</p>
          <p>카메라: ${log.cameraName}</p>
        </div>
      </div>
    </div>
    <div class="mt-2 flex justify-end">
      <a href="${log.imageUrl}" class="mx-1 text-xs bg-white border border-gray-300 text-gray-700 px-2 py-1 !rounded-button whitespace-nowrap" download>다운로드</a>
      <button onclick="openModal('${log.annotationUrl}')" class="mx-1 text-xs bg-white border border-gray-300 text-gray-700 px-2 py-1 !rounded-button whitespace-nowrap">어노테이션</button>
     </div>
  `;

  container.appendChild(logItem);
  console.log(log);
}
function openModal(url) {
  const modal = document.getElementById('annotationModal');
  const iframe = document.getElementById('annotationIframe');
  iframe.src = url;
  modal.classList.remove('hidden');
}

function closeModal() {
  const modal = document.getElementById('annotationModal');
  const iframe = document.getElementById('annotationIframe');
  iframe.src = '';  // 종료 시 리소스 제거
  modal.classList.add('hidden');
}
