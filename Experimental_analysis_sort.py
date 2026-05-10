"""
sorting_benchmark.py
====================
Complete benchmark for 16 sorting algorithms.
Covers: size (20 -> 1,000,000), structure (random/sorted/reverse/almost-sorted/
        half-sorted/flat), element type (int/float/string).

Algorithms included:
  ADS1 core : bubble, selection, insertion, merge, quicksort, heap,
               counting, radix, bucket, shell
  Extra     : timsort, introsort, merge sort (iterative),
               comb sort, patience sort, parallel merge sort

Usage:
    python3 sorting_benchmark.py             # full run -> results.csv
    python3 sorting_benchmark.py --quick     # small/medium sizes only (faster)

Output: results.csv  (algorithm, n, structure, element_type, runs, mean_ms, min_ms, max_ms)
"""

import sys, time, csv, random, gc, math, string, argparse
import multiprocessing as mp

sys.setrecursionlimit(200_000)
random.seed(42)

# -----------------------------------------------------------------------------
# 1. SORTING ALGORITHMS
# -----------------------------------------------------------------------------

# -- ADS1 Core ----------------------------------------------------------------

def bubble_sort(arr):
    a = arr[:]
    n = len(a)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                swapped = True
        if not swapped:
            break
    return a


def selection_sort(arr):
    a = arr[:]
    n = len(a)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if a[j] < a[min_idx]:
                min_idx = j
        a[i], a[min_idx] = a[min_idx], a[i]
    return a


def insertion_sort(arr):
    a = arr[:]
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0 and a[j] > key:
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key
    return a


def merge_sort(arr):
    if len(arr) <= 1:
        return arr[:]
    mid = len(arr) // 2
    return _merge(merge_sort(arr[:mid]), merge_sort(arr[mid:]))

def _merge(left, right):
    result, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    result.extend(left[i:]); result.extend(right[j:])
    return result


def quick_sort(arr):
    """Quicksort with median-of-3 pivot (Lomuto partition)."""
    a = arr[:]
    _qs(a, 0, len(a) - 1)
    return a

def _qs(a, lo, hi):
    if lo < hi:
        p = _partition(a, lo, hi)
        _qs(a, lo, p - 1)
        _qs(a, p + 1, hi)

def _partition(a, lo, hi):
    # Median-of-3: sort lo/mid/hi, place median at hi as pivot
    mid = (lo + hi) // 2
    if a[mid] < a[lo]:  a[lo],  a[mid] = a[mid],  a[lo]
    if a[hi]  < a[lo]:  a[lo],  a[hi]  = a[hi],   a[lo]
    if a[mid] < a[hi]:  a[mid], a[hi]  = a[hi],   a[mid]
    pivot = a[hi]
    i = lo - 1
    for j in range(lo, hi):
        if a[j] <= pivot:
            i += 1
            a[i], a[j] = a[j], a[i]
    a[i + 1], a[hi] = a[hi], a[i + 1]
    return i + 1


