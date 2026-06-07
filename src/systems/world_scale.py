class WorldScale:
    def __init__(self):
        self.level = 0
        self.xp = 0

    def xp_for_next(self) -> int:
        if self.level >= 60:
            return 0
        if self.level < 55:
            return 50 + self.level * 5
        return 50000 + self.level * 500

    def add_xp(self, amount: int) -> bool:
        needed = self.xp_for_next()
        if needed <= 0:
            return False
        self.xp += amount
        if self.xp >= needed:
            self.xp -= needed
            self.level += 1
            return True
        return False

    def progress(self) -> float:
        needed = self.xp_for_next()
        if needed <= 0:
            return 1.0
        return min(1.0, self.xp / needed)

    def _t(self) -> float:
        return min(1.0, self.level / 55.0)

    def enemy_hp_mult(self) -> float:
        return 1.0 + self._t() * 4.0

    def enemy_damage_mult(self) -> float:
        return 1.0 + self._t() * 4.0

    def enemy_speed_mult(self) -> float:
        return 1.0 + self._t() * 0.4

    def enemy_range_mult(self) -> float:
        return 1.0 + self._t() * 0.3

    def player_damage_mult(self) -> float:
        return 1.0 + self._t() * 4.0

    def player_speed_mult(self) -> float:
        return 1.0 + self._t() * 0.4

    def player_hp_bonus(self) -> int:
        return min(self.level, 55) * 10

    def player_melee_range_mult(self) -> float:
        return 1.0 + self._t() * 0.25

    def player_ranged_range_mult(self) -> float:
        return 1.0 + self._t() * 0.25

    def player_max_stamina_bonus(self) -> int:
        return int(self._t() * 60)

    def player_stamina_cost_mult(self) -> float:
        return 1.0 - self._t() * 0.5

    def player_fast_attack_stun_bonus(self) -> float:
        return self._t() * 0.3

    def player_shockwave_range_mult(self) -> float:
        return 1.0 + self._t() * 1.5

    def player_shockwave_damage_mult(self) -> float:
        return 1.0 + self._t() * 3.0

    def player_parry_window_bonus(self) -> int:
        return int(self._t() * 150)

    def player_block_damage_reduction(self) -> float:
        return 0.6 + self._t() * 0.15

    def has_ability(self, ability: str) -> bool:
        unlocks = {
            'charged_attack': 5,
            'block': 10,
            'parry': 15,
            'shockwave': 35,
            'fast_attack': 45,
            'execute': 55,
        }
        return self.level >= unlocks.get(ability, 999)

    def set_level(self, level: int):
        self.level = max(0, min(60, int(level)))
        self.xp = 0

    def get_milestone_tags(self) -> list[str]:
        tags = []
        if self.level >= 15:
            tags.append('aggressive')
        if self.level >= 35:
            tags.append('empowered')
        if self.level >= 55:
            tags.append('elite')
        return tags
