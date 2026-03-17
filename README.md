# Portal mit OAuth2 / OpenID Connect (Azure AD)

## Projektbeschreibung

Dieses Projekt erweitert ein bestehendes Patientenportal um eine Anmeldung über **OAuth2 / OpenID Connect (Azure AD)**.

Benutzer können sich mit ihrer **Schul-E-Mail** anmelden.
Nach erfolgreichem Login wird automatisch ein lokaler Benutzer erstellt, der zunächst **nicht aktiviert ist (`is_active=False`)** und erst durch einen Administrator freigeschaltet werden muss.

---

## Technologien

* Django
* django-allauth
* OpenID Connect (OIDC)
* Microsoft Azure AD (Entra ID)

---

## Azure App Registration

Für die Authentifizierung wurde eine Azure App Registration erstellt:

* Name: `MGIN-Portal-Auth`
* Supported account types: Single Tenant (Schulkonto)
* Redirect URI:

  ```
  http://127.0.0.1:8000/accounts/oidc/school/login/callback/
  ```

### API Permissions

Folgende Berechtigungen wurden gesetzt:

* openid
* profile
* email
* offline_access

---

## Umgebungsvariablen

Die sensiblen Daten werden **nicht im Code gespeichert**, sondern über Umgebungsvariablen gesetzt:

```bash
AZURE_CLIENT_ID=...
AZURE_CLIENT_SECRET=...
AZURE_TENANT_ID=...
```

Diese werden in Django verwendet für die OIDC-Konfiguration.

---

## Django Konfiguration (OIDC)

Der Login wurde mit `django-allauth` und dem OpenID Connect Provider umgesetzt.

Wichtige Einstellungen:

```python
SOCIALACCOUNT_PROVIDERS = {
    "openid_connect": {
        "APPS": [
            {
                "provider_id": "school",
                "name": "Schul-Login",
                "client_id": AZURE_CLIENT_ID,
                "secret": AZURE_CLIENT_SECRET,
                "settings": {
                    "server_url": f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/v2.0",
                    "fetch_userinfo": False,
                },
            }
        ]
    }
}
```

---

## Login

Der Login erfolgt über folgende URL:

```
http://127.0.0.1:8000/accounts/oidc/school/login/
```

---

## Ablauf (Login Flow)

1. Benutzer klickt auf „Mit Schul-E-Mail anmelden“
2. Weiterleitung zu Microsoft Login
3. Erfolgreiche Authentifizierung
4. Redirect zurück zur Anwendung
5. Benutzer wird lokal erstellt

---

## Benutzer-Erstellung

Beim ersten Login:

* Benutzer wird automatisch erstellt
* Daten werden aus dem ID-Token übernommen (Name, E-Mail)
* `is_active = False` wird gesetzt

---

## Admin-Freischaltung

Ein Benutzer kann sich erst vollständig einloggen, wenn er im Django Admin freigeschaltet wird:

1. Admin öffnet `/admin`
2. Benutzer auswählen
3. `is_active` aktivieren

---

## Verhalten des Systems

| Zustand           | Verhalten                       |
| ----------------- | ------------------------------- |
| User nicht aktiv  | Zugriff auf Dashboard blockiert |
| User aktiv        | Zugriff erlaubt                 |
| Login erfolgreich | Weiterleitung auf Dashboard     |

---

## Testanleitung

1. Anwendung starten:

```bash
py manage.py runserver
```

2. Login öffnen:

```
http://127.0.0.1:8000/accounts/oidc/school/login/
```

3. Mit Schulkonto anmelden

4. Erwartetes Verhalten:

* Benutzer wird erstellt
* Zugriff wird blockiert (Freischaltung nötig)

5. Admin aktiviert Benutzer

6. Login erneut testen → Zugriff funktioniert

---

## Sicherheit

* Client Secret wird **nicht im Repository gespeichert**
* Verwendung von Umgebungsvariablen
* Minimale Berechtigungen (Least Privilege)
* Kein unnötiger Zugriff auf Microsoft Graph

---


## Fazit

Das Projekt implementiert erfolgreich:

* OAuth2 / OpenID Connect Login mit Azure AD
* automatische Benutzererstellung
* Admin-Freischaltungs-Workflow
* sichere Speicherung sensibler Daten
* Integration in bestehende Django-Anwendung

---