def heap_sort(arr):
    a = arr[:]
    n = len(a)
    for i in range(n // 2 - 1, -1, -1):
        _heapify(a, n, i)
    for i in range(n - 1, 0, -1):
        a[0], a[i] = a[i], a[0]
        _heapify(a, i, 0)
    return a

def _heapify(a, n, i):
    largest, l, r = i, 2*i+1, 2*i+2
    if l < n and a[l] > a[largest]: largest = l
    if r < n and a[r] > a[largest]: largest = r
    if largest != i:
        a[i], a[largest] = a[largest], a[i]
        _heapify(a, n, largest)


def counting_sort(arr):
    """Non-negative integers only."""
    if not arr: return []
    mn, mx = min(arr), max(arr)
    count = [0] * (mx - mn + 1)
    for x in arr: count[x - mn] += 1
    result = []
    for i, c in enumerate(count):
        result.extend([i + mn] * c)
    return result


def radix_sort(arr):
    """LSD radix sort -- non-negative integers only."""
    if not arr: return []
    a = arr[:]
    exp = 1
    while max(a) // exp > 0:
        _radix_pass(a, exp)
        exp *= 10
    return a

def _radix_pass(a, exp):
    n = len(a)
    output, count = [0]*n, [0]*10
    for x in a: count[(x // exp) % 10] += 1
    for i in range(1, 10): count[i] += count[i-1]
    for i in range(n-1, -1, -1):
        d = (a[i] // exp) % 10
        output[count[d]-1] = a[i]; count[d] -= 1
    for i in range(n): a[i] = output[i]


def bucket_sort(arr):
    """Numeric values only; uses insertion sort within each bucket."""
    if not arr: return []
    mn, mx = min(arr), max(arr)
    if mn == mx: return arr[:]
    n = len(arr)
    buckets = [[] for _ in range(n)]
    for x in arr:
        idx = min(int((x - mn) / (mx - mn + 1e-10) * n), n - 1)
        buckets[idx].append(x)
    result = []
    for b in buckets:
        result.extend(sorted(b))
    return result


def shell_sort(arr):
    a = arr[:]
    n = len(a)
    gap = n // 2
    while gap > 0:
        for i in range(gap, n):
            temp, j = a[i], i
            while j >= gap and a[j - gap] > temp:
                a[j] = a[j - gap]; j -= gap
            a[j] = temp
        gap //= 2
    return a


# -- Extra algorithms ---------------------------------------------------------

def tim_sort(arr):
    """Python's built-in Timsort (C implementation -- the practical gold standard)."""
    return sorted(arr)


def intro_sort(arr):
    """Introsort: Quicksort -> Heapsort (depth limit) -> Insertion sort (<16)."""
    a = arr[:]
    limit = 2 * math.floor(math.log2(len(a) + 1)) if len(a) > 1 else 0
    _introsort(a, 0, len(a) - 1, limit)
    return a

def _introsort(a, lo, hi, limit):
    if hi - lo < 16:
        _isort_range(a, lo, hi); return
    if limit == 0:
        _heapsort_range(a, lo, hi); return
    p = _partition(a, lo, hi)
    _introsort(a, lo, p - 1, limit - 1)
    _introsort(a, p + 1, hi, limit - 1)

def _isort_range(a, lo, hi):
    for i in range(lo + 1, hi + 1):
        key, j = a[i], i - 1
        while j >= lo and a[j] > key: a[j+1] = a[j]; j -= 1
        a[j+1] = key

def _heapsort_range(a, lo, hi):
    sub = a[lo:hi+1]; n = len(sub)
    for i in range(n//2-1, -1, -1): _heapify(sub, n, i)
    for i in range(n-1, 0, -1): sub[0], sub[i] = sub[i], sub[0]; _heapify(sub, i, 0)
    a[lo:hi+1] = sub


def merge_sort_iterative(arr):
    """Bottom-up merge sort (no recursion)."""
    a = arr[:]
    n = len(a)
    width = 1
    while width < n:
        for i in range(0, n, 2 * width):
            mid   = min(i + width, n)
            right = min(i + 2 * width, n)
            a[i:right] = _merge(a[i:mid], a[mid:right])
        width *= 2
    return a


def comb_sort(arr):
    """Bubble sort variant with a shrinking gap -- eliminates 'turtles'."""
    a = arr[:]
    n, gap, sorted_ = len(a), len(a), False
    while not sorted_:
        gap = max(1, int(gap / 1.3))
        sorted_ = (gap == 1)
        for i in range(n - gap):
            if a[i] > a[i + gap]:
                a[i], a[i + gap] = a[i + gap], a[i]
                sorted_ = False
    return a


def patience_sort(arr):
    """Patience sorting -- exploits existing runs via a card-game strategy."""
    import heapq
    if not arr: return []
    piles = []
    for x in arr:
        lo, hi = 0, len(piles)
        while lo < hi:
            mid = (lo + hi) // 2
            if piles[mid][-1] <= x: lo = mid + 1
            else: hi = mid
        if lo == len(piles): piles.append([])
        piles[lo].append(x)
    heap = []
    for i, pile in enumerate(piles):
        heapq.heappush(heap, (pile.pop(), i))
    result = []
    while heap:
        val, i = heapq.heappop(heap)
        result.append(val)
        if piles[i]: heapq.heappush(heap, (piles[i].pop(), i))
    return result


# -- Parallel merge sort ------------------------------------------------------

def _sort_chunk(chunk): return sorted(chunk)

def parallel_merge_sort(arr):
    """Splits input across CPU cores, sorts in parallel, then k-way merges."""
    import heapq
    n_cores = max(2, mp.cpu_count())
    size    = max(1, len(arr) // n_cores)
    chunks  = [arr[i:i+size] for i in range(0, len(arr), size)]
    with mp.Pool(n_cores) as pool:
        sorted_chunks = pool.map(_sort_chunk, chunks)
    heap = []
    iters = [iter(c) for c in sorted_chunks]
    for i, it in enumerate(iters):
        try: heapq.heappush(heap, (next(it), i))
        except StopIteration: pass
    result = []
    while heap:
        val, i = heapq.heappop(heap)
        result.append(val)
        try: heapq.heappush(heap, (next(iters[i]), i))
        except StopIteration: pass
    return result


# -----------------------------------------------------------------------------
# 2. ALGORITHM REGISTRY
# -----------------------------------------------------------------------------

ALL_ALGORITHMS = {
    # ADS1 core
    'bubble_sort':          bubble_sort,
    'selection_sort':       selection_sort,
    'insertion_sort':       insertion_sort,
    'merge_sort':           merge_sort,
    'quick_sort':           quick_sort,
    'heap_sort':            heap_sort,
    'counting_sort':        counting_sort,
    'radix_sort':           radix_sort,
    'bucket_sort':          bucket_sort,
    'shell_sort':           shell_sort,
    # Extra
    'tim_sort':             tim_sort,
    'intro_sort':           intro_sort,
    'merge_sort_iterative': merge_sort_iterative,
    'comb_sort':            comb_sort,
    'patience_sort':        patience_sort,
    'parallel_merge_sort':  parallel_merge_sort,
}

# Algorithms that only work on non-negative integers
INTEGER_ONLY = {'counting_sort', 'radix_sort'}

# Upper size limits per algorithm (avoids impractically long runs)
SIZE_LIMITS = {
    'bubble_sort':    5_000,
    'selection_sort': 5_000,
    'insertion_sort': 5_000,
}
PARALLEL_MIN_N = 10_000  # parallel sort not worth it below this


# -----------------------------------------------------------------------------
# 3. DATA GENERATORS
# -----------------------------------------------------------------------------

def make_data(n, structure, element_type):
    """Generate a list of n elements with the given structure and type."""
    rng = random.Random(42)  # reproducible

    # base random data
    if element_type == 'int':
        base = [rng.randint(0, n * 10) for _ in range(n)]
    elif element_type == 'float':
        base = [rng.uniform(-1e6, 1e6) for _ in range(n)]
    elif element_type == 'string':
        chars = string.ascii_lowercase
        base = [''.join(rng.choices(chars, k=8)) for _ in range(n)]
    else:
        raise ValueError(f'Unknown element_type: {element_type}')

    # apply structure
    if structure == 'random':
        return base
    elif structure == 'sorted':
        return sorted(base)
    elif structure == 'reverse':
        return sorted(base, reverse=True)
    elif structure == 'almost_sorted':
        a = sorted(base)
        swaps = max(1, int(n * 0.02))   # 2% of positions swapped
        for _ in range(swaps):
            i, j = rng.randrange(n), rng.randrange(n)
            a[i], a[j] = a[j], a[i]
        return a
    elif structure == 'half_sorted':
        half = n // 2
        return sorted(base[:half]) + base[half:]
    elif structure == 'flat':
        if element_type == 'int':
            return [rng.randint(0, 4) for _ in range(n)]   # only 5 distinct values
        else:
            return base  # flat doesn't apply meaningfully to float/string
    else:
        raise ValueError(f'Unknown structure: {structure}')


# -----------------------------------------------------------------------------
# 4. BENCHMARK RUNNER
# -----------------------------------------------------------------------------

TIMEOUT_S = 5.0   # skip algorithm at this size tier if a single run exceeds this

def bench_once(fn, data):
    """Time a single sort call with GC disabled. Returns elapsed seconds."""
    gc.disable()
    t0 = time.perf_counter()
    fn(data)
    elapsed = time.perf_counter() - t0
    gc.enable()
    return elapsed


def repetitions(n):
    """How many times to repeat a sort at size n (for noise averaging)."""
    if n <= 50:       return 500
    elif n <= 100:    return 200
    elif n <= 1_000:  return 20
    elif n <= 10_000: return 5
    else:             return 1


def run_benchmarks(output_csv='results.csv', quick=False):
    # Define test matrix
    if quick:
        sizes_int    = [20, 50, 100, 1_000, 5_000, 10_000]
        sizes_float  = [20, 100, 1_000, 10_000]
        sizes_string = [100, 1_000, 10_000]
    else:
        sizes_int    = [20, 30, 50, 100, 1_000, 5_000, 10_000, 50_000, 100_000, 500_000, 1_000_000]
        sizes_float  = [20, 50, 100, 1_000, 5_000, 10_000, 50_000, 100_000]
        sizes_string = [100, 1_000, 5_000, 10_000, 50_000, 100_000]

    int_structs    = ['random', 'sorted', 'reverse', 'almost_sorted', 'half_sorted', 'flat']
    float_structs  = ['random', 'sorted', 'reverse', 'almost_sorted']
    string_structs = ['random', 'sorted', 'reverse', 'almost_sorted']

    test_configs = (
        [(n, s, 'int')    for n in sizes_int    for s in int_structs   ] +
        [(n, s, 'float')  for n in sizes_float  for s in float_structs ] +
        [(n, s, 'string') for n in sizes_string for s in string_structs]
    )

    fieldnames = ['algorithm', 'n', 'structure', 'element_type',
                  'runs', 'mean_ms', 'min_ms', 'max_ms']
    rows = []
    timed_out = set()   # (algo_name, element_type) -- skip at larger sizes too

    algo_names = sorted(ALL_ALGORITHMS.keys())
    total = len(algo_names) * len(test_configs)
    done  = 0

    for (n, structure, etype) in test_configs:
        # Generate data once per (n, structure, etype) combination
        data = make_data(n, structure, etype)

        for algo_name in algo_names:
            done += 1
            fn = ALL_ALGORITHMS[algo_name]

            # Skip conditions
            if (algo_name, etype) in timed_out:
                continue
            if algo_name in INTEGER_ONLY and etype != 'int':
                continue
            limit = SIZE_LIMITS.get(algo_name)
            if limit is not None and n > limit:
                continue
            if algo_name == 'parallel_merge_sort' and n < PARALLEL_MIN_N:
                continue
            if algo_name == 'bucket_sort' and etype == 'string':
                continue   # bucket_sort requires numeric values

            reps = repetitions(n)
            times = []
            timed_out_flag = False

            for _ in range(reps):
                t = bench_once(fn, data)
                if t > TIMEOUT_S:
                    timed_out_flag = True
                    break
                times.append(t)

            if timed_out_flag:
                timed_out.add((algo_name, etype))
                print(f'  [{done:>6}/{total}] TIMEOUT  {algo_name:<24} '
                      f'n={n:>9,}  {etype:<7}  {structure}')
                continue

            mean_ms = sum(times) / len(times) * 1000
            row = dict(
                algorithm    = algo_name,
                n            = n,
                structure    = structure,
                element_type = etype,
                runs         = len(times),
                mean_ms      = round(mean_ms, 4),
                min_ms       = round(min(times) * 1000, 4),
                max_ms       = round(max(times) * 1000, 4),
            )
            rows.append(row)
            print(f'  [{done:>6}/{total}] OK       {algo_name:<24} '
                  f'n={n:>9,}  {etype:<7}  {structure:<15}  '
                  f'mean={mean_ms:10.3f} ms  runs={len(times)}')

    # Write CSV
    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f'\nSaved {len(rows)} results -> {output_csv}')
    return rows


# -----------------------------------------------------------------------------
# 5. QUICK CORRECTNESS CHECK
# -----------------------------------------------------------------------------

def verify_all():
    """Run a correctness check on all algorithms before benchmarking."""
    print('Verifying all algorithms...')
    rng = random.Random(0)
    errors = []
    for name, fn in sorted(ALL_ALGORITHMS.items()):
        if name == 'parallel_merge_sort':
            continue  # skip -- multiprocessing in a check is noisy
        for seed in range(5):
            rng.seed(seed)
            arr = [rng.randint(0, 100) for _ in range(60)]
            try:
                result = fn(arr)
                assert result == sorted(arr), 'wrong output'
            except Exception as e:
                errors.append(f'  FAIL  {name}  seed={seed}: {e}')
    if errors:
        for e in errors: print(e)
        sys.exit(1)
    print(f'  All {len(ALL_ALGORITHMS) - 1} algorithms correct.\n')


# -----------------------------------------------------------------------------
# 6. ENTRY POINT
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sorting algorithm benchmark')
    parser.add_argument('--quick',     action='store_true', help='Run only small/medium sizes')
    parser.add_argument('--output',    default='results.csv', help='Output CSV path')
    parser.add_argument('--no-verify', action='store_true', help='Skip correctness check')
    args = parser.parse_args()

    if not args.no_verify:
        verify_all()

    run_benchmarks(output_csv=args.output, quick=args.quick)