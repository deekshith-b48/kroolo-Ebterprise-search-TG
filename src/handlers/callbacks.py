"""
Callback handlers for inline keyboard interactions.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..auth import require_auth
from ..storage import conversation_state
from ..backend import backend_client
from ..logging_config import get_logger

logger = get_logger(__name__)


@require_auth
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard button callbacks."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    try:
        if data == "connect":
            await handle_connect_callback(query, context)
        elif data.startswith("connect_"):
            await handle_platform_selection(query, context, data)
        elif data == "search_demo":
            await handle_search_demo(query, context)
        elif data == "help":
            await handle_help_callback(query, context)
        elif data == "settings":
            await handle_settings_callback(query, context)
        elif data == "cancel":
            await handle_cancel_callback(query, context)
        elif data.startswith("fetch_"):
            await handle_fetch_callback(query, context, data)
        elif data.startswith("process_"):
            await handle_process_callback(query, context, data)
        elif data.startswith("check_job_"):
            await handle_check_job_callback(query, context, data)
        elif data == "upload_file":
            await handle_upload_callback(query, context)
        elif data == "refine_search":
            await handle_refine_search_callback(query, context)
        elif data == "get_documents":
            await handle_get_documents_callback(query, context)
        elif data == "summarize_results":
            await handle_summarize_results_callback(query, context)
        elif data == "related_search":
            await handle_related_search_callback(query, context)
        elif data.startswith("demo_search_"):
            await handle_demo_search_callback(query, context, data)
        elif data.startswith("fetch_source_"):
            await handle_fetch_source_callback(query, context, data)
        elif data == "sync_all_sources":
            await handle_sync_all_callback(query, context)
        elif data == "manage_sources":
            await handle_manage_sources_callback(query, context)
        elif data == "refresh_status":
            await handle_refresh_status_callback(query, context)
        elif data == "detailed_stats":
            await handle_detailed_stats_callback(query, context)
        else:
            await query.edit_message_text("❌ Unknown command.")
            
    except Exception as e:
        logger.error("Callback error", error=str(e), user_id=user_id, data=data)
        await query.edit_message_text("❌ An error occurred. Please try again.")


async def handle_connect_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle connect button callback."""
    user_id = query.from_user.id
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
    
    await query.edit_message_text(
        "🔗 **Connect Data Source**\n\n"
        "Choose a platform to connect to your enterprise search:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def handle_platform_selection(query, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
    """Handle platform selection for connection."""
    user_id = query.from_user.id
    platform = data.replace("connect_", "")
    
    platform_names = {
        "drive": "Google Drive",
        "slack": "Slack",
        "notion": "Notion",
        "custom": "Custom URL"
    }
    
    platform_name = platform_names.get(platform, platform)
    
    # Update conversation state
    await conversation_state.set_flow(user_id, "connecting", {"platform": platform})
    
    # Show connecting message
    await query.edit_message_text(
        f"🔄 **Connecting to {platform_name}**\n\n"
        "Please wait while I set up the connection...",
        parse_mode="Markdown"
    )
    
    # Call backend to initiate connection
    try:
        result = await backend_client.connect_platform(user_id, platform)
        
        if result and "error" not in result:
            oauth_url = result.get("oauth_url")
            connection_id = result.get("connection_id")
            
            if oauth_url:
                keyboard = [
                    [InlineKeyboardButton("🔗 Authorize Access", url=oauth_url)],
                    [InlineKeyboardButton("✅ I've Authorized", callback_data=f"auth_complete_{platform}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"🔐 **Authorization Required**\n\n"
                    f"To connect {platform_name}, please:\n"
                    f"1. Click the button below to authorize access\n"
                    f"2. Complete the authorization in your browser\n"
                    f"3. Return here and click 'I've Authorized'\n\n"
                    f"**Connection ID:** `{connection_id}`",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(
                    f"✅ **{platform_name} Connected**\n\n"
                    f"Successfully connected to {platform_name}!\n"
                    f"You can now search and fetch documents from this source.",
                    parse_mode="Markdown"
                )
        else:
            error_msg = result.get("error", "Unknown error") if result else "Connection failed"
            await query.edit_message_text(
                f"❌ **Connection Failed**\n\n"
                f"Failed to connect to {platform_name}: {error_msg}\n\n"
                f"Please try again or contact support.",
                parse_mode="Markdown"
            )
    
    except Exception as e:
        logger.error("Platform connection error", error=str(e), platform=platform, user_id=user_id)
        await query.edit_message_text(
            f"❌ **Connection Error**\n\n"
            f"An error occurred while connecting to {platform_name}.\n"
            f"Please try again later.",
            parse_mode="Markdown"
        )


async def handle_search_demo(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle search demo callback."""
    demo_queries = [
        "quarterly revenue growth",
        "team meeting notes",
        "project documentation",
        "company policies",
        "customer feedback"
    ]
    
    keyboard = []
    for i, demo_query in enumerate(demo_queries):
        keyboard.append([
            InlineKeyboardButton(f"🔍 {demo_query}", callback_data=f"demo_search_{i}")
        ])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔍 **Search Demo**\n\n"
        "Try one of these example searches:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def handle_help_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle help button callback."""
    help_text = """
📖 **Quick Help**

**Basic Commands:**
• `/search <query>` - Search your data
• `/connect` - Link data sources
• `/upload` - Add documents
• `/help` - Full command list

**Tips:**
• Use natural language for searches
• Connect multiple sources for better results
• Upload files in PDF, DOC, or TXT format

Need more help? Use `/help` for detailed instructions.
    """
    
    keyboard = [
        [
            InlineKeyboardButton("🔗 Connect Sources", callback_data="connect"),
            InlineKeyboardButton("🔍 Try Search", callback_data="search_demo")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def handle_settings_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle settings callback."""
    user_id = query.from_user.id
    
    # Get user's connected sources (this would be a real API call)
    settings_text = f"""
⚙️ **Your Settings**

**User ID:** `{user_id}`
**Connected Sources:** 2
• Google Drive ✅
• Slack ✅

**Preferences:**
• Search Results: 10
• Citation Style: Inline
• Auto-sync: Enabled

**Storage Used:** 1.2 GB / 5 GB
    """
    
    keyboard = [
        [
            InlineKeyboardButton("🔗 Manage Sources", callback_data="manage_sources"),
            InlineKeyboardButton("🔄 Sync All", callback_data="sync_all")
        ],
        [
            InlineKeyboardButton("📊 View Stats", callback_data="user_stats"),
            InlineKeyboardButton("❌ Close", callback_data="cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        settings_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def handle_cancel_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle cancel callback."""
    user_id = query.from_user.id
    await conversation_state.clear_state(user_id)
    
    await query.edit_message_text(
        "❌ **Operation Cancelled**\n\n"
        "You can start over anytime using the available commands.",
        parse_mode="Markdown"
    )


async def handle_fetch_callback(query, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
    """Handle document fetch callbacks."""
    user_id = query.from_user.id
    
    if data == "fetch_sources":
        # Show available sources
        try:
            sources = await backend_client.get_sources(user_id)
            if sources and "error" not in sources:
                keyboard = []
                for source in sources.get("sources", []):
                    source_id = source.get("id")
                    source_name = source.get("name")
                    keyboard.append([
                        InlineKeyboardButton(
                            f"📁 {source_name}",
                            callback_data=f"fetch_docs_{source_id}"
                        )
                    ])
                keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    "📁 **Select Source**\n\nChoose a source to browse documents:",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(
                    "❌ No connected sources found. Use `/connect` to add sources first."
                )
        except Exception as e:
            logger.error("Fetch sources error", error=str(e), user_id=user_id)
            await query.edit_message_text("❌ Failed to fetch sources. Please try again.")
    
    elif data.startswith("fetch_docs_"):
        source_id = data.replace("fetch_docs_", "")
        await fetch_documents_from_source(query, context, source_id)


async def fetch_documents_from_source(query, context: ContextTypes.DEFAULT_TYPE, source_id: str) -> None:
    """Fetch and display documents from a specific source."""
    user_id = query.from_user.id
    
    try:
        documents = await backend_client.fetch_documents(user_id, source_id)
        
        if documents and "error" not in documents:
            docs = documents.get("documents", [])
            
            if not docs:
                await query.edit_message_text(
                    "📭 **No Documents Found**\n\n"
                    "This source doesn't contain any documents yet.",
                    parse_mode="Markdown"
                )
                return
            
            # Show first page of documents
            page_size = 5
            total_docs = len(docs)
            page_docs = docs[:page_size]
            
            docs_text = f"📄 **Documents** (showing {len(page_docs)} of {total_docs})\n\n"
            
            keyboard = []
            for doc in page_docs:
                doc_id = doc.get("id")
                doc_name = doc.get("name", "Untitled")
                doc_snippet = doc.get("snippet", "")[:50]
                
                button_text = f"📄 {doc_name}"
                if doc_snippet:
                    button_text += f" - {doc_snippet}..."
                
                keyboard.append([
                    InlineKeyboardButton(
                        button_text,
                        callback_data=f"view_doc_{doc_id}"
                    )
                ])
            
            # Add pagination if needed
            if total_docs > page_size:
                keyboard.append([
                    InlineKeyboardButton("➡️ Next Page", callback_data=f"fetch_page_1_{source_id}")
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="fetch_sources")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                docs_text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            
        else:
            error_msg = documents.get("error", "Unknown error") if documents else "Fetch failed"
            await query.edit_message_text(
                f"❌ **Fetch Failed**\n\n{error_msg}",
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error("Fetch documents error", error=str(e), user_id=user_id, source_id=source_id)
        await query.edit_message_text("❌ Failed to fetch documents. Please try again.")


async def handle_check_job_callback(query, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
    """Handle job status check callback."""
    job_id = data.replace("check_job_", "")
    user_id = query.from_user.id
    
    try:
        job_status = await backend_client.get_job_status(user_id, job_id)
        
        if job_status and "error" not in job_status:
            status = job_status.get("status", "unknown")
            progress = job_status.get("progress", 0)
            
            status_emoji = {
                "running": "🔄",
                "completed": "✅", 
                "failed": "❌",
                "queued": "⏳"
            }.get(status, "❓")
            
            status_text = f"""
📋 **Job Status Update**

🆔 **Job ID:** `{job_id}`
{status_emoji} **Status:** {status.title()}
📊 **Progress:** {progress}%
            """
            
            await query.edit_message_text(status_text.strip(), parse_mode="Markdown")
        else:
            await query.edit_message_text(f"❌ Could not get status for job {job_id}")
    
    except Exception as e:
        logger.error("Check job callback error", error=str(e), job_id=job_id)
        await query.edit_message_text("❌ Error checking job status.")


async def handle_upload_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle upload file callback."""
    user_id = query.from_user.id
    await conversation_state.set_flow(user_id, "upload_file")
    
    await query.edit_message_text(
        "📤 **Upload File**\n\n"
        "Send me a file to upload for indexing.\n\n"
        "**Supported formats:**\n"
        "• PDF, DOC, DOCX, TXT\n"
        "• Images with text\n"
        "• CSV, XLS, JSON\n\n"
        "Send your file now!",
        parse_mode="Markdown"
    )


async def handle_refine_search_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle refine search callback."""
    user_id = query.from_user.id
    await conversation_state.set_flow(user_id, "refine_search")
    
    await query.edit_message_text(
        "🔍 **Refine Your Search**\n\n"
        "Enter a more specific search query to get better results:\n\n"
        "💡 **Tips:**\n"
        "• Be more specific with keywords\n"
        "• Include dates or timeframes\n"
        "• Mention specific topics or categories\n\n"
        "Type your refined search query:",
        parse_mode="Markdown"
    )


async def handle_get_documents_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle get full documents callback."""
    user_id = query.from_user.id
    
    await query.edit_message_text(
        "📥 **Fetching Full Documents**\n\n"
        "Retrieving complete documents from your last search...",
        parse_mode="Markdown"
    )
    
    # This would fetch full documents from the last search
    # For now, show a placeholder message
    await query.edit_message_text(
        "📄 **Full Documents**\n\n"
        "Full document retrieval feature coming soon!\n\n"
        "For now, you can:\n"
        "• Use `/fetch` to browse documents by source\n"
        "• Search for specific document titles\n"
        "• Use more specific search queries",
        parse_mode="Markdown"
    )


async def handle_summarize_results_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle summarize results callback."""
    user_id = query.from_user.id
    
    await query.edit_message_text(
        "📊 **Generating Summary**\n\n"
        "Creating a comprehensive summary of your search results...",
        parse_mode="Markdown"
    )
    
    # This would generate a summary of the last search results
    # For now, show a placeholder message
    await query.edit_message_text(
        "📊 **Search Results Summary**\n\n"
        "Summary generation feature coming soon!\n\n"
        "Current search provided multiple relevant results with citations.\n"
        "Use `/search` with more specific queries for targeted results.",
        parse_mode="Markdown"
    )


async def handle_related_search_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle related search callback."""
    demo_queries = [
        "related documents",
        "similar content", 
        "follow up information",
        "additional context",
        "supplementary materials"
    ]
    
    keyboard = []
    for i, demo_query in enumerate(demo_queries):
        keyboard.append([
            InlineKeyboardButton(f"🔍 {demo_query}", callback_data=f"demo_search_{i}")
        ])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔄 **Related Search Suggestions**\n\n"
        "Try one of these related searches:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def handle_demo_search_callback(query, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
    """Handle demo search callback."""
    search_index = int(data.replace("demo_search_", ""))
    demo_queries = [
        "quarterly revenue growth",
        "team meeting notes",
        "project documentation", 
        "company policies",
        "customer feedback",
        "related documents",
        "similar content",
        "follow up information", 
        "additional context",
        "supplementary materials"
    ]
    
    if search_index < len(demo_queries):
        query_text = demo_queries[search_index]
        user_id = query.from_user.id
        
        await query.edit_message_text(
            f"🔍 **Searching for: \"{query_text}\"**\n\n"
            "Processing your search query...",
            parse_mode="Markdown"
        )
        
        # Simulate search (in real implementation, this would call backend)
        try:
            result = await backend_client.search(user_id, query_text, include_citations=True)
            
            if result and "error" not in result:
                # Format the search response
                from ..handlers.commands import format_search_response
                response_text = await format_search_response(result, query_text)
                
                # Send response (handle long messages)
                if len(response_text) > 4000:
                    response_text = response_text[:4000] + "\n\n... (truncated)"
                
                await query.edit_message_text(
                    response_text,
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
            else:
                await query.edit_message_text(
                    f"🔍 **Demo Search: \"{query_text}\"**\n\n"
                    "No backend connected - this is a demo search.\n\n"
                    "In a real implementation, this would return:\n"
                    "• AI-powered answers\n"
                    "• Source citations\n" 
                    "• Relevant documents\n\n"
                    "Connect your backend to see real results!",
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.error("Demo search error", error=str(e), query=query_text)
            await query.edit_message_text(
                f"❌ Demo search failed for: \"{query_text}\""
            )


async def handle_fetch_source_callback(query, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
    """Handle fetch from specific source callback."""
    source_id = data.replace("fetch_source_", "")
    user_id = query.from_user.id
    
    await query.edit_message_text(
        f"📥 **Fetching from Source**\n\n"
        f"Source ID: `{source_id}`\n"
        f"Status: Retrieving latest data...",
        parse_mode="Markdown"
    )
    
    try:
        result = await backend_client.sync_source(user_id, source_id)
        
        if result and "error" not in result:
            items_count = result.get("items_retrieved", 0)
            status = result.get("sync_status", "completed")
            
            await query.edit_message_text(
                f"✅ **Fetch Complete**\n\n"
                f"📂 **Source:** {source_id}\n"
                f"📊 **Items Retrieved:** {items_count}\n"
                f"✅ **Status:** {status.title()}\n\n"
                f"Data has been synchronized and is ready for search!",
                parse_mode="Markdown"
            )
        else:
            error_msg = result.get("error", "Unknown error") if result else "Fetch failed"
            await query.edit_message_text(
                f"❌ **Fetch Failed**\n\n"
                f"Source: {source_id}\n"
                f"Error: {error_msg}",
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error("Fetch source callback error", error=str(e), source_id=source_id)
        await query.edit_message_text(
            f"❌ Error fetching from source {source_id}"
        )


async def handle_sync_all_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle sync all sources callback."""
    user_id = query.from_user.id
    
    await query.edit_message_text(
        "🔄 **Syncing All Sources**\n\n"
        "Initiating synchronization for all connected sources...",
        parse_mode="Markdown"
    )
    
    try:
        # Get all sources first
        sources_data = await backend_client.get_sources(user_id)
        
        if sources_data and "error" not in sources_data:
            sources = sources_data.get("sources", [])
            
            if not sources:
                await query.edit_message_text(
                    "📂 **No Sources to Sync**\n\n"
                    "You don't have any connected sources.\n"
                    "Use `/connect` to add sources first.",
                    parse_mode="Markdown"
                )
                return
            
            # Sync each source (in a real implementation, this might be batched)
            sync_results = []
            for source in sources:
                if source.get("status") == "active":
                    source_id = source.get("id")
                    result = await backend_client.sync_source(user_id, source_id)
                    sync_results.append({
                        "source": source.get("name", source_id),
                        "success": result and "error" not in result
                    })
            
            # Format results
            success_count = sum(1 for r in sync_results if r["success"])
            total_count = len(sync_results)
            
            results_text = f"""
✅ **Sync Complete**

📊 **Results:** {success_count}/{total_count} sources synced successfully

**Details:**
            """
            
            for result in sync_results:
                status_emoji = "✅" if result["success"] else "❌"
                results_text += f"\n{status_emoji} {result['source']}"
            
            await query.edit_message_text(
                results_text.strip(),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "❌ **Sync Failed**\n\n"
                "Could not retrieve sources list.",
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error("Sync all callback error", error=str(e), user_id=user_id)
        await query.edit_message_text(
            "❌ Error during bulk sync operation."
        )


async def handle_manage_sources_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle manage sources callback."""
    user_id = query.from_user.id
    
    try:
        sources_data = await backend_client.get_sources(user_id)
        
        if sources_data and "error" not in sources_data:
            sources = sources_data.get("sources", [])
            
            if not sources:
                keyboard = [
                    [InlineKeyboardButton("🔗 Connect First Source", callback_data="connect")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    "⚙️ **Manage Sources**\n\n"
                    "No sources connected yet.\n"
                    "Connect your first source to get started!",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
                return
            
            # Create management keyboard
            keyboard = []
            for source in sources[:5]:  # Limit to first 5 sources
                source_name = source.get("name", "Unknown")
                source_id = source.get("id")
                status_emoji = "✅" if source.get("status") == "active" else "❌"
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"{status_emoji} {source_name}",
                        callback_data=f"manage_source_{source_id}"
                    )
                ])
            
            keyboard.append([
                InlineKeyboardButton("🔗 Add New Source", callback_data="connect"),
                InlineKeyboardButton("🔄 Sync All", callback_data="sync_all_sources")
            ])
            keyboard.append([InlineKeyboardButton("❌ Close", callback_data="cancel")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "⚙️ **Manage Sources**\n\n"
                "Select a source to manage or add a new one:",
                parse_mode="Markdown", 
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                "❌ Could not load sources for management."
            )
    except Exception as e:
        logger.error("Manage sources callback error", error=str(e), user_id=user_id)
        await query.edit_message_text(
            "❌ Error loading sources management."
        )


async def handle_refresh_status_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle refresh status callback.""" 
    user_id = query.from_user.id
    
    await query.edit_message_text(
        "🔄 **Refreshing Status**\n\n"
        "Fetching latest system information...",
        parse_mode="Markdown"
    )
    
    try:
        system_status = await backend_client.get_system_status()
        user_status = await backend_client.get_user_status(user_id)
        
        # Format refreshed status
        backend_status = "✅ Online" if system_status.get("backend", False) else "❌ Offline"
        
        status_message = f"""
📊 **System Status** (Refreshed)

**🖥️ Backend:** {backend_status}
**👤 Your Sources:** {user_status.get('connected_sources', 0)}
**📄 Your Documents:** {user_status.get('indexed_documents', 0)}
**🔄 Active Jobs:** {user_status.get('active_jobs', 0)}

**🕐 Last Updated:** Just now
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh Again", callback_data="refresh_status"),
                InlineKeyboardButton("📊 Detailed Stats", callback_data="detailed_stats")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            status_message.strip(),
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error("Refresh status callback error", error=str(e), user_id=user_id)
        await query.edit_message_text(
            "❌ **Status Refresh Failed**\n\n"
            "Could not fetch updated status information.",
            parse_mode="Markdown"
        )


async def handle_detailed_stats_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle detailed stats callback."""
    user_id = query.from_user.id
    
    try:
        system_status = await backend_client.get_system_status()
        user_status = await backend_client.get_user_status(user_id)
        
        # Format detailed statistics
        stats_message = f"""
📊 **Detailed Statistics**

**🖥️ System Performance:**
• API Response Time: {system_status.get('avg_response_time', 'N/A')}ms
• Daily Requests: {system_status.get('requests', 0)}
• Uptime: {system_status.get('uptime', 'Unknown')}

**👤 Your Usage:**
• Connected Sources: {user_status.get('connected_sources', 0)}
• Total Documents: {user_status.get('indexed_documents', 0)}
• Storage Used: {user_status.get('storage_used', '0 MB')}
• Searches Today: {user_status.get('searches_today', 0)}
• Files Uploaded: {user_status.get('files_uploaded', 0)}

**🔄 Recent Activity:**
• Last Search: {user_status.get('last_search', 'Never')}
• Last Upload: {user_status.get('last_upload', 'Never')}
• Last Sync: {user_status.get('last_sync', 'Never')}
        """
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Status", callback_data="refresh_status")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            stats_message.strip(),
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error("Detailed stats callback error", error=str(e), user_id=user_id)
        await query.edit_message_text(
            "❌ Could not load detailed statistics."
        )
