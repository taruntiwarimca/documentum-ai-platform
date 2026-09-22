# End-to-end validation

The golden transaction: auth → repository connect → create/check-in → xPlore index/search → retrieve/checksum → cleanup (ADR-008). GREEN status requires this suite, not just per-component process/port checks. See target architecture §11, §13 for how results feed the installation state machine and audit record shape.
