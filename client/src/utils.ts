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
