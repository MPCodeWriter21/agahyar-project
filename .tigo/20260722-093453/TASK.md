# Security: Fix DoS and performance vulnerabilities

- STATUS: CLOSED
- PRIORITY: 75
- TAGS: security, performance, dos, medium

Security audit found medium-severity denial-of-service and performance vulnerabilities that could allow resource exhaustion or server degradation.

== VULN-13 (MEDIUM): Heavy N+1-like Query Pattern in service_detail ==
File: src/services/views.py, lines 996-1027
The service_detail view iterates over all comments and replies, calling c.reactions.all() multiple times per comment. For services with many comments, this creates significant CPU load.
Fix: Use annotated counts (Count with filter) instead of Python-level iteration. Cache the reaction data in a single pass.

== VULN-14 (MEDIUM): Sitemap Generation Loads All Objects Into Memory ==
File: src/services/views.py, lines 1936-1970
sitemap_xml loads ALL Service and ServiceCenter objects into memory at once without pagination. For large datasets, this could cause memory exhaustion.
Fix: Use iterator() on the querysets or generate the sitemap in chunks. Consider using Django built-in Sitemap framework.

== VULN-15 (LOW): Admin Stats View Loads All Data Without Caching ==
File: src/services/views.py, lines 1973-2075
The admin_stats view runs multiple aggregate queries without caching. Combined effect on every page load could be expensive.
Fix: Cache the admin stats with a TTL (e.g., 5 minutes).

== VULN-12 (MEDIUM): Admin Data Import Without File Size Limit ==
File: src/services/views.py, lines 2267-2364
The admin_data_transfer import reads uploaded JSON files with no size limit (upload_file.read() loads entire file into memory). A staff member can upload arbitrarily large files causing memory exhaustion.
Fix: Add maximum file size check and limit the number of records that can be imported.

== VULN-17 (LOW): Comment Template Missing Depth Limit ==
File: templates/services/partials/comment.html, lines 120-137
The comment template recursively includes itself for replies. If database contains deeper nesting, it could cause infinite recursion.
Fix: Add maximum depth check in the template (e.g., {% if depth < 5 %}).

== VULN-16 (LOW): Missing DATA_UPLOAD_MAX_MEMORY_SIZE ==
File: src/agahyar_project/settings.py
The admin data import view reads entire file content into memory, bypassing Django multipart upload limits.
Fix: Set DATA_UPLOAD_MAX_MEMORY_SIZE explicitly and add file size check in admin import view.
