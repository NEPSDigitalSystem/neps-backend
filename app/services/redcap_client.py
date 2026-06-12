"""
NEPS Digital — REDCap Client
============================
Unified client that can use either:
1. Embedded mock REDCap (REDCAP_MOCK_ENABLED=True)
2. Deployed mock REDCap or real REDCap (REDCAP_MOCK_ENABLED=False)
"""

from typing import Optional, List, Dict, Any
import requests
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
            self.headers = {"Authorization": f"Bearer {self.api_token}"}

    def get_participants(self, country: Optional[str] = None,
                        site: Optional[str] = None,
                        status: Optional[str] = None) -> List[Dict]:
        if self.use_mock:
            return self.mock_client.get_participants(country=country, site=site, status=status)
        else:
            params = {}
            if country:
                params["country"] = country
            if site:
                params["site"] = site
            if status:
                params["status"] = status
            response = requests.get(f"{self.api_url}/participants", params=params)
            response.raise_for_status()
            return response.json()["data"]

    def get_participant(self, record_id: str) -> Optional[Dict]:
        if self.use_mock:
            return self.mock_client.get_participant(record_id)
        else:
            response = requests.get(f"{self.api_url}/participants/{record_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

    def get_survey_responses(self, record_id: Optional[str] = None,
                            instrument: Optional[str] = None,
                            event: Optional[str] = None) -> List[Dict]:
        if self.use_mock:
            return self.mock_client.get_survey_responses(record_id=record_id,
                                                        instrument=instrument,
                                                        event=event)
        else:
            params = {}
            if instrument:
                params["instrument"] = instrument
            if event:
                params["event"] = event
            if record_id:
                response = requests.get(f"{self.api_url}/participants/{record_id}/surveys", params=params)
                response.raise_for_status()
                return response.json()["responses"]
            else:
                # Get all monthly and comprehensive waves
                monthly = requests.get(f"{self.api_url}/monthly-reports", params=params).json()["data"]
                comprehensive = requests.get(f"{self.api_url}/comprehensive-waves", params=params).json()["data"]
                return monthly + comprehensive

    def get_consent_status(self, record_id: str) -> Optional[Dict]:
        if self.use_mock:
            return self.mock_client.get_consent_status(record_id)
        else:
            response = requests.get(f"{self.api_url}/participants/{record_id}/consent")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

    def get_distress_screenings(self, status: Optional[str] = None) -> List[Dict]:
        if self.use_mock:
            return self.mock_client.get_distress_screenings(status=status)
        else:
            params = {}
            if status:
                params["status"] = status
            response = requests.get(f"{self.api_url}/screenings/distress", params=params)
            response.raise_for_status()
            return response.json()["screenings"]

    def create_referral(self, record_id: str, destination: str, notes: str = "") -> Dict:
        if self.use_mock:
            return self.mock_client.create_referral(record_id, destination, notes)
        else:
            response = requests.post(
                f"{self.api_url}/referrals",
                json={"record_id": record_id, "destination": destination, "notes": notes},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    def get_wp6_sessions(self, record_id: str) -> List[Dict]:
        if self.use_mock:
            return self.mock_client.get_wp6_sessions(record_id)
        else:
            response = requests.get(f"{self.api_url}/wp6-sessions/{record_id}")
            response.raise_for_status()
            return response.json()["sessions"]

    def get_nlp_responses(self, record_id: Optional[str] = None,
                         response_type: Optional[str] = None,
                         sentiment: Optional[str] = None) -> List[Dict]:
        if self.use_mock:
            # Check if mock has NLP (in case it's outdated)
            if hasattr(self.mock_client, "nlp_responses"):
                results = self.mock_client.nlp_responses.copy()
                if record_id:
                    results = [r for r in results if r["participant_id"] == record_id]
                if response_type:
                    results = [r for r in results if r["response_type"] == response_type]
                if sentiment:
                    results = [r for r in results if r["sentiment_manual"] == sentiment]
                return results
            else:
                return []
        else:
            params = {}
            if response_type:
                params["response_type"] = response_type
            if sentiment:
                params["sentiment"] = sentiment
            if record_id:
                response = requests.get(f"{self.api_url}/participants/{record_id}/nlp-responses", params=params)
                response.raise_for_status()
                return response.json()["responses"]
            else:
                response = requests.get(f"{self.api_url}/nlp/responses", params=params)
                response.raise_for_status()
                return response.json()["data"]

    def export_records(self, format: str = "json",
                      fields: Optional[List[str]] = None,
                      events: Optional[List[str]] = None) -> Any:
        if self.use_mock:
            return self.mock_client.export_records(format=format, fields=fields, events=events)
        else:
            params = {"format": format}
            if fields:
                params["fields"] = ",".join(fields)
            if events:
                params["events"] = ",".join(events)
            response = requests.get(f"{self.api_url}/export/records", params=params)
            response.raise_for_status()
            return response.json()

    def export_metadata(self) -> Dict:
        if self.use_mock:
            return self.mock_client.export_metadata()
        else:
            response = requests.get(f"{self.api_url}/export/metadata")
            response.raise_for_status()
            return response.json()

    def get_stats(self) -> Dict:
        if self.use_mock:
            return self.mock_client.get_stats()
        else:
            response = requests.get(f"{self.api_url}/stats")
            response.raise_for_status()
            return response.json()


# Singleton client
_redcap_client = None


def get_redcap_client() -> RedCapClient:
    global _redcap_client
    if _redcap_client is None:
        _redcap_client = RedCapClient()
    return _redcap_client
