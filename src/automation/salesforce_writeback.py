"""
Salesforce Writeback Service.
Automatically updates Salesforce records with analytics results:
- Lead scores and priority ratings
- Churn risk flags on accounts
- Task creation for follow-up actions
"""

import logging
from datetime import datetime, timezone

from src.salesforce.client import SalesforceClient

logger = logging.getLogger(__name__)


class SalesforceWriteback:
    """Writes analytics results back into Salesforce objects."""

    def __init__(self, sf_client=None):
        self.sf = sf_client or SalesforceClient()

    def update_lead_scores(self, scored_leads_df):
        """
        Write lead scores and priorities back to Salesforce Lead records.

        Args:
            scored_leads_df: DataFrame with Id, Lead_Score, and Priority columns.
        """
        updated = 0
        errors = 0

        for _, row in scored_leads_df.iterrows():
            try:
                self.sf.update_record("Lead", row["Id"], {
                    "Lead_Score__c": float(row["Lead_Score"]),
                    "Priority__c": str(row["Priority"]),
                    "Last_Scored_Date__c": datetime.now(timezone.utc).isoformat(),
                })
                updated += 1
            except Exception as e:
                logger.error(f"Failed to update lead {row['Id']}: {e}")
                errors += 1

        logger.info(f"Lead score writeback: {updated} updated, {errors} errors")
        return {"updated": updated, "errors": errors}

    def update_churn_risk(self, churn_df):
        """
        Write churn risk scores back to Salesforce Account records.

        Args:
            churn_df: DataFrame with Id, Churn_Risk_Score, and Churn_Risk_Level columns.
        """
        updated = 0
        errors = 0

        for _, row in churn_df.iterrows():
            try:
                self.sf.update_record("Account", row["Id"], {
                    "Churn_Risk_Score__c": float(row["Churn_Risk_Score"]),
                    "Churn_Risk_Level__c": str(row["Churn_Risk_Level"]),
                    "Last_Churn_Analysis__c": datetime.now(timezone.utc).isoformat(),
                })
                updated += 1
            except Exception as e:
                logger.error(f"Failed to update account {row['Id']}: {e}")
                errors += 1

        logger.info(f"Churn risk writeback: {updated} updated, {errors} errors")
        return {"updated": updated, "errors": errors}

    def create_follow_up_tasks(self, high_priority_leads):
        """
        Create Task records in Salesforce for high-priority leads.

        Args:
            high_priority_leads: DataFrame of leads with Priority = 'Critical' or 'High'.
        """
        created = 0
        errors = 0

        for _, lead in high_priority_leads.iterrows():
            priority = str(lead.get("Priority", "Medium"))
            score = lead.get("Lead_Score", 0)

            try:
                self.sf.create_record("Task", {
                    "WhoId": lead["Id"],
                    "Subject": f"Follow up: {priority}-priority lead "
                               f"(Score: {score})",
                    "Description": (
                        f"Automated task created by analytics engine.\n"
                        f"Lead: {lead.get('FirstName', '')} {lead.get('LastName', '')}\n"
                        f"Company: {lead.get('Company', 'N/A')}\n"
                        f"Score: {score}\n"
                        f"Priority: {priority}\n"
                        f"Source: {lead.get('LeadSource', 'N/A')}"
                    ),
                    "Priority": "High" if priority == "Critical" else "Normal",
                    "Status": "Not Started",
                    "ActivityDate": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "Type": "Call",
                })
                created += 1
            except Exception as e:
                logger.error(f"Failed to create task for lead {lead['Id']}: {e}")
                errors += 1

        logger.info(f"Follow-up tasks: {created} created, {errors} errors")
        return {"created": created, "errors": errors}

    def create_churn_intervention_tasks(self, high_risk_accounts):
        """Create intervention tasks for high churn-risk accounts."""
        created = 0
        errors = 0

        for _, account in high_risk_accounts.iterrows():
            try:
                risk_factors = account.get("Risk_Factors", [])
                if isinstance(risk_factors, list):
                    factors_text = "\n".join(f"- {f}" for f in risk_factors)
                else:
                    factors_text = str(risk_factors)

                self.sf.create_record("Task", {
                    "WhatId": account["Id"],
                    "Subject": f"Churn intervention: {account.get('Name', 'Unknown')}",
                    "Description": (
                        f"Account flagged as high churn risk.\n"
                        f"Risk Score: {account.get('Churn_Risk_Score', 'N/A')}\n"
                        f"Risk Factors:\n{factors_text}"
                    ),
                    "Priority": "High",
                    "Status": "Not Started",
                    "ActivityDate": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "Type": "Call",
                })
                created += 1
            except Exception as e:
                logger.error(f"Failed to create intervention task: {e}")
                errors += 1

        logger.info(f"Intervention tasks: {created} created, {errors} errors")
        return {"created": created, "errors": errors}

    def run_full_writeback(self, lead_scores_df, churn_df):
        """Execute a complete writeback cycle."""
        results = {}

        # Update lead scores
        results["lead_scores"] = self.update_lead_scores(lead_scores_df)

        # Update churn risk
        results["churn_risk"] = self.update_churn_risk(churn_df)

        # Create tasks for critical/high-priority leads
        high_leads = lead_scores_df[
            lead_scores_df["Priority"].isin(["Critical", "High"])
        ]
        results["follow_up_tasks"] = self.create_follow_up_tasks(high_leads)

        # Create intervention tasks for high churn-risk accounts
        high_churn = churn_df[churn_df["Churn_Risk_Level"] == "High"]
        results["intervention_tasks"] = self.create_churn_intervention_tasks(high_churn)

        logger.info(f"Full writeback complete: {results}")
        return results
