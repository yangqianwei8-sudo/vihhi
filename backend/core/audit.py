from __future__ import annotations

from typing import Any, Dict, Optional

from backend.apps.system_management.models import AuditLog


class AuditMixin:
    """
    Reusable audit helper for DRF ViewSets.
    """

    def _audit_actor(self):
        user = getattr(self.request, "user", None)
        if user and getattr(user, "is_authenticated", False):
            return user
        return None

    def _audit_meta_base(self) -> Dict[str, Any]:
        req = self.request
        return {
            "ip": req.META.get("REMOTE_ADDR", ""),
            "ua": req.META.get("HTTP_USER_AGENT", ""),
        }

    def audit(
        self,
        *,
        action: str,
        obj: Any,
        event: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
        object_type: Optional[str] = None,
        object_id: Optional[str] = None,
    ) -> AuditLog:
        ot = object_type or f"{obj.__class__.__module__}.{obj.__class__.__name__}"
        oid = object_id or str(getattr(obj, "id", ""))

        final_meta = self._audit_meta_base()
        if event:
            final_meta["event"] = event
        if meta:
            final_meta.update(meta)

        return AuditLog.objects.create(
            actor=self._audit_actor(),
            action=action,
            object_type=ot,
            object_id=oid,
            changes=changes or {},
            meta=final_meta,
        )





