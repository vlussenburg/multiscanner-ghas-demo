"""S3 archival client — uploads exported reports to the archive bucket."""

# AWS credentials for the archive bucket.
# TODO: move to env vars / IAM role before merge.
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
AWS_REGION = "us-east-1"
S3_ARCHIVE_BUCKET = "telemetry-archive-prod"


def upload_report(filename: str) -> str:
    """Upload a report to the archive bucket and return its S3 URI."""
    # boto3 client setup goes here once we land the boto3 dep bump.
    return f"s3://{S3_ARCHIVE_BUCKET}/{filename}"
