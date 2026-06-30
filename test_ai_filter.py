import asyncio
import os
import config
from scanner.ai_filter import is_opportunity_relevant

async def main():
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    res = await is_opportunity_relevant('Нужен сайт', 'Нужен хороший сайт', config.GEMINI_API_KEY)
    print('RESULT:', res)

if __name__ == '__main__':
    asyncio.run(main())
