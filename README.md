# dns-walker

A minimalist command-line DNS walker and checker for macOS and Linux. Queries common DNS record types, prints a tidy summary, and flags common misconfigurations. Designed to drop onto any machine with Python 3 and just work.

## Quick start

```sh
# Copy the launcher and run it
chmod +x dns-walker
./dns-walker example.com
```

On the first run, `dns-walker` creates a Python venv and installs `dnspython` automatically (takes ~5 seconds, internet required). Every subsequent run is instant.

## Usage

```
dns-walker [options] <domain>

Options:
  -h / --help    Show this help and exit
  -q / --quiet   Only print detected issues (suppress full record dump)
  -d / --debug   Show each DNS query step with resolver info and timing
```

### Examples

```sh
# Full record dump + health checks
dns-walker example.com

# for script use
dns-walker --quiet example.com

# debug output
dns-walker --debug example.com

# Pipe-friendly: exit 0 = clean, exit 1 = issues found
dns-walker -q example.com && echo "DNS looks good"
```

### Sample output

```
DNS records for example.com:
  A    : 172.66.147.243, 104.20.23.154
  AAAA : 2606:4700:10::ac42:93f3, 2606:4700:10::6814:179a
  CNAME: <none>
  MX   : 0 .
  NS   : elliott.ns.cloudflare.com., hera.ns.cloudflare.com.
  SOA  : elliott.ns.cloudflare.com. dns.cloudflare.com. 2403488901 …
  TXT  : "v=spf1 -all"

No obvious issues detected
```

## Checks performed

| Check | Flags when… |
|---|---|
| A / AAAA present | Neither record type resolves |
| NS redundancy | Fewer than 2 NS records |
| SOA present | SOA record is missing |

## Installation

### Option 1: single file (recommended)

The `dns-walker` shell script is self-contained. Copy it to any host and run it:

```sh
scp dns-walker user@host:~/bin/
ssh user@host "chmod +x ~/bin/dns-walker && dns-walker example.com"
```

The venv is stored in `/usr/local/share/dns-walker` if writable (system-wide), otherwise in `~/.local/share/dns-walker` (user-local). No root required for the fallback path.

### Option 2: uv (if you have [uv](https://github.com/astral-sh/uv) installed)

The Python file carries PEP 723 inline dependency metadata, so `uv` handles everything itself:

```sh
uv run dns_walker.py example.com
```

### Option 3: classic pip

```sh
pip install dnspython
python3 dns_walker.py example.com
```

## Requirements

- Python 3.8 or later
- Internet access on the first run (to install `dnspython`)

| Platform | Install Python |
|---|---|
| macOS | `brew install python3` |
| Debian / Ubuntu | `sudo apt install python3 python3-venv` |
| RHEL / Fedora | `sudo dnf install python3` |

## Files

| File | Purpose |
|---|---|
| `dns-walker` | Self-installing shell launcher |
| `dns_walker.py` | Python source (also usable standalone via `uv run` or `pip`) |

## Exit codes

| Code | Meaning |
|---|---|
| `0` | All checks passed |
| `1` | One or more potential issues detected |
