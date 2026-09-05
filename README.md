# KiraKira Python

基于 Python 3.11、uv、NoneBot2 与 OneBot V11 的 QQ Codeforces 机器人。此项目是旧 Java 服务的独立迁移版本；不会修改旧工程、jar、MySQL 表或 NapCat 安装。

## 本地开发

1. 安装 Python 3.11 和 uv。
2. 复制 .env.example 为 .env，并填入本机的 MySQL 凭据与 OneBot token。
3. 执行 uv sync --frozen。
4. 执行 uv run python bot.py。

Windows 上可直接运行 run.bat。

## 配置

.env 仅保存在部署机，绝不可提交。公开仓库仅提供 .env.example。

- KIRAKIRA_ENABLE_SCHEDULER 默认 false。验证数据库读取、命令和一次手动监控前，请保持关闭。
- KIRAKIRA_ADMIN_GROUP_ID 可选；配置后该群管理员可使用 /listall cf。
- 最终切换时，在 NapCat 配置 Reverse WebSocket：ws://127.0.0.1:8080/onebot/v11/ws，并为 Python 生成全新的 access token；将同一 token 写入 .env 的 ONEBOT_ACCESS_TOKEN。

数据库直接复用生产的 group_user、submission 和 problem 表。程序不会运行旧 create.sql，也不会执行 DROP 或 TRUNCATE。

## 命令

- /ping
- /help（也支持 @机器人 /help）
- /bind cf <handle>
- /unbind cf <handle>
- /list cf
- /listall cf（管理员群）

## 质量检查

运行 uv run pytest、uv run ruff check . 与 uv run ruff format --check .。GitHub Actions 使用相同命令。

## 切换顺序

1. 保持旧 Java scheduler 运行，先让 Python scheduler 关闭并完成只读验证。
2. 停止旧 Java scheduler，确认 Python 命令、数据库读取及一次手动监控均正常。
3. 更新 NapCat 的反向 WebSocket 与新 token，再将 KIRAKIRA_ENABLE_SCHEDULER=true。
4. 保留旧 Java 工程作为回退，不删除数据或安装目录。
