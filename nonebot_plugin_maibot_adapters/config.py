from pydantic import BaseModel


class Config(BaseModel):
    """Plugin Config Here"""
    fastapi_url : str = "http://localhost:8000/api/message"  # 你的FastAPI地址 / 与maimcore的服务器（端口）相同
    platfrom :str = "nonebot-qq"    #如果你不知道这是什么那你就不要动它
    allow_group_list :list[str]  = []     #留空则为不启动QQ端白名单
