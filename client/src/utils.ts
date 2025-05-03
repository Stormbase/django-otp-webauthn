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
 * Appends the 'next' query parameter to the base URL if present.
 * Prefers input[name="next"] if present, otherwise falls back to URL query.
 */
export function buildCompleteAuthenticationUrl(baseUrl: string): string {
  const nextInput =
    document.querySelector<HTMLInputElement>("input[name='next']");
  const nextValue =
    nextInput?.value || new URLSearchParams(window.location.search).get("next");

  if (nextValue) {
    const url = new URL(baseUrl, window.location.origin);
    url.searchParams.set("next", nextValue);
    return url.toString();
  }

  return baseUrl;
}
