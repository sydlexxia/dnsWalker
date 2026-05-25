#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#   "dnspython>=2.0",
# ]
# ///
"""
DNS Walker – minimalist command-line DNS walker / checker

Usage:
  dns-walker [options] <domain>
  python3 dns_walker.py [options] <domain>
  uv run dns_walker.py [options] <domain>      # uv handles deps automatically

Options:
  -h / --help    Show this help and exit
  -q / --quiet   Only print detected issues (suppress full record dump)
  -d / --debug   Show each DNS query step with resolver info and timing

Checks performed:
  • A / AAAA records present
  • At least 2 NS records (fault tolerance)
  • SOA record present (zone sanity)

Exit status: 0 = all checks passed, 1 = potential issues detected.
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Dict, List

import dns.exception
import dns.resolver

RECORD_TYPES = ("A", "AAAA", "CNAME", "MX", "NS", "SOA", "TXT")


def _query(domain: str, rtype: str, debug: bool = False) -> List[str]:
    """Return rrdata strings or diagnostic tokens for a record type."""
    if debug:
        print(f"  [debug] querying {rtype} for {domain} …", file=sys.stderr, flush=True)
    t0 = time.monotonic()
    try:
        answers = dns.resolver.resolve(domain, rtype, lifetime=5)
        result = [a.to_text() for a in answers]
    except dns.resolver.NXDOMAIN:
        result = ["NXDOMAIN"]
    except dns.resolver.NoAnswer:
        result = []
    except dns.exception.Timeout:
        result = ["TIMEOUT"]
    except Exception as exc:
        result = [f"ERROR:{type(exc).__name__}:{exc}"]
    if debug:
        elapsed = time.monotonic() - t0
        label = ", ".join(result) if result else "<no records>"
        print(f"  [debug]   → {label} ({elapsed:.3f}s)", file=sys.stderr, flush=True)
    return result


def collect_records(domain: str, debug: bool = False) -> Dict[str, List[str]]:
    if debug:
        resolver = dns.resolver.get_default_resolver()
        ns_list = [str(ns) for ns in getattr(resolver, "nameservers", [])]
        print(f"[debug] resolver(s): {', '.join(ns_list) or 'system default'}", file=sys.stderr)
        print(f"[debug] querying {len(RECORD_TYPES)} record types: {', '.join(RECORD_TYPES)}", file=sys.stderr)
    return {rt: _query(domain, rt, debug=debug) for rt in RECORD_TYPES}


def _real_records(values: List[str]) -> List[str]:
    """Strip diagnostic tokens, return only real DNS answers."""
    return [v for v in values if not v.startswith(("NXDOMAIN", "TIMEOUT", "ERROR:"))]


def analyse(records: Dict[str, List[str]]) -> List[str]:
    issues: List[str] = []

    if not _real_records(records.get("A", [])) and not _real_records(records.get("AAAA", [])):
        issues.append("No A or AAAA records – site may be unreachable over HTTP/HTTPS.")

    if len(_real_records(records.get("NS", []))) < 2:
        issues.append("Fewer than two NS records – poor fault tolerance.")

    if not _real_records(records.get("SOA", [])):
        issues.append("SOA record missing – zone may be malformed.")

    return issues


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="dns-walker",
        description="Walk DNS records and detect common issues.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Exit status: 0 = all checks passed, 1 = potential issues detected.",
    )
    parser.add_argument("domain", help="Domain name to inspect (e.g. example.com)")
    parser.add_argument("-q", "--quiet", action="store_true", help="Only output detected issues")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Show each DNS query step with resolver info and timing")
    args = parser.parse_args(argv)

    domain = args.domain.strip().rstrip(".")
    if not domain or " " in domain or len(domain) > 253:
        parser.error(f"Invalid domain name: {args.domain!r}")

    if args.debug:
        print(f"[debug] starting DNS walk for: {domain}", file=sys.stderr)

    records = collect_records(domain, debug=args.debug)
    problems = analyse(records)

    if args.debug:
        print(f"[debug] analysis complete — {len(problems)} issue(s) found", file=sys.stderr)

    if not args.quiet:
        print(f"\nDNS records for {domain}:")
        for rtype, answers in records.items():
            human = ", ".join(answers) if answers else "<none>"
            print(f"  {rtype:5}: {human}")
        print()

    if problems:
        print("Potential issues detected:")
        for p in problems:
            print(f" • {p}")
        sys.exit(1)
    else:
        print("No obvious issues detected – all basic checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
