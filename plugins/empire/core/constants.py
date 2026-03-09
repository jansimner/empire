INITIAL_RULER_NUM = 1  # Default ruler number when dynasty.json is missing/corrupt

VAULT_MAX_LINES = 50
VAULT_PROMOTION_SESSIONS = 3
DEVIANT_NUDGE_SESSIONS = 5
DEVIANT_RESOLVE_SESSIONS = 10
DUSK_LAYER1_MAX = 100
DUSK_LAYER2_MAX = 50
DUSK_LAYER3_MAX = 30

# Simple succession triggers (no weighted formula — transparent and debuggable)
DAY_ENTRY_LIMIT = 30           # Suggest succession when Day exceeds this
SESSIONS_BEFORE_SUCCESSION = 5  # Suggest succession after this many sessions
STALE_RATIO_THRESHOLD = 0.6    # Suggest succession when 60%+ entries have ref score 0

# Reference tracking tiers
REF_TIER1_SCORE = 2   # Exact file path match
REF_TIER2_SCORE = 1   # Directory overlap
REF_TIER3_SCORE = 1   # 2+ keyword matches (single keyword ignored — too noisy)
REF_TIER3_MIN_KEYWORDS = 2  # Minimum keyword overlaps for tier 3

# Roman numerals for ruler names
ROMAN_NUMERALS = {
    1: "I", 2: "II", 3: "III", 4: "IV", 5: "V",
    6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X",
    11: "XI", 12: "XII", 13: "XIII", 14: "XIV", 15: "XV",
    16: "XVI", 17: "XVII", 18: "XVIII", 19: "XIX", 20: "XX",
}


def ruler_name(n: int) -> str:
    return f"Claude {ROMAN_NUMERALS.get(n, n)}"


# Entry types
ENTRY_TYPE_DECISION = "decision"     # Has sacred Why: field, never compressed
ENTRY_TYPE_OBSERVATION = "observation"  # Compresses safely through tiers

EPITHET_KEYWORDS = {
    # Creation & features
    "the Builder": ["feature", "add", "create", "new", "implement", "build", "scaffold"],
    "the Architect": ["architecture", "structure", "pattern", "design", "module", "layer", "abstraction"],
    # Quality & safety
    "the Gatekeeper": ["auth", "security", "permission", "token", "jwt", "csrf", "cors", "encrypt"],
    "the Sentinel": ["test", "spec", "assert", "coverage", "vitest", "jest", "playwright", "mock"],
    "the Debugger": ["fix", "bug", "debug", "error", "issue", "patch", "resolve", "crash"],
    # Code evolution
    "the Reformer": ["refactor", "rename", "restructure", "clean", "simplify", "extract", "deduplicate"],
    "the Surgeon": ["delete", "remove", "prune", "trim", "strip", "deprecate", "drop"],
    # Frontend & design
    "the Painter": ["ui", "css", "style", "layout", "component", "theme", "animation", "responsive"],
    "the Cartographer": ["navigation", "routing", "route", "page", "screen", "menu", "breadcrumb"],
    # Data & persistence
    "the Chronicler": ["database", "migration", "schema", "prisma", "sql", "model", "seed", "orm"],
    "the Alchemist": ["transform", "convert", "parse", "serialize", "format", "encode", "decode"],
    # Infrastructure
    "the Engineer": ["ci", "cd", "deploy", "docker", "pipeline", "infra", "config", "kubernetes"],
    "the Warden": ["monitor", "logging", "alert", "metric", "observability", "healthcheck", "sentry"],
    # API & integration
    "the Ambassador": ["api", "endpoint", "route", "controller", "rest", "graphql", "webhook", "socket"],
    "the Courier": ["email", "notification", "message", "queue", "event", "pubsub", "webhook"],
    # Performance & optimization
    "the Swift": ["performance", "optimize", "cache", "speed", "lazy", "bundle", "compress", "index"],
    # Documentation & communication
    "the Scribe": ["doc", "readme", "comment", "jsdoc", "typedoc", "changelog", "guide"],
    # Data movement
    "the Migrator": ["migrate", "migration", "upgrade", "import", "export", "sync", "transfer"],
    # Accessibility & UX
    "the Steward": ["accessibility", "a11y", "aria", "wcag", "keyboard", "screenreader", "i18n", "l10n"],
    # Payments & business logic
    "the Treasurer": ["payment", "billing", "invoice", "subscription", "price", "stripe", "checkout"],
    # Search & discovery
    "the Seeker": ["search", "filter", "sort", "query", "index", "elasticsearch", "algolia", "find"],
}
