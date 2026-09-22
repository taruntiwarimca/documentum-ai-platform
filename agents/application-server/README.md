# APP-GROK

Owns Tomcat 10 + Java 21.

**Do not install Java 21 everywhere on the assumption Tomcat supports it.** Tomcat running on a modern JDK does not certify every Documentum WAR/component deployed to it for that JDK. Maintain and enforce a `JAVA-COMPATIBILITY-MATRIX`:

```yaml
java:
  21:
    content_server: UNKNOWN
    xplore: UNKNOWN
    da: VERIFY
    tomcat: SUPPORTED_BY_TOMCAT
```

APP-GROK must hard-stop when any component's supported JDK is unresolved (`UNKNOWN`/`VERIFY`).

Design source: target architecture §5, §6.5, ADR-014.
