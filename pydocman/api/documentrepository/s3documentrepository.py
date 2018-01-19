import boto3

class S3DocumentRepository:
    def __init__(self, s3_bucket):
        self.s3_client = boto3.client('s3')
        self.s3_bucket = s3_bucket

    def get(self, s3_bucket_key):
        return self.s3_client.get_object(
            Bucket=self.s3_bucket,
            Key=s3_bucket_key
        )['Body'].read().decode()

    def put(self, s3_bucket_key, content):
        self.s3_client.put_object(
            Bucket=self.s3_bucket,
            Key=s3_bucket_key,
            Body=content.encode()
        )