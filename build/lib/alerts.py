import json
import urllib.request

class AlertEngine:
    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url
    
    def slack(self, message, title="Dapine Alert"):
        """Send alert to Slack."""
        if not self.webhook_url:
            print(f"🔔 ALERT: {title} - {message}")
            return
        
        data = {
            "blocks": [
                {"type": "header", "text": {"type": "plain_text", "text": f"🚀 {title}"}},
                {"type": "section", "text": {"type": "mrkdwn", "text": message}},
                {"type": "context", "elements": [{"type": "mrkdwn", "text": "⚡ Sent by Dapine"}]}
            ]
        }
        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(data).encode(),
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req)
            print(f"✅ Slack alert sent: {title}")
        except Exception as e:
            print(f"⚠️ Slack failed: {e}")
    
    def email(self, to, subject, body):
        """Send email alert (requires SMTP)."""
        print(f"📧 EMAIL to {to}: {subject}")
        print(f"   {body[:100]}...")