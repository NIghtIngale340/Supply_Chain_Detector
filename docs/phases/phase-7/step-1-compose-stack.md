# Phase 7 — Step 1: Build Docker Compose Stack

## Why this step

This creates reproducible local infrastructure for full-system validation.

## Your coding target

Create/complete `docker-compose.yml` with services:

- api
- worker
- db (PostgreSQL)
- redis
- grafana

## Contract

Behavior:

- one command starts all core services
- env-driven config through `.env`
- health checks or startup order safeguards

## Checklist

- [ ] Define all service images/build contexts
- [ ] Add required environment variables
- [ ] Map ports and volumes
- [ ] Validate startup and inter-service connectivity

## Done criteria

- `docker compose up` brings stack up successfully
- API can reach Redis/DB from container network
