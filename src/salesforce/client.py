"""
Salesforce REST API client.
Supports both live Salesforce connections (via simple-salesforce) and mock data mode.
"""

import json
import logging
from pathlib import Path

from config.settings import SALESFORCE_CONFIG, USE_MOCK_DATA
from src.salesforce.mock_data import MockDataGenerator

logger = logging.getLogger(__name__)


class SalesforceClient:
    """
    Unified client for Salesforce data access.
    Automatically uses mock data in development or connects to a real org.
    """

    def __init__(self, use_mock=None):
        self._use_mock = use_mock if use_mock is not None else USE_MOCK_DATA
        self._sf = None
        self._mock_data = None

        if self._use_mock:
            logger.info("Using mock Salesforce data")
            self._init_mock()
        else:
            logger.info("Connecting to Salesforce org")
            self._init_live()

    def _init_mock(self):
        """Initialize with generated mock data."""
        generator = MockDataGenerator()
        generator.generate_all()
        self._mock_data = generator.get_all_data()

    def _init_live(self):
        """Initialize a live Salesforce connection."""
        try:
            from simple_salesforce import Salesforce
            self._sf = Salesforce(
                username=SALESFORCE_CONFIG["username"],
                password=SALESFORCE_CONFIG["password"],
                security_token=SALESFORCE_CONFIG["security_token"],
                domain=SALESFORCE_CONFIG["domain"],
            )
            logger.info("Successfully connected to Salesforce")
        except Exception as e:
            logger.error(f"Failed to connect to Salesforce: {e}")
            logger.info("Falling back to mock data")
            self._use_mock = True
            self._init_mock()

    def query(self, soql):
        """Execute a SOQL query against Salesforce or mock data."""
        if self._use_mock:
            return self._mock_query(soql)
        result = self._sf.query_all(soql)
        return result.get("records", [])

    def get_leads(self, limit=None):
        """Retrieve Lead records."""
        if self._use_mock:
            data = self._mock_data["leads"]
            return data[:limit] if limit else data
        soql = "SELECT Id, FirstName, LastName, Company, Status, LeadSource, " \
               "Industry, Rating, Email, CreatedDate FROM Lead"
        if limit:
            soql += f" LIMIT {limit}"
        return self.query(soql)

    def get_opportunities(self, limit=None):
        """Retrieve Opportunity records."""
        if self._use_mock:
            data = self._mock_data["opportunities"]
            return data[:limit] if limit else data
        soql = "SELECT Id, Name, StageName, Amount, Probability, CloseDate, " \
               "AccountId, Type, IsClosed, IsWon, CreatedDate FROM Opportunity"
        if limit:
            soql += f" LIMIT {limit}"
        return self.query(soql)

    def get_accounts(self, limit=None):
        """Retrieve Account records."""
        if self._use_mock:
            data = self._mock_data["accounts"]
            return data[:limit] if limit else data
        soql = "SELECT Id, Name, Industry, AnnualRevenue, NumberOfEmployees, " \
               "Type, Rating, CreatedDate FROM Account"
        if limit:
            soql += f" LIMIT {limit}"
        return self.query(soql)

    def get_cases(self, limit=None):
        """Retrieve Case records."""
        if self._use_mock:
            data = self._mock_data["cases"]
            return data[:limit] if limit else data
        soql = "SELECT Id, CaseNumber, Subject, Status, Priority, Type, " \
               "Origin, CreatedDate, IsClosed FROM Case"
        if limit:
            soql += f" LIMIT {limit}"
        return self.query(soql)

    def get_activities(self, limit=None):
        """Retrieve Activity/Task records."""
        if self._use_mock:
            data = self._mock_data["activities"]
            return data[:limit] if limit else data
        soql = "SELECT Id, Subject, ActivityDate, Status, Type FROM Task"
        if limit:
            soql += f" LIMIT {limit}"
        return self.query(soql)

    def update_record(self, object_name, record_id, data):
        """Update a Salesforce record."""
        if self._use_mock:
            return self._mock_update(object_name, record_id, data)
        sf_object = getattr(self._sf, object_name)
        sf_object.update(record_id, data)
        logger.info(f"Updated {object_name} {record_id}")
        return True

    def create_record(self, object_name, data):
        """Create a new Salesforce record."""
        if self._use_mock:
            return self._mock_create(object_name, data)
        sf_object = getattr(self._sf, object_name)
        result = sf_object.create(data)
        logger.info(f"Created {object_name}: {result['id']}")
        return result

    def _mock_query(self, soql):
        """Simple mock SOQL parser — returns matching object data."""
        soql_lower = soql.lower()
        if "from lead" in soql_lower:
            return self._mock_data["leads"]
        elif "from opportunity" in soql_lower:
            return self._mock_data["opportunities"]
        elif "from account" in soql_lower:
            return self._mock_data["accounts"]
        elif "from case" in soql_lower:
            return self._mock_data["cases"]
        elif "from task" in soql_lower or "from activity" in soql_lower:
            return self._mock_data["activities"]
        return []

    def _mock_update(self, object_name, record_id, data):
        """Update a record in mock data."""
        obj_map = {
            "Lead": "leads", "Opportunity": "opportunities",
            "Account": "accounts", "Case": "cases",
        }
        collection = self._mock_data.get(obj_map.get(object_name, ""), [])
        for record in collection:
            if record["Id"] == record_id:
                record.update(data)
                logger.info(f"Mock updated {object_name} {record_id}")
                return True
        return False

    def _mock_create(self, object_name, data):
        """Create a record in mock data."""
        import uuid
        record_id = f"NEW{uuid.uuid4().hex[:15].upper()}"
        data["Id"] = record_id
        obj_map = {
            "Lead": "leads", "Opportunity": "opportunities",
            "Account": "accounts", "Case": "cases",
        }
        key = obj_map.get(object_name, "")
        if key in self._mock_data:
            self._mock_data[key].append(data)
        logger.info(f"Mock created {object_name}: {record_id}")
        return {"id": record_id, "success": True}

    def export_to_json(self, output_dir="data/sample"):
        """Export current data to JSON files."""
        if not self._use_mock:
            data = {
                "leads": self.get_leads(),
                "opportunities": self.get_opportunities(),
                "accounts": self.get_accounts(),
                "cases": self.get_cases(),
            }
        else:
            data = self._mock_data

        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        for name, records in data.items():
            with open(path / f"{name}.json", "w") as f:
                json.dump(records, f, indent=2, default=str)
        return {name: len(records) for name, records in data.items()}
