# Agahyar REST API Documentation

Base URL: `https://agahyar4iran.ir/api/v1/`

Interactive Swagger UI: `https://agahyar4iran.ir/api/v1/docs/`

OpenAPI 3.0 schema (YAML): `https://agahyar4iran.ir/api/v1/schema/`

---

## Authentication

Two methods are supported. Not all endpoints require authentication;
each endpoint documents its own requirement.

### Token authentication (recommended for mobile/API clients)

1. Register a new account (2-step with OTP):
   - Step 1: `POST /api/v1/auth/register/` (sends OTP, returns `pending_token`)
   - Step 2: `POST /api/v1/auth/verify-otp/` (verifies OTP, returns token)
2. Or log in with existing credentials: `POST /api/v1/auth/login/`
3. Send the token on every request:

```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

4. To log out (delete the token): `POST /api/v1/auth/logout/`

### Rate limiting

Registration and OTP verification endpoints are rate-limited:

- `POST /auth/register/`: 5 requests per minute per IP
- `POST /auth/verify-otp/`: 10 requests per minute per IP

### Session authentication (browser)

Log in through the Django admin or the application login page, then
make requests normally. CSRF protection applies.

---

## Pagination

All list endpoints are paginated at **20 items per page**. Use the
`?page=<n>` query parameter to navigate.

Response structure:

```json
{
  "count": 42,
  "next": "https://agahyar4iran.ir/api/v1/services/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

---

## Error format

Validation errors return `400 Bad Request` with a JSON body:

```json
{
  "field_name": ["Error message in Persian."]
}
```

Non-field errors use the `"detail"` key:

```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

## Endpoints

### Authentication

#### `POST /api/v1/auth/register/` (Step 1 -- Send OTP)

Validate registration fields and send an OTP to the provided phone
number. **No authentication required.** This step does NOT create
the account yet.

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | yes | Unique username (max 150 chars) |
| `password` | string | yes | Password (min 8 chars) |
| `first_name` | string | yes | First name |
| `last_name` | string | yes | Last name |
| `city` | string | yes | City of residence |
| `neighborhood` | string | yes | Neighborhood |
| `phone` | string | yes | Iranian phone number (11 digits, e.g. `09123456789`) |

**Example:**

```json
{
  "username": "ali_ahmadi",
  "password": "securepass123",
  "first_name": "علی",
  "last_name": "احمدی",
  "city": "تهران",
  "neighborhood": "ونک",
  "phone": "09123456789"
}
```

**Response** `200 OK`:

```json
{
  "pending_token": "eyJhbGciOi...",
  "phone": "0912***6789",
  "message": "کد تأیید به شماره موبایل شما ارسال شد."
}
```

The `pending_token` is a signed token (expires in 5 minutes) that
carries the registration data to step 2. The phone number is masked
in the response.

**Errors:**

| Status | Condition |
|--------|-----------|
| `400` | Duplicate username or phone, short password, missing required fields, invalid phone format |
| `429` | Too many requests (rate limit exceeded) |
| `502` | Failed to send SMS |

#### `POST /api/v1/auth/verify-otp/` (Step 2 -- Verify OTP + Create Account)

Verify the OTP code and create the user account. **No authentication
required.** Must be called within 5 minutes of step 1.

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pending_token` | string | yes | Token from step 1 |
| `otp_code` | string | yes | 6-digit OTP code |

**Example:**

```json
{
  "pending_token": "eyJhbGciOi...",
  "otp_code": "123456"
}
```

**Response** `201 Created`:

```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user_id": 42,
  "username": "ali_ahmadi"
}
```

**Errors:**

| Status | Condition |
|--------|-----------|
| `400` | Expired or invalid `pending_token`, wrong OTP code, OTP expired (5 min) |
| `429` | Too many requests (rate limit exceeded) |

#### `POST /api/v1/auth/login/`

Log in with username and password, receive an auth token. If the user
already has a token, the same token is returned (no duplicate tokens).

**No authentication required.**

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | yes | Username |
| `password` | string | yes | Password |

**Example:**

```json
{
  "username": "ali_ahmadi",
  "password": "securepass123"
}
```

**Response** `200 OK`:

```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user_id": 42,
  "username": "ali_ahmadi"
}
```

**Errors:**

| Status | Condition |
|--------|-----------|
| `400` | Missing username or password |
| `401` | Invalid credentials |

#### `POST /api/v1/auth/logout/`

Delete the caller's auth token. The token will no longer work.

**Requires authentication.**

**Response** `204 No Content`

**Errors:**

| Status | Condition |
|--------|-----------|
| `401` / `403` | Not authenticated |

#### `GET /api/v1/auth/profile/`

Get the authenticated user's profile information.

**Requires authentication.**

**Response** `200 OK`:

```json
{
  "username": "ali_ahmadi",
  "first_name": "علی",
  "last_name": "احمدی",
  "email": "ali@example.com",
  "phone": "09123456789",
  "city": "تهران",
  "neighborhood": "ونک"
}
```

**Errors:**

| Status | Condition |
|--------|-----------|
| `401` / `403` | Not authenticated |

#### `PATCH /api/v1/auth/profile/`

Update profile fields. All fields are optional; only send the fields
you want to change. Phone number is **read-only** in this endpoint;
use `/auth/profile/change-phone/` instead.

**Requires authentication.**

**Request body** (all fields optional):

| Field | Type | Description |
|-------|------|-------------|
| `first_name` | string | First name |
| `last_name` | string | Last name |
| `email` | string | Email address (empty string to clear) |
| `city` | string | City name |
| `neighborhood` | string | Neighborhood name |

**Example** (update city):

```json
{
  "city": "اصفهان",
  "neighborhood": "جلفا"
}
```

**Response** `200 OK`:

```json
{
  "username": "ali_ahmadi",
  "first_name": "علی",
  "last_name": "احمدی",
  "email": "ali@example.com",
  "phone": "09123456789",
  "city": "اصفهان",
  "neighborhood": "جلفا"
}
```

**Errors:**

| Status | Condition |
|--------|-----------|
| `400` | Duplicate email, invalid email format |
| `401` / `403` | Not authenticated |

#### `POST /api/v1/auth/profile/change-phone/` (Step 1 -- Request)

Initiate a phone number change. Sends an OTP to the **new** phone
number. The current phone is **not** changed until step 2.

**Requires authentication.**

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `new_phone` | string | yes | New Iranian phone number (11 digits) |

**Example:**

```json
{
  "new_phone": "09987654321"
}
```

**Response** `200 OK`:

```json
{
  "pending_token": "a8f5e2b1...",
  "new_phone": "0998***4321",
  "message": "کد تأیید به شماره جدید ارسال شد."
}
```

**Errors:**

| Status | Condition |
|--------|-----------|
| `400` | Same phone as current, phone already taken by another user, invalid format, missing field |
| `401` / `403` | Not authenticated |
| `502` | Failed to send SMS |

#### `POST /api/v1/auth/profile/verify-phone/` (Step 2 -- Verify + Update)

Verify the OTP code and update the phone number. Must be called within
5 minutes of step 1.

**Requires authentication.**

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pending_token` | string | yes | Token from step 1 |
| `otp_code` | string | yes | 6-digit OTP code |

**Example:**

```json
{
  "pending_token": "a8f5e2b1...",
  "otp_code": "654321"
}
```

**Response** `200 OK`:

```json
{
  "username": "ali_ahmadi",
  "first_name": "علی",
  "last_name": "احمدی",
  "email": "ali@example.com",
  "phone": "09987654321",
  "city": "تهران",
  "neighborhood": "ونک"
}
```

**Errors:**

| Status | Condition |
|--------|-----------|
| `400` | Expired or invalid `pending_token`, wrong OTP code, OTP expired (5 min) |
| `401` / `403` | Not authenticated or token belongs to different user |

#### Mobile app flow

```
1.  POST /api/v1/auth/register/
    -> { "pending_token": "...", "phone": "0912***6789" }

2.  User receives OTP via SMS, enters the code.

3.  POST /api/v1/auth/verify-otp/
    { "pending_token": "...", "otp_code": "123456" }
    -> { "token": "abc123", "user_id": 42, "username": "ali_ahmadi" }

4.  Every subsequent request:
    GET /api/v1/services/
    Header: Authorization: Token abc123

5.  POST /api/v1/auth/logout/
    Header: Authorization: Token abc123
    -> 204 (token deleted, further requests rejected)

6.  (Optional) Change phone number:
    POST /api/v1/auth/profile/change-phone/
    { "new_phone": "09987654321" }
    -> { "pending_token": "...", "new_phone": "0998***4321" }

    POST /api/v1/auth/profile/verify-phone/
    { "pending_token": "...", "otp_code": "654321" }
    -> { ... "phone": "09987654321" }
```

---

### Services

Read-only. No authentication required.

#### `GET /api/v1/services/`

List all government services.

**Query parameters:**

| Parameter | Description | Example |
|-----------|-------------|---------|
| `search` | Search by name, organization, or keywords | `?search=شناسنامه` |
| `organization` | Filter by organization name (case-insensitive) | `?organization=ثبت احوال` |
| `page` | Page number | `?page=2` |

**Response** `200 OK`:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "شناسنامه",
      "organization": "ثبت احوال",
      "organization_address": null,
      "documents": "کارت ملی|عکس",
      "documents_list": ["کارت ملی", "عکس"],
      "steps": "مراجعه به دفتر|تکمیل فرم",
      "steps_list": ["مراجعه به دفتر", "تکمیل فرم"],
      "cost": "رایگان",
      "duration": "۳ روز",
      "more_info_url": null,
      "keywords": "شناسنامه هویت",
      "centers_count": 2
    }
  ]
}
```

#### `GET /api/v1/services/<id>/`

Retrieve a single service.

**Response** `200 OK`:

```json
{
  "id": 1,
  "name": "شناسنامه",
  "organization": "ثبت احوال",
  "organization_address": null,
  "documents": "کارت ملی|عکس",
  "documents_list": ["کارت ملی", "عکس"],
  "steps": "مراجعه به دفتر|تکمیل فرم",
  "steps_list": ["مراجعه به دفتر", "تکمیل فرم"],
  "cost": "رایگان",
  "duration": "۳ روز",
  "more_info_url": null,
  "keywords": "شناسنامه هویت",
  "centers_count": 2
}
```

**Errors:**

| Status | Condition |
|--------|-----------|
| `404` | Service not found |

---

### Service Centers

Read-only. No authentication required.

#### `GET /api/v1/centers/`

List all service centers with their average rating.

**Query parameters:**

| Parameter | Description | Example |
|-----------|-------------|---------|
| `search` | Search by name, address, or city | `?search=ولیعصر` |
| `city` | Filter by city (case-insensitive) | `?city=تهران` |
| `service` | Filter by service ID | `?service=1` |
| `page` | Page number | `?page=2` |

**Response** `200 OK`:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "service": 1,
      "service_name": "شناسنامه",
      "name": "اداره ثبت احوال مرکزی",
      "address": "خیابان ولیعصر",
      "city": "تهران",
      "phone": "02112345678",
      "working_hours": "شنبه تا چهارشنبه ۸ تا ۱۴",
      "postal_code": "1234567890",
      "map_url": "https://maps.google.com/...",
      "avg_rating": 4.2
    }
  ]
}
```

`avg_rating` is `null` when no ratings exist for the center.

#### `GET /api/v1/centers/<id>/`

Retrieve a single center.

**Response** `200 OK`: Same object as above, without pagination wrapper.

**Errors:**

| Status | Condition |
|--------|-----------|
| `404` | Center not found |

---

### FAQs

Read-only. No authentication required.

#### `GET /api/v1/faqs/`

List all frequently asked questions, ordered by `order`.

**Query parameters:**

| Parameter | Description | Example |
|-----------|-------------|---------|
| `search` | Search by question, answer, or category | `?search=ثبت نام` |
| `page` | Page number | `?page=2` |

**Response** `200 OK`:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "question": "چگونه ثبت نام کنم؟",
      "answer": "از بخش ثبت نام اقدام کنید.",
      "category": "ثبت نام",
      "order": 1
    }
  ]
}
```

