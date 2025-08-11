"""
Message handlers for natural language queries and general text processing.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..auth import require_auth
from ..storage import conversation_state
from ..backend import backend_client
from ..logging_config import get_logger
from .commands import format_search_response, split_long_message

logger = get_logger(__name__)


@require_auth
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle natural language text messages as search queries."""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Skip if it's a command
    if text.startswith('/'):
        return
    
    # Check if user is in a specific conversation flow
    current_flow = await conversation_state.get_flow(user_id)
    
    if current_flow == "refine_search":
        await handle_refined_search(update, context, text)
        return
    elif current_flow == "upload_file":
        # User sent text while in upload flow
        await update.message.reply_text(
            "📤 I'm waiting for a file upload.\n\n"
            "Please send a file, or use `/cancel` to exit upload mode.",
            parse_mode="Markdown"
        )
        return
    elif current_flow:
        # Other conversation flows
        await conversation_state.clear_state(user_id)
    
    # Treat as natural language search query
    await handle_natural_language_search(update, context, text)


async def handle_natural_language_search(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str) -> None:
    """Handle natural language search queries."""
    user_id = update.effective_user.id
    
    # Filter out very short or unclear queries
    if len(query.strip()) < 3:
        await update.message.reply_text(
            "🤔 **Query too short**\n\n"
            "Please provide a more detailed search query.\n\n"
            "**Examples:**\n"
            "• \"Find documents about quarterly sales reports\"\n"
            "• \"Show me meeting notes from last week\"\n"
            "• \"What are our company policies on remote work?\"",
            parse_mode="Markdown"
        )
        return
    
    # Check for common non-search phrases
    non_search_phrases = [
        "hello", "hi", "hey", "thanks", "thank you", "ok", "okay", 
        "yes", "no", "sure", "fine", "good", "great", "nice"
    ]
    
    if query.lower().strip() in non_search_phrases:
        await update.message.reply_text(
            "👋 **Hello!**\n\n"
            "I'm here to help you search your enterprise data.\n\n"
            "**Try asking me:**\n"
            "• \"Find documents about project Alpha\"\n"
            "• \"Show me last quarter's sales reports\"\n"
            "• \"What are the latest customer feedback?\"\n\n"
            "Or use `/help` to see all available commands!",
            parse_mode="Markdown"
        )
        return
    
    # Show natural language search indicator
    search_msg = await update.message.reply_text(
        f"🔍 **Searching for:** \"{query}\"\n\n"
        "🤖 Processing your natural language query...",
        parse_mode="Markdown"
    )
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Perform the search
        result = await backend_client.search(user_id, query, include_citations=True)
        
        # Delete the search indicator message
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=search_msg.message_id
        )
        
        if not result or "error" in result:
            error_msg = result.get("error", "Unknown error") if result else "Backend unavailable"
            
            # Provide helpful error message
            await update.message.reply_text(
                f"❌ **Search Error**\n\n"
                f"I couldn't process your query: \"{query[:50]}{'...' if len(query) > 50 else ''}\"\n\n"
                f"**Error:** {error_msg}\n\n"
                f"**Try:**\n"
                f"• Using `/connect` to add data sources\n"
                f"• Uploading documents with `/upload`\n"
                f"• Checking system status with `/status`",
                parse_mode="Markdown"
            )
            return
        
        # Format and send the response
        response_text = await format_search_response(result, query)
        
        # Handle long responses
        if len(response_text) > 4000:
            chunks = split_long_message(response_text)
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await update.message.reply_text(
                        chunk, 
                        parse_mode="Markdown", 
                        disable_web_page_preview=True
                    )
                else:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=chunk,
                        parse_mode="Markdown",
                        disable_web_page_preview=True
                    )
        else:
            await update.message.reply_text(
                response_text, 
                parse_mode="Markdown", 
                disable_web_page_preview=True
            )
        
        # Show quick actions for natural language searches
        
        keyboard = [
            [
                InlineKeyboardButton("🔍 Refine Search", callback_data="refine_search"),
                InlineKeyboardButton("🔄 Related Search", callback_data="related_search")
            ],
            [
                InlineKeyboardButton("📥 Get Documents", callback_data="get_documents"),
                InlineKeyboardButton("📊 Summarize", callback_data="summarize_results")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "**What would you like to do next?**",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
        # Log successful natural language search
        logger.info(
            "Natural language search completed",
            user_id=user_id,
            query=query[:100],
            results_count=len(result.get("results", []))
        )
        
    except Exception as e:
        # Delete search indicator message if it exists
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=search_msg.message_id
            )
        except:
            pass
            
        logger.error("Natural language search error", error=str(e), user_id=user_id, query=query)
        
        await update.message.reply_text(
            "❌ **Search Error**\n\n"
            "I encountered an error while processing your query.\n\n"
            "**Please try:**\n"
            "• Using the `/search` command instead\n"
            "• Being more specific with your query\n"
            "• Checking if your data sources are connected",
            parse_mode="Markdown"
        )


async def handle_refined_search(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str) -> None:
    """Handle refined search queries from the refine search flow."""
    user_id = update.effective_user.id
    
    # Clear the flow state
    await conversation_state.clear_state(user_id)
    
    # Show refined search indicator
    refined_msg = await update.message.reply_text(
        f"🎯 **Refined Search:** \"{query}\"\n\n"
        "Processing your refined query for better results...",
        parse_mode="Markdown"
    )
    
    try:
        # Perform refined search with higher precision
        result = await backend_client.search(
            user_id, 
            query, 
            include_citations=True,
            top_k=15  # Get more results for refined search
        )
        
        # Delete the refined search indicator
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=refined_msg.message_id
        )
        
        if result and "error" not in result:
            response_text = await format_search_response(result, query)
            
            # Add a refined search header
            refined_response = f"🎯 **Refined Search Results**\n\n{response_text}"
            
            # Send the refined results
            if len(refined_response) > 4000:
                chunks = split_long_message(refined_response)
                for chunk in chunks:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=chunk,
                        parse_mode="Markdown",
                        disable_web_page_preview=True
                    )
            else:
                await update.message.reply_text(
                    refined_response,
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
        else:
            error_msg = result.get("error", "No results") if result else "Search failed"
            await update.message.reply_text(
                f"🎯 **Refined Search Results**\n\n"
                f"❌ {error_msg}\n\n"
                f"Try a different approach or check your data sources.",
                parse_mode="Markdown"
            )
            
    except Exception as e:
        # Delete refined search indicator if it exists
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=refined_msg.message_id
            )
        except:
            pass
            
        logger.error("Refined search error", error=str(e), user_id=user_id, query=query)
        await update.message.reply_text(
            "❌ Error processing your refined search. Please try again."
        )


async def handle_conversation_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle ongoing conversation flows and context."""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Get current conversation state
    current_state = await conversation_state.get_state(user_id)
    current_flow = current_state.get("flow") if current_state else None
    
    if not current_flow:
        # No active flow, treat as natural language search
        await handle_natural_language_search(update, context, text)
        return
    
    # Handle specific flows
    if current_flow == "refine_search":
        await handle_refined_search(update, context, text)
    elif current_flow == "upload_file":
        await update.message.reply_text(
            "📤 **Upload Mode Active**\n\n"
            "Please send a file to upload, or use `/cancel` to exit.",
            parse_mode="Markdown"
        )
    elif current_flow == "connect_platform":
        await update.message.reply_text(
            "🔗 **Connection Mode Active**\n\n"
            "Please use the inline buttons to select a platform, or use `/cancel` to exit.",
            parse_mode="Markdown"
        )
    else:
        # Unknown flow, clear it and treat as search
        await conversation_state.clear_state(user_id)
        await handle_natural_language_search(update, context, text)
