async function loadLogs() {
  try {
    const res = await fetch('/api/logs');
    if (!res.ok) {
      throw new Error('네트워크 오류 발생');
    }
    const logs = await res.json();
    const container = document.getElementById('logContainer');
    container.innerHTML = '';

    logs.forEach(log => {
      const logItem = document.createElement('div');
      logItem.className = 'p-4 hover:bg-gray-50 transition-colors';

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
          <button class="text-xs bg-white border border-gray-300 text-gray-700 px-2 py-1 !rounded-button whitespace-nowrap">
            상세보기
          </button>
        </div>
      `;

      container.appendChild(logItem);
    });
  } catch (error) {
    console.error('로그 로드 실패:', error);
    alert('네트워크 오류가 발생했습니다. 나중에 다시 시도해주세요.');
  }
}