#### `GET /api/v1/faqs/<id>/`

Retrieve a single FAQ.

**Errors:**

| Status | Condition |
|--------|-----------|
| `404` | FAQ not found |

---

### Comments

Comments are public. Creating, editing, and deleting require
authentication. Editing is restricted to the comment author within
24 hours of posting. Deleting is restricted to the comment author
or staff members.

Deletion is soft-deleted: deleted comments show "نظر حذف شده است."
in place of the original text, but replies remain visible.

Top-level comments are returned in the list. Replies are nested inside
each top-level comment under the `replies` array. Only one level of
nesting is allowed (replies cannot have replies).

#### `GET /api/v1/comments/`

List top-level comments, newest first.

**Query parameters:**

| Parameter | Description | Example |
|-----------|-------------|---------|
| `service` | Filter by service ID | `?service=1` |
| `service_center` | Filter by center ID | `?service_center=3` |
| `page` | Page number | `?page=2` |

**Response** `200 OK`:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 10,
      "user": {
        "id": 5,
        "username": "ali",
        "first_name": "علی",
        "last_name": "احمدی"
      },
      "service": 1,
      "service_center": null,
      "parent": null,
      "text": "خدمت خیلی خوب بود.",
      "created_at": "2025-07-16T14:30:00+03:30",
      "updated_at": "2025-07-16T14:30:00+03:30",
      "edited_at": null,
      "is_deleted": false,
      "replies": [
        {
          "id": 11,
          "user": {
            "id": 8,
            "username": "sara",
            "first_name": "سارا",
            "last_name": "کریمی"
          },
          "service": 1,
          "service_center": null,
          "parent": 10,
          "text": "موافقم!",
          "created_at": "2025-07-16T15:00:00+03:30",
          "updated_at": "2025-07-16T15:00:00+03:30",
          "edited_at": null,
          "is_deleted": false,
          "replies": []
        }
      ]
    }
  ]
}
```

#### `GET /api/v1/comments/<id>/`

Retrieve a single top-level comment with its replies.

#### `POST /api/v1/comments/`

Create a new comment. **Requires authentication.**

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | yes | Comment text (1-2000 characters) |
| `service` | int | one of two | Service ID |
| `service_center` | int | one of two | Center ID |
| `parent` | int | no | Parent comment ID (must belong to the same target) |

Exactly one of `service` or `service_center` must be provided.

**Example** -- comment on a service:

```json
{
  "service": 1,
  "text": "خدمت خیلی خوب بود."
}
```

**Example** -- reply to an existing comment:

```json
{
  "service": 1,
  "parent": 10,
  "text": "موافقم!"
}
```

**Response** `201 Created`: The created comment object.

**Errors:**

| Status | Condition |
|--------|-----------|
| `400` | Missing text, both targets, no target, invalid IDs, reply to reply, parent from different target |
| `401` / `403` | Not authenticated |

#### `PATCH /api/v1/comments/<id>/`

Update a comment. **Requires authentication. Only the author can edit, and only within 24 hours of posting.**

Only the `text` field can be changed. Fields `service`,
`service_center`, and `parent` are immutable after creation.
Successful edits set `edited_at` to the current timestamp.

**Request body:**

```json
{
  "text": "متن ویرایش شده."
}
```

**Response** `200 OK`: The updated comment object.

**Errors:**

| Status | Condition |
|--------|-----------|
| `400` | Empty text, text too long, edit window expired, comment is deleted |
| `401` / `403` | Not authenticated or not the author |

#### `DELETE /api/v1/comments/<id>/`

Delete a comment. **Requires authentication. Only the author or staff can delete.**

Deletion is soft-deleted: the comment text is replaced with a generic
message, but the comment record and its replies remain in the database.

**Response** `204 No Content`

**Errors:**

| Status | Condition |
|--------|-----------|
| `401` / `403` | Not authenticated or not the author/staff |
| `404` | Comment not found |

---

### Ratings

Ratings are **private**. Users can only see and manage their own
ratings. There is no public list or detail endpoint. The average
rating for a center is available via the center detail endpoint
(`GET /api/v1/centers/<id>/`).

#### `POST /api/v1/ratings/`

Create or update your rating for a service center. If you have already
rated the center, your score is updated (upsert).

**Requires authentication.**

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `service_center` | int | yes | Center ID |
| `score` | int | yes | Rating from 1 to 5 |

**Example:**

```json
{
  "service_center": 3,
  "score": 4
}
```

**Response** `201 Created` (new rating):

```json
{
  "id": 7,
  "service_center": 3,
  "score": 4,
  "created_at": "2025-07-16T14:30:00+03:30",
  "updated_at": "2025-07-16T14:30:00+03:30"
}
```

**Response** `200 OK` (updated existing rating):

```json
{
  "id": 7,
  "service_center": 3,
  "score": 5,
  "created_at": "2025-07-16T14:30:00+03:30",
  "updated_at": "2025-07-16T16:00:00+03:30"
}
```

**Errors:**

| Status | Condition |
|--------|-----------|
| `400` | Missing `service_center`, invalid center ID, score out of range |
| `401` / `403` | Not authenticated |

#### `GET /api/v1/ratings/mine/?service_center=<id>`

Return your own rating for the given center.

**Requires authentication.**

**Query parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `service_center` | yes | Center ID |

**Response** `200 OK`:

```json
{
  "id": 7,
  "service_center": 3,
  "score": 4,
  "updated_at": "2025-07-16T16:00:00+03:30"
}
```

**Errors:**

| Status | Condition |
|--------|-----------|
| `400` | Missing `service_center` parameter |
| `401` / `403` | Not authenticated |
| `404` | You have not rated this center |

#### `DELETE /api/v1/ratings/<id>/`

Delete your own rating.

**Requires authentication.** You can only delete your own ratings.

**Response** `204 No Content`

**Errors:**

| Status | Condition |
|--------|-----------|
| `401` / `403` | Not authenticated |
| `404` | Rating not found or belongs to another user |

---

### Bookmarks

All bookmark operations require authentication. Users can only see and
manage their own bookmarks.

#### `GET /api/v1/bookmarks/`

List your bookmarks.

**Query parameters:**

| Parameter | Description | Example |
|-----------|-------------|---------|
| `page` | Page number | `?page=2` |

**Response** `200 OK`:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 5,
      "service": {
        "id": 1,
        "name": "شناسنامه",
        "organization": "ثبت احوال",
        "organization_address": null,
        "documents": "کارت ملی|عکس",
        "documents_list": ["کارت ملی", "عکس"],
        "steps": "مراجعه به دفتر|تکمیل فرم",
        "steps_list": ["مراجعه به دفتر", "تکمیل فرم"],
        "cost": "رایگان",
        "duration": "۳ روز",
        "more_info_url": null,
        "keywords": "شناسنامه هویت",
        "centers_count": 2
      },
      "service_id": 1,
      "created_at": "2025-07-16T14:30:00+03:30"
    }
  ]
}
```

