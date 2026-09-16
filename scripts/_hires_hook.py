# -*- coding: utf-8 -*-
"""
Import-time hook: makes every chart script also emit a 300 DPI PNG of
each figure it saves, into output/hires/<same-basename-as-its-.b64>.png,
WITHOUT editing any of the ~13 chart-generating scripts and without
touching the .b64 files the website build reads (those stay at each
script's own dpi, unchanged).

Two savefig-then-write shapes exist across scripts:
  1. Immediate: fig.savefig(buf) -> b64encode -> open("chart_x.b64","w")
     right away, one chart at a time.
  2. Batched (viz*.py): several fig_to_b64(fig) calls build up a
     `charts` dict first (each closes its own figure right after
     encoding), then a single loop at the end does
     open(f"chart_{k}.b64", "w") for every entry.

Either way, the ENCODE order (fig.savefig -> PNG bytes) always matches
the WRITE order later (dict insertion order == iteration order), so a
FIFO queue of "figures saved, in the order they were saved" lines up
correctly with "*.b64 files opened for writing, in the order they're
opened" -- even when writing is deferred well past when the figure
was closed. This hook doesn't try to name-match; it just pops the
next figure off the queue for each .b64 write.

Usage: run each chart script with this preloaded, e.g.
    python3 -c "import sys; sys.path.insert(0, 'scripts'); import _hires_hook; import runpy; runpy.run_path('scripts/historical_arc.py', run_name='__main__')"
"""
import os
import collections
import builtins
import matplotlib.figure as mfigure

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIRES_DIR = os.path.join(BASE, "output", "hires")
os.makedirs(HIRES_DIR, exist_ok=True)

_queue = collections.deque()
_orig_savefig = mfigure.Figure.savefig
_orig_open = builtins.open


def _patched_savefig(self, fname, *args, **kwargs):
    fmt = kwargs.get("format")
    if fmt == "png" or (isinstance(fname, str) and fname.lower().endswith(".png")):
        _queue.append(self)
    return _orig_savefig(self, fname, *args, **kwargs)


def _patched_open(path, mode="r", *args, **kwargs):
    if isinstance(path, str) and "w" in mode and path.endswith(".b64") and _queue:
        fig = _queue.popleft()
        basename = os.path.splitext(os.path.basename(path))[0]
        hires_path = os.path.join(HIRES_DIR, basename + ".png")
        try:
            _orig_savefig(fig, hires_path, format="png", dpi=300,
                           facecolor=fig.get_facecolor())
            print(f"  [hires] {basename}.png")
        except Exception as e:
            print(f"  [hires] FAILED for {basename}: {e}")
    return _orig_open(path, mode, *args, **kwargs)


mfigure.Figure.savefig = _patched_savefig
builtins.open = _patched_open
