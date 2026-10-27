---
name: dayz-skill-authoring
description: Create reusable DayZ development skills from recurring, repository-supported workflows while excluding confidential and personal information.
---

# Authoring privacy-safe DayZ skills

Use this guide when extracting a reusable skill from work performed in a DayZ
repository. Capture repeatable techniques, not a transcript or a copy of a
specific server's implementation.

## Find reusable knowledge

1. Establish the repository's scope and inspect only relevant, available
   project sources: code, documentation, tests, and user-approved work
   summaries.
2. Look for a workflow that recurs and is supported by evidence. Record its
   trigger, prerequisites, general steps, expected result, and how to validate
   the result.
3. Keep advice accurate to the evidence. Do not invent project conventions or
   claim that a one-off task is a common workflow. If there is not enough
   evidence, ask for a sanitized example or leave the skill for later.
4. Describe concepts and procedures in your own words. Include only the
   minimum generic examples needed to make the workflow actionable.

Do not access or reproduce private Claude conversations, account data, or
unprovided work histories. Repository artifacts and summaries explicitly
approved by the user are the source of truth.

## Exclude sensitive material

Do not put any of the following in a skill, its examples, or its metadata:

- Server or organization identifiers, including server names, IP addresses,
  domains, ports, internal URLs, private APIs, deployment paths, or
  server-specific configuration and tuning.
- Personal information, including real names, usernames, email addresses,
  contact details, locations, player identifiers, or information that could
  identify a person.
- Secrets or credentials, including passwords, access tokens, API keys, private
  keys, session cookies, connection strings, or secret values embedded in
  configuration.
- Proprietary source, internal procedures, or non-public data that is not
  necessary to explain a general technique.

If sensitive material is encountered, omit it; do not copy it into a draft,
example, placeholder, or report. Do not try to make it shareable by changing
only part of the value. Use neutral placeholders such as `<HOST>` or
`<CONFIG_VALUE>` only when a placeholder is necessary, and never fill one with
a realistic value from the repository. If a credential appears exposed, alert
the user without repeating it so they can handle remediation.

## Review before sharing

1. Read the entire proposed skill, including frontmatter and examples, as if it
   will be public.
2. Search for sensitive patterns such as credentials, email addresses, IP
   addresses, URLs, and organization or server names; also manually review for
   context that automated searches cannot recognize.
3. Confirm each procedural claim is supported by a safe, reusable source and
   remove identifying details, exact private configuration, and unnecessary
   copied code.
4. Ask the user to review uncertain material. Do not publish or commit the
   skill until the review is complete.
