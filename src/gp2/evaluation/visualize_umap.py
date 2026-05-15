"""
UMAP Visualization of Player2Vec embeddings.

Reduces 32D player vectors to 2D using UMAP and colors by position.
This is Magdaci's primary validation — if the model learned football
semantics, positions should cluster naturally without ever being told
what position a player plays.

Expected result:
    - Goalkeepers form tight cluster separate from everyone
    - Defenders cluster together
    - Attackers cluster together
    - Midfielders in between
    - Full-backs bridge defenders and midfielders
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import umap
from collections import Counter

from src.gp2.paths import PLAYER2VEC_PATH, PLAYER2VEC_UMAP_PATH, PLAYER_INFO_PATH


# ==================================================================================================
# POSITION GROUPING & COLORS
# ==================================================================================================

# Map StatsBomb's positions to tactical role groups (LEFT/RIGHT SEPARATED)
POSITION_GROUPS = {
    # Goalkeepers
    "Goalkeeper": "GK",
    
    # Central Defenders (no left/right distinction needed)
    "Left Center Back": "Center Back",
    "Center Back": "Center Back",
    "Right Center Back": "Center Back",
    
    # Fullbacks (SEPARATED by side)
    "Left Back": "Left Back",
    "Right Back": "Right Back",
    "Left Wing Back": "Left Wing Back",
    "Right Wing Back": "Right Wing Back",
    
    # Defensive Midfielders
    "Left Defensive Midfield": "Defensive Mid",
    "Center Defensive Midfield": "Defensive Mid",
    "Right Defensive Midfield": "Defensive Mid",
    
    # Central Midfielders
    "Left Midfield": "Central Mid",
    "Left Center Midfield": "Central Mid",
    "Center Midfield": "Central Mid",
    "Right Center Midfield": "Central Mid",
    "Right Midfield": "Central Mid",
    
    # Attacking Midfielders
    "Left Attacking Midfield": "Attacking Mid",
    "Center Attacking Midfield": "Attacking Mid",
    "Right Attacking Midfield": "Attacking Mid",
    
    # Wingers (SEPARATED by side)
    "Left Wing": "Left Wing",
    "Right Wing": "Right Wing",
    
    # Strikers
    "Left Center Forward": "Striker",
    "Center Forward": "Striker",
    "Right Center Forward": "Striker",
    "Secondary Striker": "Striker",
}

# Color scheme — distinct colors for each tactical role
POSITION_COLORS = {
    "GK": "#FFD700",              # Gold
    "Center Back": "#1E3A8A",     # Dark Blue
    "Left Back": "#FF0095",       # Medium Blue
    "Right Back": "#8C00FF",      # Light Blue  
    "Left Wing Back": "#FF0095",  # Very Light Blue
    "Right Wing Back": "#8C00FF", # Pale Blue
    "Defensive Mid": "#000000",   # Dark Green
    "Central Mid": "#09FF00",     # Medium Green
    "Attacking Mid": "#EEFF00",   # Light Green
    "Left Wing": "#00FFF2FF",       # Red
    "Right Wing": "#FF5E00",      # Light Red
    "Striker": "#FF0000",         # Dark Red
    "Unknown": "#808080",         # Gray
}


# ==================================================================================================
# LOAD DATA
# ==================================================================================================

def load_data():
    """Load player vectors and metadata."""
    print("Loading Player2Vec...")
    data = np.load(PLAYER2VEC_PATH)
    player_ids = data["player_ids"]
    vectors = data["vectors"]
    print(f"Loaded {len(player_ids)} players with {vectors.shape[1]}D vectors")

    print(f"\nLoading player info...")
    with open(PLAYER_INFO_PATH, "r", encoding="utf-8") as f:
        player_info = json.load(f)
    print(f"Loaded info for {len(player_info)} players")

    return player_ids, vectors, player_info


# ==================================================================================================
# UMAP PROJECTION
# ==================================================================================================

def compute_umap(vectors, n_neighbors=15, min_dist=0.1, random_state=42):
    """
    Reduce 32D vectors to 2D using UMAP.
    
    Args:
        n_neighbors: local neighborhood size (15 is good default)
        min_dist:    minimum distance between points (0.1 = moderate spread)
    """
    print(f"\nComputing UMAP projection...")
    print(f"  n_neighbors={n_neighbors}, min_dist={min_dist}")
    
    reducer = umap.UMAP(
        n_components=2,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        random_state=random_state,
        metric="cosine",  # same metric as similarity search
    )
    
    embedding_2d = reducer.fit_transform(vectors)
    print(f"  Projection complete: {embedding_2d.shape}")
    
    return embedding_2d


# ==================================================================================================
# VISUALIZATION
# ==================================================================================================

def visualize(player_ids, embedding_2d, player_info):
    """Create scatter plot colored by position."""
    
    # Map each player to position group
    position_groups = []
    position_names = []
    
    for pid in player_ids:
        info = player_info.get(pid, {})
        pos = info.get("position", "Unknown")
        pos_group = POSITION_GROUPS.get(pos, "Unknown")
        position_groups.append(pos_group)
        position_names.append(pos)
    
    # Count distribution
    pos_counts = Counter(position_groups)
    print(f"\nPosition distribution:")
    for pos, count in sorted(pos_counts.items()):
        print(f"  {pos:<12}: {count}")
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Plot each position group separately for clean legend
    for pos_group in ["GK", "Center Back", "Left Back", "Right Back",
                      "Left Wing Back", "Right Wing Back",
                      "Defensive Mid", "Central Mid", "Attacking Mid",
                      "Left Wing", "Right Wing", "Striker", "Unknown"]:
        mask = np.array([pg == pos_group for pg in position_groups])
        if mask.sum() == 0:
            continue
        
        ax.scatter(
            embedding_2d[mask, 0],
            embedding_2d[mask, 1],
            c=POSITION_COLORS.get(pos_group, "#808080"),
            label=f"{pos_group} (n={mask.sum()})",
            alpha=0.6,
            s=30,
            edgecolors="white",
            linewidth=0.3,
        )
    
    ax.set_title(
        "Player2Vec — UMAP Projection (Colored by Position)\n"
        "Natural clustering validates model learned football semantics",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("UMAP Dimension 1", fontsize=12)
    ax.set_ylabel("UMAP Dimension 2", fontsize=12)
    ax.legend(loc="best", fontsize=10, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle="--")
    
    plt.tight_layout()
    
    # Save
    PLAYER2VEC_UMAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(PLAYER2VEC_UMAP_PATH, dpi=300, bbox_inches="tight")
    print(f"\nVisualization saved to: {PLAYER2VEC_UMAP_PATH}")
    
    plt.show()


# ==================================================================================================
# CLUSTER QUALITY METRICS
# ==================================================================================================

def analyze_clustering(player_ids, embedding_2d, player_info):
    """
    Quantitative analysis of position clustering.
    If model learned semantics, same-position players should be closer
    in embedding space than different-position players.
    """
    print("\n" + "="*60)
    print("CLUSTER QUALITY ANALYSIS")
    print("="*60)
    
    # Build position mapping
    pid_to_group = {}
    for pid in player_ids:
        pos = player_info.get(pid, {}).get("position", "Unknown")
        pid_to_group[pid] = POSITION_GROUPS.get(pos, "Unknown")
    
    # For each position group, compute intra-cluster vs inter-cluster distances
    from scipy.spatial.distance import pdist, cdist
    
    results = {}
    
    # Analyze all tactical role groups (left/right separated)
    for target_group in ["GK", "Center Back", "Left Back", "Right Back",
                         "Left Wing Back", "Right Wing Back",
                         "Defensive Mid", "Central Mid", "Attacking Mid",
                         "Left Wing", "Right Wing", "Striker"]:
        # Get indices of this group
        target_mask = np.array([pid_to_group[pid] == target_group for pid in player_ids])
        
        if target_mask.sum() < 2:
            continue
        
        target_points = embedding_2d[target_mask]
        other_points = embedding_2d[~target_mask]
        
        # Intra-cluster distances (within same position)
        if len(target_points) > 1:
            intra_dists = pdist(target_points, metric="euclidean")
            mean_intra = intra_dists.mean()
        else:
            mean_intra = 0
        
        # Inter-cluster distances (to other positions)
        if len(other_points) > 0:
            inter_dists = cdist(target_points, other_points, metric="euclidean")
            mean_inter = inter_dists.mean()
        else:
            mean_inter = 0
        
        # Ratio — higher is better (positions are more separated)
        ratio = mean_inter / mean_intra if mean_intra > 0 else 0
        
        results[target_group] = {
            "intra": mean_intra,
            "inter": mean_inter,
            "ratio": ratio,
        }
        
        print(f"\n{target_group}:")
        print(f"  Mean intra-cluster distance: {mean_intra:.3f}")
        print(f"  Mean inter-cluster distance: {mean_inter:.3f}")
        print(f"  Separation ratio:            {ratio:.3f}  {'✓ Good' if ratio > 1.2 else '✗ Poor'}")
    
    print("\nInterpretation:")
    print("  Ratio > 1.5  → Excellent clustering (positions well separated)")
    print("  Ratio > 1.2  → Good clustering")
    print("  Ratio < 1.0  → Poor clustering (positions mixed)")


# ==================================================================================================
# MAIN
# ==================================================================================================

def main():
    player_ids, vectors, player_info = load_data()
    embedding_2d = compute_umap(vectors)
    visualize(player_ids, embedding_2d, player_info)
    analyze_clustering(player_ids, embedding_2d, player_info)


if __name__ == "__main__":
    main()
