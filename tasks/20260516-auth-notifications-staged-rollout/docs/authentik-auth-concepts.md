# Authentik Authentication Concepts

This document explains the authentication concepts behind Stage 3 of the staged rollout plan. It is meant to make the words in the plan understandable before implementation begins.

## What authentik is

authentik is a self-hosted identity provider.

That means it can:

- let users sign in
- issue tokens to apps and backends
- integrate social login sources like Google
- act as the system your apps trust for identity

In the plan, authentik is the identity provider for:

- the mobile app
- the terminal/server login flow
- the bridge
- the cloud orchestrator

## Identity provider, relying party, and social login

### Identity provider

The identity provider is the system that authenticates the user and issues tokens.

In this plan, that is authentik.

### Upstream social login provider

Google is not the system your product services should trust directly. Google is the upstream login source that authentik can use to authenticate the human.

### Relying party

A relying party is an app or service that trusts the identity provider’s tokens.

In this plan:

- the mobile app relies on authentik
- the terminal/server relies on authentik
- bridge and cloud rely on authentik when validating tokens

## OIDC and OAuth 2.0

### OAuth 2.0

OAuth 2.0 is the framework that lets apps obtain access tokens.

### OpenID Connect (OIDC)

OIDC is an identity layer built on OAuth 2.0. It adds user identity concepts like ID tokens and discovery metadata.

### Why OIDC matters here

Using OIDC gives the project:

- standard login flows
- standard access tokens
- discovery metadata
- JWKS-based verification

## PKCE

PKCE stands for Proof Key for Code Exchange.

It protects public clients such as mobile apps and local desktop-style flows that cannot safely hold a client secret.

In this plan:

- mobile app should use Authorization Code + PKCE
- terminal/server browser-based login should use Authorization Code + PKCE

## Public client versus confidential client

### Public client

A public client cannot securely keep a client secret.

Examples:

- mobile app
- local loopback login flow in a CLI or desktop helper

### Confidential client

A confidential client can securely hold a secret on a backend.

Examples:

- some server-side admin tools
- machine-to-machine API clients

The current plan expects the mobile app and terminal/server login flows to be public clients.

## Tokens involved

### Authorization code

A short-lived code returned after the user signs in. The client exchanges it for tokens.

### Access token

The bearer token used to call APIs such as bridge or cloud.

### ID token

The token that tells the client who the user is.

### Refresh token

A token used to obtain a new access token later without prompting for full login each time.

## JWT and JWKS

### JWT

A JWT is a signed token format. Access tokens and ID tokens are often JWTs.

### JWKS

JWKS means JSON Web Key Set. It is the public key list published by the identity provider so other services can verify signed JWTs.

### Stateless validation

Stateless validation means a service like bridge can verify a JWT locally using:

- the token signature
- the issuer claim
- the audience claim
- time-based claims such as expiration
- the public keys from JWKS

It does not need to call authentik for every request.

## What authentik stores versus what the product stores

### authentik stores

- users
- sessions
- provider configuration
- social-login connections
- signing keys
- auth policies

### product services store

- server ownership
- pairing state
- push tokens
- cloud-session ownership
- sharing or group access, if added

Authentication and authorization are related but not identical:

- authentication answers “who is this?”
- authorization answers “what may they access?”

## Google login in this plan

User-visible flow:

1. User chooses “Continue with Google”.
2. authentik sends the user to Google.
3. Google authenticates the user.
4. authentik receives the result and issues its own tokens.
5. Mobile app / terminal app use authentik-issued tokens afterward.

That means:

- Google secrets belong on authentik
- bridge and cloud do not need Google client secrets

## Secrets and keys

### On authentik

- authentik secret key
- database credentials
- Redis credentials
- signing keys
- Google OAuth client ID and secret

### On bridge and cloud

- authentik issuer/discovery URL
- JWKS validation configuration
- usually no authentik private keys
- preferably no Google secrets

## Why Stage 3 comes after notifications

This plan deliberately keeps notifications decoupled from login because:

- pairing already works as an authorization model
- direct-IP and local-polling users still matter
- push delivery should not need a redesign when identity is introduced later
- open source self-hosters may want no auth service at all in their minimal deployment

What changes in Stage 3 is mainly:

- stronger verification
- identity-aware server visibility
- future support for teams, sharing, and cloud access controls

This means authentik should be treated as an optional capability layer, not as a hard dependency of the base bridge deployment.
