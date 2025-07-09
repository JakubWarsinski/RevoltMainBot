import re
import asyncio
import config as cfg

from typing import List, Optional, Tuple
from utils.change_user_role import change_user_role
from revolt import DMChannel, Member, Message, SendableEmbed, TextChannel, errors as rv_errors

QUESTIONS: List[str] = [
    "How old are you?",
    "Why would you like to join the server?",
    "How did you find out about this server?",
]

MIN_LEN: int = 10
MAX_LEN: int = 200
LEGAL_AGE: int = 18
MAX_RETRIES: int = 3
RETRYABLE_STATUS_CODES = {502, 503, 504}
BACKOFF_BASE: float = 1.5
QUESTION_TIMEOUT: int = 120


def validate_answer(index: int, answer: str) -> Tuple[bool, Optional[str]]:
    txt = answer.strip()

    if index == 0:
        if not txt.isdecimal():
            return False, "Please provide your age as a number (e.g. **23**)."
        if int(txt) < LEGAL_AGE:
            return False, "You must be at least 18 years old to pass the verification."
    else:
        if not MIN_LEN <= len(txt) <= MAX_LEN:
            return (
                False,
                (
                    f"The answer must contain between {MIN_LEN} and {MAX_LEN} characters "
                    f"(currently {len(txt)})."
                ),
            )

    return True, None


async def safe_send(channel: DMChannel, content: str, *, tries: int = MAX_RETRIES):
    for attempt in range(tries):
        try:
            return await channel.send(content)
        except rv_errors.HTTPError as err:
            status = getattr(err, "status", None) or getattr(err, "code", None)
            
            if status in RETRYABLE_STATUS_CODES:
                delay = BACKOFF_BASE ** attempt
                
                print("HTTP %s → retrying in %.2fs", status, delay)
                
                await asyncio.sleep(delay)
                
                continue
            raise 
    raise RuntimeError("safe_send: retry limit exceeded")


async def on_message(message: Message):
    if message.author.bot or not message.content:
        return
    
    author = message.author
    channel = message.channel
    command = message.content.lower()
    
    if message.channel.id == cfg.CHANNEL_IDS["Verification_check"]:
        await message.delete()

    if not command.startswith("/"):
        return

    if command == "/role hidden":
        await message.delete()
        await handle_get_hidden_role(author)
        
        return
    
    if command == "/role artist":
        await message.delete()
        await handle_get_artist_role(author)
        
        return

    if command == "/verify":
        if channel.id != cfg.CHANNEL_IDS["Verification_check"]:
            return
        
        await handle_verify_command(author)
        
        return
    

async def handle_get_hidden_role(user: Member):
    user_roles = {role.name for role in user.roles}

    if user_roles is None or len(user_roles) <= 0:
        return

    if user_roles & {"Hidden", "Unverified"}:
        return

    try:
        await change_user_role(user, ["Hidden"], replace=False)
    except Exception as exc:
        print("Failed to assign Hidden role: %s", exc)


async def handle_get_artist_role(user: Member):
    user_roles = {role.name for role in user.roles}

    if user_roles is None or len(user_roles) <= 0:
        return

    if user_roles & {"Artist", "Unverified"}:
        return

    try:
        await change_user_role(user, ["Artist"], replace=False)
    except Exception as exc:
        print("Failed to assign Artist role: %s", exc)


async def verification_form_exists(user: Member) -> bool:
    channel: TextChannel = cfg.CHANNELS["Verification"]

    try:
        messages = await channel.history(limit=100)
    except Exception as e:
        print(f"Failed to fetch verification history: {e}")
        return False

    for msg in messages:
        if not msg.embeds:
            continue

        embed = msg.embeds[0]

        if re.search(fr"<@!?{user.id}>", embed.description or ""):
            return True

    return False


async def handle_verify_command(user: Member):
    if await verification_form_exists(user):
        verify_message = (
            "﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊\n"
            ":warning: You already have an open request for verification!\n"
            "﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎"
        )

        try:
            dm = await user.open_dm()

            await dm.send(verify_message)
        except rv_errors.RevoltError as ex:
            print("Could not open DM with %s: %s", user, ex)
        
        return
    
    try:
        answers = await ask_questions(user)
        
        if answers is None:
            return

        embed = SendableEmbed(
            title="Verification form",
            description=(
                f"User: <@{user.id}>\n\n" +
                "\n\n".join(f"**{q}**\n{a}" for q, a in zip(QUESTIONS, answers))
            ),
            colour="#00EEFF",
        )

        message = await cfg.CHANNELS["Verification"].send(embed=embed)
        
        await message.add_reaction("✅")
        await message.add_reaction("❌")

    except:
        return
        

async def ask_questions(user: Member) -> Optional[List[str]]:
    try:
        dm: DMChannel = await user.open_dm()
    except rv_errors.RevoltError as ex:
        print("Could not open DM with %s: %s", user, ex)
        
        return

    header = (
        "﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊\n"
        "## Verification form\n\n"
        "You have **2 minutes** to answer each question.\n"
        "Type **`!stop`** at any time to cancel.\n"
    )

    await safe_send(dm, header)

    answers: List[str] = []

    for idx, question in enumerate(QUESTIONS, start=1):
        while True:
            question_text = (
                "﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊\n"
                f"**Question {idx}/{len(QUESTIONS)}**\n"
                f"{question}\n"
                "﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎"
            )

            await safe_send(dm, question_text)

            def check(m: Message):
                return m.author.id == user.id and m.channel.id == dm.id

            try:
                msg: Message = await cfg.CLIENT.wait_for("message", check=check, timeout=QUESTION_TIMEOUT)
            except asyncio.TimeoutError:
                time_up_text = (
                    "﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊\n"
                    "Time’s up (2 minutes).\n"
                    "If you still want to verify, run **`/verify`** on the server again.\n"
                    "﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎"
                )
                
                await safe_send(dm, time_up_text)
                
                return

            content = msg.content.strip()
            
            if content.lower() == "!stop":
                stop_text = (
                    "﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊\n"
                    "Verification **cancelled**.\n"
                    "If you still want to verify, run **`/verify`** on the server again.\n"
                    "﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎"
                )
                
                await safe_send(dm, stop_text)
                
                return

            valid, error_msg = validate_answer(idx - 1, content)
            
            if valid:
                answers.append(content)
                break

            error_text = (
                "﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊\n"
                f":warning: {error_msg}\n"
            )

            await safe_send(dm, error_text)

    finish_text = (
        "﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊﹊\n"
        "Thank you for your responses!\n"
        "Now please wait for the administrators to review your answers.\n"
        "﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎﹎"
    )

    await safe_send(dm, finish_text)

    return answers