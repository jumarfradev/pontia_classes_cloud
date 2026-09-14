"""
Storage Stack - S3 + DynamoDB
Crea los buckets S3 y tablas DynamoDB necesarias
"""

import aws_cdk as cdk
from aws_cdk import (
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    RemovalPolicy,
)
from constructs import Construct


class StorageStack(cdk.Stack):
    """Stack para almacenamiento (S3 + DynamoDB)"""
    
    def __init__(self, scope: Construct, construct_id: str, lab_name: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        
        self.lab_name = lab_name
        
        # ==================== S3 BUCKET PARA DOCUMENTOS ====================
        self.documents_bucket = s3.Bucket(
            self,
            "DocumentsBucket",
            bucket_name=f"{lab_name}-documents-{self.account}",
            versioned=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=True,
                block_public_policy=True,
                ignore_public_acls=True,
                restrict_public_buckets=True,
            ),
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        
        # ==================== DYNAMODB - TABLA DOCUMENTOS ====================
        self.documents_table = dynamodb.Table(
            self,
            "DocumentsTable",
            table_name=f"{lab_name}-documents",
            partition_key=dynamodb.Attribute(
                name="document_id",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )
        
        # ==================== DYNAMODB - TABLA QUERIES ====================
        self.queries_table = dynamodb.Table(
            self,
            "QueriesTable",
            table_name=f"{lab_name}-queries",
            partition_key=dynamodb.Attribute(
                name="query_id",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )
        
        # ==================== OUTPUTS ====================
        cdk.CfnOutput(
            self,
            "DocumentsBucketName",
            value=self.documents_bucket.bucket_name,
            export_name=f"{lab_name}-documents-bucket",
        )
        
        cdk.CfnOutput(
            self,
            "DocumentsTableName",
            value=self.documents_table.table_name,
            export_name=f"{lab_name}-documents-table",
        )
        
        cdk.CfnOutput(
            self,
            "QueriesTableName",
            value=self.queries_table.table_name,
            export_name=f"{lab_name}-queries-table",
        )
