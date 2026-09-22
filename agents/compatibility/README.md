# COMPATIBILITY-GROK

Gates every install request against a support matrix for the full requested combination (CS, xPlore, DA, Java, Tomcat, Oracle) before any domain agent runs:

```
INSTALL REQUEST → COMPATIBILITY-GROK → {CS, xPlore, DA} → Java → Tomcat → Oracle → SUPPORT MATRIX → APPROVED | BLOCKED → INSTALL
```

Grounds its decisions in the version-scoped knowledge base (`../../compatibility/` and target architecture §15), not model inference — see ADR-007.

Design source: target architecture §5, ADR-014.
