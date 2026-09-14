"""
Query Handler Lambda
Realiza búsquedas en Bedrock Knowledge Base y genera respuestas con Bedrock
"""

import json
import boto3
import os
from datetime import datetime
import uuid
import re

bedrock_agent_runtime_client = boto3.client("bedrock-agent-runtime")
dynamodb = boto3.resource("dynamodb")

DOCUMENTS_TABLE = os.environ["DOCUMENTS_TABLE"]
QUERIES_TABLE = os.environ["QUERIES_TABLE"]
KNOWLEDGE_BASE_ID = os.environ["KNOWLEDGE_BASE_ID"]

# Modelo de generacion. Ajusta segun disponibilidad en tu region/cuenta de Bedrock.
# En eu-west-1, muchos modelos requieren el ID del inference profile (prefijo eu./global.).
# Ejemplos validos: eu.amazon.nova-2-lite-v1:0, eu.anthropic.claude-3-haiku-20240307-v1:0
GENERATION_MODEL_ID = "eu.amazon.nova-2-lite-v1:0"

documents_table = dynamodb.Table(DOCUMENTS_TABLE)
queries_table = dynamodb.Table(QUERIES_TABLE)


def lambda_handler(event, context):
    """
    Maneja búsquedas RAG

    Flujo:
    1. Recibe pregunta desde API
    2. Busca en Bedrock Knowledge Base (retrieve_and_generate)
    3. Guarda en DynamoDB
    4. Retorna respuesta con fuentes
    """

    print(f"Event: {json.dumps(event)}")
    print(f"Headers recibidos: {event.get('headers', {})}")

    try:
        # ==================== PARSE REQUEST ====================
        if event.get("httpMethod") == "OPTIONS":
            print("Manejando request OPTIONS")
            response = {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Amz-Security-Token",
                    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
                    "Content-Type": "application/json",
                },
                "body": json.dumps({}),
            }
            print(f"Response OPTIONS: {json.dumps(response)}")
            return response

        if event.get("httpMethod") != "POST":
            return error_response(400, "Método no permitido")

        body = json.loads(event.get("body", "{}"))
        question = body.get("question", "").strip()

        if not question:
            return error_response(400, "question es requerido")

        # ==================== BUSCAR + GENERAR CON BEDROCK KB ====================
        print(f"Consultando Bedrock Knowledge Base: {question}")

        region = boto3.session.Session().region_name or "eu-west-1"
        # Si el ID empieza con eu. o global. es un inference profile; se usa tal cual.
        # En caso contrario se asume un foundation model estandar.
        if GENERATION_MODEL_ID.startswith(("eu.", "global.", "us.", "apac.", "us-gov-")):
            model_arn = GENERATION_MODEL_ID
        else:
            model_arn = f"arn:aws:bedrock:{region}::foundation-model/{GENERATION_MODEL_ID}"

        sources = []
        answer = ""
        kb_results_count = 0

        try:
            kb_response = bedrock_agent_runtime_client.retrieve_and_generate(
                input={"text": question},
                retrieveAndGenerateConfiguration={
                    "type": "KNOWLEDGE_BASE",
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                        "modelArn": model_arn,
                    },
                },
            )

            answer = kb_response.get("output", {}).get("text", "")
            citations = kb_response.get("citations", [])
            kb_results_count = len(citations)
            print(f"Respuesta generada ({len(answer)} chars) | Citas: {kb_results_count}")

            for i, citation in enumerate(citations, 1):
                for ref in citation.get("retrievedReferences", []):
                    location = ref.get("location", {}).get("s3Location", {})
                    uri = location.get("uri", "unknown")
                    text = ref.get("content", {}).get("text", "")
                    sources.append({
                        "document_id": uri.split("/")[-1] if uri else "unknown",
                        "score": 1.0,
                        "excerpt": text[:200] if text else f"Fuente {i}",
                    })
        except Exception as e:
            print(f"Error al consultar Bedrock KB: {str(e)}")
            answer = f"Error al consultar la base de conocimiento: {str(e)}"

        # Fallback simple si Bedrock KB no retorna fuentes
        if not sources:
            print("Bedrock KB no retorno fuentes, intentando fallback directo en S3...")
            fallback_context = search_documents_in_s3(question)
            if fallback_context:
                answer = (
                    f"{answer}\n\n(Nota: la respuesta se basa en una búsqueda directa "
                    f"mientras finaliza la indexación de Bedrock KB)\n\n{fallback_context}"
                )
                sources.append({
                    "document_id": "direct-search",
                    "score": 1.0,
                    "excerpt": fallback_context[:200],
                })

        # ==================== GUARDAR EN DYNAMODB ====================
        query_id = f"query-{str(uuid.uuid4())[:8]}"
        timestamp = datetime.utcnow().isoformat()

        try:
            queries_table.put_item(
                Item={
                    "query_id": query_id,
                    "timestamp": timestamp,
                    "question": question,
                    "answer": answer,
                    "sources": sources,
                    "kb_results_count": kb_results_count,
                }
            )
            print(f"Query guardada en DynamoDB: {query_id}")
        except Exception as e:
            print(f"Error al guardar query: {str(e)}")

        # ==================== RESPUESTA ====================
        return success_response(
            200,
            {
                "query_id": query_id,
                "question": question,
                "answer": answer,
                "sources": sources,
                "timestamp": timestamp,
            },
        )

    except Exception as e:
        print(f"Error no controlado: {str(e)}")
        return error_response(500, f"Error interno: {str(e)}")


