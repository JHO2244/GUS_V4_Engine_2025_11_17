from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# L6 – Core Data Structures
# ---------------------------------------------------------------------------

@dataclass
class ReplicationTarget:
    """
    Single logical replication target.

    v0.1 is intentionally minimal:
    - id / name    : logical identifier + human label
    - source       : logical source (e.g. repo root, backup dir)
    - path         : concrete filesystem path for this target
    - enabled      : whether this target is active in the plan
    - meta         : free-form metadata for future extensions
    """
    id: str
    name: str
    source: str
    path: str
    enabled: bool = True
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReplicationPolicy:
    """
    v0.1 policy is Guardian-safe and reversible:
    - frequency="on_demand"  → nothing auto-runs.
    - require_all_green=True → only after full test/pass state.
    - require_clean_git=False → information-only, no hard gate yet.
    """
    frequency: str = "on_demand"
    require_all_green: bool = True
    require_clean_git: bool = False
    max_snapshots: int = 5


@dataclass
class ReplicationManifest:
    """
    Minimal L6 Replication Manifest v0.1

    This is intentionally small and stable:
    - single core target (the repo itself)
    - simple policy, no side effects
    """
    manifest_version: str = "0.1"
    targets: List[ReplicationTarget] = field(
        default_factory=lambda: [
            ReplicationTarget(
                id="core_repo_snapshot",
                name="GUS Core Repository",
                source=".",
                path=".",  # v0.1: source and path are the repo root
            )
        ]
    )
    policy: ReplicationPolicy = field(default_factory=ReplicationPolicy)


@dataclass
class ReplicationPlan:
    """
    Concrete plan derived from the manifest + continuity layer.

    v0.1:
    - manifest_version : copied from manifest
    - targets          : list of ReplicationTarget entries
    - policy           : ReplicationPolicy instance
    - source_backup    : root backup path resolved for this run
    """
    manifest_version: str
    targets: List[ReplicationTarget] = field(default_factory=list)
    policy: ReplicationPolicy = field(default_factory=ReplicationPolicy)
    source_backup: str = ""

    def as_dict(self) -> dict:
        """
        Optional helper for future use; safe, pure structure.
        """
        return {
            "manifest_version": self.manifest_version,
            "targets": [
                {
                    "id": t.id,
                    "name": t.name,
                    "source": t.source,
                    "path": t.path,
                    "enabled": t.enabled,
                    "meta": dict(t.meta),
                }
                for t in self.targets
            ],
            "policy": {
                "frequency": self.policy.frequency,
                "require_all_green": self.policy.require_all_green,
                "require_clean_git": self.policy.require_clean_git,
                "max_snapshots": self.policy.max_snapshots,
            },
            "source_backup": self.source_backup,
        }


# ---------------------------------------------------------------------------
# L6 – Manifest Loader
# ---------------------------------------------------------------------------

def load_manifest() -> ReplicationManifest:
    """
    Minimal loader v0.1 – simply returns the dataclass instance.
    Safe to import from tests and other modules.
    """
    return ReplicationManifest()


# ---------------------------------------------------------------------------
# L6 – Continuity → Replication Bridge
# ---------------------------------------------------------------------------

def build_replication_plan_from_continuity(
    continuity_manifest: Any = None,
    default_targets: Optional[List[str]] = None,
) -> ReplicationPlan:
    """
    Tiny v0.1 bridge between L5 Continuity and L6 Replication.

    Guardian-safe + reversible:
    - No filesystem I/O
    - No side effects
    - Pure data construction.

    Behaviour:
    - If default_targets is provided:
        * build one ReplicationTarget per path
        * set both source and path to that path
        * use the first entry as source_backup
    - Else:
        * fall back to the ReplicationManifest defaults
    """
    base = load_manifest()

    if default_targets:
        targets: List[ReplicationTarget] = []
        for idx, target_path in enumerate(default_targets, start=1):
            targets.append(
                ReplicationTarget(
                    id=f"default_target_{idx}",
                    name=f"Default Target {idx}",
                    source=target_path,
                    path=target_path,  # ← test expects this to match default_targets[0]
                )
            )
        source_backup = default_targets[0]
    else:
        targets = list(base.targets)
        # In the base manifest, we can reasonably treat the first target's path as the backup root.
        source_backup = targets[0].path if targets else ""

    return ReplicationPlan(
        manifest_version=base.manifest_version,
        targets=targets,
        policy=base.policy,
        source_backup=source_backup,
    )


# ---------------------------------------------------------------------------
# L6 – Manual Self-check (non-critical)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    m = load_manifest()
    print("Replication Manifest v", m.manifest_version)
    print("Targets:", [f"{t.id} -> {t.path}" for t in m.targets])
    print("Policy:", m.policy)
