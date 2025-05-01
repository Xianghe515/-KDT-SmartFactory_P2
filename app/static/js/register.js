document.addEventListener("DOMContentLoaded", function () {
  const registrationForm = document.querySelector("form.register-form"); // form 태그 선택 (클래스명 명시)
  const companyNameInput = document.getElementById("company-name");
  const phoneNumberInput = document.getElementById("phone-number");
  const passwordInput = document.getElementById("password");
  const confirmPasswordInput = document.getElementById("password-confirm");
  const messageArea = document.getElementById("messageArea"); // messageArea가 있다고 가정

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

    // 간단한 유효성 검사 예시
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
      displayMessage("비밀번호와 비밀번호 확인이 일치하지 않습니다.");
      return;
    }

    // 모든 유효성 검사를 통과하면 서버로 데이터 전송
    const formData = new FormData(registrationForm); // 폼 데이터 객체 생성
    fetch(registrationForm.action, {
      // 폼의 action 속성 URL 사용
      method: "POST",
      body: formData,
    })
      .then((response) => {
        if (response.ok) {
          // 서버에서 성공 응답 (상태 코드 2xx)을 보낸 경우
          window.location.href = loginUrl;
        } else {
          // 서버에서 오류 응답 (상태 코드 4xx 또는 5xx)을 보낸 경우
          return response.json(); // 오류 메시지를 JSON 형태로 파싱
        }
      })
      .then((data) => {
        if (data && data.message) {
          displayMessage(data.message); // 서버에서 보낸 오류 메시지 표시
        } else if (!data) {
          displayMessage("회원가입에 실패했습니다. 다시 시도해주세요.");
        }
      })
      .catch((error) => {
        console.error("회원가입 요청 오류:", error);
        displayMessage("회원가입 요청 중 오류가 발생했습니다.");
      });
  }

  function displayMessage(message, type = "error") {
    if (messageArea) {
      messageArea.textContent = message;
      messageArea.className = type; // CSS 스타일링을 위한 클래스 추가 (error, success 등)
    } else {
      console.log(message); // messageArea가 없으면 콘솔에 출력
    }
  }
});
