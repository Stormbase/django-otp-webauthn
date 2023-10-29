import { Config, Support } from "./types";

/**
 * Converts a base64-encoded string to an ArrayBuffer
 */
export async function base64ToBuffer(base64: string): Promise<ArrayBuffer> {
  const binaryString = window.atob(base64);
  const binaryLen = binaryString.length;
  const bytes = new Uint8Array(binaryLen);
  for (let i = 0; i < binaryLen; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
}

/**
 * Converts an ArrayBuffer to a base64-encoded string
 */
export async function bufferToBase64(buffer: ArrayBuffer): Promise<string> {
  const bytes = new Uint8Array(buffer);
  const binaryString = Array.from(bytes)
    .map((byte) => String.fromCharCode(byte))
    .join("");

  return btoa(binaryString);
}

/**
 * Converts a PublicKeyCredential to a JSON string
 * @param credential the credential to encode as JSON
 * @returns
 */
export async function encodeAuthenticatorRegistrationResponseAsJSON(
  credential: PublicKeyCredential,
): Promise<string> {
  const publicKeyCredential = credential;
  const rawId = await bufferToBase64(publicKeyCredential.rawId);
  const id = publicKeyCredential.id;
  const type = publicKeyCredential.type;
  const authenticatorAttachment = publicKeyCredential.authenticatorAttachment;
  const response =
    publicKeyCredential.response as AuthenticatorAttestationResponse;
  const clientDataJSON = await bufferToBase64(response.clientDataJSON);
  const attestationObject = await bufferToBase64(response.attestationObject);

  let data = {
    id,
    rawId,
    type,
    transports: response.getTransports(),
    authenticatorAttachment,
    response: {
      clientDataJSON,
      attestationObject,
    },
  };

  const credentialJSON = JSON.stringify(data);
  return credentialJSON;
}


/**
 * Converts a PublicKeyCredential to a JSON string
 * @param credential the credential to encode as JSON
 * @returns
 */
export async function encodeAuthenticatorAssertionResponseAsJSON(
  credential: PublicKeyCredential,
): Promise<string> {
  const publicKeyCredential = credential;
  const rawId = await bufferToBase64(publicKeyCredential.rawId);
  const id = publicKeyCredential.id;
  const type = publicKeyCredential.type;
  const response =
    publicKeyCredential.response as AuthenticatorAssertionResponse;
  const clientDataJSON = await bufferToBase64(response.clientDataJSON);
  const authenticatorData = await bufferToBase64(response.authenticatorData);
  const signature = await bufferToBase64(response.signature);

  let data = {
    id,
    rawId,
    type,
    response: {
      clientDataJSON,
      authenticatorData,
      signature,
      userHandle: response.userHandle,
    },
  };

  const credentialJSON = JSON.stringify(data);
  return credentialJSON;
}


/**
 * Retrieves the CSRF token from the CSRF cookie
 */
export async function getCSRFToken(config: Config): Promise<string> {
  let cookieValue = "";
  const cookieName = config.csrfCookieName;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, cookieName.length + 1) === cookieName + "=") {
        cookieValue = decodeURIComponent(
          cookie.substring(cookieName.length + 1),
        );
        break;
      }
    }
  }
  return cookieValue;
}

export async function checkSupport(): Promise<Support> {
  const support: Support = {
    isUserVerifyingPlatformAuthenticatorAvailable: true,
    isSecureContext: true,
    isWebAuthnAvailable: true,
    isConditionalMediationAvailable: true,
  };

  // Check if running in a secure context
  if ("isSecureContext" in window && !window.isSecureContext) {
    console.warn(
      "This page is not running in a secure context. WebAuthn will not work.",
    );
    support.isSecureContext = false;
  }

  if (!("PublicKeyCredential" in window)) {
    console.log("This browser does not support WebAuthn");
    support.isWebAuthnAvailable = false;
  }

  // Check if conditional mediation is available
  if (
    !(
      "PublicKeyCredential" in window &&
      window.PublicKeyCredential.isConditionalMediationAvailable &&
      window.PublicKeyCredential.isConditionalMediationAvailable()
    )
  ) {
    console.log("This browser does not support conditional mediation.");
    support.isConditionalMediationAvailable = false;
  }

  if (
    !(
      "PublicKeyCredential" in window &&
      window.PublicKeyCredential
        .isUserVerifyingPlatformAuthenticatorAvailable &&
      window.PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable()
    )
  ) {
    console.log(
      "This browser does not support user verifying platform authenticators.",
    );
    support.isUserVerifyingPlatformAuthenticatorAvailable = false;
  }

  console.log("Available features:");
  console.log(support);
  return support;
}
