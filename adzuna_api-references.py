import os
import asyncio
from adzuna_api import AdzunaClient, CountryCode
from dotenv import load_dotenv
from pprint import pprint
import pandas as pd
from collections import defaultdict


async def main():
    # Charger les variables d'environnement
    load_dotenv()

    # Initialiser le client
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")

    client = AdzunaClient(app_id, app_key)

    try:

        def flatten_list_by_shema(L):
            flat_dict = defaultdict(list)

            for l in L:
                for key, value in l.model_dump().items():
                    flat_dict[key].append(value)
            return dict(flat_dict)

        def flat_list_by_shema(L):
            return [(key, value) for el in L for key, value in el.model_dump().items()]

        def save_to_csv(libelle, ref):
            pprint(ref)
            ref_dict = flatten_list_by_shema(ref)
            ref_df = pd.DataFrame(ref_dict)
            pprint(ref_df.head(5))
            ref_df.to_csv(f"./data/adzuna_{libelle}.csv", sep=",")

        categories = await client.get_categories(CountryCode.FR)
        print(len(categories.results))
        save_to_csv("categories", categories.results)
        
        

    finally:
        # Fermer le client
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
