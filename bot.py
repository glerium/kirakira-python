import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter

nonebot.init(command_start={"/"})
driver = nonebot.get_driver()
driver.register_adapter(OneBotV11Adapter)
nonebot.load_plugins("plugins")
nonebot.load_plugin("nonebot_plugin_tsugu_bangdream_bot")

if __name__ == "__main__":
    nonebot.run()
