from telegram import Update
from telegram.ext import ContextTypes
from scheduler import update_rule
from website_blocker import block_site, unblock_site

# Replace with the numeric ID you received from @userinfobot
ADMIN_CHAT_ID = 8945306032

def is_admin(update: Update) -> bool:
    return update.effective_user.id == ADMIN_CHAT_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    await update.message.reply_text("Agent Online. Send /block <app> or /unblock /blocksite or /unblocksite")

async def block_app(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    if not context.args:
        await update.message.reply_text("Specify an app (e.g., /block discord.exe)")
        return
    
    app_name = context.args[0]
    update_rule(app_name, True)
    await update.message.reply_text(f"🔒 {app_name} is now restricted.")

async def unblock_app(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    if not context.args:
        await update.message.reply_text("Specify an app (e.g., /unblock discord.exe)")
        return
    
    app_name = context.args[0]
    update_rule(app_name, False)
    await update.message.reply_text(f"✅ {app_name} is now unblocked.")

#Website Blocking below here

async def block_website_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    if not context.args:
        await update.message.reply_text("Specify a domain (e.g., /blocksite youtube.com)")
        return
    
    domain = context.args[0]
    # Call the imported function from website_blocker.py here
    block_site(domain) 
    await update.message.reply_text(f"🌐 Website blocked: {domain}")

async def unblock_website_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    if not context.args:
        await update.message.reply_text("Specify a domain (e.g., /unblocksite youtube.com)")
        return
    
    domain = context.args[0]
    # Call the imported function from website_blocker.py here
    unblock_site(domain)
    await update.message.reply_text(f"✅ Website unblocked: {domain}")