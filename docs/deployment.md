# Deployment Guide — Google Cloud Run

This guide covers deploying the Enterprise IT Support Assistant to Google Cloud Run.
For local development, see the README.md.

## Prerequisites

- Google Cloud project with billing enabled
- `gcloud` CLI authenticated: `gcloud auth login`
- APIs enabled: Cloud Run, Artifact Registry, Vertex AI, Secret Manager
- Service account with required roles (see below)

## Service Account Setup

Create a dedicated service account for the Cloud Run service:

```bash
gcloud iam service-accounts create it-assistant-sa \
  --display-name="IT Assistant Service Account" \
  --project=YOUR_PROJECT_ID

# Grant required roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:it-assistant-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"            # Vertex AI inference (PROD only)

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:it-assistant-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"  # Read secrets at runtime
```

Note: `roles/aiplatform.user` is only required in production when `LLM_BACKEND=vertex_ai`.
Dev deployments using `LLM_BACKEND=gemini_api` do not need this role.

## Secrets Setup

Store sensitive values in Secret Manager:

```bash
# JWT signing secret (min 32 chars)
echo -n "your-32-char-or-longer-jwt-secret" | \
  gcloud secrets create jwt-secret-key --data-file=- --project=YOUR_PROJECT_ID

# Webhook shared secret
echo -n "your-webhook-shared-secret" | \
  gcloud secrets create webhook-shared-secret --data-file=- --project=YOUR_PROJECT_ID

# Gemini API key (only needed if deploying with LLM_BACKEND=gemini_api)
echo -n "your-gemini-api-key" | \
  gcloud secrets create gemini-api-key --data-file=- --project=YOUR_PROJECT_ID
```

## Build and Push

```bash
# Set your project and region
export PROJECT_ID=your-project-id
export REGION=us-central1
export IMAGE=gcr.io/$PROJECT_ID/it-assistant

# Build the production image
docker build -t $IMAGE .

# Push to Google Container Registry (or Artifact Registry)
docker push $IMAGE
```

## Deploy to Cloud Run

```bash
gcloud run deploy it-assistant \
  --image=$IMAGE \
  --region=$REGION \
  --platform=managed \
  --service-account=it-assistant-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --min-instances=1 \
  --max-instances=10 \
  --memory=2Gi \
  --cpu=1 \
  --timeout=60 \
  --no-allow-unauthenticated \
  --set-env-vars="APP_ENV=production,LLM_BACKEND=vertex_ai,EMBEDDING_BACKEND=vertex_ai,\
GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_REGION=$REGION,\
USE_MOCK_INTEGRATIONS=false" \
  --set-secrets="JWT_SECRET_KEY=jwt-secret-key:latest,\
WEBHOOK_SHARED_SECRET=webhook-shared-secret:latest"
```

## Post-Deployment: Ingest Knowledge Base

After the first deployment, the ChromaDB collection is empty. You must ingest the knowledge base.
Since ChromaDB is embedded (not a separate service), ingestion runs locally and the resulting
`chroma_db/` directory is bundled into the container image or mounted via Cloud Storage.

Recommended approach for production:
1. Run ingestion locally: `python scripts/ingest_knowledge_base.py`
2. Upload the `knowledge_base/chroma_db/` directory to a Cloud Storage bucket
3. Mount it as a volume on the Cloud Run service, or
4. Bundle it into the Docker image (simpler for small knowledge bases, requires rebuild to update)

## Configure Dialogflow CX Webhook

1. In Dialogflow CX Console → Agent Settings → Webhooks
2. Set the URL to: `https://YOUR_CLOUD_RUN_URL/webhook`
3. Generate a JWT token: `python scripts/generate_jwt.py`
4. Paste the token into the Bearer Token field
5. Test with the Dialogflow CX test console

## Monitoring

Cloud Logging automatically ingests all structlog JSON output from Cloud Run stdout.

Recommended log-based alerts to create in Cloud Monitoring:

| Alert | Filter | Severity |
|---|---|---|
| Authentication failures | `jsonPayload.event="auth_error"` | WARNING |
| Password reset failures | `jsonPayload.event="password_reset_failed"` | ERROR |
| Integration errors | `jsonPayload.event="http_error"` | ERROR |
| Unhandled intents | `jsonPayload.event="intent_not_found"` | WARNING |

## Environment Variables for Production

```bash
APP_ENV=production
LLM_BACKEND=vertex_ai              # Use Vertex AI (paid, data residency)
EMBEDDING_BACKEND=vertex_ai        # Use Vertex AI embeddings (paid)
VERTEX_AI_MODEL=gemini-1.5-pro
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
GOOGLE_CLOUD_REGION=us-central1
USE_MOCK_INTEGRATIONS=false        # Use real integrations
# Secrets via Secret Manager (not env vars):
# JWT_SECRET_KEY, WEBHOOK_SHARED_SECRET, SERVICENOW_PASSWORD, etc.
```
