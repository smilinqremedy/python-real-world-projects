"""
Sample offline AWS S3 cloud storage configuration datasets for security auditing.
"""

INSECURE_PUBLIC_BUCKET = {
    "BucketName": "corporate-financial-records-prod",
    "PublicAccessBlockConfiguration": {
        "BlockPublicAcls": False,
        "IgnorePublicAcls": False,
        "BlockPublicPolicy": False,
        "RestrictPublicBuckets": False
    },
    "BucketPolicy": {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": ["s3:GetObject"],
                "Resource": ["arn:aws:s3:::corporate-financial-records-prod/*"]
            }
        ]
    },
    "ServerSideEncryptionConfiguration": None,  # Missing encryption
    "LoggingConfiguration": None,  # Missing logging
    "VersioningConfiguration": {
        "Status": "Suspended"
    }
}

HARDENED_ENTERPRISE_BUCKET = {
    "BucketName": "secure-vault-enterprise-prod",
    "PublicAccessBlockConfiguration": {
        "BlockPublicAcls": True,
        "IgnorePublicAcls": True,
        "BlockPublicPolicy": True,
        "RestrictPublicBuckets": True
    },
    "BucketPolicy": {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "EnforceTLSRequestsOnly",
                "Effect": "Deny",
                "Principal": "*",
                "Action": "s3:*",
                "Resource": [
                    "arn:aws:s3:::secure-vault-enterprise-prod",
                    "arn:aws:s3:::secure-vault-enterprise-prod/*"
                ],
                "Condition": {
                    "Bool": {
                        "aws:SecureTransport": "false"
                    }
                }
            }
        ]
    },
    "ServerSideEncryptionConfiguration": {
        "Rules": [
            {
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "aws:kms",
                    "KMSMasterKeyId": "arn:aws:kms:us-east-1:123456789012:key/sample-key-uuid"
                },
                "BucketKeyEnabled": True
            }
        ]
    },
    "LoggingConfiguration": {
        "LoggingEnabled": {
            "TargetBucket": "centralized-s3-access-logs",
            "TargetPrefix": "vault-logs/"
        }
    },
    "VersioningConfiguration": {
        "Status": "Enabled",
        "MFADelete": "Disabled"
    }
}

PARTIAL_RISK_BUCKET = {
    "BucketName": "marketing-assets-cdn",
    "PublicAccessBlockConfiguration": {
        "BlockPublicAcls": True,
        "IgnorePublicAcls": True,
        "BlockPublicPolicy": False,  # Open to public policy
        "RestrictPublicBuckets": False
    },
    "BucketPolicy": None,
    "ServerSideEncryptionConfiguration": {
        "Rules": [
            {
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }
        ]
    },
    "LoggingConfiguration": None,
    "VersioningConfiguration": {
        "Status": "Enabled"
    }
}
