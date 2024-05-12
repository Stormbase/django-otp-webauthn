export type State = {
  buttonDisabled: boolean;
  buttonLabel: string;
  status?: string;
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
