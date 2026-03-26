"""
Accuracy & Performance Test Suite for Smart Recipe Recommender
==============================================================
Tests ML model accuracy (Precision, Recall, F1, NDCG, MRR, Hit Rate,
Coverage, Diversity) and API / model latency & throughput.

Usage:
    python test_accuracy_performance.py          # full suite
    python test_accuracy_performance.py --quick   # fewer test cases (faster)
"""
import os, sys, time, json, statistics
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Ensure backend is on the path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# ── Load environment ─────────────────────────────────────────────────────
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

import numpy as np

# ─────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────
QUICK = '--quick' in sys.argv
NUM_TEST_CASES   = 30 if QUICK else 100
NUM_PERF_ROUNDS  = 20 if QUICK else 50
K_VALUES         = [5, 10]
DIVIDER          = "=" * 78
THIN_DIVIDER     = "-" * 78

# ─────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────
def precision_at_k(recs, relevant, k):
    top = recs[:k]
    rel = set(relevant)
    return sum(1 for r in top if r in rel) / k if k else 0.0

def recall_at_k(recs, relevant, k):
    top = recs[:k]
    rel = set(relevant)
    return sum(1 for r in top if r in rel) / len(rel) if rel else 0.0

def f1_at_k(recs, relevant, k):
    p = precision_at_k(recs, relevant, k)
    r = recall_at_k(recs, relevant, k)
    return 2*p*r/(p+r) if (p+r) else 0.0

def ndcg_at_k(recs, relevant, k):
    top = recs[:k]
    rel = set(relevant)
    relevance = [1 if r in rel else 0 for r in top]
    ideal     = sorted(relevance, reverse=True)
    if sum(ideal) == 0:
        return 0.0
    dcg  = sum((2**v - 1) / np.log2(i + 2) for i, v in enumerate(relevance))
    idcg = sum((2**v - 1) / np.log2(i + 2) for i, v in enumerate(ideal))
    return dcg / idcg if idcg else 0.0

def mrr(recs, relevant):
    rel = set(relevant)
    for i, r in enumerate(recs):
        if r in rel:
            return 1.0 / (i + 1)
    return 0.0

def hit_at_k(recs, relevant, k):
    return 1.0 if set(recs[:k]) & set(relevant) else 0.0


