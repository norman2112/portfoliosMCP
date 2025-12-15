# Version Policy

The OpenAPI spec at (openapi/openapi.yml) and the okrs-api application at large,
may both have changes that either
(a) are completely independent of each other, or
(b) heavily impact each other.

In order to facilitate a sane way of indicating the relationship between the
OpenAPI spec file and the underlying okrs-api application, we have written the
policy here.

## Policy

- Releases for both the okrs-api application and the OpenAPI spec use semantic
  versioning.
- The **major** version of the OpenAPI spec and the okrs-api application will
  always be the same.
- **Minor** and **patch** version numbers **may** be set on the okrs-api
  application.
- **Minor** and **patch** version numbers **may not** be set on the OpenAPI
  spec.

### Examples

Given the following versions:

- OpenAPI spec: `3.0.0`
- okrs-api app: `3.1.2`

If the OpenAPI spec is moved to `4.0.0`, then the Rest API application will also
be set to `4.0.0`.

If the okrs-api app needs a minor version, but does not affect the OpenAPI spec,
then the OpenAPI spec would remain at `3.0.0` and the okrs-api application would
become `3.2.0`.
