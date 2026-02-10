"""
AWS S3 utility functions for storing and retrieving analytics data.
"""

import json
import logging
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3DataStore:
    """Manages analytics data storage in AWS S3."""

    def __init__(self, bucket_name, region="eu-west-1"):
        self.bucket = bucket_name
        self.s3 = boto3.client("s3", region_name=region)

    def store_analytics(self, data, analysis_type, format="json"):
        """Store analytics results with timestamped partitioning."""
        now = datetime.utcnow()
        key = (
            f"analytics/{analysis_type}/"
            f"year={now.year}/month={now.month:02d}/day={now.day:02d}/"
            f"{now.strftime('%H%M%S')}_{analysis_type}.{format}"
        )

        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=json.dumps(data, indent=2, default=str),
            ContentType="application/json",
            ServerSideEncryption="AES256",
            Metadata={
                "analysis_type": analysis_type,
                "generated_at": now.isoformat(),
            },
        )
        logger.info(f"Stored {analysis_type} results at s3://{self.bucket}/{key}")
        return f"s3://{self.bucket}/{key}"

    def get_latest_results(self, analysis_type):
        """Retrieve the most recent analytics results for a given type."""
        prefix = f"analytics/{analysis_type}/"
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix,
                MaxKeys=100,
            )
            if "Contents" not in response:
                return None

            # Get the most recent file
            latest = sorted(
                response["Contents"],
                key=lambda x: x["LastModified"],
                reverse=True,
            )[0]

            obj = self.s3.get_object(Bucket=self.bucket, Key=latest["Key"])
            return json.loads(obj["Body"].read().decode("utf-8"))

        except ClientError as e:
            logger.error(f"Failed to retrieve from S3: {e}")
            return None

    def list_analysis_runs(self, analysis_type, max_results=20):
        """List recent analysis runs."""
        prefix = f"analytics/{analysis_type}/"
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix,
                MaxKeys=max_results,
            )
            if "Contents" not in response:
                return []

            return [
                {
                    "key": obj["Key"],
                    "last_modified": obj["LastModified"].isoformat(),
                    "size_bytes": obj["Size"],
                }
                for obj in sorted(
                    response["Contents"],
                    key=lambda x: x["LastModified"],
                    reverse=True,
                )
            ]
        except ClientError as e:
            logger.error(f"Failed to list S3 objects: {e}")
            return []

    def ensure_bucket_exists(self):
        """Create the S3 bucket if it doesn't exist."""
        try:
            self.s3.head_bucket(Bucket=self.bucket)
        except ClientError:
            logger.info(f"Creating bucket {self.bucket}")
            self.s3.create_bucket(
                Bucket=self.bucket,
                CreateBucketConfiguration={
                    "LocationConstraint": self.s3.meta.region_name,
                },
            )
            # Enable versioning
            self.s3.put_bucket_versioning(
                Bucket=self.bucket,
                VersioningConfiguration={"Status": "Enabled"},
            )
            logger.info(f"Bucket {self.bucket} created with versioning enabled")
