from nonebot import get_plugin_config
from pydantic import BaseModel, Field


class Config(BaseModel):
    mysql_host: str
    mysql_port: int = 3306
    mysql_database: str
    mysql_user: str
    mysql_password: str
    onebot_access_token: str = ""
    kirakira_admin_group_id: str = ""
    kirakira_enable_scheduler: bool = False
    codeforces_timeout_seconds: float = Field(default=15.0, gt=0)


def get_config() -> Config:
    return get_plugin_config(Config)
