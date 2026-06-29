# Replace unreliable javascript:history.go(-1) back navigation
- STATUS: CLOSED
- PRIORITY: 60
- TAGS: quality, ux

Several templates use javascript:history.go(-1) for back buttons. Replace with Django's {% url %} references or proper HTTP referrer handling.
