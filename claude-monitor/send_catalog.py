"""One-shot script: send tool catalog to Discord share channel.

Only sends tools that haven't been notified yet (or have significant updates).
Use --all to force send all shareable tools regardless of history.
"""

import asyncio
import os
import sys

# Set environment variables (same as start.bat)
os.environ.setdefault("CLAUDE_MONITOR_DISCORD_TOKEN", "")
os.environ.setdefault("TOOL_SHARE_CHANNEL_ID", "1486204546370899978")
os.environ.setdefault("TOOL_SHARE_USER_NAME", "かずや")
os.environ.setdefault("TOOL_SHARE_GITHUB_URL", "https://github.com/kazuya0728wa-rgb/claude-tools")

import discord

from config import DISCORD_TOKEN, TOOL_SHARE_CHANNEL_ID, USER_DISPLAY_NAME
from formatter import build_catalog_summary_embed, build_tool_card_embed
from github_pusher import get_tool_github_url, is_tool_shared
from tool_tracker import get_shareable_tools, mark_notified, reload_catalog, should_notify

FORCE_ALL = "--all" in sys.argv


async def main():
    if not DISCORD_TOKEN:
        print("ERROR: CLAUDE_MONITOR_DISCORD_TOKEN not set")
        sys.exit(1)

    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"Logged in as {client.user}")
        channel = client.get_channel(TOOL_SHARE_CHANNEL_ID)
        if not channel:
            print(f"ERROR: Channel {TOOL_SHARE_CHANNEL_ID} not found")
            await client.close()
            return

        reload_catalog()
        shareable = get_shareable_tools()

        # Filter by notification history
        to_send = []
        for tool in shareable:
            if FORCE_ALL:
                tool["notify_reason"] = "新規"
                to_send.append(tool)
            else:
                notify, reason = should_notify(tool["key"])
                if notify:
                    tool["notify_reason"] = reason
                    to_send.append(tool)

        if not to_send:
            print("No new tools to notify.")
            await client.close()
            return

        print(f"Sending: {len(to_send)} tools (of {len(shareable)} shareable)")

        # Summary header
        summary = build_catalog_summary_embed(
            USER_DISPLAY_NAME, len(to_send), len(shareable)
        )
        await channel.send(embed=summary)

        # Individual cards with buttons
        for tool in to_send:
            tool["shared"] = is_tool_shared(tool["key"])
            tool["github_url"] = get_tool_github_url(tool["key"]) or ""
            card = build_tool_card_embed(tool)

            from bot import ToolCardView
            view = ToolCardView(tool["key"])
            await channel.send(embed=card, view=view)
            mark_notified(tool["key"], tool)
            print(f"  Sent: {tool['key']} ({tool['notify_reason']})")

        print("Done! Closing...")
        await client.close()

    await client.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
