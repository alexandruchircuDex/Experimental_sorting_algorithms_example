# Experimental comparison of sorting algorithms

This artifact contains:

- `sorting_algorithms_experimental_comparison.tex` - LaTeX source of the paper.
- `sorting_algorithms_experimental_comparison.pdf` - compiled paper.
- `Experimental_analysis_sort.py` - benchmark source code.
- `results.csv` - raw experimental measurements.
- `figures/` - figures generated from the CSV data.

To reproduce the benchmark:

```bash
python3 Experimental_analysis_sort.py --output results.csv
```

For a fast smoke test:

```bash
python3 Experimental_analysis_sort.py --quick --output quick_results.csv
```
