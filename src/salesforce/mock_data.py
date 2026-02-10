"""
Generates realistic mock Salesforce data for development and demonstration.
Produces Leads, Opportunities, Accounts, Cases, and Activities.
"""

import random
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path


class MockDataGenerator:
    """Generates realistic Salesforce object data for testing and demos."""

    INDUSTRIES = [
        "Technology", "Healthcare", "Finance", "Manufacturing", "Retail",
        "Education", "Energy", "Media", "Real Estate", "Consulting",
    ]

    LEAD_SOURCES = [
        "Web", "Phone Inquiry", "Partner Referral", "Purchased List",
        "Event", "LinkedIn", "Google Ads", "Content Download",
    ]

    LEAD_STATUSES = [
        "New", "Contacted", "Qualified", "Unqualified", "Nurturing",
    ]

    OPP_STAGES = [
        "Prospecting", "Qualification", "Needs Analysis",
        "Proposal", "Negotiation", "Closed Won", "Closed Lost",
    ]

    CASE_STATUSES = ["New", "Working", "Escalated", "Closed"]
    CASE_PRIORITIES = ["Low", "Medium", "High", "Critical"]
    CASE_TYPES = ["Problem", "Feature Request", "Question", "Billing"]

    COMPANY_NAMES = [
        "Acme Corp", "Globex Industries", "Initech Solutions", "Umbrella Ltd",
        "Wayne Enterprises", "Stark Industries", "Oscorp Technologies",
        "Cyberdyne Systems", "Soylent Corp", "Massive Dynamic",
        "Hooli", "Pied Piper", "Aviato", "Raviga Capital", "Endframe",
        "TechNova", "DataStream Inc", "CloudFirst Ltd", "NexGen Solutions",
        "Quantum Analytics", "ByteForge", "Synapse Digital", "Pinnacle Systems",
        "Horizon Tech", "BlueShift AI",
    ]

    FIRST_NAMES = [
        "James", "Sarah", "Michael", "Emma", "David", "Olivia", "Robert",
        "Sophia", "William", "Isabella", "John", "Mia", "Richard", "Charlotte",
        "Thomas", "Amelia", "Daniel", "Harper", "Matthew", "Evelyn",
    ]

    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
        "Davis", "Rodriguez", "Martinez", "Anderson", "Taylor", "Thomas",
        "Moore", "Jackson", "Martin", "Lee", "Thompson", "White", "Harris",
    ]

    def __init__(self, seed=42):
        random.seed(seed)
        self._accounts = []
        self._leads = []
        self._opportunities = []
        self._cases = []
        self._activities = []

    def generate_all(self, num_accounts=25, num_leads=100,
                     num_opportunities=60, num_cases=40):
        """Generate a full set of interrelated Salesforce data."""
        self._accounts = self._generate_accounts(num_accounts)
        self._leads = self._generate_leads(num_leads)
        self._opportunities = self._generate_opportunities(num_opportunities)
        self._cases = self._generate_cases(num_cases)
        self._activities = self._generate_activities()
        return self.get_all_data()

    def _generate_accounts(self, count):
        accounts = []
        for i in range(count):
            name = self.COMPANY_NAMES[i % len(self.COMPANY_NAMES)]
            if i >= len(self.COMPANY_NAMES):
                name = f"{name} {i // len(self.COMPANY_NAMES) + 1}"

            # Create account health profiles for churn variety
            if i < count * 0.25:
                # ~25% Disengaged accounts: old activity, will have many cases
                last_activity_days = random.randint(60, 120)
                rating = "Cold"
                acc_type = "Customer"
            elif i < count * 0.50:
                # ~25% At-risk accounts: somewhat stale
                last_activity_days = random.randint(30, 70)
                rating = random.choice(["Cold", "Warm"])
                acc_type = "Customer"
            else:
                # ~50% Healthy accounts: recent activity
                last_activity_days = random.randint(1, 20)
                rating = random.choice(["Hot", "Warm"])
                acc_type = random.choice(["Customer", "Prospect", "Partner"])

            last_activity = datetime.now() - timedelta(days=last_activity_days)

            accounts.append({
                "Id": f"001{uuid.uuid4().hex[:15].upper()}",
                "Name": name,
                "Industry": random.choice(self.INDUSTRIES),
                "AnnualRevenue": random.choice([
                    500000, 1000000, 5000000, 10000000, 50000000,
                    100000000, 500000000,
                ]),
                "NumberOfEmployees": random.choice([
                    10, 50, 100, 250, 500, 1000, 5000, 10000,
                ]),
                "Type": acc_type,
                "BillingCountry": random.choice([
                    "United Kingdom", "United States", "Germany",
                    "France", "Australia", "Canada",
                ]),
                "CreatedDate": self._random_date(365).isoformat(),
                "LastActivityDate": last_activity.isoformat(),
                "Rating": rating,
            })
        return accounts

    def _generate_leads(self, count):
        leads = []
        for i in range(count):
            first = random.choice(self.FIRST_NAMES)
            last = random.choice(self.LAST_NAMES)
            company = random.choice(self.COMPANY_NAMES)
            status = random.choice(self.LEAD_STATUSES)

            # Create distinct lead profiles for score variety
            if i < count * 0.15:
                # ~15% Hot leads: big company, target industry, high engagement
                profile = "hot"
            elif i < count * 0.40:
                # ~25% Warm leads: decent engagement
                profile = "warm"
            elif i < count * 0.70:
                # ~30% Cold leads: low engagement, non-target industry
                profile = "cold"
            else:
                # ~30% Dead leads: tiny company, no engagement, stale
                profile = "dead"

            if profile == "hot":
                employees = random.choice([1000, 5000, 10000])
                revenue = random.choice([5000000, 10000000, 50000000])
                industry = random.choice(["Technology", "Finance", "Healthcare", "Consulting"])
                visits = random.randint(25, 50)
                opens = random.randint(15, 30)
                downloads = random.randint(5, 10)
                days_inactive = random.randint(0, 5)
                rating = "Hot"
            elif profile == "warm":
                employees = random.choice([100, 250, 500, 1000])
                revenue = random.choice([1000000, 5000000])
                industry = random.choice(self.INDUSTRIES)
                visits = random.randint(10, 30)
                opens = random.randint(5, 15)
                downloads = random.randint(2, 6)
                days_inactive = random.randint(5, 25)
                rating = "Warm"
            elif profile == "cold":
                employees = random.choice([10, 50, 100])
                revenue = random.choice([100000, 500000])
                industry = random.choice(["Retail", "Energy", "Real Estate", "Manufacturing"])
                visits = random.randint(1, 8)
                opens = random.randint(0, 4)
                downloads = random.randint(0, 1)
                days_inactive = random.randint(20, 45)
                rating = "Cold"
            else:  # dead
                employees = random.choice([1, 5, 10])
                revenue = random.choice([10000, 50000, 100000])
                industry = random.choice(["Media", "Real Estate", "Energy"])
                visits = random.randint(0, 2)
                opens = 0
                downloads = 0
                days_inactive = random.randint(40, 60)
                rating = "Cold"

            leads.append({
                "Id": f"00Q{uuid.uuid4().hex[:15].upper()}",
                "FirstName": first,
                "LastName": last,
                "Company": company,
                "Title": random.choice([
                    "CEO", "CTO", "VP Sales", "Director of IT",
                    "Marketing Manager", "Operations Lead", "CFO",
                    "Head of Engineering", "Product Manager",
                ]),
                "Email": f"{first.lower()}.{last.lower()}@{company.lower().replace(' ', '')}.com",
                "Phone": f"+44 7{random.randint(100, 999)} {random.randint(100000, 999999)}",
                "Status": status,
                "LeadSource": random.choice(self.LEAD_SOURCES),
                "Industry": industry,
                "AnnualRevenue": revenue,
                "NumberOfEmployees": employees,
                "Rating": rating,
                "CreatedDate": self._random_date(180).isoformat(),
                "LastActivityDate": self._random_date(14).isoformat(),
                "IsConverted": status == "Qualified" and random.random() > 0.5,
                "ConvertedDate": self._random_date(30).isoformat()
                if status == "Qualified" else None,
                # Engagement metrics for lead scoring
                "Website_Visits__c": visits,
                "Email_Opens__c": opens,
                "Content_Downloads__c": downloads,
                "Days_Since_Last_Activity__c": days_inactive,
            })
        return leads

    def _generate_opportunities(self, count):
        opportunities = []
        for _ in range(count):
            stage = random.choice(self.OPP_STAGES)
            is_closed = stage.startswith("Closed")
            amount = random.choice([
                10000, 25000, 50000, 75000, 100000, 150000,
                250000, 500000, 750000, 1000000,
            ])
            account = random.choice(self._accounts) if self._accounts else None
            close_date = self._random_date(-90 if is_closed else 90)

            opportunities.append({
                "Id": f"006{uuid.uuid4().hex[:15].upper()}",
                "Name": f"{account['Name'] + ' - ' if account else ''}New Deal",
                "AccountId": account["Id"] if account else None,
                "AccountName": account["Name"] if account else "Unknown",
                "StageName": stage,
                "Amount": amount,
                "Probability": self._stage_probability(stage),
                "CloseDate": close_date.isoformat(),
                "CreatedDate": self._random_date(180).isoformat(),
                "Type": random.choice([
                    "New Business", "Existing Business", "Renewal",
                ]),
                "LeadSource": random.choice(self.LEAD_SOURCES),
                "IsClosed": is_closed,
                "IsWon": stage == "Closed Won",
                "ForecastCategory": self._forecast_category(stage),
                "NextStep": None if is_closed else random.choice([
                    "Schedule demo", "Send proposal", "Follow up call",
                    "Technical review", "Contract negotiation",
                ]),
                "Days_In_Stage__c": random.randint(1, 45),
            })
        return opportunities

    def _generate_cases(self, count):
        cases = []
        if not self._accounts:
            return cases

        # Split accounts into at-risk (first 25%) and healthy (rest)
        at_risk_cutoff = max(1, len(self._accounts) // 4)
        at_risk_accounts = self._accounts[:at_risk_cutoff]
        healthy_accounts = self._accounts[at_risk_cutoff:]

        for i in range(count):
            # 60% of cases go to at-risk accounts (concentrated problems)
            if i < count * 0.6:
                account = random.choice(at_risk_accounts)
                priority = random.choice(["High", "Critical", "High", "Medium"])
                status = random.choice(["New", "Working", "Escalated", "Closed"])
                csat = random.choice([1, 1, 2, 2, 3]) if status == "Closed" else None
            else:
                account = random.choice(healthy_accounts)
                priority = random.choice(["Low", "Medium", "Low"])
                status = random.choice(["Closed", "Closed", "Working", "New"])
                csat = random.choice([3, 4, 4, 5, 5]) if status == "Closed" else None

            cases.append({
                "Id": f"500{uuid.uuid4().hex[:15].upper()}",
                "CaseNumber": f"CS-{random.randint(10000, 99999)}",
                "AccountId": account["Id"],
                "AccountName": account["Name"],
                "Subject": random.choice([
                    "Login issue", "Data export failure", "API rate limit",
                    "Integration error", "Performance degradation",
                    "Feature request: bulk import", "Billing discrepancy",
                    "SSO configuration", "Report not loading",
                    "Mobile app crash",
                ]),
                "Status": status,
                "Priority": priority,
                "Type": random.choice(self.CASE_TYPES),
                "Origin": random.choice(["Web", "Phone", "Email", "Chat"]),
                "CreatedDate": self._random_date(90).isoformat(),
                "ClosedDate": self._random_date(7).isoformat()
                if status == "Closed" else None,
                "IsClosed": status == "Closed",
                "Resolution_Time_Hours__c": random.randint(1, 168)
                if status == "Closed" else None,
                "Customer_Satisfaction__c": csat,
            })
        return cases

    def _generate_activities(self):
        """Generate activity records linked to leads and opportunities."""
        activities = []
        # Activities on leads
        for lead in random.sample(self._leads, min(40, len(self._leads))):
            for _ in range(random.randint(1, 5)):
                activities.append({
                    "Id": f"00T{uuid.uuid4().hex[:15].upper()}",
                    "WhoId": lead["Id"],
                    "Subject": random.choice([
                        "Email: Introduction", "Call: Discovery",
                        "Meeting: Demo", "Email: Follow up",
                        "Call: Qualification", "Email: Proposal sent",
                    ]),
                    "ActivityDate": self._random_date(60).isoformat(),
                    "Status": random.choice(["Completed", "Not Started"]),
                    "Type": random.choice(["Email", "Call", "Meeting"]),
                })
        # Activities on opportunities
        for opp in random.sample(self._opportunities,
                                 min(30, len(self._opportunities))):
            for _ in range(random.randint(1, 3)):
                activities.append({
                    "Id": f"00T{uuid.uuid4().hex[:15].upper()}",
                    "WhatId": opp["Id"],
                    "Subject": random.choice([
                        "Call: Negotiation", "Meeting: Contract review",
                        "Email: Pricing discussion", "Meeting: Technical demo",
                    ]),
                    "ActivityDate": self._random_date(30).isoformat(),
                    "Status": random.choice(["Completed", "Not Started"]),
                    "Type": random.choice(["Email", "Call", "Meeting"]),
                })
        return activities

    def get_all_data(self):
        return {
            "accounts": self._accounts,
            "leads": self._leads,
            "opportunities": self._opportunities,
            "cases": self._cases,
            "activities": self._activities,
        }

    def get_leads(self):
        return self._leads

    def get_opportunities(self):
        return self._opportunities

    def get_accounts(self):
        return self._accounts

    def get_cases(self):
        return self._cases

    def get_activities(self):
        return self._activities

    def save_to_json(self, output_dir="data/sample"):
        """Save all generated data to JSON files."""
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        data = self.get_all_data()
        for obj_name, records in data.items():
            filepath = path / f"{obj_name}.json"
            with open(filepath, "w") as f:
                json.dump(records, f, indent=2, default=str)
        return {name: len(records) for name, records in data.items()}

    def _random_date(self, days_range):
        """Generate a random date within days_range of today.
        Positive = future, negative = past, or random within range."""
        if days_range > 0:
            delta = random.randint(-days_range, 0)
        else:
            delta = random.randint(days_range, 0)
        return datetime.now() + timedelta(days=delta)

    def _stage_probability(self, stage):
        mapping = {
            "Prospecting": 10, "Qualification": 25,
            "Needs Analysis": 50, "Proposal": 65,
            "Negotiation": 80, "Closed Won": 100, "Closed Lost": 0,
        }
        return mapping.get(stage, 0)

    def _forecast_category(self, stage):
        mapping = {
            "Prospecting": "Pipeline", "Qualification": "Pipeline",
            "Needs Analysis": "Best Case", "Proposal": "Commit",
            "Negotiation": "Commit", "Closed Won": "Closed",
            "Closed Lost": "Omitted",
        }
        return mapping.get(stage, "Pipeline")
