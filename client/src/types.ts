export type State = {
  buttonDisabled: boolean;
  buttonLabel: string;
  /** Text to display in the status field. */
  status?: string;
  /** Request the focus be returned to the button. */
  requestFocus?: boolean;
};

export type Config = {
  beginRegistrationUrl: string;
  completeRegistrationUrl: string;
  beginAuthenticationUrl: string;
  completeAuthenticationUrl: string;

  // The selector for the field that will is supposed to trigger the autofill UI.
  autocompleteLoginFieldSelector?: string;

  // The name of the cookie that contains the CSRF token.
  // This is configurable because Django has a setting to change it.
  csrfCookieName: string;
};
