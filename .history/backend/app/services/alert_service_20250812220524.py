import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.alert import Alert
from app.core.config import settings

class AlertService:
    def __init__(self):
        self.alert_cooldown = {}  # Track when we last sent alerts
        
    async def load_email_config(self):
        """Load email configuration from settings.json"""
        try:
            settings_file = os.path.join(settings.CONFIG_PATH, settings.SETTINGS_CONFIG_FILE)
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    config = json.load(f)
                    return config.get('email', {})
            return {}
        except Exception as e:
            print(f"❌ Error loading email config: {e}")
            return {}
    
    async def send_email_alert(self, subject: str, message: str, email_config: dict):
        """Send email alert using SMTP"""
        try:
            if not email_config.get('enabled', False):
                return False
                
            smtp_config = email_config.get('smtp', {})
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_config.get('auth', {}).get('user', '')
            msg['To'] = ', '.join(email_config.get('to', []))
            msg['Subject'] = subject
            
            # Email body
            body = f"""
KbEye Alert - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{message}

---
This alert was sent by KbEye monitoring system.
Dashboard: http://localhost:3000
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
            if not smtp_config.get('secure', True):
                server.starttls()
            
            auth = smtp_config.get('auth', {})
            server.login(auth['user'], auth['pass'])
            
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email alert sent: {subject}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    
    async def create_alert(self, service_id: str, alert_type: str, message: str, severity: str = "error"):
        """Create and save alert to database"""
        async with AsyncSessionLocal() as db:
            alert = Alert(
                service_id=service_id,
                alert_type=alert_type,
                message=message,
                severity=severity
            )
            db.add(alert)
            await db.commit()
            return alert
    
    async def should_send_alert(self, service_id: str, alert_type: str) -> bool:
    """Check if we should send alert (avoid spam)"""
    key = f"{service_id}_{alert_type}"
    
    # Check database for recent alerts of same type
    async with AsyncSessionLocal() as db:
        from datetime import datetime, timedelta
        five_minutes_ago = datetime.now() - timedelta(minutes=5)
        
        result = await db.execute(
            select(Alert)
            .where(Alert.service_id == service_id)
            .where(Alert.alert_type == alert_type)
            .where(Alert.created_at > five_minutes_ago)
        )
        recent_alert = result.scalar_one_or_none()
        
        return recent_alert is None  # Only send if no recent alert exists
    
    async def handle_service_down(self, service_id: str, service_name: str, error_message: str):
        """Handle service down alert"""
        if not await self.should_send_alert(service_id, "service_down"):
            return
        
        # Create alert in database
        await self.create_alert(
            service_id=service_id,
            alert_type="service_down",
            message=f"Service '{service_name}' is DOWN: {error_message}",
            severity="critical"
        )
        
        # Send email if configured
        email_config = await self.load_email_config()
        if email_config.get('enabled'):
            subject = f"🚨 KbEye Alert: {service_name} is DOWN"
            message = f"""
Service: {service_name} ({service_id})
Status: DOWN
Error: {error_message}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            await self.send_email_alert(subject, message, email_config)
    
    async def handle_service_recovered(self, service_id: str, service_name: str):
        """Handle service recovery alert"""
        if not await self.should_send_alert(service_id, "service_recovered"):
            return
            
        # Create alert in database
        await self.create_alert(
            service_id=service_id,
            alert_type="service_recovered",
            message=f"Service '{service_name}' has RECOVERED",
            severity="info"
        )
        
        # Send email if configured
        email_config = await self.load_email_config()
        if email_config.get('enabled'):
            subject = f"✅ KbEye Alert: {service_name} RECOVERED"
            message = f"""
Service: {service_name} ({service_id})
Status: RECOVERED
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            await self.send_email_alert(subject, message, email_config)

# Global alert service
alert_service = AlertService()