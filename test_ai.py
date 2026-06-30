import asyncio
import config
from scanner.ai_filter import is_opportunity_relevant

async def test():
    print("Testing AI Filter...")
    
    # 1. Resume (Should be NO)
    title1 = "Ищу работу"
    desc1 = "Я junior frontend разработчик, ищу стажировку или работу на полный день."
    res1 = await is_opportunity_relevant(title1, desc1, config.GEMINI_API_KEY)
    print(f"Test 1 (Resume): Expected False, Got {res1}")

    # 2. Irrelevant job (Should be NO)
    title2 = "Требуется копирайтер"
    desc2 = "Нужен копирайтер для написания постов в Instagram на тему криптовалют. Работа постоянная."
    res2 = await is_opportunity_relevant(title2, desc2, config.GEMINI_API_KEY)
    print(f"Test 2 (Copywriter): Expected False, Got {res2}")

    # 3. Relevant gig (Should be YES)
    title3 = "Нужен лендинг на Tilda"
    desc3 = "Требуется сверстать простой одностраничник на тильде для рекламы услуг юриста. Макет есть в фигме."
    res3 = await is_opportunity_relevant(title3, desc3, config.GEMINI_API_KEY)
    print(f"Test 3 (Tilda Gig): Expected True, Got {res3}")

if __name__ == "__main__":
    asyncio.run(test())
