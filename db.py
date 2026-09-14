def upsert_buses(rows):
    if not rows:
        return 0

    conn = get_conn()
    now = datetime.utcnow().isoformat()

    try:
        for r in rows:
            conn.execute("""
                INSERT INTO buses (
                    state,
                    bus_name,
                    operator_type,
                    operator_name,
                    source_city,
                    destination_city,
                    departure_time,
                    arrival_time,
                    route,
                    stoppages,
                    bus_type,
                    frequency,
                    source,
                    last_updated
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r.get("state") or "",
                r.get("bus_name") or "",
                r.get("operator_type") or "Unknown",
                r.get("operator_name") or "",
                r.get("source_city") or "",
                r.get("destination_city") or "",
                r.get("departure_time") or "",
                r.get("arrival_time") or "",
                r.get("route") or "",
                json.dumps(
                    r.get("stoppages") or [],
                    ensure_ascii=False
                ),
                r.get("bus_type") or "",
                r.get("frequency") or "",
                r.get("source") or "unknown",
                now
            ))

        conn.commit()
        return len(rows)

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
        
