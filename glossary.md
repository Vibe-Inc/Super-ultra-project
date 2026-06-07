# Glossary

## Player Stats

| Stat | Description |
|---|---|
| HP (Health Points) | Player health. Starts at 100. When it reaches 0 the player dies and respawns at the spawn point. |
| XP (Experience Points) | Gained from defeating enemies (30-60 per kill). Accumulating enough XP triggers a level up. |
| Level | Increases every 100 XP. Each level grants +20 max HP. |
| Stamina | 100 max. Drained while sprinting (35/s), regenerates at 25/s. Also used for special attacks (charged attack: 30, parry: 50). |
| Mana | 100 max. Used to cast skills. Regenerates at 2.5/s. |
| Defense | Flat damage reduction from equipped armor. Each armor piece contributes via `get_effective_defense()`. |
| Shield | Temporary damage absorption layer that depletes before HP. |
| Speed | Base 200 px/s. Modified by sprint (1.8x), armor penalties, and status effects. |

## Resources

| Resource | Description |
|---|---|
| Gold | Currency used for buying and selling. Starting amount: 100. Earned from enemies (5-20 per kill). |
| Stamina | Used for sprinting and special combat moves. Regenerates over time. |
| Mana | Used for casting magic skills. Regenerates slowly. |

## Combat

| Term | Description |
|---|---|
| Melee Attack | Base attack dealing 15 damage, 65px range, 500ms cooldown. |
| Fast Attack | 0.6x damage, 2x knockback, 0.5s stun. Costs 4 stamina. |
| Charged Attack | Hold mouse button for 500ms. 1.8x damage, 1.3x range. Costs 30 stamina. |
| Block | Right-click to block. Reduces damage by 60%. |
| Parry | Block within 150ms of incoming attack. Costs 50 stamina. |
| Weapon Throw | Throw equipped weapon. 1.5x damage. 2s cooldown. |
| Charge Attack | Hold attack to charge over 500ms. Released as a stronger hit. |
| Combat Styles | Sword (cone arc), Mace (circular AoE), Axe (360 sweep), Spear (piercing line), Dagger (fast multi-strike), War Hammer (heavy slam + AoE stun). |

## Item Types

| Type | Sub-types | Description |
|---|---|---|
| Weapon | Melee, Ranged | Deals damage. Has damage value, durability, cooldown, weapon class, optional on-hit effects. |
| Armor | Helmet, Chestplate, Leggings, Boots, Gloves, Ring, Belt, Charm | Reduces incoming damage via defense value. Has durability. Each piece fits a specific equipment slot. |
| Consumable | Food, Potion | Single-use items that restore HP or apply status effects. Can be right-clicked in inventory. |
| Tool | Fishing rod, Pickaxe, Axe | Used for gathering resources. Has durability, power, gather type, and yield range. |
| Resource | Various | Raw materials used in crafting. Stackable. |
| Fish | Common, Uncommon, Rare, Legendary | Caught via fishing minigame. Has rarity, difficulty, speed, and spawn weight. |
| Misc | Lantern | Utility items. Lantern emits light (200px radius). |

## Armor Slots

| Slot | Description |
|---|---|
| Helmet | Head armor piece. |
| Chestplate | Torso armor piece. |
| Leggings | Leg armor piece. |
| Boots | Foot armor piece. |
| Gloves | Hand armor piece. |
| Ring | Accessory slot. Can hold special rings (Light Ring, Gay Ring). |
| Belt | Waist accessory slot. |
| Charm | Accessory slot for trinkets. |

## Item Tiers

Crafting quality tiers rolled when producing weapons, armor, or tools at the workbench. Probability depends on smelting skill level.

| Tier | Multiplier | Color |
|---|---|---|
| Horrendous | 0.50x | Rust brown |
| Poor | 0.70x | Grey |
| Common | 0.90x | Off-white |
| Fine | 1.00x | Bright white (baseline) |
| Masterwork | 1.20x | Blue |
| Epic | 1.50x | Purple |
| Legendary | 2.00x | Gold |

## Durability

Weapons, armor, and tools have a durability value. Each use (attack, gathering, taking a hit) reduces durability. Below 25% remaining, the item's effectiveness starts to scale down linearly to 50% effectiveness at 0%. Broken items (0 durability) can be repaired. Unbreakable items (marked with infinity) never wear down. Repair restores durability up to the item's max.

## Status Effects

| Effect | Type | Description |
|---|---|---|
| Regeneration | Buff | Restores HP over time. |
| Poison | Debuff | Deals damage over time (poison). |
| Burn | Debuff | Deals fire damage over time. |
| Confusion | Debuff | Inverts movement controls. |
| Dizziness | Debuff | Visual stagger effect. |
| Slow | Debuff | Reduces movement speed. |
| Freeze | Debuff | Completely immobilizes target. |
| Root | Debuff | Immobilizes target (roots). |
| Bleed | Debuff | Deals physical damage over time. |
| Blind | Debuff | Reduces accuracy. |
| Weaken | Debuff | Reduces damage dealt. |
| Curse | Debuff | Increases damage taken, lowers resistances. |
| Lethargy | Debuff | Slows target and increases attack cooldown. |
| Haste | Buff | Reduces attack cooldown, increases speed. |
| Shield | Buff | Absorbs incoming damage. |
| Strength | Buff | Adds flat damage bonus. |
| Radiant Fortitude | Buff | Increases healing received, reduces damage taken. |
| Vampiric Edge | Buff | Heals for a percentage of damage dealt. |
| Keen Insight | Buff | Increases critical hit chance. |
| Momentum | Buff | Temporary damage buff on kill. |

