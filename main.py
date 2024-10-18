from dotenv import load_dotenv
import os
import importlib

# ----------------------------------------------------------------------------------------------------------------------
#
# MAIN - To be used for tests only!
#
# ----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    # Load the .env file
    load_dotenv()

    username = os.getenv("USER")
    password = os.getenv("PASS")
    iccid = os.getenv("ICCID")

    stand_alone = False

    if stand_alone:

        # Importa il modulo 1nce.py da 1nce_account
        module_1nce = importlib.import_module("1nce_account.1nce")

        # Ottieni la classe _1nceCrawler dal modulo importato
        _1nceCrawler = getattr(module_1nce, '_1nceCrawler')

        once = _1nceCrawler(username, password)

        once.get_sim_credit(iccid)

    else:

        # Importa il modulo 1nce.py da 1nce_account
        module_1nce = importlib.import_module("custom_components.1nce._1nce")

        # Ottieni la classe _1nceCrawler dal modulo importato
        _1nce = getattr(module_1nce, '_1nce')

        _1nce_crawler = _1nce(params={
            'iccid': iccid,
            'username': username,
            'password': password
        })
        import asyncio
        asyncio.run(_1nce_crawler.fetch_data())
        import time
        time.sleep(5)
        asyncio.run(_1nce_crawler.fetch_data())





