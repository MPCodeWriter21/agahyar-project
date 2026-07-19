# Make e-mail setup more real and usable

- STATUS: OPEN
- PRIORITY: 70
- TAGS: auth, mail, email, feature, enhancement, notification

Currently sending e-mail does not work. No real reset password nor any welcome messages and even info@agahyar4iran.ir is fake.
Create a docker-compose.mailcow.yml file with proper configuration for mailcow setup.
`.env.example` will need updates as well and the integeration of the mail system with the main web container must be documented properly in DEVELOPMENT/DEPLOYMENT.
A new document, `MAIL_SETUP.md` must be added with instructions to setup and configure mailcow to use with the rest of the system and must have enough details to get everything right.
