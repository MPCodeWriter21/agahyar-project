# Add description field to services

- STATUS: CLOSED
- PRIORITY: 60
- TAGS: feature, UI, frontend

Some services might be described better with paragraphs of text instead of bullet points. Add a new optional text field to the Service model for a free-form description. This field may be empty; when empty, the corresponding element must not be rendered on the service detail page.

== Changes needed ==
1. Add a description TextField (blank=True) to the Service model in models.py
2. Create and run a migration
3. Add the field to the ServiceAdmin form so it can be edited in the admin
4. Display the description on service_detail.html, wrapped in an {% if %} guard
5. Add tests: service with description shows it; service without description does not render the section
6. Update admin bulk export/import if needed (model_to_dict already handles new fields)
7. Update the TagListWidget or admin fieldsets if the new field needs special handling
