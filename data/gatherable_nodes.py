"""Coordinate-based gatherable node definitions.

Add trees, rocks and ore veins here without touching any ``.tmx`` file.
Each :class:`GatherableNodeDef` entry becomes a live node at registry
load time. The :class:`src.core.game.Game` calls
:func:`load_gatherable_node_defs` once at startup and matches each def
to its map at runtime.

Field reference
---------------

``map_path``  -- path of the ``.tmx`` file the node lives on.
                 Must match the ``current_map_path`` strings used in
                 ``src/core/game.py`` (e.g. ``"maps/test-map-1.tmx"``).

``gather_type`` -- resource the node produces. One of:
                   * ``"wood"``  -> drops ``wood``  (chop with an axe)
                   * ``"stone"`` -> drops ``stone`` (mine with a pickaxe)
                   * ``"ore"``   -> drops ``iron_ore`` (crack with a hammer)

``x``, ``y``  -- world-space pixel position (center of the node). Use
                 a 32x32 tile size as a rough guide: tile (col, row)
                 corresponds to pixel (col*32 + 16, row*32 + 16).

``yield_item_id`` -- optional override for the dropped item id. When
                     empty the registry uses a sensible default for
                     the gather type (see
                     :func:`src.world.gatherable_nodes._default_yield_for`).

``hit_radius``  -- optional pixel radius for "is the player close
                   enough to gather". Default 64 (about 2 tiles).

``respawn_time`` -- optional seconds before the node reappears after a
                    successful gather. Default 12.

``image_path``  -- optional path to a sprite. When empty, a sensible
                   fallback is chosen from
                   :data:`src.world.gatherable_nodes.DEFAULT_SPRITE_PATHS`.

Examples
--------

The block below is a working example — a tree to the east of the
player's default spawn on test-map-1. Commented-out samples for a
rock and an ore vein follow.

The player spawns at pixel (960, 540) on ``maps/test-map-1.tmx``;
each tile is 32x32 so tile (col, row) = (col*32+16, row*32+16).
"""

from src.world.gatherable_nodes import GatherableNodeDef


GATHERABLE_NODE_DEFS = [
    # --- A tree near the player spawn (will be hidden by the
    #     instructions comment in ideas.md; remove this line if you
    #     want to start with an empty world). ---
    GatherableNodeDef(
        map_path="maps/test-map-1.tmx",
        gather_type="wood",
        x=1216,   # tile (38, 0) + 16
        y=400,    # tile (38, 12) + 16
        hit_radius=72,
        respawn_time=15.0,
    ),

    # --- A small cluster of trees further east on test-map-1. ---
    GatherableNodeDef(
        map_path="maps/test-map-1.tmx",
        gather_type="wood",
        x=1600,
        y=480,
        hit_radius=72,
    ),
    GatherableNodeDef(
        map_path="maps/test-map-1.tmx",
        gather_type="wood",
        x=1728,
        y=384,
        hit_radius=72,
    ),

    # --- A couple of rocks south of spawn. ---
    GatherableNodeDef(
        map_path="maps/test-map-1.tmx",
        gather_type="stone",
        x=1024,
        y=864,
        hit_radius=64,
    ),
    GatherableNodeDef(
        map_path="maps/test-map-1.tmx",
        gather_type="stone",
        x=1408,
        y=896,
        hit_radius=64,
    ),

    # --- An ore vein deeper into the map. ---
    GatherableNodeDef(
        map_path="maps/test-map-1.tmx",
        gather_type="ore",
        x=1856,
        y=1024,
        hit_radius=64,
        respawn_time=20.0,
    ),

    # --- A second-map example. Uncomment to use once the player can
    #     reach ``maps/test-map-2.tmx``. ---
    # GatherableNodeDef(
    #     map_path="maps/test-map-2.tmx",
    #     gather_type="wood",
    #     x=512,
    #     y=512,
    # ),
    # GatherableNodeDef(
    #     map_path="maps/test-map-2.tmx",
    #     gather_type="ore",
    #     x=960,
    #     y=704,
    #     respawn_time=20.0,
    # ),
]


def load_gatherable_node_defs():
    """Return the list of :class:`GatherableNodeDef` instances.

    Exposed as a function (rather than a bare import) so the
    definition list can be replaced or extended by tests, modding
    support, or save data in future.
    """
    return list(GATHERABLE_NODE_DEFS)
