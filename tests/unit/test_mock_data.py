"""Tests for the mock data generator."""

import pytest
from src.salesforce.mock_data import MockDataGenerator


@pytest.fixture
def generator():
    gen = MockDataGenerator(seed=42)
    gen.generate_all()
    return gen


class TestMockDataGenerator:
    def test_generates_accounts(self, generator):
        accounts = generator.get_accounts()
        assert len(accounts) == 25
        assert all("Id" in a for a in accounts)
        assert all("Name" in a for a in accounts)
        assert all("Industry" in a for a in accounts)

    def test_generates_leads(self, generator):
        leads = generator.get_leads()
        assert len(leads) == 100
        assert all("Id" in l for l in leads)
        assert all("Email" in l for l in leads)
        assert all("Lead_Score__c" not in l for l in leads)  # Not scored yet

    def test_generates_opportunities(self, generator):
        opps = generator.get_opportunities()
        assert len(opps) == 60
        assert all("StageName" in o for o in opps)
        assert all("Amount" in o for o in opps)

    def test_generates_cases(self, generator):
        cases = generator.get_cases()
        assert len(cases) == 40
        assert all("Status" in c for c in cases)
        assert all("Priority" in c for c in cases)

    def test_generates_activities(self, generator):
        activities = generator.get_activities()
        assert len(activities) > 0
        assert all("Subject" in a for a in activities)

    def test_account_ids_are_unique(self, generator):
        accounts = generator.get_accounts()
        ids = [a["Id"] for a in accounts]
        assert len(ids) == len(set(ids))

    def test_opportunities_reference_valid_accounts(self, generator):
        accounts = generator.get_accounts()
        opps = generator.get_opportunities()
        account_ids = {a["Id"] for a in accounts}
        for opp in opps:
            if opp["AccountId"]:
                assert opp["AccountId"] in account_ids

    def test_get_all_data_returns_all_objects(self, generator):
        data = generator.get_all_data()
        assert "accounts" in data
        assert "leads" in data
        assert "opportunities" in data
        assert "cases" in data
        assert "activities" in data

    def test_deterministic_with_same_seed(self):
        gen1 = MockDataGenerator(seed=99)
        gen1.generate_all()
        gen2 = MockDataGenerator(seed=99)
        gen2.generate_all()
        assert gen1.get_accounts()[0]["Name"] == gen2.get_accounts()[0]["Name"]
        assert gen1.get_leads()[0]["LastName"] == gen2.get_leads()[0]["LastName"]
