"""
Knowledge Base Stack - Amazon Bedrock Knowledge Base + S3 Data Source
Crea una Knowledge Base vectorial de Bedrock con un origen de datos S3
usando OpenSearch Serverless como vector store (gestionado por el construct).
"""

import aws_cdk as cdk
from aws_cdk import aws_s3 as s3
from constructs import Construct

from cdklabs.generative_ai_cdk_constructs import bedrock


class KnowledgeBaseStack(cdk.Stack):
    """Stack para Bedrock Knowledge Base"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        lab_name: str,
        documents_bucket: s3.Bucket,
        **kwargs
    ):
        super().__init__(scope, construct_id, **kwargs)

        self.lab_name = lab_name

        # ==================== BEDROCK KNOWLEDGE BASE ====================
        # El construct VectorKnowledgeBase crea automaticamente una coleccion
        # e indice de OpenSearch Serverless optimizados para el modelo de embeddings.
        self.knowledge_base = bedrock.VectorKnowledgeBase(
            self,
            "KnowledgeBase",
            embeddings_model=bedrock.BedrockFoundationModel.TITAN_EMBED_TEXT_V2_1024,
            instruction=(
                "Use this knowledge base to answer questions based on the uploaded documents. "
                "If the answer is not in the documents, say so clearly."
            ),
        )

        # ==================== DATA SOURCE (S3) ====================
        self.data_source = bedrock.S3DataSource(
            self,
            "S3DataSource",
            bucket=documents_bucket,
            knowledge_base=self.knowledge_base,
            data_source_name=f"{lab_name}-documents",
            chunking_strategy=bedrock.ChunkingStrategy.FIXED_SIZE,
            inclusion_prefixes=["documents/"],
        )

        # Exponer ARNs calculados para otros stacks (p. ej. IAM en LambdaStack)
        kb_id = self.knowledge_base.knowledge_base_id
        kb_arn = (
            f"arn:{cdk.Stack.of(self).partition}:bedrock:{cdk.Stack.of(self).region}:"
            f"{cdk.Stack.of(self).account}:knowledge-base/{kb_id}"
        )
        self.knowledge_base_arn = kb_arn
        self.data_source_arn = f"{kb_arn}/data-source/{self.data_source.data_source_id}"

        # ==================== OUTPUTS ====================
        cdk.CfnOutput(
            self,
            "KnowledgeBaseId",
            value=self.knowledge_base.knowledge_base_id,
            export_name=f"{lab_name}-knowledge-base-id",
        )

        cdk.CfnOutput(
            self,
            "KnowledgeBaseArn",
            value=self.knowledge_base_arn,
            export_name=f"{lab_name}-knowledge-base-arn",
        )

        cdk.CfnOutput(
            self,
            "DataSourceId",
            value=self.data_source.data_source_id,
            export_name=f"{lab_name}-data-source-id",
        )
