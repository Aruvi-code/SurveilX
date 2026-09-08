import aiofiles

async def generate_and_save_report(txt_path, alert_level, reason, audio_context):
    report_content = (
        f"ALERT LEVEL: {alert_level}\n"
        f"REASON: {reason}\n"
        f"MULTI-MODAL CONFIRMATION: {audio_context}\n"
        f"ACTION: Logging evidence."
    )
    
    async with aiofiles.open(txt_path, mode='w') as f:
        await f.write(report_content)
