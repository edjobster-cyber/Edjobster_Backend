from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from django.conf import settings
from django.urls import reverse


class CalendarService:
    """
    Provider-agnostic calendar facade.

    Phase 1: graceful no-op that standardizes data and persists a synthetic
    event id and join URL when a real provider is not connected. This lets the
    rest of the app rely on a single integration point and enables a seamless
    upgrade to Google/Microsoft/Zoom later.
    """

    @staticmethod
    def _infer_provider_from_payload(dynamic_info: Dict[str, Any]) -> str:
        basic = (dynamic_info or {}).get("basic_info", {})
        provider = (basic.get("calendar_provider") or basic.get("provider") or "none").lower()
        return provider

    @staticmethod
    def create_event_from_interview(request, interview) -> Dict[str, Optional[str]]:
        """
        Create a calendar event for the interview. Returns a dict with
        'eventId' and 'joinUrl'. For Phase 1, we generate synthetic values and
        ensure a meeting link exists, while exposing a stable interface.
        """
        provider = CalendarService._infer_provider_from_payload(interview.dynamic_interview_data or {})

        # Ensure a join link exists even without a provider
        # if not getattr(interview, "meeting_link", None):
        #     interview.generate_meeting_link()

        # Real providers can be plugged in here later.
        # For now, create a synthetic id to indicate an event was registered.
        synthetic_event_id = interview.calendar_event_id or f"local-{uuid.uuid4().hex}"

        interview.calendar_event_id = synthetic_event_id
        # if not interview.meeting_link:
        #     interview.meeting_link = f"https://meet.edjobster/{uuid.uuid4().hex[:10]}"
        # interview.save(update_fields=["calendar_event_id", "meeting_link"])

        ics_url = None
        try:
            ics_url = request.build_absolute_uri(reverse('interview-ics', args=[interview.id]))
        except Exception:
            pass

        # Audit trail
        interview.add_audit("calendar_event_created", by=getattr(request.user, 'id', None), meta={
            "provider": provider,
            "eventId": synthetic_event_id,
            "joinUrl": interview.meeting_link,
            "icsUrl": ics_url,
        })

        return {
            "eventId": synthetic_event_id,
            "joinUrl": interview.meeting_link,
            "icsUrl": ics_url,
            "provider": provider,
        }

    @staticmethod
    def update_event_on_reschedule(interview) -> None:
        """Update the provider event when interview is rescheduled.
        Phase 1: just audit; real providers would call their APIs here."""
        interview.add_audit("calendar_event_updated", meta={
            "eventId": interview.calendar_event_id,
            "start_at": getattr(interview, 'start_at', None) or str(getattr(interview, 'date', '')),
            "end_at": getattr(interview, 'end_at', None) or str(getattr(interview, 'time_end', '')),
        })

    @staticmethod
    def set_rsvp(interview, status: str, by: Optional[str] = None) -> None:
        """Push RSVP to provider (no-op Phase 1) and audit."""
        interview.add_audit("calendar_rsvp", by=by, meta={
            "eventId": interview.calendar_event_id,
            "status": status,
        })


