document.addEventListener("DOMContentLoaded", function () {
  const part1 = document.getElementById("business-part1");
  const part2 = document.getElementById("business-part2");
  const part3 = document.getElementById("business-part3");
  const verifyButton = document.getElementById("verify-button");
  const errorMessage = document.getElementById("error-message");
  const loadingMessage = document.getElementById("loading-message");
  const representativeNameInput = document.getElementById(
    "representative-name"
  );
  const emailInput = document.getElementById("email");

  function validateInputs() {
    const isValidPart1 = /^\d{3}$/.test(part1.value);
    const isValidPart2 = /^\d{2}$/.test(part2.value);
    const isValidPart3 = /^\d{5}$/.test(part3.value);
    const representativeName = representativeNameInput.value.trim();
    const email = emailInput.value.trim();

    if (
      isValidPart1 &&
      isValidPart2 &&
      isValidPart3 &&
      representativeName &&
      email
    ) {
      verifyButton.disabled = false;
      verifyButton.classList.remove("cursor-not-allowed", "opacity-70");
    } else {
      verifyButton.disabled = true;
      verifyButton.classList.add("cursor-not-allowed", "opacity-70");
    }
    errorMessage.classList.add("hidden");
  }

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
  representativeNameInput.addEventListener("input", validateInputs);
  emailInput.addEventListener("input", validateInputs);
});
