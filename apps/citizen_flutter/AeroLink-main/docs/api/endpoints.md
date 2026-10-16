# Initial API Plan

## Online backend
- GET /api/v1/health
- POST /api/v1/auth/login
- GET /api/v1/alerts
- GET /api/v1/nodes
- GET /api/v1/incidents
- POST /api/v1/incidents
- PATCH /api/v1/incidents/{id}/status

## ESP32 local API
- GET /health
- POST /sos
- GET /message/{id}
- GET /node-info
