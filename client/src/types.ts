export type PubKeyCredential = {
  type: string;
  alg: number;
};

export type BeginRegistrationPayload = {
  publicKey: {
    rp: {
      name: string;
      id: string;
    };
    user: {
      id: string;
      name: string;
      displayName: string;
    };
    challenge: string;
    pubKeyCredParams: PublicKeyCredentialParameters[];
    excludeCredentials: PubKeyDescriptor[];
  };
};

export type PubKeyDescriptor = {
  id: string;
  type: string;
  transports: string[];
};

export type AllowedCredential = {
  id: string;
  type: string;
  transports?: string[];
};

export type BeginAuthenticationPayload = {
  publicKey: {
    rpId: string;
    challenge: string;
    allowCredentials: AllowedCredential[];
  };
};

export type Support = {
  isSecureContext: boolean;
  isWebAuthnAvailable: boolean;
  isConditionalMediationAvailable: boolean;
  isUserVerifyingPlatformAuthenticatorAvailable: boolean;
};

export type Config = {
  autocompleteLoginFieldSelector: string | null;
  csrfCookieName: string;
  beginRegistrationUrl: string;
  beginAuthenticationUrl: string;
  completeRegistrationUrl: string;
  completeAuthenticationUrl: string;
  messages: MessageConfig;
};

export type MessageConfig = {
  registration: {
    error: {
      serverError: string;
      serverUnreachable: string;
      clientSideInvalidDomainError: string;
      clientSideCreationUnknownError: string;
      clientSideCreationNotAllowedError: string;
      clientSideInvalidStateError: string;
    };
  };
  authentication: {
    success: string;
    error: {
      serverError: string;
      serverUnreachable: string;
      clientSideInvalidDomainError: string;
      clientSideUnknownError: string;
      clientSideNotAllowedError: string;
      clientSideInvalidStateError: string;
    };
  };
};
