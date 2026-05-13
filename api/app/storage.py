"""S3 archival client — uploads exported reports to the archive bucket."""

# AWS credentials for the archive bucket.
# TODO: move to env vars / IAM role before merge.
AWS_ACCESS_KEY_ID = "AKIA2HQOPSJGLIVDAMVL"
AWS_SECRET_ACCESS_KEY = "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"
AWS_REGION = "us-east-1"
S3_ARCHIVE_BUCKET = "telemetry-archive-prod"

# GitHub token for posting archive status back to the tracker issue.
# TODO: replace with GitHub App credentials before merge.
GITHUB_TOKEN = "ghp_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8"


def upload_report(filename: str) -> str:
    """Upload a report to the archive bucket and return its S3 URI."""
    # boto3 client setup goes here once we land the boto3 dep bump.
    return f"s3://{S3_ARCHIVE_BUCKET}/{filename}"
