"""
Command handlers for the Telegram bot.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..auth import require_auth, require_admin
from ..storage import conversation_state
from ..backend import backend_client
from ..logging_config import get_logger

logger = get_logger(__name__)


@require_auth
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    
    welcome_message = f"""
🚀 **Welcome to Enterprise Search Bot**

Hi {user.first_name}! I'm your AI-powered search assistant that can help you:

🔍 **Search** across all your connected data sources
📁 **Connect** to Google Drive, Slack, Notion, and more
📤 **Upload** documents for instant indexing
🔄 **Sync** your data sources automatically
📊 **Process** documents with AI-powered analysis

**Quick Start:**
• Use `/connect` to link your data sources
• Use `/search <query>` to find information
• Use `/help` to see all available commands

Let's get started! 🎯
    """
    
    keyboard = [
        [
            InlineKeyboardButton("🔗 Connect Sources", callback_data="connect"),
            InlineKeyboardButton("🔍 Search Demo", callback_data="search_demo")
        ],
        [
            InlineKeyboardButton("📚 Help", callback_data="help"),
            InlineKeyboardButton("⚙️ Settings", callback_data="settings")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
    
    # Clear any existing conversation state
    await conversation_state.clear_state(user.id)


@require_auth
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command with comprehensive command guide."""
    
    help_text = """
� **Enterprise Search Bot - Command Guide**

**🔍 Search & Discovery**
`/search <query>` - AI-powered search with citations and sources
`/fetch [source]` - Browse and fetch documents from connected sources

**🔗 Data Source Management**
`/connect` - Connect to external platforms (Drive, Slack, Notion, etc.)
`/sources` - List all your connected data sources with status
`/update [source_id]` - Manually sync data from specific sources

**📤 File Management**
`/upload` - Upload files for instant AI indexing and search
`/process [doc_id]` - Process specific documents or all pending files

**⚙️ System & Status**
`/status [job_id]` - Check system status or specific background job
`/settings` - View and manage your personal settings
`/help` - Show this comprehensive help guide

**🎯 Search Examples:**
• `/search quarterly revenue growth and market trends`
• `/search team meeting notes from last week`
• `/search project Alpha documentation and requirements`
• `/search customer feedback about new features`

**💡 Pro Tips:**
✅ **Natural Language:** Use conversational queries for better AI responses
✅ **Citations:** All answers include source links and document references  
✅ **Multi-Source:** Connect multiple platforms for comprehensive search
✅ **File Formats:** Supports PDF, DOC, TXT, CSV, images with text, and more
✅ **Real-time:** Upload files and search immediately after processing

**🚀 Quick Start:**
1. Use `/connect` to link your data sources
2. Upload documents with `/upload` 
3. Search with `/search your question here`
4. Check status anytime with `/status`

**👨‍💼 Admin Commands** (if you're an admin):
`/admin stats` - View system statistics and usage metrics
`/admin users` - Manage authorized users and permissions

Need personalized help? Contact your system administrator.
    """
    
    keyboard = [
        [
            InlineKeyboardButton("🔗 Connect Sources", callback_data="connect"),
            InlineKeyboardButton("🔍 Try Demo Search", callback_data="search_demo")
        ],
        [
            InlineKeyboardButton("📤 Upload File", callback_data="upload_file"),
            InlineKeyboardButton("📊 Check Status", callback_data="refresh_status")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


@require_auth
async def connect_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /connect command."""
    user_id = update.effective_user.id
    
    # Set conversation flow
    await conversation_state.set_flow(user_id, "connect_platform")
    
    keyboard = [
        [
            InlineKeyboardButton("📁 Google Drive", callback_data="connect_drive"),
            InlineKeyboardButton("💬 Slack", callback_data="connect_slack")
        ],
        [
            InlineKeyboardButton("📝 Notion", callback_data="connect_notion"),
            InlineKeyboardButton("🌐 Custom URL", callback_data="connect_custom")
        ],
        [
            InlineKeyboardButton("❌ Cancel", callback_data="cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔗 **Connect Data Source**\n\n"
        "Choose a platform to connect to your enterprise search:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


@require_auth
async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /search command with enhanced UX."""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "🔍 **Search Usage**\n\n"
            "Use: `/search <your query>`\n\n"
            "**Examples:**\n"
            "• `/search quarterly revenue growth`\n"
            "• `/search team meeting notes from last week`\n"
            "• `/search API documentation`\n\n"
            "💡 **Tips:**\n"
            "• Use natural language for better results\n"
            "• I'll provide sources and citations\n"
            "• Connect multiple sources for comprehensive search",
            parse_mode="Markdown"
        )
        return
    
    query = " ".join(context.args)
    
    # Show enhanced loading message
    loading_message = await update.message.reply_text("🔍 Searching across all sources...")
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Perform search
    try:
        result = await backend_client.search(user_id, query, include_citations=True)
        
        # Delete loading message
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=loading_message.message_id
        )
        
        if not result or "error" in result:
            error_msg = result.get("error", "Unknown error") if result else "Backend unavailable"
            await update.message.reply_text(
                f"❌ Search failed: {error_msg}\n\n"
                "Please try again or contact support if the issue persists."
            )
            return
        
        # Format response with citations
        response_text = await format_search_response(result, query)
        
        # Send response (split if too long)
        if len(response_text) > 4000:
            # Split into chunks
            chunks = split_long_message(response_text)
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await update.message.reply_text(chunk, parse_mode="Markdown", disable_web_page_preview=True)
                else:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=chunk,
                        parse_mode="Markdown",
                        disable_web_page_preview=True
                    )
        else:
            await update.message.reply_text(response_text, parse_mode="Markdown", disable_web_page_preview=True)
        
        # Show quick actions if we have results
        if result.get("results") and len(result["results"]) > 0:
            keyboard = [
                [
                    InlineKeyboardButton("🔍 Refine Search", callback_data="refine_search"),
                    InlineKeyboardButton("📥 Get Documents", callback_data="get_documents")
                ],
                [
                    InlineKeyboardButton("📊 Summarize", callback_data="summarize_results"),
                    InlineKeyboardButton("🔄 Related Search", callback_data="related_search")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "**Quick Actions:**",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            
    except Exception as e:
        # Delete loading message if it exists
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=loading_message.message_id
            )
        except:
            pass
            
        logger.error("Search command error", error=str(e), user_id=user_id, query=query)
        await update.message.reply_text(
            "❌ Search error. Please try again or check your connections."
        )


async def format_search_response(result: dict, query: str = "") -> str:
    """Format search results with Perplexity-style citations."""
    answer = result.get("answer", "")
    citations = result.get("citations", [])
    results = result.get("results", [])
    
    if not answer and not results:
        return "❌ No results found for your query.\n\n💡 Try:\n• Using different keywords\n• Connecting more data sources\n• Checking if your sources are properly synced"
    
    # Start with the query header
    response = f"🔍 **Search Results for: \"{query}\"**\n\n"
    
    # Add the AI-generated answer if available
    if answer:
        response += f"{answer}\n\n"
    
    # Add citations in Perplexity style
    if citations:
        response += "📚 **Sources:**\n"
        for i, citation in enumerate(citations, 1):
            cite_id = citation.get("id", i)
            title = citation.get("title", f"Document {i}")
            url = citation.get("url", "")
            source = citation.get("source", "Unknown")
            snippet = citation.get("snippet", "")
            
            # Format citation entry
            if url:
                response += f"[{cite_id}] [{title}]({url})\n"
            else:
                response += f"[{cite_id}] {title}\n"
                
            response += f"    📂 {source}"
            
            if snippet:
                # Clean and truncate snippet
                clean_snippet = snippet.replace('\n', ' ').strip()
                if len(clean_snippet) > 100:
                    clean_snippet = clean_snippet[:100] + "..."
                response += f" | {clean_snippet}"
            response += "\n\n"
    
    # Add raw results if no AI answer
    elif results:
        response += "📄 **Found Documents:**\n"
        for i, result_item in enumerate(results[:5], 1):  # Limit to top 5
            title = result_item.get("title", f"Document {i}")
            source = result_item.get("source", "Unknown")
            snippet = result_item.get("snippet", "")
            url = result_item.get("url", "")
            
            if url:
                response += f"{i}. [{title}]({url})\n"
            else:
                response += f"{i}. {title}\n"
                
            response += f"   📂 {source}"
            if snippet:
                clean_snippet = snippet.replace('\n', ' ').strip()[:80]
                response += f" — {clean_snippet}..."
            response += "\n\n"
    
    # Add footer with search stats
    total_results = len(results) if results else len(citations)
    if total_results > 0:
        response += f"📊 Found {total_results} result{'s' if total_results != 1 else ''}"
        
        # Add timing info if available
        search_time = result.get("search_time")
        if search_time:
            response += f" in {search_time}ms"
    
    return response


def split_long_message(text: str, max_length: int = 4000) -> list:
    """Split long message into chunks."""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    for line in text.split('\n'):
        if len(current_chunk) + len(line) + 1 <= max_length:
            current_chunk += line + '\n'
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = line + '\n'
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


@require_auth
async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /upload command."""
    user_id = update.effective_user.id
    
    await conversation_state.set_flow(user_id, "upload_file")
    
    await update.message.reply_text(
        "📤 **Upload File**\n\n"
        "Send me a file to upload for indexing. Supported formats:\n"
        "• PDF documents\n"
        "• Word documents (.doc, .docx)\n"
        "• Text files (.txt)\n"
        "• Images with text\n\n"
        "Or use `/cancel` to abort.",
        parse_mode="Markdown"
    )


@require_auth
async def sources_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /sources command - show connected data sources."""
    user_id = update.effective_user.id
    
    try:
        sources_data = await backend_client.get_sources(user_id)
        
        if not sources_data or "error" in sources_data:
            error_msg = sources_data.get("error", "Unknown error") if sources_data else "Backend unavailable"
            await update.message.reply_text(
                f"❌ Failed to fetch sources: {error_msg}\n\n"
                "Please try again or use `/connect` to add sources."
            )
            return
        
        sources = sources_data.get("sources", [])
        
        if not sources:
            keyboard = [
                [InlineKeyboardButton("🔗 Connect Sources", callback_data="connect")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "📂 **No Sources Connected**\n\n"
                "You haven't connected any data sources yet.\n"
                "Use the button below to get started!",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            return
        
        # Format sources list
        sources_message = "📂 **Your Connected Sources:**\n\n"
        
        for i, source in enumerate(sources, 1):
            name = source.get("name", f"Source {i}")
            platform = source.get("platform", "Unknown")
            status = source.get("status", "unknown")
            last_sync = source.get("last_sync", "Never")
            doc_count = source.get("document_count", 0)
            
            # Status emoji
            status_emoji = "✅" if status == "active" else "❌" if status == "error" else "⏸️"
            
            sources_message += f"{i}. **{name}**\n"
            sources_message += f"   🔧 Platform: {platform.title()}\n"
            sources_message += f"   {status_emoji} Status: {status.title()}\n"
            sources_message += f"   📄 Documents: {doc_count}\n"
            sources_message += f"   🔄 Last Sync: {last_sync}\n\n"
        
        # Add quick action buttons
        keyboard = [
            [
                InlineKeyboardButton("🔄 Sync All", callback_data="sync_all_sources"),
                InlineKeyboardButton("🔗 Add Source", callback_data="connect")
            ],
            [
                InlineKeyboardButton("📊 Source Details", callback_data="source_details"),
                InlineKeyboardButton("⚙️ Manage", callback_data="manage_sources")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            sources_message,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error("Sources command error", error=str(e), user_id=user_id)
        await update.message.reply_text(
            "❌ Error fetching sources. Please try again."
        )


@require_auth
async def fetch_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /fetch command - fetch data from specific source."""
    user_id = update.effective_user.id
    
    # Check if source was specified
    if context.args:
        source_name = " ".join(context.args)
        await handle_fetch_from_source(update, context, source_name)
        return
    
    # Show available sources for selection
    try:
        sources_data = await backend_client.get_sources(user_id)
        
        if not sources_data or "error" in sources_data:
            await update.message.reply_text(
                "❌ Cannot fetch sources. Use `/connect` to add sources first."
            )
            return
        
        sources = sources_data.get("sources", [])
        
        if not sources:
            keyboard = [
                [InlineKeyboardButton("🔗 Connect Sources", callback_data="connect")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "📥 **No Sources to Fetch From**\n\n"
                "Connect data sources first to fetch documents.",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            return
        
        # Create source selection keyboard
        keyboard = []
        for source in sources:
            source_id = source.get("id")
            source_name = source.get("name", "Unknown")
            platform = source.get("platform", "")
            status = source.get("status", "")
            
            # Only show active sources
            if status == "active":
                button_text = f"📁 {source_name}"
                if platform:
                    button_text += f" ({platform})"
                
                keyboard.append([
                    InlineKeyboardButton(button_text, callback_data=f"fetch_source_{source_id}")
                ])
        
        if not keyboard:
            await update.message.reply_text(
                "❌ No active sources available for fetching.\n"
                "Please check your source connections."
            )
            return
        
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📥 **Fetch Data from Source**\n\n"
            "Select a source to fetch latest data:",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error("Fetch command error", error=str(e), user_id=user_id)
        await update.message.reply_text(
            "❌ Error accessing sources. Please try again."
        )


async def handle_fetch_from_source(update: Update, context: ContextTypes.DEFAULT_TYPE, source_name: str) -> None:
    """Handle fetching from a specific source."""
    user_id = update.effective_user.id
    
    loading_message = await update.message.reply_text(f"📥 Fetching data from {source_name}...")
    
    try:
        result = await backend_client.fetch_from_source(user_id, source_name)
        
        # Delete loading message
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=loading_message.message_id
        )
        
        if not result or "error" in result:
            error_msg = result.get("error", "Unknown error") if result else "Fetch failed"
            await update.message.reply_text(
                f"❌ **Fetch Failed**\n\n"
                f"Error fetching from {source_name}: {error_msg}"
            )
            return
        
        # Format fetch results
        fetch_message = f"""
✅ **Data Fetch Complete**

📂 **Source:** {result.get('source_name', source_name)}
📊 **Items Retrieved:** {result.get('item_count', 0)}
📅 **Last Updated:** {result.get('last_updated', 'Unknown')}
🔄 **Sync Status:** {result.get('sync_status', 'Unknown')}

**Summary:**
{result.get('summary', 'Data successfully fetched and indexed.')}
        """
        
        await update.message.reply_text(fetch_message.strip(), parse_mode="Markdown")
        
    except Exception as e:
        # Delete loading message if it exists
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=loading_message.message_id
            )
        except:
            pass
            
        logger.error("Fetch source error", error=str(e), user_id=user_id, source=source_name)
        await update.message.reply_text(
            f"❌ Error fetching from {source_name}. Check if the source is properly connected."
        )


@require_auth
async def process_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /process command - process uploaded documents."""
    user_id = update.effective_user.id
    
    # Check if specific document ID was provided
    if context.args:
        doc_id = context.args[0]
        await handle_process_document(update, context, doc_id)
        return
    
    # Process all pending documents
    loading_message = await update.message.reply_text("⚙️ Processing your documents...")
    
    try:
        result = await backend_client.process_documents(user_id)
        
        # Delete loading message
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=loading_message.message_id
        )
        
        if not result or "error" in result:
            error_msg = result.get("error", "Unknown error") if result else "Processing failed"
            await update.message.reply_text(
                f"❌ **Processing Failed**\n\n{error_msg}"
            )
            return
        
        # Format processing results
        document_count = result.get("document_count", 0)
        summary = result.get("summary", "Documents processed successfully.")
        processing_time = result.get("processing_time", "Unknown")
        
        process_message = f"""
✅ **Processing Complete**

📊 **Processed:** {document_count} document{'s' if document_count != 1 else ''}
⏱️ **Time:** {processing_time}

**Summary:**
{summary}

Your documents are now searchable!
        """
        
        # Add quick actions
        keyboard = [
            [
                InlineKeyboardButton("🔍 Search Now", callback_data="search_demo"),
                InlineKeyboardButton("📤 Upload More", callback_data="upload_file")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            process_message.strip(),
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        # Delete loading message if it exists
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=loading_message.message_id
            )
        except:
            pass
            
        logger.error("Process command error", error=str(e), user_id=user_id)
        await update.message.reply_text(
            "❌ Error processing documents. Please try again."
        )


async def handle_process_document(update: Update, context: ContextTypes.DEFAULT_TYPE, doc_id: str) -> None:
    """Handle processing a specific document."""
    user_id = update.effective_user.id
    
    loading_message = await update.message.reply_text(f"⚙️ Processing document {doc_id}...")
    
    try:
        result = await backend_client.process_document(user_id, doc_id)
        
        # Delete loading message
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=loading_message.message_id
        )
        
        if not result or "error" in result:
            error_msg = result.get("error", "Unknown error") if result else "Processing failed"
            await update.message.reply_text(
                f"❌ **Processing Failed**\n\n"
                f"Document {doc_id}: {error_msg}"
            )
            return
        
        # Format processing results
        doc_name = result.get("document_name", doc_id)
        status = result.get("status", "processed")
        
        await update.message.reply_text(
            f"✅ **Document Processed**\n\n"
            f"📄 **Document:** {doc_name}\n"
            f"✅ **Status:** {status.title()}\n\n"
            f"The document is now searchable!",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        # Delete loading message if it exists
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=loading_message.message_id
            )
        except:
            pass
            
        logger.error("Process document error", error=str(e), user_id=user_id, doc_id=doc_id)
        await update.message.reply_text(
            f"❌ Error processing document {doc_id}. Please try again."
        )


@require_auth
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command - show system and job status."""
    user_id = update.effective_user.id
    
    # Check if specific job ID was provided
    if context.args:
        job_id = context.args[0]
        await handle_job_status(update, context, job_id)
        return
    
    # Show general system status
    try:
        system_status = await backend_client.get_system_status()
        user_status = await backend_client.get_user_status(user_id)
        
        # Format system status
        backend_status = "✅ Online" if system_status.get("backend", False) else "❌ Offline"
        api_status = "✅ Connected" if system_status.get("api", False) else "❌ Disconnected"
        
        requests_count = system_status.get("requests", 0)
        avg_response_time = system_status.get("avg_response_time", "N/A")
        
        # Format user status
        connected_sources = user_status.get("connected_sources", 0)
        indexed_documents = user_status.get("indexed_documents", 0)
        storage_used = user_status.get("storage_used", "0 MB")
        active_jobs = user_status.get("active_jobs", 0)
        
        status_message = f"""
📊 **System Status**

**🖥️ Backend Services:**
• Backend API: {backend_status}
• External APIs: {api_status}
• Requests Today: {requests_count}
• Avg Response: {avg_response_time}ms

**👤 Your Account:**
• Connected Sources: {connected_sources}
• Indexed Documents: {indexed_documents}
• Storage Used: {storage_used}
• Active Jobs: {active_jobs}

**🕐 Last Updated:** {system_status.get('timestamp', 'Unknown')}
        """
        
        # Add quick actions
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh_status"),
                InlineKeyboardButton("📊 Detailed Stats", callback_data="detailed_stats")
            ],
            [
                InlineKeyboardButton("🔗 Check Sources", callback_data="check_sources"),
                InlineKeyboardButton("📋 View Jobs", callback_data="view_jobs")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            status_message.strip(),
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error("Status command error", error=str(e), user_id=user_id)
        
        # Fallback status message
        fallback_message = """
📊 **System Status** ⚠️

❌ **Unable to fetch complete status**

**Basic Status:**
• Bot: ✅ Online
• Your Session: ✅ Active
• Last Command: Just now

Please try again or contact support if issues persist.
        """
        
        await update.message.reply_text(
            fallback_message.strip(),
            parse_mode="Markdown"
        )


async def handle_job_status(update: Update, context: ContextTypes.DEFAULT_TYPE, job_id: str) -> None:
    """Handle checking status of a specific job."""
    user_id = update.effective_user.id
    
    try:
        job_status = await backend_client.get_job_status(user_id, job_id)
        
        if not job_status or "error" in job_status:
            error_msg = job_status.get("error", "Job not found") if job_status else "Status unavailable"
            await update.message.reply_text(
                f"❌ **Job Status Error**\n\n"
                f"Job {job_id}: {error_msg}"
            )
            return
        
        # Format job status
        job_name = job_status.get("name", job_id)
        status = job_status.get("status", "unknown")
        progress = job_status.get("progress", 0)
        started_at = job_status.get("started_at", "Unknown")
        estimated_completion = job_status.get("estimated_completion", "Unknown")
        
        # Status emoji
        status_emoji = {
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
            "queued": "⏳",
            "cancelled": "⏹️"
        }.get(status.lower(), "❓")
        
        job_message = f"""
📋 **Job Status**

**🆔 Job ID:** `{job_id}`
**📝 Name:** {job_name}
**{status_emoji} Status:** {status.title()}
**📊 Progress:** {progress}%
**⏰ Started:** {started_at}
**🎯 ETA:** {estimated_completion}
        """
        
        # Add progress bar if running
        if status.lower() == "running" and progress > 0:
            progress_bar = "█" * (progress // 10) + "░" * (10 - progress // 10)
            job_message += f"\n**Progress Bar:** `{progress_bar}` {progress}%"
        
        # Add error details if failed
        if status.lower() == "failed":
            error_details = job_status.get("error", "No details available")
            job_message += f"\n\n**❌ Error:** {error_details}"
        
        await update.message.reply_text(
            job_message.strip(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error("Job status error", error=str(e), user_id=user_id, job_id=job_id)
        await update.message.reply_text(
            f"❌ Error checking job {job_id}. Please try again."
        )


@require_admin
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin commands."""
    if not context.args:
        await update.message.reply_text(
            "🔧 **Admin Commands**\n\n"
            "`/admin stats` - Show system statistics\n"
            "`/admin users` - List authorized users\n"
            "`/admin add_user <user_id>` - Add user to whitelist\n"
            "`/admin remove_user <user_id>` - Remove user from whitelist\n"
            "`/admin backend <url>` - Update backend URL",
            parse_mode="Markdown"
        )
        return
    
    subcommand = context.args[0].lower()
    
    if subcommand == "stats":
        await show_admin_stats(update, context)
    elif subcommand == "users":
        await show_admin_users(update, context)
    elif subcommand == "add_user" and len(context.args) > 1:
        await add_user_admin(update, context, int(context.args[1]))
    elif subcommand == "remove_user" and len(context.args) > 1:
        await remove_user_admin(update, context, int(context.args[1]))
    else:
        await update.message.reply_text("❌ Invalid admin command. Use `/admin` for help.")


async def show_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show system statistics."""
    # This would typically fetch real stats from backend/storage
    stats_text = """
📊 **System Statistics**

**Users:**
• Authorized: 5
• Active (24h): 3
• Total Commands: 127

**Backend:**
• Status: ✅ Online
• Response Time: 245ms
• Last Sync: 2 minutes ago

**Storage:**
• Documents Indexed: 1,247
• Storage Used: 2.3 GB
• Active Jobs: 2
    """
    
    await update.message.reply_text(stats_text, parse_mode="Markdown")


async def show_admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show authorized users."""
    from ..auth import auth_manager
    
    users_text = "👥 **Authorized Users**\n\n"
    for user_id in auth_manager.allowed_users:
        is_admin = "👑" if user_id in auth_manager.admin_users else "👤"
        users_text += f"{is_admin} `{user_id}`\n"
    
    await update.message.reply_text(users_text, parse_mode="Markdown")


async def add_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    """Add user to whitelist."""
    from ..auth import auth_manager
    
    if auth_manager.add_user(user_id):
        await update.message.reply_text(f"✅ User `{user_id}` added to whitelist.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"ℹ️ User `{user_id}` already in whitelist.", parse_mode="Markdown")


async def remove_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    """Remove user from whitelist."""
    from ..auth import auth_manager
    
    if auth_manager.remove_user(user_id):
        await update.message.reply_text(f"✅ User `{user_id}` removed from whitelist.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ Cannot remove user `{user_id}` (not found or admin).", parse_mode="Markdown")
