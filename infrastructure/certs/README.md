# SSL/TLS Certificates for Production

Place your TLS certificate and private key in this directory:
- `fullchain.pem`: Full certificate chain (cert + intermediate CA)
- `privkey.pem`: Private key

### Option 1: Self-Signed Certificate for Testing/Staging
Generate a self-signed certificate for local production testing:
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout privkey.pem \
  -out fullchain.pem \
  -subj "/CN=localhost"
```

### Option 2: Let's Encrypt (Certbot)
If deploying to a domain (e.g. `eob.example.com`):
```bash
certbot certonly --standalone -d eob.example.com
cp /etc/letsencrypt/live/eob.example.com/fullchain.pem infrastructure/certs/
cp /etc/letsencrypt/live/eob.example.com/privkey.pem infrastructure/certs/
chmod 600 infrastructure/certs/privkey.pem
```
