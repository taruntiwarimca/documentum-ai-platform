# DB-GROK

Owns Oracle. Responsibilities:

- OS prerequisite validation
- Oracle installation
- Listener
- Database creation
- Tablespaces
- Users
- Password policy
- Character set validation
- Network configuration
- JDBC connectivity
- Backup configuration
- Health monitoring

Target tools (via `mcp/oracle-mcp/`):

```
oracle.precheck()          oracle.install()            oracle.create_listener()
oracle.create_database()   oracle.create_tablespace()  oracle.create_user()
oracle.test_connection()   oracle.execute_readonly_sql() oracle.health()
oracle.logs()              oracle.backup()
```

Design source: target architecture §6.2.
