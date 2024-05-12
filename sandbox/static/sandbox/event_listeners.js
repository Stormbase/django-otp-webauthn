/*
 * A script to listen for events dispatched by the default OTP WebAuthn JavaScript implementation
 * It logs received events to the console for debugging purposes.
 */
document.addEventListener("DOMContentLoaded", function () {
  //   Registration events
  document.addEventListener("otp_webauthn.register_start", function (event) {
    console.log("[sandbox] otp_webauthn.register_start event received", event);
  });
  document.addEventListener("otp_webauthn.register_complete", function (event) {
    console.log(
      "[sandbox] otp_webauthn.register_complete event received",
      event
    );
  });
  document.addEventListener("otp_webauthn.register_failed", function (event) {
    console.log("[sandbox] otp_webauthn.register_failed event received", event);
  });

  // Verification events
  document.addEventListener(
    "otp_webauthn.verification_start",
    function (event) {
      console.log(
        "[sandbox] otp_webauthn.verification_start event received",
        event
      );
    }
  );
  document.addEventListener(
    "otp_webauthn.verification_complete",
    function (event) {
      console.log(
        "[sandbox] otp_webauthn.verification_complete event received",
        event
      );
    }
  );
  document.addEventListener(
    "otp_webauthn.verification_failed",
    function (event) {
      console.log(
        "[sandbox] otp_webauthn.verification_failed event received",
        event
      );
    }
  );
});
