"""Coordinate-based gatherable node definitions.

Add trees, rocks and ore veins here without touching any ``.tmx`` file.
Each :class:`GatherableNodeDef` entry becomes a live node at registry
load time. The :class:`src.core.game.Game` calls
:func:`load_gatherable_node_defs` once at startup and matches each def
to its map at runtime.

Gathering is now driven entirely by the ``is_wood_gatherable`` /
``is_stone_gatherable`` / ``is_ore_gatherable`` tile properties placed
on the ``.tmx`` files -- the coordinate-based nodes have been removed.
This list is kept so the loading infrastructure keeps working, but
nothing is registered at startup.
"""

from src.world.gatherable_nodes import GatherableNodeDef


GATHERABLE_NODE_DEFS: list[GatherableNodeDef] = [
    # Intentionally empty. Wood / stone / ore are gathered from tiles
    # tagged with the is_*_gatherable custom properties in the .tmx.
]


def load_gatherable_node_defs():
    """Return the list of :class:`GatherableNodeDef` instances.

    Exposed as a function (rather than a bare import) so the
    definition list can be replaced or extended by tests, modding
    support, or save data in future.
    """
    return list(GATHERABLE_NODE_DEFS)
