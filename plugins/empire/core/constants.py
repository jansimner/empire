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

# Entry types
ENTRY_TYPE_DECISION = "decision"     # Has sacred Why: field, never compressed
ENTRY_TYPE_OBSERVATION = "observation"  # Compresses safely through tiers

EPITHET_KEYWORDS = {
    "the Builder": ["feature", "add", "create", "new", "implement", "build"],
    "the Gatekeeper": ["auth", "security", "permission", "token", "jwt", "csrf", "cors"],
    "the Debugger": ["fix", "bug", "debug", "error", "issue", "patch", "resolve"],
    "the Reformer": ["refactor", "rename", "restructure", "clean", "simplify", "extract"],
    "the Painter": ["ui", "css", "style", "layout", "component", "design", "theme"],
    "the Chronicler": ["database", "migration", "schema", "prisma", "sql", "model"],
    "the Sentinel": ["test", "spec", "assert", "coverage", "vitest", "jest", "playwright"],
    "the Engineer": ["ci", "cd", "deploy", "docker", "pipeline", "infra", "config"],
    "the Ambassador": ["api", "endpoint", "route", "controller", "rest", "graphql"],
    "the Scribe": ["doc", "readme", "comment", "jsdoc", "typedoc"],
    "the Swift": ["performance", "optimize", "cache", "speed", "lazy", "bundle"],
}
