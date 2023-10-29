import { getConfig } from "./config";
import { base64ToBuffer, checkSupport, encodeAuthenticatorAssertionResponseAsJSON, getCSRFToken } from "./support";
import { Config, BeginAuthenticationPayload } from "./types";

(() =>
  (async function () {
    const config = await getConfig();
    const support = await checkSupport();

    if (!support.isSecureContext && !support.isWebAuthnAvailable) {
      console.warn(
        "WebAuthn is not available. Please use a secure context (HTTPS) and a browser that supports WebAuthn.",
      );
    }

    if (config.autocompleteLoginFieldSelector) {
      await setupLoginFormAutocomplete(config);
    }
    // If there is no login field, we show the verification button instead
    else {
      await setPasskeyVerificationButtonVisible(true);
      await setupPasskeyVerificationButton(config);
    }

    if (support.isConditionalMediationAvailable && config.autocompleteLoginFieldSelector && !!document.querySelector(config.autocompleteLoginFieldSelector)) {
      console.log("Conditional mediation is available, will try to use it now...");
      await handleAuthentication(config, true);
    }
  })())();

async function tryFetchBeginAuthenticationResponseData(
  config: Config,
): Promise<BeginAuthenticationPayload | null> {
  try {
    const response = await fetch(config.beginAuthenticationUrl, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-CSRFToken": await getCSRFToken(config),
      },
    });

    if (!response.ok) {
      const message = config.messages.authentication.error.serverError.replace(
        "$status_code$",
        response.status.toString(),
      );
      alert(message);
      return null;
    }
    return await response.json();
  } catch (e: unknown) {
    alert(config.messages.authentication.error.serverUnreachable);
    throw e;
  }
}

/**
 * Return the next url from a hidden input on the page or from in the query string.
 *
 * @returns string|null the next url or null if not present
 */
async function getNextUrl(): Promise<string|null> {
  const nextUrlElement = document.querySelector("input[name=next]");
  const nextUrlParameter = new URLSearchParams(window.location.search).get("next");
  return (nextUrlElement && nextUrlElement.getAttribute("value")) || nextUrlParameter || null;
}

async function tryFetchCompleteAuthenticationResponseData(
  config: Config,
  credential: PublicKeyCredential,
): Promise<Response> {
  try {
    const credentialJSON = await encodeAuthenticatorAssertionResponseAsJSON(credential);

    // If there is a next url, we append it to the complete authentication url so that the user is redirected to it after
    const nextUrl = await getNextUrl();
    const url = nextUrl ? `${config.completeAuthenticationUrl}?next=${encodeURIComponent(nextUrl)}` : config.completeAuthenticationUrl;
    const response = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-CSRFToken": await getCSRFToken(config),
      },
      body: credentialJSON,
    });
    if (!response.ok) {
      alert(
        config.messages.authentication.error.serverError.replace(
          "$status_code$",
          response.status.toString(),
        ),
      );
      return response;
    }
    return response;
  } catch (e: unknown) {
    alert(config.messages.authentication.error.serverUnreachable);
    throw e;
  }
}


/**
 * Add the webauthn autocomplete attribute to the target element
 */
async function setupLoginFormAutocomplete(config: Config): Promise<void> {
  if (!config.autocompleteLoginFieldSelector) {
    return;
  }

  const targetElement: HTMLElement | null = document.querySelector(
    config.autocompleteLoginFieldSelector,
  );
  if (!targetElement) {
    throw new Error(
      `Target element not found. Selector: ${config.autocompleteLoginFieldSelector}`,
    );
  }
  const originalAutocompleteString =
    targetElement.getAttribute("autocomplete") || "";
  targetElement.setAttribute(
    "autocomplete",
    originalAutocompleteString + " webauthn",
  );
}

async function beginAuthentication(config: Config, conditional: boolean): Promise<PublicKeyCredential | null> {
  const data = await tryFetchBeginAuthenticationResponseData(
    config,
  );
  if (!data) {
    return null;
  }

  const challenge = await base64ToBuffer(data.publicKey.challenge);
  let allowCredentials = undefined;

  if ("allowCredentials" in data.publicKey) {
    allowCredentials = await Promise.all(data.publicKey.allowCredentials.map(async (cred) => ({
      ...cred,
      id: await base64ToBuffer(cred.id),
    })));
  }


  try {
    const credential = await navigator.credentials.get({
      publicKey: {
        rpId: data.publicKey.rpId,
        challenge: challenge,
        // @ts-ignore: there is a inconsequential type mismatch with our credential id binary buffer
        allowCredentials: allowCredentials,
      },
      mediation: conditional ? "conditional" : undefined,
    }) as PublicKeyCredential;

    return credential;
  }
  catch (e: unknown) {
    if (e instanceof DOMException) {
      if (e.name === "NotAllowedError") {
        alert(config.messages.authentication.error.clientSideNotAllowedError);

      }
      else if (e.name === "SecurityError") {
        alert(config.messages.authentication.error.clientSideInvalidDomainError);
      }
      else if (e.name === "InvalidStateError") {
        alert(config.messages.authentication.error.clientSideInvalidStateError);
      }
      else {
        alert(config.messages.authentication.error.clientSideUnknownError);
      }
    }
    console.error(e);
  }
  return null;
}

async function handleAuthentication(config: Config, conditional: boolean): Promise<void> {
  const credential = await beginAuthentication(config, conditional);
  if (!credential) {
    return;
  }

  const response = await tryFetchCompleteAuthenticationResponseData(config, credential);
  const responseJSON = await response.json();
  if (responseJSON.redirect_url) {
    window.location.href = responseJSON.redirect_url;
  }
}

/**
 * Setup event handlers for the passkey verification button.
 *
 * @param config
 */
async function setupPasskeyVerificationButton(config: Config): Promise<void> {
  const passkeyVerificationButton = document.getElementById(
    "passkey-verification-button",
  );
  if (!passkeyVerificationButton) {
    return;
  }

  passkeyVerificationButton.addEventListener("click", async (_) => handleAuthentication(config, false));
}

async function setPasskeyVerificationButtonVisible(
  visible: boolean,
): Promise<void> {
  const placeholderElement = document.getElementById(
    "passkey-verification-placeholder",
  );
  const availableTemplate = document.getElementById(
    "passkey-verification-available-template",
  ) as HTMLTemplateElement;
  const fallbackTemplate = document.getElementById(
    "passkey-verification-unavailable-template",
  ) as HTMLTemplateElement;

  if (!placeholderElement) {
    throw new Error("Placeholder element not found");
  }

  if (!availableTemplate) {
    throw new Error("Available template not found");
  }

  if (visible) {
    const clone = availableTemplate.content.cloneNode(true);
    placeholderElement.replaceWith(clone);
  } else {
    if (fallbackTemplate) {
      const clone = fallbackTemplate.content.cloneNode(true);
      placeholderElement.replaceWith(clone);
    } else {
      placeholderElement.remove();
    }
  }
}
