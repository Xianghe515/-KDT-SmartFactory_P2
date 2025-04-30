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
