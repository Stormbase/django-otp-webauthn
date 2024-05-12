# Security

We take the security of the open source projects we maintain seriously. If you believe you have found a legit security vulnerability, please report it to us as described below.

DO NOT CREATE AN ISSUE TO REPORT A SECURITY PROBLEM.

ONLY REPORT SECURITY ISSUES TO THE EMAIL ADDRESS LISTED BELOW.

WE DO NOT OFFER PAYMENTS FOR SECURITY REPORTS (please don't ask for a [beg bounty](https://www.troyhunt.com/beg-bounties/)).

## Before reporting a security issue

Before reporting a security issue, please check the following:

- Do not break the law. Do not attempt to access data that is not yours or cause disruption to others in any way. Only interact with your own systems and data. Or that you have explicit permission to interact with.
- Ensure you are using the latest version of the project. Maybe the issue has already been fixed in a newer version.
- This project uses [duo-labs/py_webauthn](https://github.com/duo-labs/py_webauthn) as underlying library for WebAuthn. Please check if the issue is present in that library or in this project. If it is in py_webauthn, please report it to them instead.

## What counts as a security issue

An non-exhaustive list of things we consider to be security issues:

- Information disclosure to unauthorized parties. Usernames, other non-publicly available data, etc.
  - Special for this project: any action that could confirm/deny the existence of a specific user account. In it's default configuration, this project should not leak any information about the existence of a user account.
- Authentication bypasses.
- Replay attacks.
- Denial of service attacks. This includes things like consuming excessive resource usage, severe crashes, etc.

## What does NOT count as a security issue

Some things that we do NOT consider to be security issues but are sometimes reported as such:

- Bugs or issues that do not have a security impact - yes, we still want to hear about these but please do not report them as security issues.
- Dependencies with vulnerable versions. We try to do some minimal vetting of our direct dependencies and keep them up to date, but ultimately we have limited control over what is installed on your system. We believe it is your own responsibility to keep up-to-date and not install vulnerable software. If you believe a dependency we are using is inherently insecure, please report it to us and we will consider it.
  - As an example: if a security issue is discovered in a dependency of this project, we won't take action unless the patched version of that dependency is not compatible with this project. In that case, we will take action solve the issue so that you can keep using this project without having to install vulnerable software.
- Very specific configuration issues or misconfigurations. While we aim to provide Django system checks to alert to common misconfigurations, we cannot account for all possible configurations. If you have a specific common configuration that you believe to be insecure, contact us and we can discuss it. **When in doubt, report it.**
- Vague reports, or other reports (including automated ones) that do not inspire confidence that a real security issue is present. We are unlikely to spend much time investigating these reports.

You will get a response regardless of whether we consider the report to be a security issue or not.

## Contact us over email

Please send an email to [security@stormbase.digital](mailto:security@stormbase.digital) with a description of the security issue and any relevant information that could help us reproduce it.

If you can, please include the following information:

- The project name and version that you believe is affected.
- A description of the security issue. What is the impact? How could it be exploited?
- Steps to reproduce the issue - please provide a minimal reproduction example. The easier it is for us to reproduce it, the faster we can fix it.
- Possible solutions, if you have suggestions we would love to hear them. Git patches over email are welcome too.
- Your name/handle for recognition in an acknowledgment, if you want.
- If you feel confident doing so, an estimated severity rating for the issue.

## Response

We aim to respond with a confirmation that we have received your report and are investigating it within 72 hours. We may ask for more information or more time to investigate. If you have not received a response within 72 hours, please send a follow-up email to ensure we have received your report. You may also try to contact us over other channels after the 72 hours have passed but please do not disclose any information about the security issue in those channels.

If the report is confirmed, we will work on a fix and release it as soon as possible. We are happy to review patches to fix the issue, provided you submit them as a git patch. **DO NOT CREATE A PULL REQUEST**. We will keep you updated on the progress and expected timeline. We ask that you maintain confidentiality about the issue until a fix is released.

If the report is not confirmed, we will explain why we believe it is not a security issue. If you disagree, we can discuss it further. But do note that reports that appear to be low effort are unlikely to be reconsidered.

We acknowledge all _confirmed_ reports in the security advisory and release notes of the fixed version. If you would like to be acknowledged by name/handle, please let us know.

Once a fix is released, we will disclose the security issue in the release notes and publish a security advisory. At this point, you are free to disclose the issue to the public if you wish. Maybe you could write a cool blog post about it? We'd read it!

## Thank you

Thank you for disclosing security issues responsibly. You are awesome for helping keep open source software safe and secure for everyone. Your time and effort are appreciated around the world.

## No bounties

Because this project is unpaid open source maintained by volunteers, we cannot offer any monetary rewards for security reports. There is just no budget to pay out bounties.
