import logging

# Set up audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

def record_audit_event(actor_id: str, action: str, resource_id: str, details: dict):
    """
    Records an append-only audit event. 
    In production, this would write to an immutable audit ledger or database table.
    """
    event = {
        "actor_id": actor_id,
        "action": action,
        "resource_id": resource_id,
        "details": details
    }
    audit_logger.info(f"AUDIT EVENT: {event}")
    # TODO: Add SQLAlchemy insert to audit_events table
