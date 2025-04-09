import os
import asyncio
from adzuna_api import AdzunaClient, CountryCode
from dotenv import load_dotenv


async def main():
    # Charger les variables d'environnement
    load_dotenv()

    # Initialiser le client
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")

    client = AdzunaClient(app_id, app_key)

    try:
        # Rechercher des offres d'emploi
        results = await client.search_jobs(
            country=CountryCode.FR,
            what="python developer",
            where="Paris",
            results_per_page=10,
        )

        # Afficher les résultats
        for job in results.results:
            print(f"Titre: {job.title}")
            print(
                f"Entreprise: {job.company.display_name if job.company else 'Non spécifiée'}"
            )
            print(f"URL: {job.redirect_url}")
            print("-" * 30)

    finally:
        # Fermer le client
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