#### `POST /api/v1/bookmarks/`

Bookmark a service.

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `service_id` | int | yes | Service ID |

**Example:**

```json
{
  "service_id": 1
}
```

**Response** `201 Created`: The created bookmark object.

**Errors:**

| Status | Condition |
|--------|-----------|
| `400` | Invalid service ID |
| `401` / `403` | Not authenticated |
| `409` | Service already bookmarked |

#### `DELETE /api/v1/bookmarks/<id>/`

Remove a bookmark. You can only delete your own bookmarks.

**Response** `204 No Content`

**Errors:**

| Status | Condition |
|--------|-----------|
| `401` / `403` | Not authenticated or not the owner |
| `404` | Bookmark not found |

---

## Security model

| Resource | List | Retrieve | Create | Update | Delete |
|----------|------|----------|--------|--------|--------|
| Auth register | -- | -- | Public (2-step OTP) | -- | -- |
| Auth login | -- | -- | Public | -- | -- |
| Auth profile | -- | Auth (GET) | -- | Auth (PATCH) | -- |
| Auth phone change | -- | -- | Auth (2-step OTP) | -- | -- |
| Auth logout | -- | -- | Auth | -- | -- |
| Services | Public | Public | -- | -- | -- |
| Centers | Public | Public | -- | -- | -- |
| FAQs | Public | Public | -- | -- | -- |
| Comments | Public | Public | Auth | Auth (owner) | Auth (owner) |
| Ratings | -- | -- | Auth | -- | Auth (owner) |
| Bookmarks | Auth | Auth | Auth | -- | Auth (owner) |

"--" means the endpoint does not exist.

## Interactive documentation

The Swagger UI is available at `/api/v1/docs/`. It provides an
interactive interface to try out all endpoints directly from the
browser. The schema is also available as raw OpenAPI 3.0 YAML at
`/api/v1/schema/`.
