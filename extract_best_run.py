#!/usr/bin/env python3
"""
Parse a finetune log file and output the best run as CSV on stdout.
Usage: python3 parse_log.py <log_file>

Output columns: all parameter columns (T0, T1, ...) + score + Trimmed Mean + STD Dev + STD Dev %
Exit code 0 on success, 1 on error (no best run found or empty results).
"""

import sys
import re

LOG_RE = re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \[\w+\] finetune: (.*)')

def strip_prefix(line):
    """Strip log timestamp/level prefix, return inner content or None."""
    m = LOG_RE.match(line)
    return m.group(1) if m else None


def parse_fixed_width(header_line, data_line):
    """
    Parse a fixed-width table row given the header and data lines (already stripped of log prefix).
    Column boundaries are inferred from the header: each column starts at its first char and ends
    where the next column starts (or end of string).
    Returns a dict {column_name: value}.
    """
    # Find start position of each column name in the header
    col_starts = []
    for m in re.finditer(r'\S+(?:\s+\S+)*?(?=\s{2,}|$)', header_line.rstrip()):
        col_starts.append((m.start(), m.group()))
    # Reparse: find column positions by locating runs of non-spaces
    # We want multi-word column names like "Trimmed Mean" and "STD Dev %"
    # Strategy: split on 2+ spaces
    headers = re.split(r'  +', header_line.strip())
    # Get the start position of each header in the stripped header line
    positions = []
    search_from = 0
    stripped_header = header_line  # keep original (with leading whitespace)
    for h in headers:
        idx = stripped_header.index(h, search_from)
        positions.append(idx)
        search_from = idx + len(h)

    # Extract values from data line using the same positions
    row = {}
    for i, (pos, hdr) in enumerate(zip(positions, headers)):
        end = positions[i + 1] if i + 1 < len(positions) else len(data_line)
        val = data_line[pos:end].strip() if pos < len(data_line) else ''
        row[hdr.strip()] = val
    return row


def parse_log(path):
    with open(path, 'r') as f:
        lines = f.read().splitlines()

    # --- Find best run params (last "Best run" section) ---
    best_idx = None
    for i, line in enumerate(lines):
        if 'Best run (trimmed mean):' in line:
            best_idx = i

    if best_idx is None:
        print(f"ERROR: no 'Best run (trimmed mean)' section found in {path}", file=sys.stderr)
        sys.exit(1)

    # Read header and data row for best run
    best_header_line, best_data_line = None, None
    for line in lines[best_idx + 1:]:
        c = strip_prefix(line)
        if c is None:
            continue
        if best_header_line is None:
            best_header_line = c
        else:
            best_data_line = c
            break

    if not best_header_line or not best_data_line:
        print("ERROR: could not parse best run section", file=sys.stderr)
        sys.exit(1)

    best_row = parse_fixed_width(best_header_line, best_data_line)
    param_cols = list(best_row.keys())   # e.g. ['T0', 'T1', 'Trimmed Mean']

    # --- Find matching row in "Measuring performance" section ---
    measure_header_line = None
    result_row = None
    in_measure = False

    for line in lines:
        if 'Measuring performance of the best runs' in line:
            in_measure = True
            continue
        if not in_measure:
            continue
        c = strip_prefix(line)
        if c is None or not c.strip():
            continue
        if measure_header_line is None:
            measure_header_line = c
            continue
        # Parse this data row
        row = parse_fixed_width(measure_header_line, c)
        # Check if param cols match
        if all(row.get(k, '').strip() == best_row[k].strip() for k in param_cols):
            result_row = row
            break

    if not result_row:
        print("ERROR: could not match best run in 'Measuring performance' section", file=sys.stderr)
        sys.exit(1)

    headers = list(result_row.keys())
    print(','.join(headers))
    print(','.join(result_row[h] for h in headers))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <log_file>", file=sys.stderr)
        sys.exit(1)
    parse_log(sys.argv[1])