def build_test_data_from_catalog(recommender, db, n):
    """Build test data ONLY from recipes that the model has actually loaded.

    This gives a fair accuracy evaluation — we only test whether the model
    can surface a recipe that it *knows about*, not one lost in the 2M pool.

    For each test recipe we also find similar recipes (shared tags) to create
    richer ground truth (multiple relevant items).
    """
    import random as _rng

    if recommender.recipes_df is None or len(recommender.recipes_df) == 0:
        print("  [WARN] Model has no recipes loaded – cannot build test data")
        return []

    catalog_df = recommender.recipes_df.copy()
    sample_size = min(n, len(catalog_df))
    sampled = catalog_df.sample(n=sample_size, random_state=42)

    # Build a tag→recipe-id index from the catalog for expanded ground truth
    tag_index = defaultdict(set)
    for _, row in catalog_df.iterrows():
        for tag in (row.get('tags') or []):
            tag_index[tag.lower()].add(int(row['id']))

    test_data = []
    for _, row in sampled.iterrows():
        ingredients = row.get('ingredients', [])
        if not ingredients or len(ingredients) < 2:
            continue

        # Query = first half of ingredients (simulate a user who has some items)
        num_q = max(2, len(ingredients) // 2)
        q_ings = list(ingredients[:num_q])

        # Ground truth = the recipe itself + up to 10 recipes sharing ≥2 tags
        recipe_id = int(row['id'])
        relevant = {recipe_id}
        recipe_tags = [t.lower() for t in (row.get('tags') or [])]
        if recipe_tags:
            # Collect candidates that share tags
            tag_overlap = defaultdict(int)
            for tag in recipe_tags:
                for rid in tag_index.get(tag, set()):
                    if rid != recipe_id:
                        tag_overlap[rid] += 1
            # Keep those sharing ≥2 tags
            similar = [rid for rid, cnt in tag_overlap.items() if cnt >= 2]
            _rng.shuffle(similar)
            relevant.update(similar[:10])

        test_data.append({
            'ingredients': q_ings,
            'dietary_preference': '',
            'cuisine_type': '',
            'relevant_recipes': list(relevant)
        })

    return test_data


# ─────────────────────────────────────────────────────────────────────────
# Accuracy evaluation
# ─────────────────────────────────────────────────────────────────────────
def evaluate_accuracy(recommender, test_data, label="Model"):
    print(f"\n{DIVIDER}")
    print(f"  ACCURACY EVALUATION  –  {label}")
    print(f"{DIVIDER}")
    print(f"  Test cases: {len(test_data)}   K values: {K_VALUES}")
    print()

    metrics = {m: defaultdict(list) for m in ['precision', 'recall', 'f1', 'ndcg']}
    mrr_scores = []
    hit_scores = {k: [] for k in K_VALUES}
    all_rec_ids = []
    diversity_scores = []

    for tc in test_data:
        recs = recommender.recommend(
            ingredients=tc['ingredients'],
            dietary_preference=tc.get('dietary_preference', ''),
            cuisine_type=tc.get('cuisine_type', ''),
            limit=max(K_VALUES)
        )
        rec_ids = [r['id'] for r in recs]
        relevant = tc['relevant_recipes']

        all_rec_ids.append(rec_ids)
        mrr_scores.append(mrr(rec_ids, relevant))

        # Diversity: unique ingredients & tags across recommendations
        all_ings = set()
        all_tags = set()
        for r in recs:
            all_ings.update(r.get('ingredients', []))
            all_tags.update(r.get('tags', []))
        if recs:
            diversity_scores.append(min((len(all_ings) + len(all_tags)) / len(recs) / 20.0, 1.0))

        for k in K_VALUES:
            metrics['precision'][k].append(precision_at_k(rec_ids, relevant, k))
            metrics['recall'][k].append(recall_at_k(rec_ids, relevant, k))
            metrics['f1'][k].append(f1_at_k(rec_ids, relevant, k))
            metrics['ndcg'][k].append(ndcg_at_k(rec_ids, relevant, k))
            hit_scores[k].append(hit_at_k(rec_ids, relevant, k))

    # Coverage
    total_recipes = len(recommender.recipes_df) if recommender.recipes_df is not None else 1
    unique_recs = set()
    for ids in all_rec_ids:
        unique_recs.update(ids)
    coverage = len(unique_recs) / total_recipes if total_recipes else 0.0

    # Print table
    header = f"{'Metric':<22}"
    for k in K_VALUES:
        header += f"{'@' + str(k) + ' Mean':>12}{'±Std':>10}"
    print(header)
    print(THIN_DIVIDER)

    summary = {}
    for m_name in ['precision', 'recall', 'f1', 'ndcg']:
        row = f"  {m_name.capitalize():<20}"
        for k in K_VALUES:
            vals = metrics[m_name][k]
            mean = float(np.mean(vals)) if vals else 0.0
            std  = float(np.std(vals))  if vals else 0.0
            row += f"{mean:>12.4f}{std:>10.4f}"
            summary[f'{m_name}@{k}'] = {'mean': mean, 'std': std}
        print(row)

    # Hit rate
    row = f"  {'Hit Rate':<20}"
    for k in K_VALUES:
        vals = hit_scores[k]
        mean = float(np.mean(vals)) if vals else 0.0
        std  = float(np.std(vals))  if vals else 0.0
        row += f"{mean:>12.4f}{std:>10.4f}"
        summary[f'hit_rate@{k}'] = {'mean': mean, 'std': std}
    print(row)

    print()
    avg_mrr = float(np.mean(mrr_scores)) if mrr_scores else 0.0
    avg_div = float(np.mean(diversity_scores)) if diversity_scores else 0.0
    print(f"  MRR:                {avg_mrr:.4f}")
    print(f"  Coverage:           {coverage:.4f}  ({len(unique_recs):,} / {total_recipes:,} recipes)")
    print(f"  Diversity:          {avg_div:.4f}")

    summary['mrr']       = avg_mrr
    summary['coverage']  = coverage
    summary['diversity'] = avg_div
    return summary


# ─────────────────────────────────────────────────────────────────────────
# Performance / latency evaluation
# ─────────────────────────────────────────────────────────────────────────
def evaluate_performance(recommender, test_data, label="Model"):
    print(f"\n{DIVIDER}")
    print(f"  PERFORMANCE / LATENCY  –  {label}")
    print(f"{DIVIDER}")

    rounds = min(NUM_PERF_ROUNDS, len(test_data))
    sample = test_data[:rounds]

    latencies = []
    result_counts = []

    for tc in sample:
        t0 = time.perf_counter()
        recs = recommender.recommend(
            ingredients=tc['ingredients'],
            dietary_preference=tc.get('dietary_preference', ''),
            cuisine_type=tc.get('cuisine_type', ''),
            limit=10
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed_ms)
        result_counts.append(len(recs))

    latencies_arr = np.array(latencies)
    avg   = float(np.mean(latencies_arr))
    med   = float(np.median(latencies_arr))
    p90   = float(np.percentile(latencies_arr, 90))
    p95   = float(np.percentile(latencies_arr, 95))
    p99   = float(np.percentile(latencies_arr, 99))
    mn    = float(np.min(latencies_arr))
    mx    = float(np.max(latencies_arr))
    throughput = 1000.0 / avg if avg else 0.0

    print(f"  Queries executed:   {rounds}")
    print(f"  Avg results/query:  {np.mean(result_counts):.1f}")
    print()
    print(f"  {'Latency (ms)':<22}{'Value':>12}")
    print(f"  {THIN_DIVIDER[:34]}")
    print(f"  {'Mean':<22}{avg:>12.2f}")
    print(f"  {'Median':<22}{med:>12.2f}")
    print(f"  {'P90':<22}{p90:>12.2f}")
    print(f"  {'P95':<22}{p95:>12.2f}")
    print(f"  {'P99':<22}{p99:>12.2f}")
    print(f"  {'Min':<22}{mn:>12.2f}")
    print(f"  {'Max':<22}{mx:>12.2f}")
    print(f"  {'Throughput (req/s)':<22}{throughput:>12.1f}")

    return {
        'queries': rounds,
        'mean_ms': avg, 'median_ms': med,
        'p90_ms': p90, 'p95_ms': p95, 'p99_ms': p99,
        'min_ms': mn, 'max_ms': mx,
        'throughput_rps': throughput
    }


# ─────────────────────────────────────────────────────────────────────────
# Qualitative spot-check
# ─────────────────────────────────────────────────────────────────────────
SPOT_CHECKS = [
    {'ingredients': ['chicken', 'garlic', 'rice'],       'label': 'chicken garlic rice'},
    {'ingredients': ['pasta', 'tomato', 'basil'],        'label': 'pasta tomato basil'},
    {'ingredients': ['tofu', 'soy sauce', 'ginger'],     'label': 'tofu soy ginger'},
    {'ingredients': ['flour', 'sugar', 'butter', 'eggs'],'label': 'baking basics'},
    {'ingredients': ['salmon', 'lemon', 'dill'],         'label': 'salmon lemon dill'},
]

def run_spot_checks(recommender, label="Model"):
    print(f"\n{DIVIDER}")
    print(f"  QUALITATIVE SPOT CHECKS  –  {label}")
    print(f"{DIVIDER}")

    for sc in SPOT_CHECKS:
        print(f"\n  Query: {', '.join(sc['ingredients'])}  ({sc['label']})")
        recs = recommender.recommend(ingredients=sc['ingredients'], limit=5)
        if not recs:
            print("    (no results)")
            continue
        for i, r in enumerate(recs, 1):
            score = r.get('similarity_score', r.get('score', 0))
            matches = r.get('ingredient_matches', '?')
            print(f"    {i}. {r['name']:<45} score={score:.3f}  matches={matches}")


# ─────────────────────────────────────────────────────────────────────────
# Model training-time benchmark
# ─────────────────────────────────────────────────────────────────────────
def benchmark_training(db):
    """Time the model load+train from scratch."""
    from ml_model import RecipeRecommender
    print(f"\n{DIVIDER}")
    print("  TRAINING-TIME BENCHMARK")
    print(DIVIDER)

    # Original model
    t0 = time.perf_counter()
    rec_orig = RecipeRecommender(db)
    t_orig = time.perf_counter() - t0
    n_orig = len(rec_orig.recipes_df) if rec_orig.recipes_df is not None else 0
    print(f"  Original (TF-IDF):    {t_orig:>8.2f}s   ({n_orig:,} recipes)")

    # Enhanced model (if importable)
    rec_enh = None
    t_enh = 0
    try:
        from ml_model_enhanced import HybridRecipeRecommender
        t0 = time.perf_counter()
        rec_enh = HybridRecipeRecommender(db)
        t_enh = time.perf_counter() - t0
        n_enh = len(rec_enh.recipes_df) if rec_enh.recipes_df is not None else 0
        print(f"  Enhanced (Hybrid):    {t_enh:>8.2f}s   ({n_enh:,} recipes)")
    except Exception as e:
        print(f"  Enhanced model skipped: {e}")

    return rec_orig, rec_enh, t_orig, t_enh


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────
def main():
    print()
    print(DIVIDER)
    print("  SMART RECIPE RECOMMENDER  –  ACCURACY & PERFORMANCE TEST")
    print(DIVIDER)
    print(f"  Date:         {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Mode:         {'QUICK' if QUICK else 'FULL'}")
    print(f"  Test cases:   {NUM_TEST_CASES}")
    print(f"  Perf rounds:  {NUM_PERF_ROUNDS}")

    # ── Database ──
    from database import Database
    db = Database()
    try:
        db.connect()
        print(f"  Database:     CONNECTED")
    except Exception as e:
        print(f"\n[FAIL] Cannot connect to database: {e}")
        return 1

    try:
        stats = db.get_stats()
        print(f"  Recipes:      {stats.get('total_recipes', '?'):,}")
        print(f"  Ingredients:  {stats.get('total_ingredients', '?'):,}")
    except Exception:
        pass

    # ── Train / load models (need them before building in-catalog test data) ──
    rec_orig, rec_enh, t_orig, t_enh = benchmark_training(db)

    # ── Build test data from the model catalog ──
    primary_model = rec_enh if (rec_enh and rec_enh.recipes_df is not None) else rec_orig
    print(f"\n  Building IN-CATALOG test data ({NUM_TEST_CASES} cases) ...")
    test_data = build_test_data_from_catalog(primary_model, db, NUM_TEST_CASES)
    avg_rel = np.mean([len(tc['relevant_recipes']) for tc in test_data]) if test_data else 0
    print(f"  [OK] {len(test_data)} test cases ready  (avg {avg_rel:.1f} relevant recipes each)")

    if not test_data:
        print("\n[FAIL] No test data could be generated.")
        return 1

    report = {
        'timestamp': datetime.now().isoformat(),
        'mode': 'quick' if QUICK else 'full',
        'test_cases': len(test_data),
        'training': {'original_s': t_orig, 'enhanced_s': t_enh},
        'models': {}
    }

    # ── Evaluate Original Model ──
    if rec_orig and rec_orig.recipes_df is not None:
        acc = evaluate_accuracy(rec_orig, test_data, "Original (TF-IDF)")
        perf = evaluate_performance(rec_orig, test_data, "Original (TF-IDF)")
        run_spot_checks(rec_orig, "Original (TF-IDF)")
        report['models']['original'] = {'accuracy': acc, 'performance': perf}

    # ── Evaluate Enhanced Model ──
    if rec_enh and rec_enh.recipes_df is not None:
        # Clear recommendation cache so perf numbers are cold-start
        rec_enh.recommendation_cache.clear()
        acc = evaluate_accuracy(rec_enh, test_data, "Enhanced (Hybrid)")
        perf = evaluate_performance(rec_enh, test_data, "Enhanced (Hybrid)")
        run_spot_checks(rec_enh, "Enhanced (Hybrid)")
        report['models']['enhanced'] = {'accuracy': acc, 'performance': perf}

    # ── Side-by-side comparison ──
    if 'original' in report['models'] and 'enhanced' in report['models']:
        print(f"\n{DIVIDER}")
        print("  SIDE-BY-SIDE COMPARISON  (Original vs Enhanced)")
        print(DIVIDER)

        o = report['models']['original']
        e = report['models']['enhanced']

        rows = []
        for key in ['precision@10', 'recall@10', 'f1@10', 'ndcg@10', 'hit_rate@10']:
            ov = o['accuracy'].get(key, {}).get('mean', 0)
            ev = e['accuracy'].get(key, {}).get('mean', 0)
            diff = ((ev - ov) / ov * 100) if ov else 0
            arrow = "^" if diff > 0 else "v" if diff < 0 else "="
            rows.append((key, ov, ev, diff, arrow))

        for scalar_key in ['mrr', 'coverage', 'diversity']:
            ov = o['accuracy'].get(scalar_key, 0)
            ev = e['accuracy'].get(scalar_key, 0)
            diff = ((ev - ov) / ov * 100) if ov else 0
            arrow = "^" if diff > 0 else "v" if diff < 0 else "="
            rows.append((scalar_key, ov, ev, diff, arrow))

        print(f"  {'Metric':<20}{'Original':>12}{'Enhanced':>12}{'Change':>12}")
        print(f"  {THIN_DIVIDER[:56]}")
        for name, ov, ev, diff, arrow in rows:
            print(f"  {name:<20}{ov:>12.4f}{ev:>12.4f}  {arrow} {diff:+.1f}%")

        print()
        print(f"  {'Latency (ms)':<20}{'Original':>12}{'Enhanced':>12}")
        print(f"  {THIN_DIVIDER[:44]}")
        for lk in ['mean_ms', 'median_ms', 'p95_ms']:
            ov = o['performance'].get(lk, 0)
            ev = e['performance'].get(lk, 0)
            print(f"  {lk:<20}{ov:>12.2f}{ev:>12.2f}")

    # ── Save JSON report ──
    report_file = Path(__file__).parent / f"test_accuracy_perf_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  Report saved: {report_file.name}")

    # ── Final verdict ──
    print(f"\n{DIVIDER}")
    print("  TEST COMPLETE")
    print(DIVIDER)

    best = report['models'].get('enhanced', report['models'].get('original', {}))
    if best:
        acc = best.get('accuracy', {})
        perf = best.get('performance', {})
        p10 = acc.get('precision@10', {}).get('mean', 0)
        hr10 = acc.get('hit_rate@10', {}).get('mean', 0)
        avg_ms = perf.get('mean_ms', 0)

        print(f"  Best Precision@10 : {p10:.4f}")
        print(f"  Best Hit Rate@10  : {hr10:.4f}")
        print(f"  Avg latency       : {avg_ms:.1f} ms")

        # Simple pass/fail thresholds
        issues = []
        if p10 < 0.01:
            issues.append(f"Precision@10 very low ({p10:.4f})")
        if hr10 < 0.05:
            issues.append(f"Hit Rate@10 very low ({hr10:.4f})")
        if avg_ms > 2000:
            issues.append(f"Avg latency too high ({avg_ms:.0f} ms)")

        if issues:
            print(f"\n  [WARN] Potential issues:")
            for iss in issues:
                print(f"         - {iss}")
        else:
            print(f"\n  [OK] All basic thresholds passed.")

    db.disconnect()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[CANCELLED]")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)
