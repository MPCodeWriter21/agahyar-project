# Performance optimization

- STATUS: OPEN
- PRIORITY: 60
- TAGS: performance

Optimize database queries, caching, and page load times.

- Fix N+1 query issues (use select_related/prefetch_related)
- Add database indexing on frequently queried fields
- Enable Django caching framework (database or Redis backend)
- Cache template fragments for repeated content
- Minify CSS/JS assets
- Enable GZip compression
- Lazy-load images in templates
- Profile page load times and identify bottlenecks

Related: Task(20260629-111523)
