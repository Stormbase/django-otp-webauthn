import { State, Config } from "./types";
import { getCSRFToken, getConfig } from "./utils";
import {
  browserSupportsWebAuthn,
  startRegistration,
  WebAuthnError,
} from "@simplewebauthn/browser";

/**
 * This function is immediately invoked and sets up the registration button
 */
(() =>
  (async function () {
    const REGISTER_BUTTON_ID = "passkey-register-button";
    const REGISTER_STATUS_MESSAGE_ID = "passkey-register-status-message";
    const REGISTER_STATUS_MESSAGE_VISIBLE_CLASS = "visible";
    const REGISTER_PLACEHOLDER_ID = "passkey-registration-placeholder";
    const REGISTER_FALLBACK_TEMPLATE_ID =
      "passkey-registration-unavailable-template";
    const REGISTER_AVAILABLE_TEMPLATE_ID =
      "passkey-registration-available-template";

    const EVENT_REGISTER_START = "otp_webauthn.register_start";
    const EVENT_REGISTER_COMPLETE = "otp_webauthn.register_complete";
    const EVENT_REGISTER_FAILED = "otp_webauthn.register_failed";

    async function setupPasskeyRegistrationButton(
      config: Config,
    ): Promise<void> {
      const passkeyRegisterButton = document.getElementById(REGISTER_BUTTON_ID);
      if (!passkeyRegisterButton) {
        return;
      }

      const buttonLabel =
        passkeyRegisterButton.textContent || gettext("Register a Passkey");

      // Register button click handler
      passkeyRegisterButton.addEventListener("click", async (_) => {
        passkeyRegisterButton.dispatchEvent(
          new CustomEvent(EVENT_REGISTER_START, { bubbles: true }),
        );
        await setPasskeyRegisterState({
          buttonDisabled: true,
          buttonLabel: gettext("Registering..."),
        });

        // Begin registration: fetch options and challenge
        const response = await fetch(config.beginRegistrationUrl, {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "X-CSRFToken": await getCSRFToken(config),
            Accept: "application/json",
          },
        });

        if (!response.ok) {
          setPasskeyRegisterState({
            buttonDisabled: false,
            buttonLabel,
            requestFocus: true,
            status: gettext(
              "Registration failed. Unable to fetch registration options from server.",
            ),
          });
          passkeyRegisterButton.dispatchEvent(
            new CustomEvent(EVENT_REGISTER_FAILED, {
              detail: {
                response,
              },
              bubbles: true,
            }),
          );
          return;
        }

        let attResp;

        try {
          attResp = await startRegistration(await response.json());
        } catch (error: unknown) {
          console.error(error);
          if (error instanceof Error || error instanceof WebAuthnError) {
            switch (error.name) {
              case "AbortError":
                setPasskeyRegisterState({
                  buttonDisabled: false,
                  buttonLabel,
                  status: gettext("Registration aborted."),
                  requestFocus: true,
                });
                break;
              case "InvalidStateError":
                setPasskeyRegisterState({
                  buttonDisabled: false,
                  buttonLabel,
                  status: gettext(
                    "Registration failed. You most likely already have a Passkey registered for this site.",
                  ),
                  requestFocus: true,
                });
                break;
              case "NotAllowedError":
                setPasskeyRegisterState({
                  buttonDisabled: false,
                  buttonLabel,
                  status: gettext("Registration aborted or not allowed."),
                  requestFocus: true,
                });
                break;
              case "SecurityError":
                setPasskeyRegisterState({
                  buttonDisabled: false,
                  buttonLabel,
                  status: gettext(
                    "Registration failed. A technical problem occurred that prevents you from registering a Passkey for this site.",
                  ),
                  requestFocus: true,
                });
                break;
              default:
                setPasskeyRegisterState({
                  buttonDisabled: false,
                  buttonLabel,
                  status: gettext(
                    "Registration failed. An unknown error occurred.",
                  ),
                  requestFocus: true,
                });
                throw error;
            }
            passkeyRegisterButton.dispatchEvent(
              new CustomEvent(EVENT_REGISTER_FAILED, {
                detail: {
                  error,
                },
                bubbles: true,
              }),
            );
            return;
          }
        }

        setPasskeyRegisterState({
          buttonDisabled: true,
          buttonLabel: gettext("Finishing registration..."),
        });

        // Complete
        const verificationResp = await fetch(config.completeRegistrationUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": await getCSRFToken(config),
          },
          credentials: "same-origin",
          body: JSON.stringify(attResp),
        });

        if (!verificationResp.ok) {
          setPasskeyRegisterState({
            buttonDisabled: false,
            buttonLabel,
            status: gettext(
              "Registration failed. The server was unable to verify this passkey.",
            ),
            requestFocus: true,
          });
          passkeyRegisterButton.dispatchEvent(
            new CustomEvent(EVENT_REGISTER_FAILED, {
              detail: {
                response: verificationResp,
              },
              bubbles: true,
            }),
          );
          return;
        }

        // Check if the response is a JSON object
        if (
          !verificationResp.headers
            .get("content-type")
            ?.includes("application/json")
        ) {
          setPasskeyRegisterState({
            buttonDisabled: false,
            buttonLabel,
            status: gettext("Registration failed. A server error occurred."),
            requestFocus: true,
          });
          passkeyRegisterButton.dispatchEvent(
            new CustomEvent(EVENT_REGISTER_FAILED, {
              detail: {
                response: verificationResp,
              },
              bubbles: true,
            }),
          );
          return;
        }

        // Wait for the results of verification
        const verificationJSON = await verificationResp.json();

        // Show UI appropriate for the `verified` status
        if (verificationJSON && verificationJSON.id) {
          setPasskeyRegisterState({
            buttonDisabled: false,
            buttonLabel,
            status: gettext("Registration successful!"),
            requestFocus: true,
          });
          passkeyRegisterButton.dispatchEvent(
            new CustomEvent(EVENT_REGISTER_COMPLETE, {
              detail: {
                response: verificationJSON,
                id: verificationJSON.id,
              },
              bubbles: true,
            }),
          );
        } else {
          const msg =
            verificationJSON.error ||
            gettext("An error occurred during registration.");
          setPasskeyRegisterState({
            buttonDisabled: false,
            buttonLabel,
            status: msg,
            requestFocus: true,
          });
          passkeyRegisterButton.dispatchEvent(
            new CustomEvent(EVENT_REGISTER_FAILED, {
              detail: {
                response: verificationResp,
              },
              bubbles: true,
            }),
          );
        }
      });

      async function setPasskeyRegisterState(state: State): Promise<void> {
        const passkeyRegisterButton = document.getElementById(
          REGISTER_BUTTON_ID,
        ) as HTMLButtonElement;
        if (!passkeyRegisterButton) {
          return;
        }
        const passkeyStatusText = document.getElementById(
          REGISTER_STATUS_MESSAGE_ID,
        ) as HTMLElement;

        passkeyRegisterButton.disabled = state.buttonDisabled;
        passkeyRegisterButton.textContent = state.buttonLabel;

        if (passkeyStatusText) {
          if (state.status) {
            // If there is a status message, we want to make sure screen readers
            // announce it to the user for clarity as to what is happening.
            passkeyRegisterButton.setAttribute(
              "aria-describedby",
              REGISTER_STATUS_MESSAGE_ID,
            );
            passkeyStatusText.classList.add(
              REGISTER_STATUS_MESSAGE_VISIBLE_CLASS,
            );
            passkeyStatusText.innerText = state.status;
            passkeyStatusText.setAttribute("aria-live", "assertive");

            if (state.requestFocus) {
              passkeyRegisterButton.focus();
            }
          } else {
            passkeyRegisterButton.removeAttribute("aria-describedby");
            passkeyStatusText.removeAttribute("aria-live");
            passkeyStatusText.classList.remove(
              REGISTER_STATUS_MESSAGE_VISIBLE_CLASS,
            );
          }
        }
      }
    }

    async function setPasskeyRegisterVisible(visible: boolean): Promise<void> {
      const placeholderElement = document.getElementById(
        REGISTER_PLACEHOLDER_ID,
      );
      const availableTemplate = document.getElementById(
        REGISTER_AVAILABLE_TEMPLATE_ID,
      ) as HTMLTemplateElement;
      const fallbackTemplate = document.getElementById(
        REGISTER_FALLBACK_TEMPLATE_ID,
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

    const config = await getConfig();

    if (!browserSupportsWebAuthn()) {
      await setPasskeyRegisterVisible(false);
      return;
    } else {
      await setPasskeyRegisterVisible(true);
      await setupPasskeyRegistrationButton(config);
    }
  })())();
