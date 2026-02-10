"""
Azure Blob Storage utility functions for storing and retrieving analytics data.
"""

import json
import logging
import os
from datetime import datetime

from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.identity import DefaultAzureCredential

from config.settings import AZURE_CONFIG

logger = logging.getLogger(__name__)


class AzureBlobStore:
    """Manages analytics data storage in Azure Blob Storage."""

    def __init__(self, connection_string=None, container_name=None):
        self.container = container_name or AZURE_CONFIG["storage_container"]
        conn_str = connection_string or AZURE_CONFIG["storage_connection_string"]

        if conn_str:
            self.blob_service = BlobServiceClient.from_connection_string(conn_str)
        else:
            # Use managed identity in Azure
            credential = DefaultAzureCredential()
            account_url = os.environ.get(
                "AZURE_STORAGE_ACCOUNT_URL",
                "https://sfanalyticsdata.blob.core.windows.net",
            )
            self.blob_service = BlobServiceClient(
                account_url=account_url, credential=credential
            )

    def store_analytics(self, data, analysis_type):
        """Store analytics results with timestamped path."""
        now = datetime.utcnow()
        blob_name = (
            f"analytics/{analysis_type}/"
            f"{now.strftime('%Y/%m/%d')}/"
            f"{now.strftime('%H%M%S')}_{analysis_type}.json"
        )

        container_client = self.blob_service.get_container_client(self.container)

        # Ensure container exists
        try:
            container_client.get_container_properties()
        except Exception:
            container_client.create_container()
            logger.info(f"Created container: {self.container}")

        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(
            json.dumps(data, indent=2, default=str),
            overwrite=True,
            content_settings=ContentSettings(content_type="application/json"),
            metadata={
                "analysis_type": analysis_type,
                "generated_at": now.isoformat(),
            },
        )

        logger.info(f"Stored {analysis_type} results at {blob_name}")
        return blob_client.url

    def get_latest_results(self, analysis_type):
        """Retrieve the most recent analytics results."""
        container_client = self.blob_service.get_container_client(self.container)
        prefix = f"analytics/{analysis_type}/"

        blobs = list(container_client.list_blobs(name_starts_with=prefix))
        if not blobs:
            return None

        latest = sorted(blobs, key=lambda b: b.last_modified, reverse=True)[0]
        blob_client = container_client.get_blob_client(latest.name)
        content = blob_client.download_blob().readall()
        return json.loads(content.decode("utf-8"))

    def list_analysis_runs(self, analysis_type, max_results=20):
        """List recent analysis runs."""
        container_client = self.blob_service.get_container_client(self.container)
        prefix = f"analytics/{analysis_type}/"

        blobs = list(container_client.list_blobs(name_starts_with=prefix))
        blobs = sorted(blobs, key=lambda b: b.last_modified, reverse=True)

        return [
            {
                "name": blob.name,
                "last_modified": blob.last_modified.isoformat(),
                "size_bytes": blob.size,
            }
            for blob in blobs[:max_results]
        ]
