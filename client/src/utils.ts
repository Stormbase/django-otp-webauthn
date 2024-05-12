import { Config } from "./types";

/**
 * Finds the config object in the DOM and deserializes it.
 * @returns Config the config object
 */
export async function getConfig(): Promise<Config> {
  let config: Config | null = null;
  const configElement = document.getElementById(
    "otp_webauthn_config",
  ) as HTMLScriptElement;

  if (configElement) {
    config = JSON.parse(configElement.innerText) as Config;
    return Object.freeze(config);
  }
  throw new Error("otp_webauthn_config element not found");
}

/**
 * Retrieves the CSRF token from a the cookie.
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
