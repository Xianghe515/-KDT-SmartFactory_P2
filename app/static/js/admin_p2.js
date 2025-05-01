// admin_p2.js
// 인증번호(4/4/4) 입력란 자동 포커스, 붙여넣기, 백스페이스 이동, 버튼 활성화

document.addEventListener("DOMContentLoaded", function () {
  const segments = [
    { el: document.getElementById("verify-part1"), len: 4 },
    { el: document.getElementById("verify-part2"), len: 4 },
    { el: document.getElementById("verify-part3"), len: 4 },
  ];
  const verifyButton = document.getElementById("verify-button");
  const errorMessage = document.getElementById("error-message");
  const errorText = document.getElementById("error-text");
  const loadingMessage = document.getElementById("loading-message");
  const form = document.querySelector("form");

  // 다음 입력칸으로 포커스 이동 (setTimeout으로 focus 보장)
  function moveToNext(idx) {
    if (
      idx < segments.length - 1 &&
      segments[idx].el.value.length === segments[idx].len
    ) {
      setTimeout(() => segments[idx + 1].el.focus(), 0);
    }
  }

  // 입력 이벤트: 숫자만 허용, 길이 제한, 자동 포커스
  function handleInput(idx) {
    const { el, len } = segments[idx];
    // 숫자 외 제거 및 최대 길이 제한
    el.value = el.value.replace(/[^0-9]/g, "").slice(0, len);
    // 입력 후 다음 칸 이동
    if (el.value.length === len) moveToNext(idx);
    validateInputs();
  }

  // keyup 이벤트: 키 입력 후에도 포커스 이동 보조
  function handleKeyUp(idx, e) {
    if (
      !["Backspace", "ArrowLeft", "ArrowRight"].includes(e.key) &&
      segments[idx].el.value.length === segments[idx].len
    ) {
      moveToNext(idx);
    }
  }

  // 붙여넣기 이벤트: 12자리 분할 입력
  function handlePaste(e) {
    const pasted = (e.clipboardData || window.clipboardData).getData("text");
    const nums = pasted.replace(/[^0-9]/g, "");
    const totalLen = segments.reduce((sum, s) => sum + s.len, 0);
    if (nums.length >= totalLen) {
      e.preventDefault();
      let pos = 0;
      segments.forEach(({ el, len }) => {
        el.value = nums.slice(pos, pos + len);
        pos += len;
      });
      // 모든 분할 후 마지막 칸 포커스
      if (segments.length > 0) {
        segments[segments.length - 1].el.focus();
      }
      validateInputs();
    }
  }

  // 백스페이스 키로 이전 칸으로 이동
  function handleBackspace(e, idx) {
    if (
      e.key === "Backspace" &&
      segments[idx].el.value.length === 0 &&
      idx > 0
    ) {
      segments[idx - 1].el.focus();
    }
  }

  // 이벤트 등록
  segments.forEach((s, idx) => {
    s.el.addEventListener("input", () => handleInput(idx));
    s.el.addEventListener("keyup", (e) => handleKeyUp(idx, e));
    s.el.addEventListener("paste", handlePaste);
    s.el.addEventListener("keydown", (e) => handleBackspace(e, idx));
  });

  // 전체 칸 채워졌는지 확인 및 버튼 활성화/비활성화
  function validateInputs() {
    const allFilled = segments.every(({ el, len }) => el.value.length === len);
    verifyButton.disabled = !allFilled;
    // 버튼 활성화/비활성화에 따른 스타일 변경
    if (allFilled) {
      verifyButton.classList.remove(
        "bg-gray-200",
        "text-gray-500",
        "cursor-not-allowed"
      );
      verifyButton.classList.add("bg-primary", "text-white", "cursor-pointer");
    } else {
      verifyButton.classList.remove(
        "bg-primary",
        "text-white",
        "cursor-pointer"
      );
      verifyButton.classList.add(
        "bg-gray-200",
        "text-gray-500",
        "cursor-not-allowed"
      );
    }
    errorMessage.classList.add("hidden");
  }

  // 인증 버튼 클릭 (fetch로 서버 검증)
  verifyButton.addEventListener("click", function (e) {
    if (verifyButton.disabled) return;
    e.preventDefault();
    loadingMessage.classList.remove("hidden");
    verifyButton.disabled = true;
    verifyButton.classList.add("bg-gray-300", "cursor-not-allowed");
    verifyButton.classList.remove("bg-primary", "text-white", "cursor-pointer");

    fetch(form.action, { method: form.method, body: new FormData(form) })
      .then((res) => {
        loadingMessage.classList.add("hidden");
        if (res.ok) return res.json();
        throw new Error("HTTP " + res.status);
      })
      .then((data) => {
        if (data.success) window.location.href = data.redirect_url;
        else throw new Error(data.message);
      })
      .catch((err) => {
        errorText.textContent = err.message || "인증에 실패했습니다.";
        errorMessage.classList.remove("hidden");
        verifyButton.disabled = false;
        verifyButton.classList.remove("bg-gray-300", "cursor-not-allowed");
        verifyButton.classList.add(
          "bg-primary",
          "text-white",
          "cursor-pointer"
        );
      });
  });

  // 초기 상태 체크
  validateInputs();
});
