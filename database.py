"""MySQL storage functions for DebugMate analysis history.

The diagnosis module stays independent: this module receives its result and
stores it. Database settings are read from the process environment.
"""

import os


class DatabaseError(Exception):
    """Raised when DebugMate cannot connect to or use its history database."""

    def __init__(self, message, *, safe_message=None):
        super().__init__(message)
        # Optional detail is deliberately separate from driver exception text.
        self.safe_message = safe_message


def get_connection():
    """Connect to MySQL using environment variables; never embed credentials."""
    required = ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise DatabaseError(
            "Missing required database environment settings.",
            safe_message="Missing settings: " + ", ".join(missing),
        )

    try:
        import mysql.connector

        return mysql.connector.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ.get("DB_PORT", "3306")),
            database=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            connection_timeout=5,
        )
    except Exception as exc:
        # Do not include connection arguments, which could expose credentials.
        raise DatabaseError("Could not connect to the DebugMate database.") from exc


def save_analysis(error_text, result):
    """Insert one diagnosis using SQL placeholders and commit it."""
    sql = """INSERT INTO debug_history
             (error_type, error_text, explanation, suggested_fix, status)
             VALUES (%s, %s, %s, %s, %s)"""
    values = (
        result.get("error_type"),
        error_text,
        result.get("explanation", ""),
        result.get("suggested_fix", ""),
        result.get("status", "unknown"),
    )
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(sql, values)
        connection.commit()
        return cursor.lastrowid
    except Exception as exc:
        raise DatabaseError("Could not save the analysis to history.") from exc
    finally:
        _close(cursor)
        _close(connection)


def get_recent_history(limit=50):
    """Return the newest analyses first, with a bounded page size."""
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        return _fetch_recent(cursor, limit)
    except Exception as exc:
        raise DatabaseError("Could not load analysis history.") from exc
    finally:
        _close(cursor)
        _close(connection)


def get_dashboard_stats():
    """Return real summary metrics, grouped counts, and recent rows."""
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """SELECT COUNT(*) AS total,
                      COUNT(DISTINCT error_type) AS distinct_error_types,
                      COALESCE(SUM(CASE WHEN status = 'supported' THEN 1 ELSE 0 END), 0) AS recognized,
                      COALESCE(SUM(CASE WHEN status IN ('unknown', 'malformed') THEN 1 ELSE 0 END), 0) AS uncertain
               FROM debug_history"""
        )
        summary = cursor.fetchone()
        cursor.execute(
            """SELECT COALESCE(error_type, 'Unidentified') AS error_type,
                      COUNT(*) AS count
               FROM debug_history
               GROUP BY error_type
               ORDER BY count DESC, error_type ASC"""
        )
        by_error_type = cursor.fetchall()
        recent_analyses = _fetch_recent(cursor, 6)
        return {
            "total": summary["total"],
            "distinct_error_types": summary["distinct_error_types"],
            "recognized": summary["recognized"],
            "uncertain": summary["uncertain"],
            "by_error_type": by_error_type,
            "recent_analyses": recent_analyses,
        }
    except Exception as exc:
        raise DatabaseError("Could not load dashboard statistics.") from exc
    finally:
        _close(cursor)
        _close(connection)


def _fetch_recent(cursor, limit):
    """Fetch a small, newest-first list using a parameterized row limit."""
    sql = """SELECT id, error_type, error_text, explanation, suggested_fix,
                    status, created_at
             FROM debug_history
             ORDER BY created_at DESC, id DESC
             LIMIT %s"""
    bounded_limit = max(1, min(int(limit), 200))
    cursor.execute(sql, (bounded_limit,))
    return cursor.fetchall()


def _close(resource):
    """Close a cursor or connection when it was successfully created."""
    if resource is not None:
        try:
            resource.close()
        except Exception:
            pass
