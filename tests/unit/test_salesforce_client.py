"""Tests for the Salesforce client (mock mode)."""

import pytest
from src.salesforce.client import SalesforceClient


@pytest.fixture
def client():
    return SalesforceClient(use_mock=True)


class TestSalesforceClient:
    def test_initialises_in_mock_mode(self, client):
        assert client._use_mock is True

    def test_get_leads(self, client):
        leads = client.get_leads()
        assert len(leads) > 0
        assert all("Id" in l for l in leads)

    def test_get_leads_with_limit(self, client):
        leads = client.get_leads(limit=5)
        assert len(leads) == 5

    def test_get_opportunities(self, client):
        opps = client.get_opportunities()
        assert len(opps) > 0

    def test_get_accounts(self, client):
        accounts = client.get_accounts()
        assert len(accounts) > 0

    def test_get_cases(self, client):
        cases = client.get_cases()
        assert len(cases) > 0

    def test_get_activities(self, client):
        activities = client.get_activities()
        assert len(activities) > 0

    def test_mock_query_leads(self, client):
        results = client.query("SELECT Id FROM Lead")
        assert len(results) > 0

    def test_mock_query_opportunities(self, client):
        results = client.query("SELECT Id FROM Opportunity")
        assert len(results) > 0

    def test_mock_update_record(self, client):
        leads = client.get_leads()
        lead_id = leads[0]["Id"]
        result = client.update_record("Lead", lead_id, {"Rating": "Hot"})
        assert result is True

    def test_mock_create_record(self, client):
        result = client.create_record("Lead", {
            "FirstName": "Test",
            "LastName": "Lead",
            "Company": "Test Co",
        })
        assert result["success"] is True
        assert "id" in result
