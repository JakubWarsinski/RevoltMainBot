import re
import asyncio
import config as cfg

from revolt import errors as rv_errors, Message, User, SendableEmbed
from utils.change_user_role import change_user_role


async def on_raw_reaction_add(payload: dict):
    if payload["user_id"] in cfg.BOT_IDS:
        return

    if payload["channel_id"] != cfg.CHANNEL_IDS["Verification"]:
        return

    emoji = payload["emoji_id"]

    if emoji not in ("✅", "❌"):
        return

    try:
        message: Message = await cfg.CHANNELS["Verification"].fetch_message(payload["id"])
    except rv_errors.RevoltError as err:
        print("Failed to fetch message: %s", err)
        
        return

    msg = message.embeds[0]

    m = re.search(r"<@!?(\w+)>", msg.description or "")
    
    if m:
        target_user_id = m.group(1)

    if not target_user_id:
        return

    target_user: User = cfg.CLIENT.get_user(target_user_id)
    target_user = target_user.to_member(cfg.SERVER)

    if target_user is None:
        return

    if emoji == "✅":
        try:
            dm = await target_user.open_dm()

            await change_user_role(target_user, ["Member"], replace=True)
           
            succed_text = (
                "﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊\n"
                "## Your verification has been **accepted**.\n"
                "Welcome to the server!\n"
                "﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎"
            )

            await dm.send(succed_text)

            try:
                await message.delete()
            except rv_errors.RevoltError:
                pass

            new_user_text = (
                f"User: <@{target_user_id}>\n\n"
                "Has joined to our server!"
            )

            embed = SendableEmbed(
                title="New Member",
                description = (new_user_text),
                colour="#FFEE00",
            )

            await cfg.CHANNELS["Welcome"].send(embed=embed)
        except Exception as exc:
            print("Granting role failed: %s", exc)

        return

    if emoji == "❌":
        moderator = cfg.CLIENT.get_user(payload["user_id"])

        dm = await moderator.open_dm()

        reason_text = (
                "﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊\n"
                "## You have rejected the verification.\n"
                "Write the **reason** below (you have 2 min).\n"
                "﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎"
            )
        
        await dm.send(reason_text)

        def reason_check(m: Message):
            return m.author.id == moderator.id and m.channel.id == dm.id

        try:
            reason = await cfg.CLIENT.wait_for("message", check=reason_check, timeout=120)
        except asyncio.TimeoutError:
            time_up_text = (
                "﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊\n"
                "Time’s up (2 minutes).\n"
                "If you still want to verify, add emoji once again.\n"
                "﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎"
            )

            await dm.send(time_up_text)
            
            return

        if not reason:
            return
        
        user_dm = await target_user.open_dm()

        deined_text = (
                "﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊\n"
                "## Your verification has been denied\n"
                f"**Reason:** {reason.content}\n"
                "﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎"
            )

        await user_dm.send(deined_text)

        try:
            await message.delete()
        except rv_errors.RevoltError:
            pass