import { State, Config } from "./types";
import { getCSRFToken, getConfig } from "./utils";
import {
  browserSupportsWebAuthn,
  browserSupportsWebAuthnAutofill,
  startAuthentication,
  WebAuthnError,
} from "@simplewebauthn/browser";

/**
 * This function is immediately invoked and sets up the registration button
 */
(() =>
  (async function () {
    const VERIFICATION_BUTTON_ID = "passkey-verification-button";
    const VERIFICATION_STATUS_MESSAGE_ID =
      "passkey-verification-status-message";
    const VERIFICATION_STATUS_MESSAGE_VISIBLE_CLASS = "visible";
    const VERIFICATION_PLACEHOLDER_ID = "passkey-verification-placeholder";
    const VERIFICATION_FALLBACK_TEMPLATE_ID =
      "passkey-verification-unavailable-template";
    const VERIFICATION_AVAILABLE_TEMPLATE_ID =
      "passkey-verification-available-template";

    const EVENT_VERIFICATION_START = "otp_webauthn.verification_start";
    const EVENT_VERIFICATION_COMPLETE = "otp_webauthn.verification_complete";
    const EVENT_VERIFICATION_FAILED = "otp_webauthn.verification_failed";

    async function setupPasskeyAutofill(config: Config) {
      if (!config.autocompleteLoginFieldSelector) {
        return;
      }

      // Find the login field
      const loginField = document.querySelector(
        config.autocompleteLoginFieldSelector,
      ) as HTMLInputElement;

      if (!loginField) {
        console.error(
          `Could not find login field with selector ${config.autocompleteLoginFieldSelector}. WebAuthn autofill cannot continue.`,
        );
        return;
      }

      // Add "webauthn" to the autocomplete attribute, necessary for the browser to trigger the autofill UI
      const originalAutocompleteString =
        loginField.getAttribute("autocomplete") || "";
      loginField.setAttribute(
        "autocomplete",
        // Order of the values is important; webauthn must be the last value
        originalAutocompleteString + " webauthn",
      );

      loginField.dispatchEvent(
        new CustomEvent(EVENT_VERIFICATION_START, {
          detail: { fromAutofill: true },
          bubbles: true,
        }),
      );

      // Begin authentication: fetch options and challenge
      const response = await fetch(config.beginAuthenticationUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "X-CSRFToken": await getCSRFToken(config),
          Accept: "application/json",
        },
      });

      if (!response.ok) {
        console.error(
          "Unable to fetch options from server. Will not attempt autofill.",
        );
        loginField.dispatchEvent(
          new CustomEvent(EVENT_VERIFICATION_FAILED, {
            detail: {
              fromAutofill: true,
              response,
            },
            bubbles: true,
          }),
        );
        return;
      }

      let attResp;
      try {
        // Important: the second argument to startAuthentication is to call for the browser autofill UI
        attResp = await startAuthentication(await response.json(), true);
      } catch (error: unknown) {
        console.error(
          "Got error during the webauthn credential autofill call",
          error,
        );
        loginField.dispatchEvent(
          new CustomEvent(EVENT_VERIFICATION_FAILED, {
            detail: {
              fromAutofill: true,
              error,
            },
            bubbles: true,
          }),
        );
        return;
      }
      // Find out if there is a hidden 'next' field on the page
      const next = document.querySelector(
        "input[name='next']",
      ) as HTMLInputElement;
      let completeAuthenticationUrl = config.completeAuthenticationUrl;
      if (next && next.value) {
        completeAuthenticationUrl += `?next=${encodeURIComponent(next.value)}`;
      }

      // Complete
      const verificationResp = await fetch(completeAuthenticationUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": await getCSRFToken(config),
        },
        credentials: "same-origin",
        body: JSON.stringify(attResp),
      });

      // Check if the verification response is not JSON, which points to a server error
      if (
        !verificationResp.headers
          .get("content-type")
          ?.includes("application/json")
      ) {
        loginField.dispatchEvent(
          new CustomEvent(EVENT_VERIFICATION_FAILED, {
            detail: {
              fromAutofill: true,
              response: verificationResp,
            },
            bubbles: true,
          }),
        );
        alert(gettext("Verification failed. A server error occurred."));
        return;
      }

      // Wait for the results of verification
      const verificationJSON = await verificationResp.json();

      // Handle failed verification
      if (!verificationResp.ok && "detail" in verificationJSON) {
        loginField.dispatchEvent(
          new CustomEvent(EVENT_VERIFICATION_FAILED, {
            detail: {
              fromAutofill: true,
              response: verificationResp,
            },
            bubbles: true,
          }),
        );
        alert(verificationJSON.detail);
        return;
      }

      // Show UI appropriate for the `verified` status
      if (verificationJSON && verificationJSON.id) {
        loginField.dispatchEvent(
          new CustomEvent(EVENT_VERIFICATION_COMPLETE, {
            detail: {
              fromAutofill: true,
              response: verificationResp,
            },
            bubbles: true,
          }),
        );
        // Redirect to the next page
        if (verificationJSON.redirect_url) {
          window.location.href = verificationJSON.redirect_url;
        }
      } else {
        loginField.dispatchEvent(
          new CustomEvent(EVENT_VERIFICATION_FAILED, {
            detail: {
              fromAutofill: true,
              response: verificationResp,
            },
            bubbles: true,
          }),
        );
        const msg =
          verificationJSON.error ||
          gettext("An error occurred during verification.");
        alert(msg);
      }
    }

    async function setupPasskeyVerificationButton(
      config: Config,
    ): Promise<void> {
      const passkeyVerifyButton = document.getElementById(
        VERIFICATION_BUTTON_ID,
      );
      if (!passkeyVerifyButton) {
        return;
      }

      const buttonLabel =
        passkeyVerifyButton.innerText || gettext("Verify with Passkey");

      passkeyVerifyButton.addEventListener("click", async (_) => {
        passkeyVerifyButton.dispatchEvent(
          new CustomEvent(EVENT_VERIFICATION_START, {
            detail: {
              fromAutofill: false,
            },
            bubbles: true,
          }),
        );
        await setPasskeyVerifyState({
          buttonDisabled: true,
          buttonLabel: gettext("Verifying..."),
        });

        // Begin authentication: fetch options and challenge
        const response = await fetch(config.beginAuthenticationUrl, {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "X-CSRFToken": await getCSRFToken(config),
            Accept: "application/json",
          },
        });

        if (!response.ok) {
          await setPasskeyVerifyState({
            buttonDisabled: false,
            buttonLabel,
            requestFocus: true,
            status: gettext(
              "Verification failed. Could not retrieve parameters from the server.",
            ),
          });
          passkeyVerifyButton.dispatchEvent(
            new CustomEvent(EVENT_VERIFICATION_FAILED, {
              detail: {
                fromAutofill: false,
                response,
              },
              bubbles: true,
            }),
          );
          return;
        }

        let attResp;

        try {
          attResp = await startAuthentication(await response.json());
        } catch (error: unknown) {
          if (error instanceof Error || error instanceof WebAuthnError) {
            console.error(error);

            switch (error.name) {
              case "AbortError":
                await setPasskeyVerifyState({
                  buttonDisabled: false,
                  buttonLabel,
                  requestFocus: true,
                  status: gettext("Verification aborted."),
                });
                break;
              case "NotAllowedError":
                await setPasskeyVerifyState({
                  buttonDisabled: false,
                  buttonLabel,
                  requestFocus: true,
                  status: gettext("Verification canceled or not allowed."),
                });
                break;
              default:
                await setPasskeyVerifyState({
                  buttonDisabled: false,
                  buttonLabel,
                  requestFocus: true,
                  status: gettext(
                    "Verification failed. An unknown error occurred.",
                  ),
                });
                throw error;
            }
            passkeyVerifyButton.dispatchEvent(
              new CustomEvent(EVENT_VERIFICATION_FAILED, {
                detail: {
                  fromAutofill: false,
                  error,
                },
                bubbles: true,
              }),
            );
            return;
          }
        }

        await setPasskeyVerifyState({
          buttonDisabled: true,
          buttonLabel: gettext("Finishing verification..."),
        });

        // Find out if there is a hidden 'next' field on the page
        const next = document.querySelector(
          "input[name='next']",
        ) as HTMLInputElement;
        let completeAuthenticationUrl = config.completeAuthenticationUrl;
        if (next && next.value) {
          completeAuthenticationUrl += `?next=${encodeURIComponent(next.value)}`;
        }

        // Complete
        const verificationResp = await fetch(completeAuthenticationUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": await getCSRFToken(config),
          },
          credentials: "same-origin",
          body: JSON.stringify(attResp),
        });

        if (
          !verificationResp.headers
            .get("content-type")
            ?.includes("application/json")
        ) {
          await setPasskeyVerifyState({
            buttonDisabled: false,
            buttonLabel,
            requestFocus: true,
            status: gettext(
              "Verification failed. An unknown server error occurred.",
            ),
          });
          passkeyVerifyButton.dispatchEvent(
            new CustomEvent(EVENT_VERIFICATION_FAILED, {
              detail: {
                fromAutofill: false,
                response: verificationResp,
              },
              bubbles: true,
            }),
          );
          return;
        }

        // Wait for the results of verification
        const verificationJSON = await verificationResp.json();

        if (!verificationResp.ok) {
          const msg =
            verificationJSON.detail ||
            gettext("Verification failed. An unknown error occurred.");
          await setPasskeyVerifyState({
            buttonDisabled: false,
            buttonLabel,
            requestFocus: true,
            status: msg,
          });
          passkeyVerifyButton.dispatchEvent(
            new CustomEvent(EVENT_VERIFICATION_FAILED, {
              detail: {
                fromAutofill: false,
                response: verificationResp,
              },
              bubbles: true,
            }),
          );
          return;
        }

        // Show UI appropriate for the `verified` status
        if (verificationJSON && verificationJSON.id) {
          await setPasskeyVerifyState({
            buttonDisabled: false,
            buttonLabel,
            status: gettext("Verification successful!"),
          });

          passkeyVerifyButton.dispatchEvent(
            new CustomEvent(EVENT_VERIFICATION_COMPLETE, {
              detail: {
                fromAutofill: false,
                response: verificationResp,
                id: verificationJSON.id,
              },
              bubbles: true,
            }),
          );

          // Redirect to the next page
          if (verificationJSON.redirect_url) {
            window.location.href = verificationJSON.redirect_url;
          }
        } else {
          const msg =
            verificationJSON.error ||
            gettext("An error occurred during verification.");
          await setPasskeyVerifyState({
            buttonDisabled: false,
            buttonLabel,
            requestFocus: true,
            status: msg,
          });
        }
      });
    }

    async function setPasskeyVerifyState(state: State): Promise<void> {
      const passkeyAuthButton = document.getElementById(
        VERIFICATION_BUTTON_ID,
      ) as HTMLButtonElement;
      if (!passkeyAuthButton) {
        return;
      }
      const passkeyStatusText = document.getElementById(
        VERIFICATION_STATUS_MESSAGE_ID,
      ) as HTMLElement;

      passkeyAuthButton.disabled = state.buttonDisabled;
      passkeyAuthButton.innerText = state.buttonLabel;

      if (passkeyStatusText) {
        // If there is a status message, we want to make sure screen readers
        // announce it to the user for clarity as to what is happening.
        if (state.status) {
          passkeyAuthButton.setAttribute(
            "aria-describedby",
            VERIFICATION_STATUS_MESSAGE_ID,
          );
          passkeyStatusText.classList.add(
            VERIFICATION_STATUS_MESSAGE_VISIBLE_CLASS,
          );
          passkeyStatusText.innerText = state.status;
          passkeyStatusText.setAttribute("aria-live", "assertive");

          if (state.requestFocus) {
            passkeyAuthButton.focus();
          }
        } else {
          passkeyAuthButton.removeAttribute("aria-describedby");
          passkeyStatusText.removeAttribute("aria-live");
          passkeyStatusText.classList.remove(
            VERIFICATION_STATUS_MESSAGE_VISIBLE_CLASS,
          );
        }
      }
    }

    async function setPasskeyVerificationVisible(
      visible: boolean,
    ): Promise<void> {
      const placeholderElement = document.getElementById(
        VERIFICATION_PLACEHOLDER_ID,
      );
      const availableTemplate = document.getElementById(
        VERIFICATION_AVAILABLE_TEMPLATE_ID,
      ) as HTMLTemplateElement;
      const fallbackTemplate = document.getElementById(
        VERIFICATION_FALLBACK_TEMPLATE_ID,
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
    if (
      config.autocompleteLoginFieldSelector &&
      (await browserSupportsWebAuthnAutofill())
    ) {
      setupPasskeyAutofill(config);
    }

    if (!browserSupportsWebAuthn()) {
      await setPasskeyVerificationVisible(false);
    } else {
      await setPasskeyVerificationVisible(true);
      setupPasskeyVerificationButton(config);
    }
  })())();
