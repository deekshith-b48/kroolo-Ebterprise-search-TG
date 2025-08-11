"""
File upload handlers for the Telegram bot.
"""
import os
from typing import Optional
from datetime import datetime

from telegram import Update, File, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..auth import require_auth
from ..storage import conversation_state, file_storage
from ..backend import backend_client
from ..config import settings
from ..logging_config import get_logger

logger = get_logger(__name__)


@require_auth
async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle file uploads from users - enhanced version."""
    user_id = update.effective_user.id
    
    # Check if user is in upload flow
    current_flow = await conversation_state.get_flow(user_id)
    if current_flow != "upload_file":
        await update.message.reply_text(
            "📤 To upload files, please use the `/upload` command first."
        )
        return
    
    # Get the file
    file_obj = None
    filename = None
    
    if update.message.document:
        file_obj = update.message.document
        filename = file_obj.file_name
    elif update.message.photo:
        file_obj = update.message.photo[-1]  # Get highest quality
        filename = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    elif update.message.voice:
        file_obj = update.message.voice
        filename = f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ogg"
    elif update.message.audio:
        file_obj = update.message.audio
        filename = file_obj.file_name or f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
    else:
        await update.message.reply_text(
            "❌ **Unsupported File Type**\n\n"
            "Supported formats:\n"
            "• 📄 Documents: PDF, DOC, DOCX, TXT, RTF\n"
            "• 🖼️ Images: JPG, PNG, GIF (with text)\n" 
            "• 🎵 Audio: MP3, WAV, OGG\n"
            "• 📊 Data: CSV, XLS, XLSX, JSON\n"
            "• 📝 Text: MD, HTML, XML",
            parse_mode="Markdown"
        )
        return
    
    # Check file size
    file_size_mb = file_obj.file_size / (1024 * 1024) if file_obj.file_size else 0
    if file_size_mb > settings.max_file_size_mb:
        await update.message.reply_text(
            f"❌ **File Too Large**\n\n"
            f"Maximum size: {settings.max_file_size_mb}MB\n"
            f"Your file: {file_size_mb:.1f}MB\n\n"
            f"💡 Try compressing the file or splitting it into smaller parts.",
            parse_mode="Markdown"
        )
        return
    
    # Check if file type is supported
    if not is_supported_file_type(filename):
        await update.message.reply_text(
            f"❌ **Unsupported File Extension**\n\n"
            f"File: `{filename}`\n"
            f"Extension not supported for processing.\n\n"
            f"Use `/help` to see supported formats.",
            parse_mode="Markdown"
        )
        return
    
    try:
        # Show enhanced processing message
        processing_msg = await update.message.reply_text(
            f"📤 **Uploading and Processing File**\n\n"
            f"📄 **File:** `{filename}`\n"
            f"📊 **Size:** {file_size_mb:.1f} MB\n"
            f"🔧 **Type:** {get_file_extension(filename).upper()[1:]}\n"
            f"⏳ **Status:** Downloading from Telegram...",
            parse_mode="Markdown"
        )
        
        # Download file from Telegram with progress
        telegram_file: File = await file_obj.get_file()
        
        # Update status
        await processing_msg.edit_text(
            f"📤 **Uploading and Processing File**\n\n"
            f"📄 **File:** `{filename}`\n"
            f"📊 **Size:** {file_size_mb:.1f} MB\n"
            f"🔧 **Type:** {get_file_extension(filename).upper()[1:]}\n"
            f"⏳ **Status:** Uploading to backend...",
            parse_mode="Markdown"
        )
        
        file_data = await telegram_file.download_as_bytearray()
        
        # Prepare enhanced metadata
        metadata = {
            "original_filename": filename,
            "file_size": file_obj.file_size,
            "file_size_mb": file_size_mb,
            "upload_date": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "telegram_file_id": file_obj.file_id,
            "mime_type": getattr(file_obj, 'mime_type', None),
            "file_extension": get_file_extension(filename),
            "supported": is_supported_file_type(filename)
        }
        
        # Add additional metadata based on file type
        if hasattr(file_obj, 'width') and hasattr(file_obj, 'height'):
            metadata["dimensions"] = f"{file_obj.width}x{file_obj.height}"
        if hasattr(file_obj, 'duration'):
            metadata["duration"] = file_obj.duration
        
        # Add text content if provided
        if update.message.caption:
            metadata["caption"] = update.message.caption
            metadata["has_caption"] = True
        
        # Update status
        await processing_msg.edit_text(
            f"📤 **Uploading and Processing File**\n\n"
            f"📄 **File:** `{filename}`\n"
            f"📊 **Size:** {file_size_mb:.1f} MB\n"
            f"🔧 **Type:** {get_file_extension(filename).upper()[1:]}\n"
            f"⏳ **Status:** Processing and indexing...",
            parse_mode="Markdown"
        )
        
        # Upload to backend
        result = await backend_client.upload_file(
            user_id=user_id,
            file_data=file_data,
            filename=filename,
            metadata=metadata
        )
        
        if result and "error" not in result:
            job_id = result.get("job_id")
            document_id = result.get("document_id")
            processing_time = result.get("processing_time", "Unknown")
            
            # Format success message
            success_msg = f"""
