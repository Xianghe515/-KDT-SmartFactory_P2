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
});

async function loadLogs() {
  const res = await fetch('/api/logs');
  const logs = await res.json();
  const container = document.getElementById('logContainer');
  container.innerHTML = '';

  logs.forEach(log => {
    const logItem = document.createElement('div');
    logItem.className = 'flex items-center space-x-3 p-2 bg-white shadow rounded hover:bg-gray-50';
    logItem.innerHTML = `
      <img src="${log.url}" class="w-16 h-16 object-cover rounded border" />
      <div>
        <p class="text-sm text-gray-800">${log.filename}</p>
        <p class="text-xs text-gray-500">${log.timestamp}</p>
      </div>
    `;
    container.appendChild(logItem);
  });
}

// 페이지 로드 시 한 번 실행하고, 이후 10초마다 갱신
loadLogs();
setInterval(loadLogs, 10000);