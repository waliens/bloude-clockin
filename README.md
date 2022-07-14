# Bloude-ClockIn

## Lister ses personnages
Permet de renseigner sa liste de personnages et son main, à faire une fois par personnage pour lequel c'est pertinent. 
Par défaut `@user` réfère à utilisateur courant (si pas indiqué à l'appel de la commande). Seuls les admins peuvent lancer la commande pour d'autres users.
```
/character add [@user] (menu sequence: character? > class? > role?)
/character delete [@user] (menu sequence: character?) 
/character update [@user] (menu sequence: character? > newname?)
/character main [@user] (menu sequence: character) 
```

**ADMIN** Liste les personnages d'un utilisateur:
```
/characters [@user] (list all characters)
``` 

## Jetons de présence
À chaque sortie raid "hors-guilde", chaque joueur doit indiquer sa sortie: avec quel personnage (s'il en a renseigné plusieurs, voir ci dessus) et dans quel raid
```
/token (menu sequence: character (default: main)? > raid?)
```

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
