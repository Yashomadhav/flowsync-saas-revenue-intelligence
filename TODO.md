# TODO - Fix remaining thorough test failures

- [ ] Add `/api/v1/health` endpoint in `apps/api/main.py`
- [ ] Add `/api/v1/funnel/trial-usage` route in `apps/api/routers/funnel.py`
- [ ] Add trial usage metric method in `apps/api/services/metrics_funnel.py` and wire through `MetricsService` if required
- [ ] Fix Chargebee webhook 500 path in `apps/api/routers/webhook.py` for payment payload variants
- [ ] Update expectations in `scripts/thorough_test.py`:
  - [ ] invalid ingest key expected status 401
  - [ ] empty records batch expected status 422
  - [ ] missing required field expected status 422
- [ ] Re-run full thorough test suite and verify all pass
