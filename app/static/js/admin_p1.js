document.addEventListener("DOMContentLoaded", function () {
  const representativeNameInput = document.getElementById(
    "representative-name"
  );
  const part1 = document.getElementById("business-part1");
  const part2 = document.getElementById("business-part2");
  const part3 = document.getElementById("business-part3");
  const verifyButton = document.getElementById("verify-button");
  const errorMessage = document.getElementById("error-message");
  const errorText = document.getElementById("error-text");
  const loadingMessage = document.getElementById("loading-message");

  // 입력 필드 자동 포커스 이동 설정
  part1.addEventListener("input", function () {
    if (this.value.length >= 3) {
      this.value = this.value.slice(0, 3);
      part2.focus();
    }
    validateInputs();
  });

  part2.addEventListener("input", function () {
    if (this.value.length >= 2) {
      this.value = this.value.slice(0, 2);
      part3.focus();
    }
    validateInputs();
  });

  part3.addEventListener("input", function () {
    if (this.value.length > 5) {
      this.value = this.value.slice(0, 5);
    }
    validateInputs();
  });

  // 백스페이스 처리
  part2.addEventListener("keydown", function (e) {
    if (e.key === "Backspace" && this.value.length === 0) {
      part1.focus();
    }
  });

  part3.addEventListener("keydown", function (e) {
    if (e.key === "Backspace" && this.value.length === 0) {
      part2.focus();
    }
  });

  // 입력값 검증
  function validateInputs() {
    const isNameFilled = representativeNameInput.value.trim() !== "";
    const isValidPart1 = /^\d{3}$/.test(part1.value);
    const isValidPart2 = /^\d{2}$/.test(part2.value);
    const isValidPart3 = /^\d{5}$/.test(part3.value);

    if (isNameFilled && isValidPart1 && isValidPart2 && isValidPart3) {
      verifyButton.disabled = false;
      verifyButton.classList.remove(
        "bg-gray-200",
        "text-gray-500",
        "cursor-not-allowed"
      );
      verifyButton.classList.add("bg-primary", "text-white", "cursor-pointer");
    } else {
      verifyButton.disabled = true;
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

  // 인증 버튼 클릭 이벤트
  verifyButton.addEventListener("click", function () {
    if (verifyButton.disabled) return;

    const representativeName = representativeNameInput.value.trim();
    const businessNumber = `${part1.value}-${part2.value}-${part3.value}`;

    // 형식 검증
    if (!isValidBusinessNumber(businessNumber)) {
      showError("올바른 사업자 등록번호 형식이 아닙니다");
      return;
    }

    // 로딩 상태 표시
    loadingMessage.classList.remove("hidden");
    verifyButton.disabled = true;
    verifyButton.classList.add("bg-gray-300", "cursor-not-allowed");
    verifyButton.classList.remove(
      "bg-primary",
      "hover:bg-primary/90",
      "cursor-pointer"
    );

    // CSV 검증 시뮬레이션 (실제로는 외부 파일에서 읽어와야 함)
    setTimeout(function () {
      loadingMessage.classList.add("hidden");

      // **가상의 CSV 데이터** (실제로는 외부 파일에서 읽어와야 함)
      const validData = [
        { businessNumber: "123-12-12345", representativeName: "김대표" },
        { businessNumber: "987-65-43210", representativeName: "이사장" },
        // ... 더 많은 데이터
      ];

      const found = validData.find(
        (item) =>
          item.businessNumber === businessNumber &&
          item.representativeName === representativeName
      );

      if (found) {
        // 성공 시 다음 페이지로 이동
        window.location.href = "/next-page";
      } else {
        // 실패 시 오류 메시지
        showError("대표자명 또는 사업자번호가 일치하지 않습니다.");
        verifyButton.disabled = false;
        verifyButton.classList.remove("bg-gray-300", "cursor-not-allowed");
        verifyButton.classList.add(
          "bg-primary",
          "hover:bg-primary/90",
          "cursor-pointer"
        );
      }
    }, 1500);
  });

  function isValidBusinessNumber(number) {
    // 간단한 형식 검증 (실제로는 더 복잡한 검증 로직이 필요할 수 있음)
    const regex = /^\d{3}-\d{2}-\d{5}$/;
    return regex.test(number);
  }

  function showError(message) {
    errorText.textContent = message;
    errorMessage.classList.remove("hidden");
  }

  // 초기 입력 필드 검증
  representativeNameInput.addEventListener("input", validateInputs);
});
