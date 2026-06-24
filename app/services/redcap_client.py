"""
NEPS Digital — REDCap Client
============================
Unified async client that can use either:
1. Embedded mock REDCap (REDCAP_MOCK_ENABLED=True)
2. Real REDCap API       (REDCAP_MOCK_ENABLED=False)

All public methods are async so FastAPI routes can await them
without blocking the server event loop.
"""

from typing import Optional, List, Dict, Any
import httpx
from app.core.config import get_settings
from app.services.redcap_mock import RedCapMockClient


class RedCapClient:
    def __init__(self):
        self.settings = get_settings()
        self.use_mock = self.settings.REDCAP_MOCK_ENABLED

        if self.use_mock:
            self.mock_client = RedCapMockClient()
        else:
            self.api_url = self.settings.REDCAP_API_URL.rstrip("/")
            self.api_token = self.settings.redcap_api_token or "mock_token_neps_2025"
            self.headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }

    # ------------------------------------------------------------------
    # Internal helper — one shared httpx client per call
    # ------------------------------------------------------------------
    def _client(self) -> httpx.AsyncClient:
        """Return a configured async HTTP client."""
        return httpx.AsyncClient(
            headers=self.headers,
            timeout=httpx.Timeout(30.0),   # 30s timeout on all REDCap calls
        )

    # ------------------------------------------------------------------
    # Participants
    # ------------------------------------------------------------------
    async def get_participants(
        self,
        country: Optional[str] = None,
        site: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict]:
        if self.use_mock:
            return self.mock_client.get_participants(
                country=country, site=site, status=status
            )

        params = {}
        if country:
            params["country"] = country
        if site:
            params["site"] = site
        if status:
            params["status"] = status

        async with self._client() as client:
            response = await client.get(f"{self.api_url}/participants", params=params)
            response.raise_for_status()
            return response.json()["data"]

    async def get_participant(self, record_id: str) -> Optional[Dict]:
        if self.use_mock:
            return self.mock_client.get_participant(record_id)

        async with self._client() as client:
            response = await client.get(f"{self.api_url}/participants/{record_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

    # ------------------------------------------------------------------
    # Surveys
    # ------------------------------------------------------------------
    async def get_survey_responses(
        self,
        record_id: Optional[str] = None,
        instrument: Optional[str] = None,
        event: Optional[str] = None,
    ) -> List[Dict]:
        if self.use_mock:
            return self.mock_client.get_survey_responses(
                record_id=record_id, instrument=instrument, event=event
            )

        params = {}
        if instrument:
            params["instrument"] = instrument
        if event:
            params["event"] = event

        async with self._client() as client:
            if record_id:
                response = await client.get(
                    f"{self.api_url}/participants/{record_id}/surveys", params=params
                )
                response.raise_for_status()
                return response.json()["responses"]
            else:
                monthly_r = await client.get(
                    f"{self.api_url}/monthly-reports", params=params
                )
                comprehensive_r = await client.get(
                    f"{self.api_url}/comprehensive-waves", params=params
                )
                monthly_r.raise_for_status()
                comprehensive_r.raise_for_status()
                return monthly_r.json()["data"] + comprehensive_r.json()["data"]

    # ------------------------------------------------------------------
    # Consent
    # ------------------------------------------------------------------
    async def get_consent_status(self, record_id: str) -> Optional[Dict]:
        if self.use_mock:
            return self.mock_client.get_consent_status(record_id)

        async with self._client() as client:
            response = await client.get(
                f"{self.api_url}/participants/{record_id}/consent"
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

    # ------------------------------------------------------------------
    # Distress screenings
    # ------------------------------------------------------------------
    async def get_distress_screenings(
        self, status: Optional[str] = None
    ) -> List[Dict]:
        if self.use_mock:
            return self.mock_client.get_distress_screenings(status=status)

        params = {}
        if status:
            params["status"] = status

        async with self._client() as client:
            response = await client.get(
                f"{self.api_url}/screenings/distress", params=params
            )
            response.raise_for_status()
            return response.json()["screenings"]

    # ------------------------------------------------------------------
    # Referrals
    # ------------------------------------------------------------------
    async def create_referral(
        self, record_id: str, destination: str, notes: str = ""
    ) -> Dict:
        if self.use_mock:
            return self.mock_client.create_referral(record_id, destination, notes)

        async with self._client() as client:
            response = await client.post(
                f"{self.api_url}/referrals",
                json={"record_id": record_id, "destination": destination, "notes": notes},
            )
            response.raise_for_status()
            return response.json()

    # ------------------------------------------------------------------
    # WP6 sessions
    # ------------------------------------------------------------------
    async def get_wp6_sessions(self, record_id: str) -> List[Dict]:
        if self.use_mock:
            return self.mock_client.get_wp6_sessions(record_id)

        async with self._client() as client:
            response = await client.get(f"{self.api_url}/wp6-sessions/{record_id}")
            response.raise_for_status()
            return response.json()["sessions"]

    # ------------------------------------------------------------------
    # NLP responses
    # ------------------------------------------------------------------
    async def get_nlp_responses(
        self,
        record_id: Optional[str] = None,
        response_type: Optional[str] = None,
        sentiment: Optional[str] = None,
    ) -> List[Dict]:
        if self.use_mock:
            if hasattr(self.mock_client, "nlp_responses"):
                results = self.mock_client.nlp_responses.copy()
                if record_id:
                    results = [r for r in results if r["participant_id"] == record_id]
                if response_type:
                    results = [r for r in results if r["response_type"] == response_type]
                if sentiment:
                    results = [r for r in results if r["sentiment_manual"] == sentiment]
                return results
            return []

        params = {}
        if response_type:
            params["response_type"] = response_type
        if sentiment:
            params["sentiment"] = sentiment

        async with self._client() as client:
            if record_id:
                response = await client.get(
                    f"{self.api_url}/participants/{record_id}/nlp-responses",
                    params=params,
                )
                response.raise_for_status()
                return response.json()["responses"]
            else:
                response = await client.get(
                    f"{self.api_url}/nlp/responses", params=params
                )
                response.raise_for_status()
                return response.json()["data"]

    # ------------------------------------------------------------------
    # Exports
    # ------------------------------------------------------------------
    async def export_records(
        self,
        format: str = "json",
        fields: Optional[List[str]] = None,
        events: Optional[List[str]] = None,
    ) -> Any:
        if self.use_mock:
            return self.mock_client.export_records(
                format=format, fields=fields, events=events
            )

        params: Dict[str, Any] = {"format": format}
        if fields:
            params["fields"] = ",".join(fields)
        if events:
            params["events"] = ",".join(events)

        async with self._client() as client:
            response = await client.get(f"{self.api_url}/export/records", params=params)
            response.raise_for_status()
            return response.json()

    async def export_metadata(self) -> Dict:
        if self.use_mock:
            return self.mock_client.export_metadata()

        async with self._client() as client:
            response = await client.get(f"{self.api_url}/export/metadata")
            response.raise_for_status()
            return response.json()

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------
    async def get_stats(self) -> Dict:
        if self.use_mock:
            return self.mock_client.get_stats()

        async with self._client() as client:
            response = await client.get(f"{self.api_url}/stats")
            response.raise_for_status()
            return response.json()


# Initialise lazily — avoids the threading race condition
# of lazy initialisation with a global variable, but prevents
# module-level side effects during testing.
_redcap_client = None


def get_redcap_client() -> RedCapClient:
    global _redcap_client
    if _redcap_client is None:
        _redcap_client = RedCapClient()
    return _redcap_client
