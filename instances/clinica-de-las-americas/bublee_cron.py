"""
bublee_cron.py — Scheduled tasks for Bublee (memory consolidation, cleanup).
"""
from __future__ import annotations
import logging, asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

log = logging.getLogger("bublee.cron")

_scheduler: AsyncIOScheduler = None


def init_scheduler(memory_engine=None, instance_ids: list = None):
    """Initialize the cron scheduler. Call during app startup."""
    global _scheduler
    if _scheduler:
        return _scheduler

    _scheduler = AsyncIOScheduler()

    if memory_engine and instance_ids:
        for iid in instance_ids:
            _scheduler.add_job(
                _run_consolidation,
                CronTrigger(day_of_week="sun", hour=3, minute=0),
                args=[memory_engine, iid],
                id=f"consolidation_{iid}",
                replace_existing=True,
            )
            # Weekly report every Monday at 9am
            _scheduler.add_job(
                _send_weekly_report,
                CronTrigger(day_of_week="mon", hour=9, minute=0),
                args=[iid],
                id=f"weekly_report_{iid}",
                replace_existing=True,
            )
            # NPS check every 15 minutes
            _scheduler.add_job(
                _check_finished_appointments,
                "interval",
                minutes=15,
                args=[iid],
                id=f"nps_check_{iid}",
                replace_existing=True,
            )
            log.info(f"[cron] consolidation (Sun 3am) + weekly report (Mon 9am) + NPS check (15m) scheduled for {iid}")

    _scheduler.start()
    log.info("[cron] scheduler started")
    return _scheduler


async def _run_consolidation(memory_engine, instance_id: str):
    """Run weekly memory consolidation for an instance."""
    try:
        await memory_engine.weekly_consolidation(instance_id)
        log.info(f"[cron] consolidation complete: {instance_id}")
    except Exception as e:
        log.error(f"[cron] consolidation failed for {instance_id}: {e}")


async def _send_weekly_report(instance_id: str):
    """Send weekly report to admin."""
    try:
        from bublee_weekly_report import generate_weekly_report
        report = await generate_weekly_report(instance_id)
        log.info(f"[cron] weekly report generated for {instance_id}")
        # TODO: wire send_fn when admin_jid is available in cron context
    except Exception as e:
        log.error(f"[cron] weekly report failed: {e}")


async def _check_finished_appointments(instance_id: str):
    """Check for finished appointments and trigger NPS surveys."""
    from datetime import datetime, timedelta
    from src.core.globals import db
    try:
        from src.interfaces.web.app import bublee
    except ImportError:
        log.warning("[cron] could not import bublee runtime for NPS checks")
        return

    now = datetime.now()
    
    try:
        with db._conn() as c:
            rows = c.execute("""
                SELECT * FROM appointments 
                WHERE status='confirmada' AND nps_status='pending'
            """).fetchall()
    except Exception as e:
        log.warning(f"[cron] failed to query appointments for NPS: {e}")
        return

    for row in rows:
        apt = dict(row)
        apt_id = apt["id"]
        dt_str = apt["datetime_slot"]
        duration = apt.get("duration_minutes", 60) or 60
        
        try:
            dt_str_clean = dt_str.replace(" ", "T")
            if len(dt_str_clean) == 16:  # YYYY-MM-DDTHH:MM
                dt_str_clean += ":00"
            start_dt = datetime.fromisoformat(dt_str_clean)
        except Exception:
            continue
            
        end_dt = start_dt + timedelta(minutes=duration)
        
        # Trigger NPS survey if current time is at least 2 hours past the end of the appointment
        if now >= end_dt + timedelta(hours=2):
            chat_id = apt.get("chat_id")
            patient_name = apt.get("patient_name") or "Paciente"
            service = apt.get("service") or "servicio"
            
            nps_question = (
                f"¡Hola {patient_name}! 😊 Espero que estés súper bien.\n\n"
                f"¿Cómo te fue hoy en tu cita para *{service}*? Nos encantaría saber tu opinión del 1 al 5."
            )
            
            try:
                # Update status to 'sent' before sending to prevent race conditions or double sends
                db.update_appointment(apt_id, nps_status="sent")
                
                await bublee._send_message(chat_id, nps_question)
                log.info(f"[cron] NPS question sent to {chat_id} for appointment {apt_id}")
            except Exception as e:
                log.error(f"[cron] Failed to send NPS question to {chat_id}: {e}")


def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        log.info("[cron] scheduler stopped")
