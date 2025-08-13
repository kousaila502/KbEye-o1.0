import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models.alert import Alert
from app.core.config import settings

class AlertService:
    def __init__(self):
        # No more memory-based cooldown - we use state transitions
        pass
        
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
                severity=severity,
                is_resolved=False
            )
            db.add(alert)
            await db.commit()
            await db.refresh(alert)
            return alert
    
    async def has_active_down_alert(self, service_id: str) -> bool:
        """Check if service already has an active down alert"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Alert)
                .where(Alert.service_id == service_id)
                .where(Alert.alert_type == "service_down")
                .where(Alert.is_resolved == False)
            )
            active_alert = result.scalar_one_or_none()
            return active_alert is not None
    
    async def resolve_service_alerts(self, service_id: str, alert_types: list = None):
        """Resolve active alerts for a service (auto-resolve on recovery)"""
        if alert_types is None:
            alert_types = ["service_down"]  # Default: only resolve down alerts
            
        async with AsyncSessionLocal() as db:
            # Update alerts to resolved
            result = await db.execute(
                update(Alert)
                .where(Alert.service_id == service_id)
                .where(Alert.alert_type.in_(alert_types))
                .where(Alert.is_resolved == False)
                .values(
                    is_resolved=True,
                    resolved_at=datetime.utcnow()
                )
            )
            
            resolved_count = result.rowcount
            await db.commit()
            
            if resolved_count > 0:
                print(f"✅ Auto-resolved {resolved_count} alerts for {service_id}")
            
            return resolved_count
    
    async def get_service_alerts(self, service_id: str, limit: int = 20, active_only: bool = False):
        """Get alerts for a specific service"""
        async with AsyncSessionLocal() as db:
            query = select(Alert).where(Alert.service_id == service_id)
            
            if active_only:
                query = query.where(Alert.is_resolved == False)
                
            query = query.order_by(Alert.created_at.desc()).limit(limit)
            
            result = await db.execute(query)
            alerts = result.scalars().all()
            
            return [
                {
                    "id": alert.id,
                    "service_id": alert.service_id,
                    "alert_type": alert.alert_type,
                    "message": alert.message,
                    "severity": alert.severity,
                    "is_resolved": alert.is_resolved,
                    "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                    "created_at": alert.created_at.isoformat()
                }
                for alert in alerts
            ]
    
    async def handle_service_down(self, service_id: str, service_name: str, error_message: str):
        """Handle service down - ONLY if not already down (state-based)"""
        
        # Check if service already has an active down alert
        if await self.has_active_down_alert(service_id):
            # Service already has down alert - don't spam
            return None
        
        # Create new down alert (first time down)
        alert = await self.create_alert(
            service_id=service_id,
            alert_type="service_down",
            message=f"Service '{service_name}' is DOWN: {error_message}",
            severity="critical"
        )
        
        print(f"🚨 NEW ALERT: {service_name} is DOWN")
        
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
        
        return alert
    
    async def handle_service_recovered(self, service_id: str, service_name: str):
        """Handle service recovery - Auto-resolve down alerts (no recovery spam)"""
        
        # Auto-resolve any active down alerts for this service
        resolved_count = await self.resolve_service_alerts(service_id, ["service_down"])
        
        if resolved_count > 0:
            print(f"✅ {service_name} RECOVERED - auto-resolved {resolved_count} alerts")
            
            # Send email notification only if we actually resolved alerts
            email_config = await self.load_email_config()
            if email_config.get('enabled'):
                subject = f"✅ KbEye: {service_name} RECOVERED"
                message = f"""
Service: {service_name} ({service_id})
Status: RECOVERED
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Automatically resolved {resolved_count} down alert(s).
                """
                await self.send_email_alert(subject, message, email_config)
        
        return resolved_count
    
    async def cleanup_old_alerts(self, hours_old: int = 24):
        """Auto-resolve very old alerts (cleanup maintenance)"""
        async with AsyncSessionLocal() as db:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)
            
            result = await db.execute(
                update(Alert)
                .where(Alert.created_at < cutoff_time)
                .where(Alert.is_resolved == False)
                .values(
                    is_resolved=True,
                    resolved_at=datetime.utcnow()
                )
            )
            
            resolved_count = result.rowcount
            await db.commit()
            
            if resolved_count > 0:
                print(f"🧹 Auto-resolved {resolved_count} old alerts (>{hours_old}h)")
            
            return resolved_count

# Global alert service
alert_service = AlertService()