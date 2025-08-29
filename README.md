## ULand 2D Light

<code><a href="https://github.com/umarurize/ULand_2D_Light"><img height="25" src="https://github.com/umarurize/ULand_2D_Light/blob/master/logo/ULand.png" alt="ULand 2D Light" /></a>&nbsp;ULand 2D Light</code>

![Total Git clones](https://img.shields.io/badge/dynamic/json?label=Total%20Git%20clones&query=$&url=https://cdn.jsdelivr.net/gh/umarurize/ULand_2D_Light@master/clone_count.txt&color=brightgreen)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/umarurize/ULand_2D_Light/total)

### :bell:Introductions
<details>
<summary>Rich features</summary>
    
- [x] Claim a land
- [x] Query a land
- [x] Rename a land
- [x] Sell a land
- [x] Teleport to a land
- [x] Transfer ownership of a land
- [x] Add/remove a member for a land
- [x] Update teleport point for a land
- [x] Edit/update security settings for a land
- [x] Public lands
- [x] Manage a land (Operatores)

</details>

<details>
<summary>Ultra protection</summary>
    
- [x] Make the land public
- [x] Can thunder spawn in the land?
- [x] Can explosions spawn in the land?
- [x] Can strangers place blocks in the land?
- [x] Can strangers break blocks in the land?
- [x] Can strangers left click blocks in the land?
- [x] Can strangers right click blocks in the land?
- [x] Can strangers right click entities in the land?
- [x] Can strangers damage players or entities in the land?
- [x] Can fire damage players or entities in the land?
- [x] Can poison effect be applied to players or entities in the land?
- [x] Can wither effect be applied to players or entities in the land?
- [x] Can wither enter the land? 

</details>

* **Full GUI support**
* **Hot reload support:**
* **Localized languages support**

### :hammer:Installation
<details>
<summary>Check your Endstone's version</summary>
    
*  **Endstone 0.10.0+**
   *   250827
*  **Endstone 0.6.0 - Endstone 0.9.4**
    *  250406
    *  250221 
*  **Endstone 0.5.6 - Endstone 0.5.7.1**
    *  250127
    *  250113
    *  250110

</details>

[Required pre-plugin] [UMoney](https://github.com/umarurize/UMoney)

[Optional pre-plugin] ZX_UI

Put `.whl` file into the endstone plugins folder, and then start the server. Enter the command `/utp` to call out the main form.

### :computer:Download
Now, you can get the release version form this repo or <code><a href="https://www.minebbs.com/resources/uland-2d-light-gui.9967/"><img height="20" src="https://github.com/umarurize/umaru-cdn/blob/main/images/minebbs.png" alt="Minebbs" /></a>&nbsp;Minebbs</code>.

### :file_folder:File structure
```
Plugins/
├─ uland/
│  ├─ config.json
│  ├─ land.json
│  ├─ lang/
│  │  ├─ zh_CN.json
│  │  ├─ en_US.json
```

### :pencil:Configuration
ULand allows operators or players to edit/update relevant settings through GUI forms with ease, here are just simple explanations for relevant configurations.

`config.json`
```json5
{
    "max_land_num_can_per_player_has": 5,
    "create_a_new_land_time_limit": 60,
    "max_area_can_per_land_achieve": 10000,
    "price_for_per_square_block": 10,
    "selling_price_for_per_square_block": 5
}
```

`land.json` (for example)
```json5
{
    "TheDeerInDream": {
        "f9f713237a66930c85cf74ced9d50ed1b2f8f004a29f628ff61aedf65b360d24": {
            "name": "TheDeerInDream's land",
            "creation_datetime": "2025-01-16",
            "price": 61250,
            "dim": "Overworld",
            "posa": [
                -4759,
                -5514
            ],
            "posb": [
                -4661,
                -5639
            ],
            "area": 12250,
            "tp_pos": [
                -4704,
                127,
                -5570
            ],
            "members": [
                "umaru rize",
                "SoleWool4183955"
            ],
            "security_settings": {
                "is_land_public": false,
                "can_thunder_spawn": false,
                "can_explosion_spawn": false,
                "can_stranger_place_block": false,
                "can_stranger_break_block": false,
                "can_stranger_left_click_block": false,
                "can_stranger_right_click_block": false,
                "can_stranger_right_click_entity": false,
                "can_stranger_damage_player_or_entity": false,
                "can_fire_damage_player_or_entity": false,
                "can_poison_effect_applied_to_player_or_entity": false,
                "can_wither_effect_applied_to_player_or_entity": false,
                "can_wither_enter_land": false
            }
}
```

### :globe_with_meridians:Languages
- [x] `zh_CN`
- [x] `en_US`

Off course you can add your mother language to ULand, just creat `XX_XX.json` (such as `ja_JP.json`) and translate value with reference to `en_US.json`.

You can also creat a PR to this repo to make your mother language one of the official languages of ULand.

### :camera:Screenshots
You can view related screenshots of ULand from images folder of this repo.

### :fire:Operation document
you can go to the operation document folder of this repo to learn how to use ULand.

<div style="width: 100%; text-align: center;">
  <img src="https://github.com/umarurize/ULand_2D_Light/blob/master/logo/ULand2.png" style="max-width: 100%; height: auto;">
</div>

![](https://img.shields.io/badge/language-python-blue.svg) [![GitHub License](https://img.shields.io/github/license/umarurize/UTP)](LICENSE)


