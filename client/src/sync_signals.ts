import { SyncSignalConfig } from "./types";

/**
 * Client-side sync signals for WebAuthn credentials.
 *
 * Reads JSON configuration from a script[id="webauthn-sync-signals-config"] and
 * calls the PublicKeyCredential.signalCurrentUserDetails and
 * PublicKeyCredential.signalAllAcceptedCredentials browser APIs to update user details
 * and to hide removed credentials, so they won't be shown in future authentication prompts.
 */
(() => async () => {
  const configScript = document.getElementById(
    "otp_webauthn_sync_signals_config",
  );
  if (!configScript) {
    return;
  }

  const config = JSON.parse(
    configScript.textContent || "{}",
  ) as SyncSignalConfig;
  if (!config) {
    return;
  }
  // Remove the config script tag from the DOM now that we've read it
  // don't make it available to any other scripts for security/privacy reasons
  configScript.remove();

  // Signal current user details
  if (
    typeof PublicKeyCredential === "undefined" ||
    typeof PublicKeyCredential.signalCurrentUserDetails !== "function"
  ) {
    console.warn(
      "PublicKeyCredential.signalCurrentUserDetails is not supported by this browser.",
    );
    return;
  } else {
    const payload = {
      rpId: config.rpId,
      userId: config.userId,
      name: config.name,
      displayName: config.displayName,
    };
    await PublicKeyCredential.signalCurrentUserDetails(payload);
    console.log(
      "[WebAuthn] Signaled current user details to the browser.",
      payload,
    );
  }

  // Signal all accepted credentials
  if (
    typeof PublicKeyCredential === "undefined" ||
    typeof PublicKeyCredential.signalAllAcceptedCredentials !== "function"
  ) {
    console.warn(
      "PublicKeyCredential.signalAllAcceptedCredentials is not supported by this browser.",
    );
    return;
  } else {
    const payload = {
      rpId: config.rpId,
      userId: config.userId,
      allAcceptedCredentialIds: config.credentialIds,
    };
    await PublicKeyCredential.signalAllAcceptedCredentials(payload);
    console.log(
      "[WebAuthn] Signaled accepted credentials to the browser.",
      payload,
    );
  }
})()();
