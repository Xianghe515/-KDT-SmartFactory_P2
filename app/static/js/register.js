document.addEventListener("DOMContentLoaded", function () {
  const registrationForm = document.querySelector("form.register-form"); // form 태그 선택 (클래스명 명시)
  const companyNameInput = document.getElementById("company-name");
  const phoneNumberInput = document.getElementById("phone-number");
  const passwordInput = document.getElementById("password");
  const confirmPasswordInput = document.getElementById("password-confirm");
  const messageArea = document.getElementById("messageArea"); // messageArea가 있다고 가정

  function displayMessage(message, type = "error") {
    if (messageArea) {
      messageArea.innerHTML = `<div class="flash-message mt-0 bg-red-50 text-red-700 p-3 rounded-md text-sm ${type}">${message}</div>`;
    } else {
      console.log(message); // messageArea가 없으면 콘솔에 출력
    }
  }

  if (registrationForm) {
    registrationForm.addEventListener("submit", function (event) {
      event.preventDefault(); // 기본 제출 동작 방지
      validateRegistration();
    });
  }

  function validateRegistration() {
    const companyName = companyNameInput.value.trim();
    const phoneNumber = phoneNumberInput.value.trim();
    const password = passwordInput.value;
    const confirmPassword = confirmPasswordInput.value;

    // 유효성 검사
    if (companyName.length < 2) {
      displayMessage("사업체명은 최소 2글자 이상이어야 합니다.");
      return;
    }

    if (phoneNumber.replace(/[^0-9]/g, "").length < 10) {
      displayMessage("유효한 전화번호를 입력해주세요.");
      return;
    }

    if (password.length < 6) {
      displayMessage("비밀번호는 최소 6글자 이상이어야 합니다.");
      return;
    }

    if (password !== confirmPassword) {
      displayMessage("비밀번호가 일치하지 않습니다.");
      return;
    }

    // 모든 유효성 검사를 통과하면 서버로 데이터 전송
    const formData = new FormData(registrationForm); // 폼 데이터 객체 생성
    fetch(registrationForm.action, {
      method: "POST",
      body: formData,
    })
    .then(async (response) => {
      const contentType = response.headers.get("Content-Type");
    
      if (contentType && contentType.includes("application/json")) {
        // 만약 나중에 JSON 응답도 일부 쓴다면
        const data = await response.json();
        console.log(data)
        if (data.redirect_url) {
          console.log(data.redirect_url)
          window.location.href = data.redirect_url;
        } else {
          displayMessage(data.message || "오류가 발생했습니다.");
        }
      } else if (contentType && contentType.includes("text/html")) {
        // HTML 응답일 경우, 오류 메시지를 HTML에서 추출 (간단 버전)
        const html = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, "text/html");
        const flashMessage = doc.querySelector(".flash-message"); // flash 메시지 렌더링된 DOM 가정
        if (flashMessage) {
          displayMessage(flashMessage.textContent.trim());
        } else {
          displayMessage("서버 유효성 검사 실패. 입력값을 확인하세요.");
        }
      } else {
        displayMessage("알 수 없는 응답 형식입니다.");
      }
    })
    .catch((error) => {
      console.error("회원가입 요청 오류:", error);
      displayMessage("회원가입 요청 중 오류가 발생했습니다.");
    });
    
    
  }


});
