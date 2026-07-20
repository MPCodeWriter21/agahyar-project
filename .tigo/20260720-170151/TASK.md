# Fix admin export/import: full data transfer with related models

- STATUS: OPEN
- PRIORITY: 50
- TAGS: backend, admin, data
- DUE: 2026-07-25

## Description

The admin panel export/import currently only handles one table at a time and
does not properly transfer related data (ServiceCenterPhone and M2M services).
The management commands also miss ServiceCenterPhone and InfoReport, and the
import does not handle FK ordering or M2M resolution.

### Checkpoints

- [x] Add `services` M2M to `ServiceCenterResource` fields
- [x] Create `ServiceCenterPhoneResource` in resources.py
- [x] Register `ServiceCenterPhoneAdmin` in admin.py
- [x] Add `ServiceCenterPhone` and `InfoReport` to `export_data`
- [x] Fix `import_data` FK ordering and M2M resolution
- [x] Add tests for M2M export, ServiceCenterPhoneResource, import ordering
- [x] Run lint and test suite