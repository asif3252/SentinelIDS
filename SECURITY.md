# Security policy

SentinelIDS is an offline research and learning application. Only the current main branch is maintained, on a best-effort basis.

## Reporting a vulnerability

Use the repository's Security tab to report privately if private vulnerability reporting is enabled. Otherwise, contact the maintainer through a public professional contact listed on their GitHub profile. Do not put credentials, private network captures, personal identifiers or exploit details in public issues. For non-sensitive bugs, use the bug-report template.

## Deployment boundary

- Bind to `127.0.0.1` for local use. This project does not implement authentication, authorization or tenant isolation.
- Do not publish private captures, exported predictions or credentials in this repository.
- Upload CSV data only. The app does not load executable serialized models.
- Limits reduce accidental oversized inputs; the app is not hardened against hostile uploads or denial of service.
- An alert is a request for human review. This tool does not establish compromise or take containment actions.
- Review dependency updates and scan your deployment environment before broader use.
