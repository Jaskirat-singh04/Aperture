# Security Policy

Aperture is an early-stage, pre-release project. There is no stable release yet, and no
public deployment to protect, but the project is permission and access-control focused, so
reports are still welcome and taken seriously.

## Reporting A Vulnerability

Do not open a public GitHub issue for a security vulnerability. Instead, use GitHub's private
vulnerability reporting for this repository (Security tab, "Report a vulnerability"), or
contact the maintainer directly through their GitHub profile.

Please include:

- A description of the issue and its potential impact.
- Steps to reproduce, or a minimal example.
- The affected version or commit.

## Scope

Of particular interest, given the project's purpose:

- Any way for a user to retrieve or cite a document they are not permitted to read.
- Any way for a user in one tenant to retrieve another tenant's data.
- Any way to bypass or tamper with the audit log.
- Any way to bypass OIDC token validation.

## Response

As a solo-maintained project, there is no formal SLA. Reports are reviewed as soon as
practical, and a fix or mitigation plan is communicated back to the reporter.