## Skills (Active)

| Skill | Mana | Cooldown | Description |
|---|---|---|---|
| Dash | 0 | 900ms | Quick burst of movement. |
| Fireball | 20 | 1300ms | Launches explosive fireball (28 damage, 110px blast radius, knockback). |
| Flame Shield | 15 | 14000ms | Surrounds player with flames (8 DPS, 110px radius, 6s duration). |
| Frost Nova | 25 | 8000ms | Freezes all enemies in radius for 3s. |
| Ice Armor | 30 | 16000ms | Shield absorbing 30 damage, slows attackers (8s duration). |
| Glacial Cascade | 22 | 3000ms | Ice shards dealing 35 damage, freezing enemies for 2s. |
| Chain Lightning | 18 | 2500ms | Lightning bolt jumping between up to 5 enemies (22 damage each). |
| Thunderstrike | 28 | 4000ms | Calls lightning from above (55 damage in a column). |
| Entangling Roots | 22 | 7000ms | Roots immobilizing enemies for 4s. |
| Summon Spirit | 35 | 12000ms | Summons nature spirit ally (15 damage, 10s duration). |
| Shadow Step | 20 | 6000ms | Teleport through shadows, brief invulnerability. |
| Dark Pact | 25 | 8000ms | Sacrifices 10% HP to deal 60 shadow damage to all nearby enemies. |
| Arcane Missiles | 24 | 4000ms | Fires 5 homing missiles (14 damage each). |
| Mystic Barrier | 25 | 12000ms | Barrier reflecting 30% of incoming damage (5s duration). |
| Berserker's Rage | 30 | 20000ms | +50% damage dealt, +20% damage taken (8s duration). |
| Chrono Shift | 40 | 30000ms | Slows time. +25% attack speed (3s duration). |

## Passives

| Passive | Description |
|---|---|
| Pyromancer's Fury | Fire skills deal +25% damage with +15% area. |
| Static Field | 12% chance to deal 20 lightning damage on hit. |
| Regeneration | Restores 3 HP per second. |
| Poison Blade | Attacks apply poison (6 DPS, 5s duration). |
| Mana Flow | All skill cooldowns reduced by 20%. |

## Keystones

| Keystone | Description |
|---|---|
| Eternal Fortress | +40 max HP, +80% defense, -15% movement speed. |
| Soul Harvest | Killing an enemy restores 5 HP. Each kill stacks +2% damage (8s stack duration). |
| Void Walker | 30% dodge chance. On dodge, teleport and leave an afterimage dealing 18 damage. |
| Elemental Mastery | +35% elemental damage. Using two elements within 3s triggers a combo bonus. |
| Berserker's Rage | Active skill. +50% damage dealt, +20% damage taken for 8s. |
| Chrono Shift | Active skill. Slow time, +25% attack speed for 3s. |

## Weapon Runes (Sockets)

| Rune | Effect |
|---|---|
| Fire Rune | 10% chance to Burn on hit. |
| Ice Rune | 10% chance to Slow on hit. |
| Lightning Rune | 10% chance to Daze on hit. |
| Void Rune | 10% chance to Curse on hit. |

## Crafting

| Term | Description |
|---|---|
| Crafting Grid | 3x3 grid for arranging ingredients to match recipes. |
| Recipe Book | Lists all available crafting recipes. |
| Output Slot | Shows the crafted result when ingredients match a recipe. |
| Smelting Skill | Skill leveled by crafting. Higher level improves tier roll chances. |
| Tempering Minigame | Timing minigame triggered when picking up crafted weapons/armor/tools. Success can upgrade tier. |
| Workbench | Crafting station in the smeltery. |
| Anvil | Repair station for damaged items. |

## Enemies

| Term | Description |
|---|---|
| AI Profile | Behavioral template (e.g., stalker, brute). Determines how the enemy behaves. |
| AI State | Current behavior: idle, patrol, chase, attack. |
| Detection Range | Distance at which the enemy notices the player. |
| Attack Range | Distance at which the enemy initiates an attack. |
| Attack Phases | Wind-up (telegraph start), Telegraph (visual warning), Strike (damage applied). |
| Stun | Temporarily disables enemy movement and interrupts attacks. |
| Contact Damage | Some enemies deal damage just by touching the player. |

## NPCs

| Term | Description |
|---|---|
| NPC (Non-Player Character) | Interactive character in the game world. |
| Interaction Range | 100px. Distance at which the E prompt appears. |
| Merchant | NPC type that opens a trading interface. Has a shop inventory. |
| Dialogue | Lines of text the NPC displays. |

## Map

| Term | Description |
|---|---|
| .tmx File | Tiled map file format. Maps are created in the Tiled editor and loaded at runtime via PyTMX. |
| Collision Layer | Tile layer marking solid obstacles. Parsed by the collision system. |
| Map Transition | Walking to the edge of one map loads the adjacent map. |
| Spawn Points | Per-map coordinates where enemies, NPCs, and the player appear. |

## Controls

| Key | Action |
|---|---|
| WASD / Arrow Keys | Move character. |
| Mouse Left Click | Attack / Interact / Pick up items. |
| Mouse Right Click | Block / Use consumable / Sell item. |
| Mouse Wheel | Scroll hotbar active slot. |
| E | Interact with NPC / Open trading. |
| I | Toggle inventory panel. |
| ESC | Open pause menu. |
| 1-0 | Hotbar slots (select and use). |
| Shift + Click | Quick-move item between inventories. |
| Middle Click | Open split popup for stacked items. |
