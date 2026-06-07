"""Verify that the petting feature is fully removed and original files parse."""
import os
import sys

ROOT = r"d:\PASHA\Documents\Super-ultra-project"
sys.path.insert(0, ROOT)

errors_found = 0

# 1) Syntax check for all modified files
import ast
for rel in (
    r"src\entities\peaceful_mob.py",
    r"src\entities\peaceful_mob_visuals.py",
    r"src\core\game.py",
):
    path = os.path.join(ROOT, rel)
    try:
        with open(path, "r", encoding="utf-8") as f:
            ast.parse(f.read(), filename=path)
        print(f"OK   {rel} parses")
    except SyntaxError as exc:
        errors_found += 1
        print(f"FAIL {rel}: {exc}")

# 2) Verify the petting feature is GONE
for rel in (
    r"src\entities\peaceful_mob.py",
    r"src\core\game.py",
):
    path = os.path.join(ROOT, rel)
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    # The petting feature added these symbols; none should remain.
    needles = [
        ("pet_cooldown", "pet_cooldown attribute/tick"),
        ("def pet(self)", "PeacefulMob.pet() method"),
        ('"Pet! \u2665"', "'Pet!' floating text"),
        ("_find_nearby_peaceful_mob_for_petting", "Petting helper"),
        ("pygame.K_t", "K_t binding (note: other code may legitimately use K_t)"),
    ]
    for needle, label in needles:
        if needle in src:
            # K_t may legitimately appear elsewhere (e.g. menu open) so we
            # only flag it if the *context* is the petting handler.
            if needle == "pygame.K_t":
                # Look for the actual petting block we added
                if "_find_nearby_peaceful_mob_for_petting" in src or "pet_mob.pet()" in src:
                    errors_found += 1
                    print(f"FAIL {rel} still has the K_t petting handler")
                else:
                    print(f"OK   {rel} has no petting K_t handler (other K_t uses are fine)")
            else:
                errors_found += 1
                print(f"FAIL {rel} still references {label} ({needle!r})")
        else:
            print(f"OK   {rel} no longer has {label}")

# 3) Verify the original Tavern Cat registration is still in place
try:
    from src.entities.peaceful_mob import PEACEFUL_MOB_REGISTRY
    if "tavern_cat" in PEACEFUL_MOB_REGISTRY:
        print("OK   tavern_cat is still registered in PEACEFUL_MOB_REGISTRY")
    else:
        errors_found += 1
        print("FAIL tavern_cat is missing from PEACEFUL_MOB_REGISTRY")
except Exception as exc:
    errors_found += 1
    print(f"ERR  {exc}")

print()
if errors_found:
    print(f"VERIFICATION FAILED: {errors_found} error(s)")
    sys.exit(1)
else:
    print("VERIFICATION PASSED: petting is fully removed, original tavern cat intact.")
