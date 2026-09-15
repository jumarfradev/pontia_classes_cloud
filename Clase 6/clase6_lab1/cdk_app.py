#!/usr/bin/env python3
"""
RAG Lab - AWS CDK Application
Despliegue completo de una aplicación RAG con Bedrock Knowledge Base, Lambda, API Gateway y Bedrock
"""

import aws_cdk as cdk
from aws_cdk import aws_s3 as s3
from stacks.storage_stack import StorageStack
from stacks.knowledge_base_stack import KnowledgeBaseStack
from stacks.lambda_stack import LambdaStack
from stacks.api_stack import ApiStack
from stacks.frontend_stack import FrontendStack


class RagLabApp(cdk.App):
    """Aplicación CDK para RAG Lab.

    Lee la configuración del contexto CDK (cdk.json o flags -c) con
    fallback a argumentos de línea de comandos para compatibilidad.

    Uso recomendado:
        cdk deploy --all
        cdk deploy --all -c lab_name=rag-lab-alumno
        cdk deploy --all -c lab_name=rag-lab-alumno -c stack=storage
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Leer configuracion del contexto CDK (cdk.json o -c flags)
        lab_name       = (self.node.try_get_context("lab_name") or "rag-lab").lower()
        region         = self.node.try_get_context("region")         or "eu-west-1"
        specific_stack = self.node.try_get_context("stack")          or None
        ctx_upload     = self.node.try_get_context("upload_frontend")
        # upload_frontend solo activo si se pasa explicitamente como true en contexto
        upload_frontend = (ctx_upload is True)

        self.lab_name = lab_name
        self.aws_region = region
        self.upload_frontend = upload_frontend
        self.specific_stack = specific_stack
        
        # Si se especifica un stack, solo desplegar ese
        if specific_stack:
            self._deploy_specific_stack(lab_name, region, upload_frontend)
        else:
            self._deploy_all_stacks(lab_name, region, upload_frontend)
    
    def _deploy_specific_stack(self, lab_name: str, region: str, upload_frontend: bool):
        """Desplegar solo un stack específico"""
        if self.specific_stack == "storage":
            StorageStack(
                self,
                f"{lab_name}-storage",
                lab_name=lab_name,
                env=cdk.Environment(region=region)
            )
        elif self.specific_stack == "knowledgebase":
            # Para Bedrock Knowledge Base necesitamos el storage primero
            storage_stack = StorageStack(
                self,
                f"{lab_name}-storage",
                lab_name=lab_name,
                env=cdk.Environment(region=region)
            )
            kb_stack = KnowledgeBaseStack(
                self,
                f"{lab_name}-kb",
                lab_name=lab_name,
                documents_bucket=storage_stack.documents_bucket,
                env=cdk.Environment(region=region)
            )
            kb_stack.add_dependency(storage_stack)
        elif self.specific_stack == "lambdas":
            # Para lambdas necesitamos storage y knowledge base
            storage_stack = StorageStack(
                self,
                f"{lab_name}-storage",
                lab_name=lab_name,
                env=cdk.Environment(region=region)
            )
            kb_stack = KnowledgeBaseStack(
                self,
                f"{lab_name}-kb",
                lab_name=lab_name,
                documents_bucket=storage_stack.documents_bucket,
                env=cdk.Environment(region=region)
            )
            kb_stack.add_dependency(storage_stack)
            lambda_stack = LambdaStack(
                self,
                f"{lab_name}-lambdas",
                lab_name=lab_name,
                documents_bucket=storage_stack.documents_bucket,
                documents_table=storage_stack.documents_table,
                queries_table=storage_stack.queries_table,
                knowledge_base_id=kb_stack.knowledge_base.knowledge_base_id,
                data_source_id=kb_stack.data_source.data_source_id,
                knowledge_base_arn=kb_stack.knowledge_base_arn,
                data_source_arn=kb_stack.data_source_arn,
                env=cdk.Environment(region=region)
            )
            lambda_stack.add_dependency(storage_stack)
            lambda_stack.add_dependency(kb_stack)
        elif self.specific_stack == "api":
            # Para API necesitamos todos los anteriores (sin frontend)
            self._deploy_all_stacks(lab_name, region, upload_frontend=False)
        elif self.specific_stack == "frontend":
            # Para frontend solo necesitamos recuperar el API endpoint
            self._deploy_frontend_only(lab_name, region)
    
    def _deploy_frontend_only(self, lab_name: str, region: str):
        """Desplegar solo el frontend sin recrear los stacks anteriores"""
        import boto3
        
        # Recuperar el API endpoint del stack existente
        cf_client = boto3.client('cloudformation', region_name=region)
        
        try:
            # Obtener el API stack para el endpoint
            api_stack_name = f"{lab_name}-api"
            api_response = cf_client.describe_stacks(StackName=api_stack_name)
            api_outputs = {o['OutputKey']: o['OutputValue'] for o in api_response['Stacks'][0].get('Outputs', [])}
            
            api_endpoint = api_outputs.get('ApiEndpoint')
            
            if not api_endpoint:
                raise Exception(f"No se encontró el API endpoint. API outputs: {api_outputs}")
            
            # Desplegar solo el frontend stack (crea su propio bucket)
            FrontendStack(
                self,
                f"{lab_name}-frontend",
                lab_name=lab_name,
                api_endpoint=api_endpoint,
                env=cdk.Environment(region=region)
            )
        except Exception as e:
            print(f"Error al recuperar el API endpoint: {e}")
            print("Asegúrate de que ya has desplegado el stack API")
            raise
    
    def _deploy_all_stacks(self, lab_name: str, region: str, upload_frontend: bool):
        """Desplegar todos los stacks"""
        # ==================== STORAGE STACK ====================
        storage_stack = StorageStack(
            self,
            f"{lab_name}-storage",
            lab_name=lab_name,
            env=cdk.Environment(region=region)
        )
        
        # ==================== KNOWLEDGE BASE STACK ====================
        kb_stack = KnowledgeBaseStack(
            self,
            f"{lab_name}-kb",
            lab_name=lab_name,
            documents_bucket=storage_stack.documents_bucket,
            env=cdk.Environment(region=region)
        )
        kb_stack.add_dependency(storage_stack)

        # ==================== LAMBDA STACK ====================
        lambda_stack = LambdaStack(
            self,
            f"{lab_name}-lambdas",
            lab_name=lab_name,
            documents_bucket=storage_stack.documents_bucket,
            documents_table=storage_stack.documents_table,
            queries_table=storage_stack.queries_table,
            knowledge_base_id=kb_stack.knowledge_base.knowledge_base_id,
            data_source_id=kb_stack.data_source.data_source_id,
            knowledge_base_arn=kb_stack.knowledge_base_arn,
            data_source_arn=kb_stack.data_source_arn,
            env=cdk.Environment(region=region)
        )
        lambda_stack.add_dependency(storage_stack)
        lambda_stack.add_dependency(kb_stack)
        
        # ==================== API STACK ====================
        api_stack = ApiStack(
            self,
            f"{lab_name}-api",
            lab_name=lab_name,
            upload_function=lambda_stack.upload_function,
            query_function=lambda_stack.query_function,
            env=cdk.Environment(region=region)
        )
        api_stack.add_dependency(lambda_stack)
        
        # ==================== FRONTEND STACK ====================
        if upload_frontend:
            api_endpoint_str = str(api_stack.api_endpoint)
            frontend_stack = FrontendStack(
                self,
                f"{lab_name}-frontend",
                lab_name=lab_name,
                api_endpoint=api_endpoint_str,
                env=cdk.Environment(region=region)
            )
            frontend_stack.add_dependency(api_stack)


if __name__ == "__main__":
    app = RagLabApp()
    app.synth()
