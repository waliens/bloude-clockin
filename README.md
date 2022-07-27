# Bloude-ClockIn

## Lister ses personnages
Permet de renseigner sa liste de personnages et son main, à faire une fois par personnage pour lequel c'est pertinent. 
Par défaut `@for_user` réfère à utilisateur courant (si pas indiqué à l'appel de la commande). 
**ADMIN** Seuls les admins peuvent lancer la commande pour d'autres users qu'eux.
```
/character add name role class [@for_user] [is_main]
/character delete name [@for_user] 
/character update name [@for_user] [role] [class] [is_main] [new_name] 
/characters [@for_user]
```

## Jetons de présence
À chaque sortie raid "hors-guilde", chaque joueur doit indiquer sa sortie: avec quel personnage (s'il en a renseigné plusieurs, voir ci dessus) et dans quel raid.
Par défaut, le main de l'utilisateur actuel à l'heure indiquée:
```
/presence [character] [when] [@for_user]
```

Cette requête ouvre un formulaire pour sélectionner le raid.

**ADMIN** Générer automatiquement des jetons de présence depuis les raid-helpers. En cas d'absence d'un joueur, mettre à jour le raid helper (déplacer le(s) absent(s) vers le rôle d'absence approprié et ajouter le(s) remplaçant(s) en inscrit(s)), ensuite relancer la commande ci dessous qui fera la différence entre les deux versions de l'event. Les joueurs passés d'inscrits à non-inscrits seront marqués comme 'absent dernière minute':
```
/rh-token id-raidhelper
```

## Renseigner un loot "hors-guilde"
La query permettrait de rentrer un nom partiel de l'item et de choisir dans une liste de matches.
```
/loot (menu sequence: char? > item (par query ou par id)?)
```

## Administration
Renseigner les informations de la google sheet
```
/gsheetkey ...
```

Renseigner quels rôles discord sont admin:
```
/adminrole roles
```