def success_response(status_code, body):
    """Retorna respuesta exitosa"""
    response = {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Amz-Security-Token",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        },
        "body": json.dumps(body),
    }
    print(f"Response success: {json.dumps(response)}")
    return response


def search_documents_in_s3(question):
    """Busca directamente en los documentos de S3 cuando Bedrock KB aun no tiene resultados"""
    try:
        s3_client = boto3.client("s3")

        # Obtener todos los documentos de DynamoDB
        response = documents_table.scan()
        documents = response.get("Items", [])

        if not documents:
            return ""

        # Extraer palabras clave de la pregunta
        keywords = re.findall(r'\b\w+\b', question.lower())
        keywords = [word for word in keywords if len(word) > 3]

        if not keywords:
            return ""

        relevant_content = ""

        for doc in documents:
            if doc.get("status") == "processing":
                try:
                    s3_path = doc.get("s3_path", "")
                    if "s3://" in s3_path:
                        bucket_key = s3_path.replace("s3://", "").split("/", 1)
                        if len(bucket_key) == 2:
                            bucket_name, object_key = bucket_key
                            obj = s3_client.get_object(Bucket=bucket_name, Key=object_key)
                            content = obj["Body"].read()

                            # Solo indexamos archivos de texto plano en el fallback
                            if doc.get("filename", "").lower().endswith(".txt"):
                                text = content.decode("utf-8", errors="ignore")
                                content_lower = text.lower()
                                keyword_matches = sum(1 for keyword in keywords if keyword in content_lower)
                                if keyword_matches > 0:
                                    relevance = keyword_matches / len(keywords)
                                    if relevance > 0.3:
                                        relevant_content += (
                                            f"\n[Documento: {doc.get('filename')}] "
                                            f"(Relevancia: {relevance:.0%})\n{text[:1000]}\n"
                                        )
                            else:
                                # Para PDFs mostramos solo que existen
                                relevant_content += (
                                    f"\n[Documento: {doc.get('filename')}] "
                                    "(PDF pendiente de indexar en Bedrock KB)\n"
                                )

                except Exception as e:
                    print(f"Error procesando documento {doc.get('document_id')}: {str(e)}")
                    continue

        return relevant_content[:2000] if relevant_content else ""

    except Exception as e:
        print(f"Error en búsqueda directa en S3: {str(e)}")
        return ""


def error_response(status_code, message):
    """Retorna respuesta de error"""
    response = {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Amz-Security-Token",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        },
        "body": json.dumps({"error": message}),
    }
    print(f"Response error: {json.dumps(response)}")
    return response
