from telegram.ext import ApplicationBuilder, CommandHandler
from bot import start, block_app, unblock_app, block_website_cmd, unblock_website_cmd
from blocker import scan_and_kill

async def background_scan(context):
    scan_and_kill()

def main():
    # Paste your @BotFather token inside the quotes
    app = ApplicationBuilder().token("8897261823:AAGaDD31Sd4DdTwKZT066CTki17L-Zqu-Cs").build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("block", block_app))
    app.add_handler(CommandHandler("unblock", unblock_app))

    #Website handlers below
    app.add_handler(CommandHandler("blocksite", block_website_cmd))
    app.add_handler(CommandHandler("unblocksite", unblock_website_cmd))

    app.job_queue.run_repeating(background_scan, interval=5)

    print("System active. Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main()