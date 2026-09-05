from __future__ import annotations

from nonebot import on_command
from nonebot.adapters.onebot.v11 import GROUP, GroupMessageEvent, Message
from nonebot.params import CommandArg

from . import database
from .commands import is_group_admin
from .course_schedule import load_schedule


def parse_subscription_args(args: str, count: int) -> list[str] | None:
    parts = args.strip().split(maxsplit=count - 1)
    return parts if len(parts) == count else None


subscribe = on_command("subscribe", permission=GROUP, priority=10, block=True)
unsubscribe = on_command("unsubscribe", permission=GROUP, priority=10, block=True)
subscriptions = on_command("subscriptions", permission=GROUP, priority=10, block=True)


async def _require_admin(event: GroupMessageEvent, matcher: object) -> None:
    if not is_group_admin(event.sender.role):
        await matcher.finish("仅群管理员或群主可以修改课程订阅。")


@subscribe.handle()
async def handle_subscribe(event: GroupMessageEvent, args: Message = CommandArg()) -> None:
    await _require_admin(event, subscribe)
    parsed = parse_subscription_args(args.extract_plain_text(), 2)
    if parsed is None:
        await subscribe.finish("用法：/subscribe class all/[老师姓名]")
    subscription_type, target = parsed
    if subscription_type.lower() != "class":
        await subscribe.finish(f"暂不支持订阅类型：{subscription_type}")
    schedule = load_schedule()
    if target.lower() != "all" and target not in schedule.teachers:
        await subscribe.finish(f"未找到教师：{target}")
    outcome = await database.add_class_subscription(str(event.group_id), target)
    messages = {
        "all": "已订阅全部课程。",
        "teacher": f"已订阅教师：{target}。",
        "exists": "该订阅已存在。",
        "covered": f"当前已订阅全部课程，无需单独订阅{target}。",
    }
    await subscribe.finish(messages[outcome])


@unsubscribe.handle()
async def handle_unsubscribe(event: GroupMessageEvent, args: Message = CommandArg()) -> None:
    await _require_admin(event, unsubscribe)
    parsed = parse_subscription_args(args.extract_plain_text(), 2)
    if parsed is None:
        await unsubscribe.finish("用法：/unsubscribe class all/[老师姓名]")
    subscription_type, target = parsed
    if subscription_type.lower() != "class":
        await unsubscribe.finish(f"暂不支持订阅类型：{subscription_type}")
    removed = await database.remove_subscription(str(event.group_id), "class", target)
    await unsubscribe.finish("已取消订阅。" if removed else "未找到该订阅。")


@subscriptions.handle()
async def handle_subscriptions(event: GroupMessageEvent, args: Message = CommandArg()) -> None:
    parsed = args.extract_plain_text().strip().split()
    if len(parsed) != 1:
        await subscriptions.finish("用法：/subscriptions class")
    subscription_type = parsed[0]
    if subscription_type.lower() != "class":
        await subscriptions.finish(f"暂不支持订阅类型：{subscription_type}")
    targets = await database.list_subscriptions(str(event.group_id), "class")
    await subscriptions.finish(
        "当前没有课程订阅。" if not targets else "课程订阅：" + "、".join(targets)
    )
