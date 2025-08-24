export enum StatusEnum {
  UNKNOWN_ERROR = "unknown-error",
  STATE_ERROR = "state-error",
  SECURITY_ERROR = "security-error",
  GET_OPTIONS_FAILED = "get-options-failed",
  ABORTED = "aborted",
  NOT_ALLOWED_OR_ABORTED = "not-allowed-or-aborted",
  SERVER_ERROR = "server-error",
  SUCCESS = "success",
  BUSY = "busy",
}

export type State = {
  buttonDisabled: boolean;
  buttonLabel: string;
  /** Text to display in the status field. */
  status?: string;
  statusEnum?: StatusEnum;
  /** Request the focus be returned to the button. */
  requestFocus?: boolean;
};

export type Config = {
  beginRegistrationUrl: string;
  completeRegistrationUrl: string;
  beginAuthenticationUrl: string;
  completeAuthenticationUrl: string;

  // The selector for the field that is supposed to trigger the autofill UI.
  autocompleteLoginFieldSelector?: string;
  // The selector used to find the "next" field containing the URL to redirect to
  nextFieldSelector: string;

  csrfToken: string;
};
