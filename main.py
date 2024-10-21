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

        from custom_components.once.once import Once

        OnceObj = Once(params={
            'iccid': iccid,
            'username': username,
            'password': password
        })
        import asyncio
        asyncio.run(OnceObj.fetch_data())
        import time
        time.sleep(5)
        asyncio.run(OnceObj.fetch_data())





