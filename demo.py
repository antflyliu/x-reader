import asyncio
from x_reader.reader import UniversalReader
from dotenv import load_dotenv

load_dotenv()

async def main():
    # twitter_url = "https://x.com/shao__meng/status/2025864146466529519"
    # twitter_url = "https://x.com/DavisNc9527/status/2022609806041751959"
    twitter_url = "https://x.com/BlockBeatsAsia/status/2026226771410960764"
    
    
    # twitter_url = "https://www.channelbiz.fr/2025/06/19/rag-open-source-souverain-une-alternative-francaise-pour-securiser-lia/"
    # twitter_url = "https://hackernoon.com/rag-a-data-problem-disguised-as-ai"
    
    # twitter_url = "https://tqzbqjcnfhg.feishu.cn/docx/ItKddfwIgo0tHHx0yGdc5HaGn7d" # 飞书文档内容采集不全
    
    # 微信公众号内容采集
    # twitter_url = "https://mp.weixin.qq.com/s/XZ6obaWrsSxaEWzlRkANpg"
    # twitter_url = "https://mp.weixin.qq.com/s?__biz=MzkwNDExODE4Nw==&mid=2247492204&idx=1&sn=85fbf11d99db11ca6f37c5f0aab77391&scene=142&poc_token=HFlFnWmjf7GjY5Skp1DCRGqTpcL0FOlOotHeuz4w"
    # twitter_url = "https://mp.weixin.qq.com/s/D98rfJX1NZmAD4xxs1h-Xg?scene=1"
    
    # twitter_url = "https://www.citriniresearch.com/p/2028gic"
    
    
    reader = UniversalReader()
    content = await reader.read(twitter_url)
    print(content.title)
    # print(content.content)

asyncio.run(main())