✅ **File Uploaded Successfully**

📄 **File:** {filename}
📊 **Size:** {file_size_mb:.1f} MB
🔧 **Type:** {get_file_extension(filename).upper()[1:]}
🆔 **Document ID:** `{document_id or 'Assigned'}`
            """
            
            if job_id:
                success_msg += f"🔄 **Processing Job:** `{job_id}`\n"
                success_msg += f"⏱️ **Processing Time:** {processing_time}\n\n"
                success_msg += f"**Status:** File is being processed in the background.\n"
                success_msg += f"Use `/status {job_id}` to check progress."
            else:
                success_msg += f"⏱️ **Processing Time:** {processing_time}\n\n"
                success_msg += f"**Status:** ✅ File has been indexed and is ready for search!"
            
            await processing_msg.edit_text(success_msg.strip(), parse_mode="Markdown")
            
            # Store job info for tracking
            if job_id:
                await conversation_state.update_state(user_id, {
                    "last_upload_job": job_id,
                    "last_upload_file": filename,
                    "last_upload_document_id": document_id
                })
            
            # Add quick action buttons
            
            if job_id:
                keyboard = [
                    [
                        InlineKeyboardButton("📋 Check Status", callback_data=f"check_job_{job_id}"),
                        InlineKeyboardButton("📤 Upload Another", callback_data="upload_file")
                    ]
                ]
            else:
                keyboard = [
                    [
                        InlineKeyboardButton("🔍 Search Now", callback_data="search_demo"),
                        InlineKeyboardButton("📤 Upload Another", callback_data="upload_file")
                    ]
                ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="**Quick Actions:**",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        
        else:
            error_msg = result.get("error", "Unknown error") if result else "Upload failed"
            await processing_msg.edit_text(
                f"❌ **Upload Failed**\n\n"
                f"📄 **File:** {filename}\n"
                f"❌ **Error:** {error_msg}\n\n"
                f"Please try again or contact support if the issue persists.",
                parse_mode="Markdown"
            )
    
    except Exception as e:
        logger.error("File upload error", error=str(e), user_id=user_id, filename=filename)
        
        # Try to update the processing message
        try:
            await processing_msg.edit_text(
                f"❌ **Upload Error**\n\n"
                f"📄 **File:** {filename}\n"
                f"❌ **Error:** An unexpected error occurred\n\n"
                f"Please try again or use a different file format.",
                parse_mode="Markdown"
            )
        except:
            # If editing fails, send a new message
            await update.message.reply_text(
                "❌ An error occurred during upload. Please try again."
            )
    
    finally:
        # Clear upload flow
        await conversation_state.clear_state(user_id)


async def get_file_info(file_obj) -> dict:
    """Extract file information for logging and metadata."""
    info = {
        "file_id": file_obj.file_id,
        "file_size": getattr(file_obj, 'file_size', 0),
    }
    
    if hasattr(file_obj, 'file_name'):
        info["file_name"] = file_obj.file_name
    if hasattr(file_obj, 'mime_type'):
        info["mime_type"] = file_obj.mime_type
    if hasattr(file_obj, 'width'):
        info["width"] = file_obj.width
    if hasattr(file_obj, 'height'):
        info["height"] = file_obj.height
    if hasattr(file_obj, 'duration'):
        info["duration"] = file_obj.duration
    
    return info


def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    if not filename:
        return ""
    return os.path.splitext(filename)[1].lower()


def is_supported_file_type(filename: str) -> bool:
    """Check if file type is supported for upload."""
    if not filename:
        return False
    
    supported_extensions = {
        '.pdf', '.doc', '.docx', '.txt', '.rtf',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp',
        '.mp3', '.wav', '.ogg', '.m4a',
        '.csv', '.xlsx', '.xls',
        '.md', '.html', '.xml', '.json'
    }
    
    ext = get_file_extension(filename)
    return ext in supported_extensions
