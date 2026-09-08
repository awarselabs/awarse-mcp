import os
import json
import urllib.request
import re
from datetime import datetime, timedelta
import dotenv

dotenv.load_dotenv()

def get_cloudflare_metrics():
    """Query Cloudflare GraphQL API for 24h traffic data."""
    cf_token = os.getenv("CF_API_TOKEN")
    cf_zone = os.getenv("CF_ZONE_ID")

    if not cf_token or not cf_zone:
        return {"pageviews": "N/A (Token missing)", "uniques": "N/A"}

    url = "https://api.cloudflare.com/client/v4/graphql"
    
    # 24-hour window
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)
    
    query = """
    query {
      viewer {
        zones(filter: {zoneTag: "%s"}) {
          httpRequests1dGroups(
            limit: 1
            filter: {date_geq: "%s", date_leq: "%s"}
          ) {
            sum {
              requests
              pageViews
            }
            uniq {
              uniques
            }
          }
        }
      }
    }
    """ % (cf_zone, yesterday.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d"))

    req = urllib.request.Request(
        url,
        data=json.dumps({"query": query}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {cf_token}",
            "Content-Type": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            groups = data["data"]["viewer"]["zones"][0]["httpRequests1dGroups"]
            if groups:
                return {
                    "requests": groups[0]["sum"]["requests"],
                    "pageviews": groups[0]["sum"]["pageViews"],
                    "uniques": groups[0]["uniq"]["uniques"]
                }
    except Exception as e:
        print(f"[-] Cloudflare query failed: {e}")

    return {"requests": 0, "pageviews": 0, "uniques": 0}

def get_glama_metrics():
    """Extract public views and install badges from the Glama server listing."""
    url = "https://glama.ai/mcp/servers/awarselabs/awarse-mcp"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    
    metrics = {"status": "Online", "installs": "N/A"}
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8")
            # Simple heuristic regex for badge or install count matches
            install_match = re.search(r'(\d+)\s+(installs|uses|downloads)', html, re.I)
            if install_match:
                metrics["installs"] = install_match.group(1)
    except Exception as e:
        metrics["status"] = f"Error: {e}"
        
    return metrics

def build_report():
    cf = get_cloudflare_metrics()
    glama = get_glama_metrics()
    
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    
    report = f"""# Daily Growth & Traffic Digest ({date_str})

**awarselabs.com (Trailing 24h)**
* **Unique Visitors:** {cf.get('uniques', 'N/A')}
* **Page Views:** {cf.get('pageviews', 'N/A')}
* **Total HTTP Requests:** {cf.get('requests', 'N/A')}

**Glama Registry (awarse-mcp)**
* **Listing Status:** {glama.get('status')}
* **Recorded Installs/Interactions:** {glama.get('installs')}

---
*Report generated autonomously by Awarse Operations Agent.*
"""
    return report

def dispatch_report(report_text):
    resend_key = os.getenv("RESEND_API_KEY")
    recipient = os.getenv("REPORT_RECIPIENT", "sean@awarselabs.com")

    if not resend_key:
        print("\n--- Dry Run Report Output ---\n")
        print(report_text)
        return

    payload = {
        "from": "Awarse Agent <agent@awarselabs.com>",
        "to": [recipient],
        "subject": f"Awarse Labs Traffic Digest - {datetime.utcnow().strftime('%b %d')}",
        "text": report_text
    }

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {resend_key}",
            "Content-Type": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status in (200, 201):
                print("[✓] Report successfully sent to inbox.")
    except Exception as e:
        print(f"[-] Failed to dispatch email report: {e}")

if __name__ == "__main__":
    digest = build_report()
    dispatch_report(digest)
