# DR MULTISERVICES — Bot Telegram

Assistant de présentation, demandes de devis et de rendez-vous.
Basés à Marrakech • Interventions partout au Maroc.

## Installation

Python 3.11 ou supérieur :

```bash
pip install -r requirements.txt
python dr_multiservices_bot.py
```

Définir `TELEGRAM_BOT_TOKEN` dans les secrets de l'hébergeur.
`OPENAI_API_KEY` est facultative : sans elle, menus et formulaires fonctionnent.
`OPENAI_BASE_URL` permet un fournisseur compatible (facultatif).
`OPENAI_MODEL` vaut `gpt-4.1-mini` par défaut. Les appels IA peuvent être facturés
par le fournisseur ; ChatGPT Plus ne les inclut pas.

## Parcours

- `/start`, `/services`, `/contact`, `/urgence` : informations et menu.
- `/devis`, `/rdv` : formulaires accessibles en conversation privée.
- `/cancel` ou `/start` : abandon du formulaire et effacement du brouillon en mémoire.
- Aucun prix standard ni garantie non validée dans le catalogue.
- Les réponses IA suivent la langue du client, sans traduction automatique des menus.
- Les rendez-vous restent des demandes à confirmer par l'équipe.

## Données et exploitation

Les formulaires sont sauvegardés localement en JSON avec remplacement atomique.
Définir `DATA_DIR` sur un volume persistant privé de l'hébergeur ; sinon les demandes
peuvent disparaître à un redéploiement. Les anciens fichiers JSON à la racine restent
compatibles avec la configuration par défaut. Une seule instance doit écrire ces fichiers.
Prévoir sauvegarde et suppression des demandes traitées selon votre durée de conservation.
Aucune notification administrateur n'est activée : l'équipe doit consulter les fichiers
sur l'hébergeur. Une confirmation au client signifie uniquement sauvegarde locale.

Les coordonnées et messages ne sont pas inscrits dans les logs applicatifs. Les questions
libres sont transmises au fournisseur IA configuré ; les réponses des formulaires ne le sont pas.
Les secrets et fichiers clients sont exclus de Git. Ne jamais joindre un vrai fichier client
à une issue ou une pull request publique.

**Action nécessaire :** des identifiants ont été présents dans l'ancien `render.yaml` public.
Révoquer le jeton avec BotFather et la clé chez son fournisseur, puis renseigner les nouveaux
secrets sur l'hébergeur. Leur suppression du fichier ne les efface pas de l'historique Git.
Ne pas réutiliser ces identifiants.

## Tests hors ligne

```bash
python -m unittest discover -s tests -v
```

Aucun message Telegram ni appel IA réel n'est émis par ces tests.
