# Testing & Verification Strategy

## 1. Multi-Tiered Testing Strategy

### A. Unit Tests (`backend/tests/`)
- Ingestion & Metadata: Validate GeoTIFF header parsing, CRS projection detection, and no-data masking.
- GIS Operations: Validate reprojection consistency, sub-pixel co-registration transforms, and geodesic area calculations.
- Machine Learning Models: Validate forward pass shapes for `SiameseUNet` and baseline difference modules on synthetic tensor inputs.
- AI Agent Tools: Validate that agent tool handlers properly serialize DB query outputs and reject malformed schemas.

### B. Integration Tests
- API Workflow: End-to-end simulation from `POST /images/upload` to `POST /analyses/{id}/run`, status polling, GeoJSON retrieval, and PDF generation.

### C. Frontend Verification
- Component rendering via Vitest & React Testing Library.
- Map and slider interaction testing.

## 2. Running Tests
```bash
# Backend tests
pytest backend/tests -v

# Frontend tests
cd frontend && npm run test
```
