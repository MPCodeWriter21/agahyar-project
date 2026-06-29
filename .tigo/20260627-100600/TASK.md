# Remove bare except:pass in scraper.py
- STATUS: CLOSED
- PRIORITY: 85
- TAGS: quality, bug

get_ai_suggestion() has a bare 'except: pass' on line 131 that silently swallows all errors. Add specific exception handling and logging.
