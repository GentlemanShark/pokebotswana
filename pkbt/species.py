from dataclasses import dataclass

@dataclass(frozen=True)
class SpriteCheck:
    crosshair: tuple[int, int]
    normal_hex: str
    shiny_hex: str | None = None

@dataclass(frozen=True)
class Species:
    wild: SpriteCheck | None = None
    summary: SpriteCheck | None = None
    other_names: list[str] | None = None

SPECIES = {
    "ABRA": Species(
        wild=SpriteCheck(
            crosshair=(178, 39),
            normal_hex="#ffef29"
        )
    ),
    "AERODACTYL": Species(
        wild=SpriteCheck(
            crosshair=(162, 33),
            normal_hex="#cecede"
        )
    ),
    "ALAKAZAM": Species(
        wild=SpriteCheck(
            crosshair=(174, 29),
            normal_hex="#ffef29"
        )
    ),
    "ARBOK": Species(
        wild=SpriteCheck(
            crosshair=(179, 53),
            normal_hex="#bd84ad"
        )
    ),
    "ARCANINE": Species(
        wild=SpriteCheck(
            crosshair=(176, 55),
            normal_hex="#ef7331"
        )
    ),
    "BLASTOISE": Species(
        wild=SpriteCheck(
            crosshair=(183, 59),
            normal_hex="#7394e7"
        )
    ),
    "CATERPIE": Species(
        wild=SpriteCheck(
            crosshair=(174, 56),
            normal_hex="#7b9c63"
        )
    ),
    "CLEFAIRY": Species(
        wild=SpriteCheck(
            crosshair=(183, 44),
            normal_hex="#ad6331"
        )
    ),
    "CLOYSTER": Species(
        wild=SpriteCheck(
            crosshair=(181, 32),
            normal_hex="#ad7bbd"
        )
    ),
    "CROBAT": Species(
        wild=SpriteCheck(
            crosshair=(182, 45),
            normal_hex="#c65ace"
        )
    ),
    "CUBONE": Species(
        wild=SpriteCheck(
            crosshair=(183, 68),
            normal_hex="#946b31"
        )
    ),
    "DEWGONG": Species(
        wild=SpriteCheck(
            crosshair=(166, 48),
            normal_hex="#e7f7ef"
        )
    ),
    "DIGLETT": Species(
        wild=SpriteCheck(
            crosshair=(172, 55),
            normal_hex="#d6394a"
        )
    ),
    "DITTO": Species(
        wild=SpriteCheck(
            crosshair=(173, 59),
            normal_hex="#ef9cd6"
        )
    ),
    "DODUO": Species(
        wild=SpriteCheck(
            crosshair=(175, 45),
            normal_hex="#bd8c52"
        )
    ),
    "DRAGONITE": Species(
        wild=SpriteCheck(
            crosshair=(183, 41),
            normal_hex="#d6b55a"
        )
    ),
    "DROWZEE": Species(
        wild=SpriteCheck(
            crosshair=(169, 55),
            normal_hex="#bd8c52"
        )
    ),
    "EKANS": Species(
        wild=SpriteCheck(
            crosshair=(170, 46),
            normal_hex="#bd73a5"
        )
    ),
    "ELECTRODE": Species(
        wild=SpriteCheck(
            crosshair=(184, 54),
            normal_hex="#e74200"
        )
    ),
    "EXEGGCUTE": Species(
        wild=SpriteCheck(
            crosshair=(175, 53),
            normal_hex="#ffbda5"
        )
    ),
    "EXEGGUTOR": Species(
        wild=SpriteCheck(
            crosshair=(173, 22),
            normal_hex="#9cd64a"
        )
    ),
    "FEAROW": Species(
        wild=SpriteCheck(
            crosshair=(177, 45),
            normal_hex="#ad7352"
        )
    ),
    "GENGAR": Species(
        wild=SpriteCheck(
            crosshair=(178, 39),
            normal_hex="#9c6b84"
        )
    ),
    "GEODUDE": Species(
        wild=SpriteCheck(
            crosshair=(173, 48),
            normal_hex="#adb563"
        )
    ),
    "GLOOM": Species(
        wild=SpriteCheck(
            crosshair=(180, 54),
            normal_hex="#4a5a7b"
        )
    ),
    "GOLBAT": Species(
        wild=SpriteCheck(
            crosshair=(183, 40),
            normal_hex="#6384ce"
        )
    ),
    "GOLDEEN": Species(
        wild=SpriteCheck(
            crosshair=(173, 49),
            normal_hex="#ef7b42"
        )
    ),
    "GOLDUCK": Species(
        wild=SpriteCheck(
            crosshair=(176, 43),
            normal_hex="#7b7bb5"
        ),
        other_names=["GOLDUC☃("]
    ),
    "GRIMER": Species(
        wild=SpriteCheck(
            crosshair=(173, 41),
            normal_hex="#c69cb5"
        )
    ),
    "GROWLITHE": Species(
        wild=SpriteCheck(
            crosshair=(178, 55),
            normal_hex="#c65221"
        )
    ),
    "GYRADOS": Species(
        wild=SpriteCheck(
            crosshair=(165, 31),
            normal_hex="#739ce7"
        )
    ),
    "HERACROSS": Species(
        wild=SpriteCheck(
            crosshair=(173, 54),
            normal_hex="#7b8cde"
        )
    ),
    "HITMONCHAN": Species(
        wild=SpriteCheck(
            crosshair=(186, 39),
            normal_hex="#e76339"
        )
    ),
    "HITMONLEE": Species(
        wild=SpriteCheck(
            crosshair=(173, 36),
            normal_hex="#cea584"
        )
    ),
    "HOPPIP": Species(
        wild=SpriteCheck(
            crosshair=(185, 45),
            normal_hex="#ff6352"
        )
    ),
    "HORSEA": Species(
        wild=SpriteCheck(
            crosshair=(180, 50),
            normal_hex="#8494b5"
        )
    ),
    "HYPNO": Species(
        wild=SpriteCheck(
            crosshair=(167, 30),
            normal_hex="#ffef9c"
        )
    ),
    "JIGGLYPUFF": Species(
        wild=SpriteCheck(
            crosshair=(180, 54),
            normal_hex="#7363de"
        )
    ),
    "JYNX": Species(
        wild=SpriteCheck(
            crosshair=(176, 62),
            normal_hex="#ef4242"
        )
    ),
    "KADABRA": Species(
        wild=SpriteCheck(
            crosshair=(174, 28),
            normal_hex="#ffef29"
        )
    ),
    "KAKUNA": Species(
        wild=SpriteCheck(
            crosshair=(174, 56),
            normal_hex="#8c7b00"
        )
    ),
    "KANGASKHAN": Species(
        wild=SpriteCheck(
            crosshair=(189, 60),
            normal_hex="#9c735a"
        )
    ),
    "KINGDRA": Species(
        wild=SpriteCheck(
            crosshair=(161, 31),
            normal_hex="#9cbdf7"
        )
    ),
    "KOFFING": Species(
        wild=SpriteCheck(
            crosshair=(179, 44),
            normal_hex="#bd7bb5"
        )
    ),
    "KRABBY": Species(
        wild=SpriteCheck(
            crosshair=(172, 58),
            normal_hex="#ef5221"
        )
    ),
    "LAPRAS": Species(
        wild=SpriteCheck(
            crosshair=(165, 58),
            normal_hex="#ffef94"
        )
    ),
    "LARVITAR": Species(
        wild=SpriteCheck(
            crosshair=(176, 50),
            normal_hex="#b5deb5"
        ),
        summary=SpriteCheck(
            crosshair=(59, 66),
            normal_hex="#b5deb5"
        )
    ),
    "MACHAMP": Species(
        wild=SpriteCheck(
            crosshair=(183, 38),
            normal_hex="#add6b5"
        )
    ),
    "MACHOKE": Species(
        wild=SpriteCheck(
            crosshair=(187, 44),
            normal_hex="#ada5d6"
        ),
        other_names=["MACHO♦(E"]
    ),
    "MACHOP": Species(
        wild=SpriteCheck(
            crosshair=(170, 58),
            normal_hex="#a5c6ad"
        )
    ),
    "MAGIKARP": Species(
        wild=SpriteCheck(
            crosshair=(165, 44),
            normal_hex="#ff6b21"
        )
    ),
    "MAGNEMITE": Species(
        wild=SpriteCheck(
            crosshair=(172, 50),
            normal_hex="#94bd9c"
        )
    ),
    "MAGNETON": Species(
        wild=SpriteCheck(
            crosshair=(182, 41),
            normal_hex="#94bd9c"
        )
    ),
    "MANKEY": Species(
        wild=SpriteCheck(
            crosshair=(178, 52),
            normal_hex="#f7deb5"
        )
    ),
    "MAROWAK": Species(
        wild=SpriteCheck(
            crosshair=(187, 52),
            normal_hex="#a57331"
        ),
        other_names=["MAROWA♦("]
    ),
    "MEOWTH": Species(
        wild=SpriteCheck(
            crosshair=(193, 50),
            normal_hex="#ce7b10"
        )
    ),
    "METAPOD": Species(
        wild=SpriteCheck(
            crosshair=(174, 56),
            normal_hex="#9cd64a"
        )
    ),
    "MUK": Species(
        wild=SpriteCheck(
            crosshair=(175, 42),
            normal_hex="#c69cb5"
        )
    ),
    "NATU": Species(
        wild=SpriteCheck(
            crosshair=(173, 62),
            normal_hex="#52c64a"
        )
    ),
    "NIDORAN♀": Species(
        wild=SpriteCheck(
            crosshair=(174, 56),
            normal_hex="#94cebd"
        )
    ),
    "NIDORAN♂": Species(
        wild=SpriteCheck(
            crosshair=(174, 56),
            normal_hex="#63426b"
        )
    ),
    "NIDORINA": Species(
        wild=SpriteCheck(
            crosshair=(172, 52),
            normal_hex="#c6e7ef"
        )
    ),
    "NIDORINO": Species(
        wild=SpriteCheck(
            crosshair=(179, 48),
            normal_hex="#de94ce"
        )
    ),
    "ODDISH": Species(
        wild=SpriteCheck(
            crosshair=(179, 60),
            normal_hex="#4a6b84"
        )
    ),
    "ONIX": Species(
        wild=SpriteCheck(
            crosshair=(174, 47),
            normal_hex="#ded6d6"
        )
    ),
    "PARAS": Species(
        wild=SpriteCheck(
            crosshair=(168, 46),
            normal_hex="#ff7b7b"
        )
    ),
    "PARASECT": Species(
        wild=SpriteCheck(
            crosshair=(183, 40),
            normal_hex="#ef3131"
        )
    ),
    "PERSIAN": Species(
        wild=SpriteCheck(
            crosshair=(183, 39),
            normal_hex="#ffe784"
        )
    ),
    "PHANPY": Species(
        wild=SpriteCheck(
            crosshair=(174, 58),
            normal_hex="#6394c6"
        )
    ),
    "PIDGEOTTO": Species(
        wild=SpriteCheck(
            crosshair=(172, 48),
            normal_hex="#ad7b5a"
        )
    ),
    "PIDGEY": Species(
        wild=SpriteCheck(
            crosshair=(174, 53),
            normal_hex="#ce8c63"
        )
    ),
    "PIKACHU": Species(
        wild=SpriteCheck(
            crosshair=(174, 56),
            normal_hex="#ffef00"
        )
    ),
    "PILOSWINE": Species(
        wild=SpriteCheck(
            crosshair=(170, 50),
            normal_hex="#c6a552"
        )
    ),
    "PONYTA": Species(
        wild=SpriteCheck(
            crosshair=(187, 35),
            normal_hex="#ffe721"
        )
    ),
    "PORYGON": Species(
        summary=SpriteCheck(
            crosshair=(66, 53),
            normal_hex="#ffc6a5"
        )
    ),
    "PRIMEAPE": Species(
        wild=SpriteCheck(
            crosshair=(177, 55),
            normal_hex="#e7bd8c"
        )
    ),
    "PSYDUCK": Species(
        wild=SpriteCheck(
            crosshair=(182, 54),
            normal_hex="#e7a531"
        ),
        other_names=["PSYDUC☃("]
    ),
    "RAPIDASH": Species(
        wild=SpriteCheck(
            crosshair=(195, 16),
            normal_hex="#ffe721"
        )
    ),
    "RATICATE": Species(
        wild=SpriteCheck(
            crosshair=(181, 51),
            normal_hex="#a57b31"
        )
    ),
    "RATTATA": Species(
        wild=SpriteCheck(
            crosshair=(174, 53),
            normal_hex="#b573b5"
        )
    ),
    "RHYHORN": Species(
        wild=SpriteCheck(
            crosshair=(162, 47),
            normal_hex="#bdbdce"
        )
    ),
    "SCYTHER": Species(
        wild=SpriteCheck(
            crosshair=(174, 45),
            normal_hex="#73ad42"
        ),
        summary=SpriteCheck(
            crosshair=(71, 57),
            normal_hex="#9cde4a",
            shiny_hex="#63bd31"
        )
    ),
    "SKARMORY": Species(
        wild=SpriteCheck(
            crosshair=(171, 43),
            normal_hex="#c6c6ce"
        )
    ),
    "SEEL": Species(
        wild=SpriteCheck(
            crosshair=(180, 50),
            normal_hex="#e7e7f7"
        )
    ),
    "SENTRET": Species(
        wild=SpriteCheck(
            crosshair=(176, 61),
            normal_hex="#946b21"
        )
    ),
    "SPEAROW": Species(
        wild=SpriteCheck(
            crosshair=(182, 50),
            normal_hex="#f7525a"
        )
    ),
    "STEELIX": Species(
        wild=SpriteCheck(
            crosshair=(180, 25),
            normal_hex="#849cad"
        )
    ),
    "SUICUNE": Species(
        wild=SpriteCheck(
            crosshair=(164, 25),
            normal_hex="#8c31e7"
        )
    ),
    "SWINUB": Species(
        wild=SpriteCheck(
            crosshair=(178, 60),
            normal_hex="#c6a552"
        )
    ),
    "TANGELA": Species(
        wild=SpriteCheck(
            crosshair=(166, 44),
            normal_hex="#84bdd6"
        )
    ),
    "TENTACOOL": Species(
        wild=SpriteCheck(
            crosshair=(173, 36),
            normal_hex="#6bb5e7"
        )
    ),
    "TYRANITAR": Species(
        wild=SpriteCheck(
            crosshair=(168, 24),
            normal_hex="#a5d6a5"
        )
    ),
    "VENONAT": Species(
        wild=SpriteCheck(
            crosshair=(177, 50),
            normal_hex="#ff7b52"
        )
    ),
    "VOLTORB": Species(
        wild=SpriteCheck(
            crosshair=(175, 45),
            normal_hex="#ff5221"
        )
    ),
    "WEEDLE": Species(
        wild=SpriteCheck(
            crosshair=(174, 56),
            normal_hex="#efad42"
        )
    ),
    "WEEZING": Species(
        wild=SpriteCheck(
            crosshair=(169, 42),
            normal_hex="#d694ad"
        )
    ),
    "WOBBUFFET": Species(
        wild=SpriteCheck(
            crosshair=(174, 49),
            normal_hex="#4a9cbd"
        )
    ),
    "WOOPER": Species(
        wild=SpriteCheck(
            crosshair=(176, 55),
            normal_hex="#8cc6f7"
        )
    ),
    "YANMA": Species(
        wild=SpriteCheck(
            crosshair=(172, 47),
            normal_hex="#ff7b42"
        )
    ),
    "ZUBAT": Species(
        wild=SpriteCheck(
            crosshair=(173, 51),
            normal_hex="#6b8cbd"
        )
    )
}