Mail Setup (Mailcow)
====================

This document explains how to set up [Mailcow](https://.mailcow.email/) as the
mail server for the Agahyar project.  Mailcow provides a complete, self-hosted
email solution with SMTP (Postfix), IMAP (Dovecot), anti-spam (Rspamd), and a
web-based administration UI.

Overview
--------

Agahyar sends email for:

- **Password reset links** -- Django's built-in ``PasswordResetView`` sends a
  reset link when a user requests password recovery via email.

In development, email is printed to the terminal (console backend).  In
production, you need a real SMTP server.  Mailcow fills this role.

Prerequisites
-------------

- A server with a **public static IP** and a domain pointed at it
- Docker and Docker Compose installed
- Ports **25**, **465**, **587**, and **993** open on the server firewall
- A ``docker network create traefik-network`` (already created for the
  main stack)

> **Important:** Many cloud providers (AWS, GCP, Azure, DigitalOcean) block
> port 25 by default.  You may need to request unblocking from your provider
> before Mailcow can receive inbound mail.

DNS Configuration
-----------------

Before starting Mailcow, create the following DNS records for your mail
domain (e.g. ``agahyar4iran.ir``):

### MX Record

```
Type:  MX
Name:  @
Value: mail.agahyar4iran.ir
TTL:   3600
```

### A Record (mail subdomain)

```
Type:  A
Name:  mail
Value: <your-server-public-ip>
TTL:   3600
```

### SPF Record (TXT)

```
Type:  TXT
Name:  @
Value: v=spf1 mx a -all
TTL:   3600
```

### DKIM Record (TXT)

After Mailcow is running, retrieve the DKIM key from the admin panel
(``https://mail.agahyar4iran.ir:8443``) under **ARC → DKIM keys**.  Add
a TXT record:

```
Type:  TXT
Name:  dkim._domainkey
Value: (paste the DKIM key from the Mailcow admin panel)
TTL:   3600
```

### DMARC Record (TXT)

```
Type:  TXT
Name:  _dmarc
Value: v=DMARC1; p=quarantine; rua=mailto:admin@agahyar4iran.ir
TTL:   3600
```

### Reverse DNS (rDNS / PTR)

Set the PTR record for your server's IP to ``mail.agahyar4iran.ir``.  This
is usually configured through your hosting provider's control panel, not
through DNS.

> **Tip:** Use [mail-tester.com](https://www.mail-tester.com/) to verify your
> DNS records and email configuration after setup.

Mailcow Installation
--------------------

### 1. Clone the Mailcow configuration

```bash
mkdir -p mailcow
cd mailcow
```

### 2. Create the Mailcow environment file

```bash
cat > mailcow/.env <<EOF
MAILCOW_HOSTNAME=mail.agahyar4iran.ir
MAILCOW_ADMINCGColor=41B3FF
TZ=Asia/Tehran
SKIP_CLAMD=y
SKIP_SOLR=y
EOF
```

### 3. Create required directories

```bash
mkdir -p mailcow/docker-data/dms/conf
mkdir -p mailcow/docker-data/dms/mailqueue
```

### 4. Create the Docker network

```bash
docker network create mail-network
```

### 5. Start Mailcow

```bash
docker compose -f docker-compose.mailcow.yml up -d
```

### 6. Create the first mailbox

Open the Mailcow admin panel at ``https://<server-ip>:8443``:

- Default login: ``admin`` / ``moohoo``
- **Change the admin password immediately**
- Go to **Mailboxes** and create your first mailbox:
  - ``noreply@agahyar4iran.ir`` (for outgoing system emails)
  - ``admin@agahyar4iran.ir`` (for administration)

### 7. Verify Mailcow is running

```bash
# Check all containers are up
docker compose -f docker-compose.mailcow.yml ps

# Test SMTP locally
docker compose -f docker-compose.mailcow.yml exec mail \
  postmap -q noreply@agahyar4iran.ir
```

Django Integration
------------------

### 1. Connect the web container to the mail network

Add ``mail-network`` to the web service in your main compose file
(``docker-compose.prod.yml`` or ``docker-compose.dev.yml``):

```yaml
services:
  web:
    # ... existing configuration ...
    networks:
      - traefik-network
      - mail-network

networks:
  traefik-network:
    external: true
  mail-network:
    external: true
```

### 2. Update your ``.env`` file

```ini
# Email via Mailcow
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mail
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@agahyar4iran.ir
EMAIL_HOST_PASSWORD=<password-for-the-mailbox>
DEFAULT_FROM_EMAIL=noreply@agahyar4iran.ir
SERVER_EMAIL=server@agahyar4iran.ir
```

> **Note:** ``EMAIL_HOST=mail`` works because the web container is on the
> same Docker network as the Mailcow ``mail`` service.  Docker DNS resolves
> ``mail`` to the container's IP.

### 3. Restart the web container

```bash
docker compose -f docker-compose.prod.yml up -d web
```

Verification
------------

### Send a test email from Django's shell

```bash
docker compose -f docker-compose.prod.yml exec web uv run --no-sync python -c "
from django.core.mail import send_mail
result = send_mail(
    subject='Test email from Agahyar',
    message='This is a test message from the Agahyar project.',
    from_email='noreply@agahyar4iran.ir',
    recipient_list=['admin@agahyar4iran.ir'],
    fail_silently=False,
)
print('Email sent successfully' if result else 'Failed to send email')
"
```

### Test password reset flow

1. Go to the login page and click "Forgot password"
2. Enter an email address of a registered user
3. Check the Mailcow admin panel or the user's mailbox for the reset email

### Check Mailcow logs

```bash
# Postfix logs
docker compose -f docker-compose.mailcow.yml logs mail

# Dovecot logs
docker compose -f docker-compose.mailcow.yml logs imap

# Rspamd logs
docker compose -f docker-compose.mailcow.yml logs rspamd-filter
```

Troubleshooting
---------------

### Emails are not being sent

1. **Check the Django logs** for SMTP errors:
   ```bash
   docker compose -f docker-compose.prod.yml logs web | grep -i smtp
   ```

2. **Verify the web container can reach the mail service:**
   ```bash
   docker compose -f docker-compose.prod.yml exec web uv run --no-sync python -c "
   import socket
   print(socket.getaddrinfo('mail', 587))
   "
   ```

3. **Check Mailcow is running:**
   ```bash
   docker compose -f docker-compose.mailcow.yml ps
   ```

### Emails land in spam

1. **Verify DNS records** -- use [mail-tester.com](https://www.mail-tester.com/)
2. **Check SPF** -- ``dig TXT agahyar4iran.ir``
3. **Check DKIM** -- ``dig TXT dkim._domainkey.agahyar4iran.ir``
4. **Check DMARC** -- ``dig TXT _dmarc.agahyar4iran.ir``
5. **Check rDNS/PTR** -- ``dig -x <your-server-ip>``
6. **Warm up the IP** -- start with low volumes and gradually increase

### Port 25 is blocked

Most cloud providers block port 25 by default.  Contact your provider to
request unblocking.  Alternatively, use an external SMTP relay (e.g. Amazon
SES, Mailgun, SendGrid) by changing ``EMAIL_HOST``, ``EMAIL_PORT``, and
credentials in your ``.env``.

### Connection refused errors

Ensure the ``mail-network`` Docker network exists and both stacks are
connected to it:

```bash
docker network ls | grep mail-network
docker network inspect mail-network
```

Development (Console Backend)
-----------------------------

In development, no Mailcow setup is needed.  The default console backend
prints all emails to the terminal:

```bash
# The default .env.example has no EMAIL_BACKEND set, so the console
# backend is used automatically.
docker compose -f docker-compose.dev.yml up --build
```

When a password reset email is triggered, the full email content (including
the reset link) will appear in the web container's console output.

References
----------

- [Mailcow Documentation](https://docs.mailcow.email/)
- [Mailcow Docker Compose](https://github.com/mailcow/mailcow-dockerized)
- [Django Email Configuration](https://docs.djangoproject.com/en/stable/topics/email/)
- [mail-tester.com](https://www.mail-tester.com/) -- email deliverability testing
