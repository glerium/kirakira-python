from __future__ import annotations

import re

from .status import get_status_message

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.params import CommandArg

from . import database
from .codeforces import CodeforcesError, CodeforcesUserNotFound

HANDLE_RE = re.compile(r"^[A-Za-z0-9_-]+$")
HELP_TEXT = (
    "/status: 查看机器人状态\n"
    "/bind cf [codeforces_id]: 绑定CF账号\n"
    "/unbind cf [codeforces_id]: 解绑CF账号\n"
    "/list cf: 列出自己绑定的CF账号\n"
    "/listall cf: 列出所有人绑定的CF账号\n"
    "/help tsugu: 查看 Tsugu 指令"
)

TSUGU_HELP_TEXT = (
    "Tsugu 指令：\n"
    "玩家：/绑定玩家 [服务器]、/玩家状态、/查玩家 <ID> [服务器]\n"
    "资料：/查卡 <关键词>、/查卡面 <ID>、/查角色 <关键词>、/查活动 <关键词>\n"
    "歌曲：/查曲 <关键词>、/查谱面 <曲目ID> [难度]、/随机曲 <条件>、/查询分数表 <服务器>\n"
    "活动：/查试炼 [活动ID]、/ycx <档位> [活动ID] [服务器]、/ycxall、/lsycx\n"
    "其他：/ycm [关键词]、/抽卡模拟 [次数] [卡池ID]\n"
    "详细用法：/help 查卡、/help ycx、/help 绑定玩家"
)


def parse_cf_arguments(args: str, expected_count: int) -> list[str] | None:
    parts = args.strip().split()
    if len(parts) != expected_count or not parts or parts[0].lower() != "cf":
        return None
    return parts


def valid_handle(handle: str) -> bool:
    return bool(HANDLE_RE.fullmatch(handle))


def is_group_admin(role: str) -> bool:
    return role in {"admin", "owner"}


status_command = on_command("status", priority=10, block=True)
ping = on_command("ping", priority=10, block=True)


@status_command.handle()
async def handle_status(bot: Bot) -> None:
    await status_command.finish(await get_status_message(str(bot.self_id)))


@ping.handle()
async def handle_ping(bot: Bot) -> None:
    await ping.finish(await get_status_message(str(bot.self_id)))


help_command = on_command("help", priority=10, block=True)


@help_command.handle()
async def handle_help(args: Message = CommandArg()) -> None:
    help_arg = args.extract_plain_text().strip().lower()
    if help_arg == "tsugu":
        await help_command.finish(TSUGU_HELP_TEXT)
    if help_arg:
        help_command.skip()
    await help_command.finish(HELP_TEXT)


bind = on_command("bind", priority=10, block=True)


@bind.handle()
async def handle_bind(event: GroupMessageEvent, args: Message = CommandArg()) -> None:
    parsed = parse_cf_arguments(args.extract_plain_text(), 2)
    if parsed is None or not valid_handle(parsed[1]):
        await bind.finish("指令格式错误：/bind cf [codeforces_id]")
    cf_id = parsed[1]
    group_id, user_id = str(event.group_id), str(event.user_id)
    if await database.cf_id_exists_in_group(group_id, cf_id):
        await bind.finish("Codeforces ID 已被绑定")

    from . import get_codeforces_client

    try:
        await get_codeforces_client().get_recent_accepted(cf_id)
    except CodeforcesUserNotFound:
        await bind.finish("Codeforces 用户不存在")
    except CodeforcesError:
        await bind.finish("Codeforces API 暂时不可用，请稍后再试")

    if not await database.add_binding(group_id, user_id, cf_id):
        await bind.finish("Codeforces ID 已被绑定")
    await bind.finish("账号绑定成功")


unbind = on_command("unbind", priority=10, block=True)


@unbind.handle()
async def handle_unbind(event: GroupMessageEvent, args: Message = CommandArg()) -> None:
    parsed = parse_cf_arguments(args.extract_plain_text(), 2)
    if parsed is None:
        await unbind.finish("指令格式错误：/unbind cf [codeforces_id]")
    removed = await database.remove_binding(str(event.group_id), str(event.user_id), parsed[1])
    await unbind.finish("账号解绑成功" if removed else "未找到该绑定")


list_command = on_command("list", priority=10, block=True)


@list_command.handle()
async def handle_list(event: GroupMessageEvent, args: Message = CommandArg()) -> None:
    if parse_cf_arguments(args.extract_plain_text(), 1) is None:
        await list_command.finish("指令格式错误：/list cf")
    ids = await database.get_user_cf_ids(str(event.group_id), str(event.user_id))
    await list_command.finish("暂无绑定账号" if not ids else "\n".join(ids))


listall = on_command("listall", priority=10, block=True)


@listall.handle()
async def handle_listall(event: GroupMessageEvent, args: Message = CommandArg()) -> None:
    if parse_cf_arguments(args.extract_plain_text(), 1) is None:
        await listall.finish("指令格式错误：/listall cf")
    if not is_group_admin(str(event.sender.role)):
        await listall.finish("权限不够，本操作至少需要管理员权限！")
    rows = await database.get_bindings_in_group(str(event.group_id))
    if not rows:
        await listall.finish("暂无绑定账号")
    await listall.finish("\n".join(f"{user_id}: {cf_id}" for user_id, cf_id in rows))
