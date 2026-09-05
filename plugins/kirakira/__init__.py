from nonebot import get_driver

from . import commands as commands
from . import course_commands as course_commands
from . import course_reminder as course_reminder
from . import monitor as monitor
from .codeforces import CodeforcesClient
from .config import get_config
from .database import close_pool, init_pool

_client: CodeforcesClient | None = None


def get_codeforces_client() -> CodeforcesClient:
    if _client is None:
        raise RuntimeError("Codeforces client is not initialized")
    return _client


driver = get_driver()


@driver.on_startup
async def startup() -> None:
    global _client
    config = get_config()
    await init_pool(config)
    _client = CodeforcesClient(config.codeforces_timeout_seconds)


@driver.on_shutdown
async def shutdown() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None
    await close_pool()
