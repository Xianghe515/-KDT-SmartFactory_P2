// document.addEventListener("DOMContentLoaded", () => {
//   const cameraSelect = document.getElementById("cameraSelect");
//   const cameraStream = document.getElementById("cameraStream");

//   if (cameraSelect && cameraStream) {
//     cameraSelect.addEventListener("change", function () {
//       const selectedCameraId = this.value;
//       cameraStream.src = `/camera/stream/${selectedCameraId}`;
//     });

//     // 페이지 로드시 초기 카메라 스트림 설정 (첫 번째 옵션 값 사용)
//     const initialCameraId = cameraSelect.value;
//     cameraStream.src = `/camera/stream/${initialCameraId}`;
//   } else {
//     console.error(
//       "cameraSelect 또는 cameraStream 엘리먼트를 찾을 수 없습니다."
//     );
//   }
// });
const canvas = new fabric.Canvas('labelCanvas');
let rect;

// 드래그 박스 만들기
canvas.on('mouse:down', function(options) {
    const pointer = canvas.getPointer(options.e);
    rect = new fabric.Rect({
        left: pointer.x,
        top: pointer.y,
        width: 0,
        height: 0,
        fill: 'rgba(255, 0, 0, 0.3)',
        stroke: 'red',
        strokeWidth: 1,
        selectable: false
    });
    canvas.add(rect);
});

canvas.on('mouse:move', function(options) {
    if (!rect) return;
    const pointer = canvas.getPointer(options.e);
    rect.set({ width: pointer.x - rect.left, height: pointer.y - rect.top });
    canvas.renderAll();
});

canvas.on('mouse:up', function() {
    rect.set({ selectable: true });
    rect = null;
});

function sendLabel() {
    const objs = canvas.getObjects();
    const labelData = objs.map(obj => ({
        x: obj.left,
        y: obj.top,
        width: obj.width * obj.scaleX,
        height: obj.height * obj.scaleY,
        class: "bird-drop",  // 실제 UI에서 선택하게 할 수 있음
    }));

    fetch('/save_label', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(labelData[0])  // 하나만 보내는 예시
    }).then(res => res.json())
      .then(data => console.log(data));
}