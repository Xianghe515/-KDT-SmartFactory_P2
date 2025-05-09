document.addEventListener("DOMContentLoaded", function () {
  const notificationBtn = document.getElementById("notificationBtn");
  const notificationDropdown = document.getElementById("notificationDropdown");
  notificationBtn.addEventListener("click", function (e) {
    e.stopPropagation();
    notificationDropdown.classList.toggle("hidden");
  });
  document.addEventListener("click", function (e) {
    if (!notificationDropdown.contains(e.target)) {
      notificationDropdown.classList.add("hidden");
    }
  });
  const resizeHandle = document.getElementById("resize-handle");
  const leftPanel = resizeHandle.previousElementSibling;
  const rightPanel = resizeHandle.nextElementSibling;
  let isResizing = false;
  resizeHandle.addEventListener("mousedown", function (e) {
    isResizing = true;
    document.body.style.cursor = "col-resize";
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", stopResize);
    e.preventDefault();
  });
  function handleMouseMove(e) {
    if (!isResizing) return;
    const containerWidth = leftPanel.parentElement.clientWidth;
    const newLeftWidth = (e.clientX / containerWidth) * 100;
    // 최소 30%, 최대 70% 제한
    if (newLeftWidth >= 30 && newLeftWidth <= 70) {
      leftPanel.style.width = `${newLeftWidth}%`;
      rightPanel.style.width = `${100 - newLeftWidth}%`;
    }
  }
  function stopResize() {
    isResizing = false;
    document.body.style.cursor = "";
    document.removeEventListener("mousemove", handleMouseMove);
    document.removeEventListener("mouseup", stopResize);
  }
  // 슬라이더 값 표시
  const sensitivitySlider = document.querySelectorAll(".custom-range")[0];
  const sensitivityValue = sensitivitySlider.nextElementSibling;
  sensitivitySlider.addEventListener("input", function () {
    sensitivityValue.textContent = `${this.value}%`;
  });
  const thresholdSlider = document.querySelectorAll(".custom-range")[1];
  const thresholdValue = thresholdSlider.nextElementSibling;
  thresholdSlider.addEventListener("input", function () {
    thresholdValue.textContent = `${this.value}%`;
  });
});
