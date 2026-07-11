content = """# =============================================================================
# CADDYFILE OPTIMIZADO PARA NEXUS
# Reverse Proxy + SSL Automático + Seguridad Reforzada
# =============================================================================
{
    email admin@nexusys.duckdns.org
    admin off
    log {
        output stdout
        format console
        level INFO
    }
    servers {
        protocols h1 h2 h2c h3
        timeouts {
            read_body 60s
            read_header 10s
            write 120s
            idle 300s
        }
    }
}

(nova_security) {
    encode gzip zstd
    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
        Referrer-Policy "strict-origin-when-cross-origin"
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        Permissions-Policy "camera=(), microphone=(), geolocation=()"
        Cross-Origin-Opener-Policy "same-origin"
        Cross-Origin-Resource-Policy "same-site"
        Content-Security-Policy "default-src 'self' https: data: blob: 'unsafe-inline' 'unsafe-eval'; connect-src 'self' https: wss:; img-src 'self' https: data: blob:; font-src 'self' https: data:; style-src 'self' https: 'unsafe-inline'; script-src 'self' https: 'unsafe-inline' 'unsafe-eval' blob:; frame-ancestors 'self'; base-uri 'self'; form-action 'self'"
        -Server
        -X-Powered-By
    }
}

(nova_proxy) {
    handle /api/* {
        reverse_proxy 127.0.0.1:8000
    }
    reverse_proxy 127.0.0.1:3005
}

:80 {
    respond /health 200
}

nexusys.duckdns.org {
    tls {
        protocols tls1.2 tls1.3
    }
    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        -Server
        -X-Powered-By
    }
    encode gzip zstd
    log {
        output stdout
        format json {
            time_format iso8601
        }
    }

    handle /telegram/* {
        reverse_proxy 127.0.0.1:8001
    }
    handle /health {
        reverse_proxy 127.0.0.1:8001
    }
    handle /setup-webhook {
        reverse_proxy 127.0.0.1:8001
    }
    handle /omni/* {
        reverse_proxy 127.0.0.1:9001
    }
    handle /webhook/bublee_2026* {
        reverse_proxy 127.0.0.1:8001
    }
    handle /webhook/bublee_clinica-de-las-americas_2ed44661cb56cd55* {
        reverse_proxy 127.0.0.1:8003
    }
    reverse_proxy 127.0.0.1:5678 {
        transport http {
            dial_timeout 30s
            response_header_timeout 300s
            read_timeout 300s
            write_timeout 300s
            keepalive 120s
            keepalive_idle_conns 20
        }
        header_up Host {host}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
        header_up X-Forwarded-Host {host}
        header_up Connection "upgrade"
        header_up Upgrade {http.request.header.Upgrade}
        health_uri /healthz
        health_interval 30s
        health_timeout 10s
        health_status 200
        flush_interval -1
    }
}

bublee.nexusys.duckdns.org {
    tls {
        protocols tls1.2 tls1.3
    }
    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        -Server
        -X-Powered-By
    }
    encode gzip zstd
    reverse_proxy 127.0.0.1:8003
}

bublee.duckdns.org {
    tls {
        protocols tls1.2 tls1.3
    }
    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        -Server
        -X-Powered-By
    }
    encode gzip zstd

    handle /video-bg {
        root * /home/ubuntu/bublee/brand-assets
        rewrite * /Backgroundvideo.mp4
        file_server
    }

    handle {
        reverse_proxy 127.0.0.1:8003
    }
}
"""

with open('/etc/caddy/Caddyfile', 'w') as f:
    f.write(content)
