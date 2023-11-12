import { getConfig } from "./config";
import {
  checkSupport,
  getCSRFToken,
  base64ToBuffer,
  encodeAuthenticatorRegistrationResponseAsJSON,
} from "./support";
import { BeginRegistrationPayload, Config } from "./types";

(() =>
  (async function () {
    const config = await getConfig();
    const support = await checkSupport();

    const showPasskeyRegister =
      support.isSecureContext && support.isWebAuthnAvailable;

    setPasskeyRegisterVisible(showPasskeyRegister);

    if (showPasskeyRegister) {
      await setupPasskeyRegistrationButton(config);
    }
  })())();

async function setupPasskeyRegistrationButton(config: Config): Promise<void> {
  const passkeyRegisterButton = document.getElementById(
    "passkey-register-button"
  );
  if (!passkeyRegisterButton) {
    return;
  }

  passkeyRegisterButton.addEventListener("click", async (_) => {
    const credential = await beginRegistration(config);
    if (!credential) {
      return;
    }

    await tryFetchCompleteRegistrationResponseData(config, credential);
    alert("Registration complete");
  });
}

async function tryFetchCompleteRegistrationResponseData(
  config: Config,
  credential: PublicKeyCredential
): Promise<boolean> {
  try {
    const credentialJSON = await encodeAuthenticatorRegistrationResponseAsJSON(
      credential
    );
    const response = await fetch(config.completeRegistrationUrl, {
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
        config.messages.registration.error.serverError.replace(
          "$status_code$",
          response.status.toString()
        )
      );
      return false;
    }
    return false;
  } catch (e: unknown) {
    alert(config.messages.registration.error.serverUnreachable);
    throw e;
  }
}

async function tryFetchBeginRegistrationResponseData(
  config: Config
): Promise<BeginRegistrationPayload | null> {
  try {
    const response = await fetch(config.beginRegistrationUrl, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-CSRFToken": await getCSRFToken(config),
      },
    });

    if (!response.ok) {
      const message = config.messages.registration.error.serverError.replace(
        "$status_code$",
        response.status.toString()
      );
      alert(message);
      return null;
    }
    const data: BeginRegistrationPayload = await response.json();
    return data;
  } catch (e: unknown) {
    alert(config.messages.registration.error.serverUnreachable);
    throw e;
  }
}

async function tryRegisterCredentials(
  config: Config,
  creationOptions: CredentialCreationOptions
): Promise<PublicKeyCredential | null> {
  try {
    return (await navigator.credentials.create(
      creationOptions
    )) as PublicKeyCredential;
  } catch (e: unknown) {
    console.log("Creation options used:");
    console.log(creationOptions);
    if (e instanceof DOMException) {
      if (e.name === "NotAllowedError") {
        alert(
          config.messages.registration.error.clientSideCreationNotAllowedError
        );
        throw e;
      }
      // This is a slightly crude way of checking for the error, but it works for now
      // Most browsers that were tested will throw a SecurityError with a message containing "registrable domain"
      // The error is about the domain not being eligible for registration (because it is not a valid TLD or a test domain)
      // We want to show an accurate error message to the user (or more likely a developer testing the library)
      if (
        e.name === "SecurityError" &&
        e.message.includes("registrable domain")
      ) {
        alert(
          config.messages.registration.error.clientSideInvalidDomainError.replace(
            "$domain$",
            window.location.hostname
          )
        );
        throw e;
      }
      if (
        // Happens when the same passkey is registered twice, for example
        e.name === "InvalidStateError"
      ) {
        // Some browsers will show a sensible error message - some will fail silently
        // We want to ensure that the user always sees feedback, even if some browsers already show a sensible one.
        alert(config.messages.registration.error.clientSideInvalidStateError);
        throw e;
      }
    }
    alert(config.messages.registration.error.clientSideCreationUnknownError);
    throw e;
  }
}

async function beginRegistration(
  config: Config
): Promise<PublicKeyCredential | null> {
  console.log("We shall begin registration");

  const data = await tryFetchBeginRegistrationResponseData(config);
  if (!data) {
    return null;
  }

  const challenge = await base64ToBuffer(data.publicKey.challenge);
  const userId = await base64ToBuffer(data.publicKey.user.id);

  const excludeCredentials = await Promise.all(
    data.publicKey.excludeCredentials.map(async (cred) => {
      return {
        type: cred.type,
        transports: cred.transports,
        id: await base64ToBuffer(cred.id),
      } as PublicKeyCredentialDescriptor;
    })
  );

  // Add the decoded data back to the options
  const creationOptions: CredentialCreationOptions = {
    publicKey: {
      ...data.publicKey,
      challenge,
      user: {
        ...data.publicKey.user,
        id: userId,
      },
      excludeCredentials: excludeCredentials,
    },
  };

  return await tryRegisterCredentials(config, creationOptions);
}

async function setPasskeyRegisterVisible(visible: boolean): Promise<void> {
  const placeholderElement = document.getElementById(
    "passkey-registration-placeholder"
  );
  const availableTemplate = document.getElementById(
    "passkey-registration-available-template"
  ) as HTMLTemplateElement;
  const fallbackTemplate = document.getElementById(
    "passkey-registration-unavailable-template"
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
