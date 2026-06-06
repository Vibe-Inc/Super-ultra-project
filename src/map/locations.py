from src.core.logger import logger

LOCATION_DEFS = {
    "peaceful_forest": {
        "id": "peaceful_forest",
        "name": "Peaceful Forest",
        "maps": ["maps/test-map-1.tmx", "maps/test-map-2.tmx"],
        "connections": ["temple"],
        "entry_map": "maps/test-map-1.tmx",
        "entry_tile": (36, 17),
    },
    "temple": {
        "id": "temple",
        "name": "Temple",
        "maps": ["maps/test-map-3.tmx"],
        "connections": ["peaceful_forest", "cave"],
        "entry_map": "maps/test-map-3.tmx",
        "entry_tile": None,
        "entry_spawn_type": "bottom_center",
    },
    "cave": {
        "id": "cave",
        "name": "Dark Cave",
        "maps": [],
        "connections": ["temple"],
        "entry_map": None,
        "entry_tile": None,
    },
}

LOCATION_SLOTS = [
    "peaceful_forest",
    "temple",
    "cave",
    None,
    None,
    None,
    None,
    None,
]


def get_location_id(map_path):
    for loc_id, loc in LOCATION_DEFS.items():
        if map_path in loc["maps"]:
            return loc_id
    return None


def get_location(loc_id):
    return LOCATION_DEFS.get(loc_id)


def get_connected_locations(loc_id):
    loc = get_location(loc_id)
    if loc:
        return list(loc["connections"])
    return []


def can_travel(from_loc, to_loc):
    if from_loc == to_loc:
        return False
    loc = get_location(from_loc)
    target = get_location(to_loc)
    if loc and to_loc in loc["connections"] and target and target["maps"]:
        return True
    return False
