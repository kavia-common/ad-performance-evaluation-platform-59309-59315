# Creative Scoring Backend (Django)

This service exposes REST APIs for uploading creatives, managing metadata, generating synthetic audiences, scoring creatives, getting recommendations, running comparative tests, exporting scorecards (PDF/CSV), and managing admin score weightings.

Key endpoints (all under /api):
- GET /health/ — service health
- POST /upload/ — upload creative with metadata (auth required)
- GET /creatives/ — list user creatives (auth required)
- POST /audience/ — create/update synthetic audience (auth required)
- POST /score/ — compute and persist scorecard (auth required)
- GET /recommendations/ — get scorecard recommendations (auth required)
- POST /comparative_test/ — compare two creatives for an audience (auth required)
- GET /export/?format=pdf|csv — export scorecard
- GET/POST /admin/weightings — list/create score weightings (admin only)

Setup:
- pip install -r requirements.txt
- python manage.py migrate
- python manage.py createsuperuser
- python manage.py runserver

Docs:
- /docs for Swagger UI
- /redoc for ReDoc

Media/Static:
- MEDIA_ROOT: media/
- STATIC_ROOT: staticfiles/
