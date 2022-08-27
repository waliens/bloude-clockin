# Guild-ClockIn

## Help

Help command displaying and explaing available commands. The help will only display admin commands if launched by an admin in private mode. To launch command publicly, use the `public` parameter.

```
/help [public?] 
```

## Characters management

A set of commands for managing the list of player characters. Only admin can manage characters on behalf of other players (see `@for_user` parameter). A character has a name, a role (e.g. healer, tank), a class (e.g. druid, warrior). Each player can only have on main character.
```
/character create name role class [@for_user] [is_main?]
/character update name [@for_user] [role] [class] [is_main?] [new_name] 
/character delete name [@for_user] 
/characters [@for_user] [public?]
```

## Attendance

A set of commands for registering raid attendance. Only admin can manage attendances on behalf of other players (see `@for_user` parameter).

A player can manually register an attendance at a given date. In this case, he can only register attendance once per reset. By default, commands are applied to the current player's main character at the current time.
```
/presence [character] [when] [@for_user]
```

Attendance can be extracted from different sources to facilitate raid helpers event or raid composition tool:
```
/presence ???
```
It should be possible to update the attendance in case of changes. If a player is not in the composition anymore, he should be unregistered. If a player announces he is not available anymore shortly before the raid begins, it should be registered.

Attendance to a raid can be extracted from Warcraft logs:
```
/presence [logid]
```

## Loot

A set of commands to register loots. Items can be selected by id. Items that are not unique can be registered several time. 
```
/loot register item_id|item_name [character] [@for_user]  
/loot delete item_id [remove_all?] [character] [@for_user]  
/loots [character] [@for_user] [slot] [show_ids?]
```

## Administration
Set the bot locale for the guild.
```
/settings locale en|fr
```

Set the bot cheer message (response to /cheer command):
```
/settings cheer msg
```
