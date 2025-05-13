document.addEventListener("DOMContentLoaded", () => {
  const cameraSelect = document.getElementById("cameraSelect");
  const cameraStream = document.getElementById("cameraStream");
  let currentCameraId = cameraSelect.value; // 현재 선택된 카메라 ID 저장

  if (cameraSelect && cameraStream) {
    cameraSelect.addEventListener("change", function () {
      const selectedCameraId = this.value;
      if (selectedCameraId !== currentCameraId) {
        console.log(`카메라 변경: ${currentCameraId} -> ${selectedCameraId}`);
        cameraStream.src = `/camera/stream/${selectedCameraId}`;
        currentCameraId = selectedCameraId;
      }
    });

    // 페이지 로드시 초기 카메라 스트림 설정
    cameraStream.src = `/camera/stream/${currentCameraId}`;
  } else {
    console.error(
      "cameraSelect 또는 cameraStream 엘리먼트를 찾을 수 없습니다."
    );
  }

  // 카메라 상태 업데이트 함수
  function updateCameraStatusUI(status) {
    console.log("카메라 상태 업데이트:", status); // 받은 상태 정보 로깅
    for (const cameraId in status) {
      const isConnected = status[cameraId];
      const statusElement = document.getElementById(`camera${cameraId}Status`);
      const textElement = document.getElementById(`camera${cameraId}Text`);
      if (statusElement && textElement) {
        statusElement.dataset.status = isConnected ? "active" : "deactivate";
        textElement.textContent = `${cameraId}번 카메라 ${
          isConnected ? "연결됨" : "연결 끊김"
        }`;

        if (!isConnected) {
          console.log(`${cameraId}번 카메라 연결 끊김 감지`); // 연결 끊김 감지 로깅
          cameraStream.src = ""; // 스트림 해제
          reconnectCamera(cameraId); // 재연결 시도
        }
      }
    }
  }

  // 카메라 상태를 주기적으로 확인하는 함수
  function fetchCameraStatus() {
    fetch("/camera/api/camera_status") // URL 프리픽스 적용
      .then((response) => response.json())
      .then((data) => {
        updateCameraStatusUI(data);
      })
      .catch((error) => {
        console.error("카메라 상태를 가져오는 데 실패했습니다:", error);
      });
  }

  // 카메라 재연결 함수
  function reconnectCamera(cameraId) {
    const cameraStream = document.getElementById("cameraStream");
    cameraStream.src = `/camera/stream/${cameraId}`; // 카메라 재연결
    console.log(
      `${cameraId}번 카메라 재연결 시도 URL: /camera/stream/${cameraId}`
    );
  }

  // 페이지 로딩 후 초기 상태를 한번 가져오고, 주기적으로 상태 업데이트
  fetchCameraStatus();
  setInterval(fetchCameraStatus, 5000); // 5초마다 상태 업데이트
});

const canvas = new fabric.Canvas("labelCanvas");
let rect;

// 드래그 박스 만들기
canvas.on("mouse:down", function (options) {
  const pointer = canvas.getPointer(options.e);
  rect = new fabric.Rect({
    left: pointer.x,
    top: pointer.y,
    width: 0,
    height: 0,
    fill: "rgba(255, 0, 0, 0.3)",
    stroke: "red",
    strokeWidth: 1,
    selectable: false,
  });
  canvas.add(rect);
});

canvas.on("mouse:move", function (options) {
  if (!rect) return;
  const pointer = canvas.getPointer(options.e);
  rect.set({ width: pointer.x - rect.left, height: pointer.y - rect.top });
  canvas.renderAll();
});

canvas.on("mouse:up", function () {
  rect.set({ selectable: true });
  rect = null;
});

function sendLabel() {
  const objs = canvas.getObjects();
  const labelData = objs.map((obj) => ({
    x: obj.left,
    y: obj.top,
    width: obj.width * obj.scaleX,
    height: obj.height * obj.scaleY,
    class: "bird-drop", // 실제 UI에서 선택하게 할 수 있음
  }));

  fetch("/save_label", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(labelData[0]), // 하나만 보내는 예시
  })
    .then((res) => res.json())
    .then((data) => console.log(data));
}
