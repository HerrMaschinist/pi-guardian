# nginx – PI Guardian Deployment

nginx serviert das UI-Build auf Port 3001 und proxyt `/api/*` an den FastAPI-Router (Port 8071).

---

## Deployment auf dem Raspberry Pi

### 1. nginx installieren

```bash
sudo apt update && sudo apt install -y nginx
```

### 2. Config nach sites-available kopieren

```bash
sudo cp /home/Alex/pi-guardian-ui/../nginx/pi-guardian.conf \
    /etc/nginx/sites-available/pi-guardian
```

Oder direkt aus dem geklonten Repo:

```bash
sudo cp ~/pi-guardian/nginx/pi-guardian.conf \
    /etc/nginx/sites-available/pi-guardian
```

### 3. Symlink nach sites-enabled setzen

```bash
sudo ln -s /etc/nginx/sites-available/pi-guardian \
    /etc/nginx/sites-enabled/pi-guardian
```

### 4. Default-Site deaktivieren

```bash
sudo rm -f /etc/nginx/sites-enabled/default
```

### 5. Config testen

```bash
sudo nginx -t
```

Erwartete Ausgabe:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 6. nginx starten und beim Boot aktivieren

```bash
sudo systemctl enable nginx
sudo systemctl start nginx
```

Bei bereits laufendem nginx:

```bash
sudo systemctl reload nginx
```

### 7. Verifikation

**Health-Check über nginx-Proxy:**
```bash
curl http://192.168.50.10:3001/api/health
# Erwartet: {"status":"ok"}
```

**UI im Browser:**
```
http://192.168.50.10:3001
```

**Logs prüfen:**
```bash
sudo tail -f /var/log/nginx/pi-guardian.access.log
sudo tail -f /var/log/nginx/pi-guardian.error.log
```

---

## Hinweise

- Zugriff ist auf LAN `192.168.50.0/24` beschränkt (`deny all` für alle anderen)
- Kein TLS – internes LAN, kein öffentlicher Zugriff
- UFW-Regel für Port 3001 muss aktiv sein (laut bestehendem `ufw-status`: bereits offen)
- FastAPI-Router muss auf `127.0.0.1:8071` laufen (via systemd `pi-guardian-router.service`)
