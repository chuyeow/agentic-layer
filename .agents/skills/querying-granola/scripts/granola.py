#!/usr/bin/env python3
"""Query Granola meeting cache for context."""

import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# Cache location (macOS and Windows supported)
if sys.platform == "darwin":
    CACHE_PATH = Path.home() / "Library/Application Support/Granola/cache-v3.json"
elif sys.platform == "win32":
    CACHE_PATH = Path(os.environ.get("APPDATA", "")) / "Granola/cache-v3.json"
else:
    # Linux/other - try macOS-style path as fallback
    CACHE_PATH = Path.home() / ".config/Granola/cache-v3.json"

# Preview length thresholds (characters)
# These control how much text is shown in search results and previews
MIN_NOTES_LENGTH = 20      # Minimum chars to consider a meeting as having notes
MIN_RICH_NOTES_LENGTH = 50 # Minimum chars to prefer AI summary over user notes
PREVIEW_SHORT = 200        # Short preview (profile command)
PREVIEW_MEDIUM = 300       # Medium preview (recent command)
PREVIEW_LONG = 400         # Long preview (search command)
PREVIEW_FULL = 500         # Fuller preview (client command)

# Global caches for enriched data lookups
_panels_by_doc_id = None
_metadata_by_doc_id = None
_transcripts_by_doc_id = None


def load_cache():
    """Load and parse Granola cache. Exits gracefully if unavailable."""
    global _panels_by_doc_id, _metadata_by_doc_id, _transcripts_by_doc_id

    if not CACHE_PATH.exists():
        print(f"Error: Granola cache not found at {CACHE_PATH}")
        print("Make sure Granola is installed and has recorded meetings.")
        sys.exit(1)
    try:
        with open(CACHE_PATH, "r") as f:
            raw = json.load(f)
        cache = json.loads(raw["cache"])
        state = cache["state"]

        # Build panels lookup by document_id (AI summaries)
        _panels_by_doc_id = {}
        for panel_id, panel_data in state.get("documentPanels", {}).items():
            if isinstance(panel_data, dict):
                for inner_id, inner in panel_data.items():
                    if isinstance(inner, dict) and inner.get("document_id"):
                        doc_id = inner["document_id"]
                        if doc_id not in _panels_by_doc_id:
                            _panels_by_doc_id[doc_id] = []
                        _panels_by_doc_id[doc_id].append(inner)

        # Build metadata lookup (enriched attendee info with company names)
        _metadata_by_doc_id = state.get("meetingsMetadata", {})

        # Build transcripts lookup (raw transcript when available)
        _transcripts_by_doc_id = state.get("transcripts", {})

        return state
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error: Could not parse Granola cache: {e}")
        sys.exit(1)
    except PermissionError:
        print(f"Error: Permission denied reading {CACHE_PATH}")
        sys.exit(1)


def extract_text_from_doc(node):
    """Recursively extract text from a structured doc node."""
    if not isinstance(node, dict):
        return ""

    # Direct text node
    if node.get("type") == "text":
        return node.get("text", "")

    # Container with content array
    texts = []
    content = node.get("content") or []
    for child in content:
        texts.append(extract_text_from_doc(child))

    # Join with appropriate separator based on node type
    node_type = node.get("type", "")
    if node_type in ("paragraph", "heading", "listItem"):
        return " ".join(texts) + "\n"
    return " ".join(texts)


def get_ai_summary(doc_id):
    """Get AI-generated summary from documentPanels."""
    if _panels_by_doc_id is None:
        return ""
    panels = _panels_by_doc_id.get(doc_id, [])
    for panel in panels:
        if panel.get("title") == "Summary":
            content = panel.get("content", "")
            if isinstance(content, str):
                # HTML content - strip tags roughly
                text = re.sub(r'<[^>]+>', ' ', content)
                return ' '.join(text.split())
            elif isinstance(content, dict):
                # Structured content
                return extract_text_from_doc(content).strip()
    return ""


def get_transcript(doc_id):
    """Get raw transcript when available (only cached for recent meetings)."""
    if _transcripts_by_doc_id is None:
        return None
    chunks = _transcripts_by_doc_id.get(doc_id, [])
    if not chunks:
        return None

    # Sort by timestamp and join text
    sorted_chunks = sorted(chunks, key=lambda c: c.get("start_timestamp", ""))
    texts = [c.get("text", "") for c in sorted_chunks if c.get("text")]
    if texts:
        return " ".join(texts)
    return None


def get_enriched_attendee_info(doc_id):
    """Get enriched attendee info from meetingsMetadata (includes company names)."""
    if _metadata_by_doc_id is None:
        return {}
    meta = _metadata_by_doc_id.get(doc_id, {})
    attendees = meta.get("attendees", [])

    # Build lookup by email
    enriched = {}
    for att in attendees:
        email = att.get("email", "").lower()
        if not email:
            continue
        details = att.get("details", {})
        person = details.get("person", {})
        company = details.get("company", {})

        enriched[email] = {
            "name": person.get("name", {}).get("fullName", ""),
            "company": company.get("name", ""),
            "avatar": person.get("avatar", ""),
        }
    return enriched


def get_notes(doc, include_ai_summary=True):
    """Extract notes from a document, combining user notes and AI summary."""
    doc_id = doc.get("id", "")

    # Get AI summary first (usually richer)
    ai_summary = ""
    if include_ai_summary:
        ai_summary = get_ai_summary(doc_id)

    # Get user notes
    user_notes = ""
    notes_plain = doc.get("notes_plain") or ""
    if len(notes_plain) > MIN_NOTES_LENGTH:
        user_notes = notes_plain
    else:
        notes_md = doc.get("notes_markdown") or ""
        if len(notes_md) > MIN_NOTES_LENGTH:
            user_notes = notes_md
        else:
            notes_dict = doc.get("notes")
            if isinstance(notes_dict, dict):
                extracted = extract_text_from_doc(notes_dict).strip()
                if len(extracted) > MIN_NOTES_LENGTH // 2:
                    user_notes = extracted

    # Prefer AI summary if available (it's more comprehensive)
    if len(ai_summary) > MIN_RICH_NOTES_LENGTH:
        return ai_summary
    elif user_notes:
        return user_notes
    elif ai_summary:
        return ai_summary
    return ""


def get_attendees(doc):
    """Extract attendees from a document, enriched with company names when available."""
    doc_id = doc.get("id", "")
    attendees = []
    seen_emails = set()

    # Get enriched info from metadata (has company names)
    enriched = get_enriched_attendee_info(doc_id)

    # Try people.attendees first
    people = doc.get("people")
    if isinstance(people, dict):
        for att in people.get("attendees", []):
            if isinstance(att, dict):
                email = att.get("email", "")
                if email and email not in seen_emails:
                    seen_emails.add(email)
                    email_lower = email.lower()
                    enriched_info = enriched.get(email_lower, {})
                    attendees.append({
                        "name": enriched_info.get("name") or att.get("name", ""),
                        "email": email,
                        "company": enriched_info.get("company", ""),
                    })

    # Fallback to google_calendar_event.attendees
    if not attendees:
        gcal = doc.get("google_calendar_event")
        if isinstance(gcal, dict):
            for att in gcal.get("attendees", []):
                if isinstance(att, dict):
                    email = att.get("email", "")
                    if email and email not in seen_emails:
                        seen_emails.add(email)
                        email_lower = email.lower()
                        enriched_info = enriched.get(email_lower, {})
                        attendees.append({
                            "name": enriched_info.get("name") or att.get("displayName", ""),
                            "email": email,
                            "company": enriched_info.get("company", ""),
                        })

    return attendees


def get_email_domain(email):
    """Extract domain from email."""
    if not email or "@" not in email:
        return None
    return email.split("@")[1].lower()


def search_meetings(query: str, limit: int = 20, include_empty: bool = False):
    """Search meetings by title, content, or attendees."""
    state = load_cache()
    docs = state["documents"]
    query_lower = query.lower()

    results = []
    for doc_id, doc in docs.items():
        title = doc.get("title", "")
        notes = get_notes(doc)
        attendees = get_attendees(doc)

        # Skip meetings without notes unless requested
        if not include_empty and len(notes) < MIN_NOTES_LENGTH:
            continue

        score = 0

        # Title match (highest priority)
        if query_lower in title.lower():
            score += 3

        # Notes content match
        if query_lower in notes.lower():
            score += 1

        # Attendee name or email match
        for att in attendees:
            if query_lower in att.get("name", "").lower():
                score += 2
            if query_lower in att.get("email", "").lower():
                score += 2

        if score > 0:
            results.append((score, doc.get("created_at", ""), doc))

    # Sort by date (most recent first), then score
    results.sort(key=lambda x: (x[1], x[0]), reverse=True)

    if limit > 0:
        results = results[:limit]

    return [(doc.get("title"), doc.get("created_at", "")[:10], get_notes(doc), get_attendees(doc))
            for _, _, doc in results]


def get_meeting_context(title_query: str):
    """Get full context for a specific meeting."""
    state = load_cache()
    docs = state["documents"]
    query_lower = title_query.lower()

    # Find most recent matching meeting
    matches = []
    for doc in docs.values():
        if query_lower in doc.get("title", "").lower():
            matches.append(doc)

    if not matches:
        return None

    # Sort by date, get most recent
    matches.sort(key=lambda d: d.get("created_at", ""), reverse=True)
    doc = matches[0]
    doc_id = doc.get("id", "")

    return {
        "title": doc.get("title"),
        "date": doc.get("created_at"),
        "notes": get_notes(doc),
        "summary": doc.get("summary"),
        "overview": doc.get("overview"),
        "attendees": get_attendees(doc),
        "transcript": get_transcript(doc_id),
    }


def recent_meetings(limit: int = 20):
    """Get recent meetings with notes."""
    state = load_cache()
    docs = state["documents"]

    sorted_docs = sorted(
        docs.values(),
        key=lambda d: d.get("created_at", ""),
        reverse=True
    )

    results = []
    for doc in sorted_docs:
        notes = get_notes(doc)
        date = doc.get("created_at", "")
        if len(notes) > MIN_RICH_NOTES_LENGTH:
            results.append({
                "title": doc.get("title"),
                "date": date[:10] if date else "",
                "notes_preview": notes[:PREVIEW_MEDIUM],
                "attendees": get_attendees(doc)
            })
            if len(results) >= limit:
                break

    return results


def client_meetings(client_name: str, limit: int = 0):
    """Get meetings related to a specific name (by title, notes, or email)."""
    # limit=0 means no limit
    return search_meetings(client_name, limit=limit, include_empty=False)


def domain_stats():
    """Get meeting counts by email domain."""
    state = load_cache()
    docs = state["documents"]

    domain_counts = Counter()
    domain_contacts = {}  # domain -> set of names

    for doc in docs.values():
        attendees = get_attendees(doc)
        for att in attendees:
            domain = get_email_domain(att.get("email", ""))
            if domain:
                domain_counts[domain] += 1
                if domain not in domain_contacts:
                    domain_contacts[domain] = set()
                name = att.get("name") or att.get("email", "").split("@")[0]
                if name:
                    domain_contacts[domain].add(name)

    return [(domain, count, list(domain_contacts[domain])[:5])
            for domain, count in domain_counts.most_common(30)]


def people_stats():
    """Get meeting counts by person."""
    state = load_cache()
    docs = state["documents"]

    person_counts = Counter()
    person_emails = {}

    for doc in docs.values():
        attendees = get_attendees(doc)
        for att in attendees:
            email = att.get("email", "")
            name = att.get("name") or email.split("@")[0]
            if email:
                person_counts[name] += 1
                person_emails[name] = email

    return [(name, count, person_emails.get(name, ""))
            for name, count in person_counts.most_common(30)]


def company_profile(domain: str):
    """Get comprehensive profile for a company by email domain."""
    state = load_cache()
    docs = state["documents"]
    domain_lower = domain.lower().replace("@", "")

    meetings = []
    meetings_without_notes = 0
    contacts = {}  # email -> {name, count, last_seen}

    for doc in docs.values():
        attendees = get_attendees(doc)
        domain_match = False

        for att in attendees:
            email = att.get("email", "").lower()
            if domain_lower in email:
                domain_match = True
                name = att.get("name") or email.split("@")[0]
                company = att.get("company", "")
                if email not in contacts:
                    contacts[email] = {"name": name, "company": company, "count": 0, "last_seen": ""}
                contacts[email]["count"] += 1
                # Update company if we get a better value
                if company and not contacts[email].get("company"):
                    contacts[email]["company"] = company
                date = doc.get("created_at", "")
                if date > contacts[email]["last_seen"]:
                    contacts[email]["last_seen"] = date

        if domain_match:
            notes = get_notes(doc)
            if len(notes) > MIN_NOTES_LENGTH:
                meetings.append({
                    "title": doc.get("title"),
                    "date": doc.get("created_at", "")[:10],
                    "attendees": attendees,
                    "notes_preview": notes[:PREVIEW_SHORT]
                })
            else:
                meetings_without_notes += 1

    # Sort meetings by date
    meetings.sort(key=lambda m: m["date"], reverse=True)

    # Sort contacts by meeting count
    sorted_contacts = sorted(contacts.items(), key=lambda x: x[1]["count"], reverse=True)

    return {
        "domain": domain_lower,
        "meetings_with_notes": len(meetings),
        "meetings_without_notes": meetings_without_notes,
        "contacts": sorted_contacts[:10],
        "recent_meetings": meetings[:10],
        "first_meeting": meetings[-1]["date"] if meetings else None,
        "last_meeting": meetings[0]["date"] if meetings else None,
    }


def timeline(query: str, months: int = 12):
    """Show meeting frequency over time for a query."""
    state = load_cache()
    docs = state["documents"]
    query_lower = query.lower()

    # Group meetings by month
    monthly = defaultdict(list)

    for doc in docs.values():
        title = doc.get("title", "")
        notes = get_notes(doc)
        attendees = get_attendees(doc)
        date = doc.get("created_at", "")

        if len(notes) < MIN_NOTES_LENGTH:
            continue

        match = False
        if query_lower in title.lower() or query_lower in notes.lower():
            match = True
        for att in attendees:
            if query_lower in att.get("email", "").lower() or query_lower in att.get("name", "").lower():
                match = True

        if match and date:
            month_key = date[:7]  # YYYY-MM
            monthly[month_key].append(title)

    # Get last N months
    now = datetime.now()
    result = []
    for i in range(months):
        d = now - timedelta(days=30 * i)
        key = d.strftime("%Y-%m")
        meetings = monthly.get(key, [])
        result.append((key, len(meetings), meetings[:5]))

    return result


def stale_clients(days: int = 60):
    """Find domains with no recent meetings."""
    state = load_cache()
    docs = state["documents"]

    domain_last_seen = {}
    domain_total = Counter()

    for doc in docs.values():
        date = doc.get("created_at", "")
        attendees = get_attendees(doc)
        for att in attendees:
            domain = get_email_domain(att.get("email", ""))
            if domain:
                domain_total[domain] += 1
                if domain not in domain_last_seen or date > domain_last_seen[domain]:
                    domain_last_seen[domain] = date

    # Filter to domains with at least 3 meetings but none recently
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    stale = []
    for domain, last_date in domain_last_seen.items():
        if domain_total[domain] >= 3 and last_date < cutoff:
            stale.append((domain, domain_total[domain], last_date[:10]))

    stale.sort(key=lambda x: x[2])  # Oldest first
    return stale


def active_clients(days: int = 30):
    """Find most active domains in recent period."""
    state = load_cache()
    docs = state["documents"]

    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    domain_counts = Counter()
    domain_contacts = defaultdict(set)

    for doc in docs.values():
        date = doc.get("created_at", "")
        if date < cutoff:
            continue
        attendees = get_attendees(doc)
        for att in attendees:
            domain = get_email_domain(att.get("email", ""))
            if domain:
                domain_counts[domain] += 1
                name = att.get("name") or att.get("email", "").split("@")[0]
                domain_contacts[domain].add(name)

    return [(domain, count, list(domain_contacts[domain])[:3])
            for domain, count in domain_counts.most_common(20)]


def format_attendees(attendees, show_email=False, show_company=False):
    """Format attendees for display."""
    if not attendees:
        return ""
    parts = []
    for a in attendees:
        if not a.get("email") and not a.get("name"):
            continue
        name = a.get("name") or a.get("email", "").split("@")[0]
        company = a.get("company", "")

        if show_email and show_company and company:
            parts.append(f"{name} <{a['email']}> @ {company}")
        elif show_email:
            parts.append(f"{name} <{a['email']}>")
        elif show_company and company:
            parts.append(f"{name} @ {company}")
        else:
            parts.append(name)

    return ", ".join(parts[:5]) + ("..." if len(parts) > 5 else "")


def print_help():
    print("""Granola Meeting Query Tool

Commands:
  search <query> [--limit N]  Search meetings by title, content, or attendees
  client <name> [--limit N]   Get all meetings for a name (no limit by default)
  context <title>             Get full notes for a specific meeting
  recent [N]                  List N most recent meetings (default 20)
  domains                     Show meeting counts by email domain
  people                      Show meeting counts by person
  profile <domain>            Get comprehensive company profile by email domain
  timeline <query> [N]        Show meeting frequency over time (default 12 months)
  active [N]                  Show most active domains in last N days (default 30)
  stale [N]                   Show domains with no meetings in N days (default 60)

Examples:
  granola.py client acme
  granola.py client "John Smith" --limit 5
  granola.py search "quarterly review"
  granola.py context "Team Standup"
  granola.py domains
  granola.py people
  granola.py profile acme.com
  granola.py timeline acme
  granola.py active 14
  granola.py stale 90
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    cmd = sys.argv[1]

    # Parse --limit flag
    limit = None
    args = sys.argv[2:]
    if "--limit" in args:
        idx = args.index("--limit")
        if idx + 1 < len(args):
            limit = int(args[idx + 1])
            args = args[:idx] + args[idx+2:]

    if cmd == "help" or cmd == "--help":
        print_help()

    elif cmd == "search" and args:
        query = " ".join(args)
        results = search_meetings(query, limit=limit or 20)
        print(f"Found {len(results)} meetings matching '{query}':\n")
        for title, date, notes, attendees in results:
            print(f"## {title} ({date})")
            if attendees:
                print(f"**Attendees**: {format_attendees(attendees)}")
            preview = notes[:PREVIEW_LONG].strip()
            if preview:
                print(preview + ("..." if len(notes) > PREVIEW_LONG else ""))
            print()

    elif cmd == "recent":
        n = int(args[0]) if args else 20
        results = recent_meetings(n)
        print(f"Recent {len(results)} meetings:\n")
        for m in results:
            print(f"## {m['title']} ({m['date']})")
            if m['attendees']:
                print(f"**Attendees**: {format_attendees(m['attendees'])}")
            print(m['notes_preview'][:PREVIEW_MEDIUM])
            print()

    elif cmd == "client" and args:
        client = " ".join(args)
        results = client_meetings(client, limit=limit or 0)
        print(f"Found {len(results)} meetings for '{client}':\n")
        for title, date, notes, attendees in results:
            print(f"## {title} ({date})")
            if attendees:
                print(f"**Attendees**: {format_attendees(attendees)}")
            preview = notes[:PREVIEW_FULL].strip()
            if preview:
                print(preview + ("..." if len(notes) > PREVIEW_FULL else ""))
            print()

    elif cmd == "context" and args:
        title_query = " ".join(args)
        ctx = get_meeting_context(title_query)
        if ctx:
            print(f"# {ctx['title']}")
            print(f"**Date**: {ctx['date'][:10] if ctx['date'] else 'Unknown'}")
            if ctx['attendees']:
                print(f"**Attendees**: {format_attendees(ctx['attendees'], show_email=True, show_company=True)}")
            if ctx['overview']:
                print(f"\n**Overview**: {ctx['overview']}")
            print(f"\n## Notes\n\n{ctx['notes']}")
            if ctx.get('transcript'):
                print(f"\n## Transcript\n\n{ctx['transcript']}")
        else:
            print(f"No meeting found matching '{title_query}'")

    elif cmd == "domains":
        stats = domain_stats()
        print("Meeting counts by email domain:\n")
        for domain, count, contacts in stats:
            contacts_str = ", ".join(contacts[:3])
            print(f"  {domain}: {count} meetings ({contacts_str})")

    elif cmd == "people":
        stats = people_stats()
        print("Meeting counts by person:\n")
        for name, count, email in stats:
            print(f"  {name}: {count} meetings ({email})")

    elif cmd == "profile" and args:
        domain = args[0]
        profile = company_profile(domain)
        print(f"# Company Profile: {profile['domain']}\n")
        print(f"**Meetings with Notes**: {profile['meetings_with_notes']}")
        if profile['meetings_without_notes'] > 0:
            print(f"**Meetings without Notes**: {profile['meetings_without_notes']}")
        print(f"**First Meeting**: {profile['first_meeting'] or 'N/A'}")
        print(f"**Last Meeting**: {profile['last_meeting'] or 'N/A'}\n")

        print("## Contacts")
        for email, info in profile['contacts']:
            company_str = f" @ {info['company']}" if info.get('company') else ""
            print(f"  - {info['name']} <{email}>{company_str} ({info['count']} meetings, last: {info['last_seen'][:10]})")

        print("\n## Recent Meetings")
        for m in profile['recent_meetings'][:5]:
            print(f"\n### {m['title']} ({m['date']})")
            print(f"Attendees: {format_attendees(m['attendees'], show_company=True)}")
            print(m['notes_preview'][:PREVIEW_SHORT])

    elif cmd == "timeline" and args:
        query = args[0]
        months = int(args[1]) if len(args) > 1 else 12
        results = timeline(query, months)
        print(f"Meeting timeline for '{query}' (last {months} months):\n")
        for month, count, titles in results:
            bar = "█" * count
            print(f"  {month}: {bar} ({count})")
            if titles and count > 0:
                for t in titles[:2]:
                    print(f"           └─ {t[:50]}")

    elif cmd == "active":
        days = int(args[0]) if args else 30
        results = active_clients(days)
        print(f"Most active domains in last {days} days:\n")
        for domain, count, contacts in results:
            contacts_str = ", ".join(contacts)
            print(f"  {domain}: {count} meetings ({contacts_str})")

    elif cmd == "stale":
        days = int(args[0]) if args else 60
        results = stale_clients(days)
        print(f"Domains with no meetings in {days}+ days:\n")
        if not results:
            print("  None - all domains are active!")
        for domain, total, last_date in results:
            print(f"  {domain}: {total} total meetings, last: {last_date}")

    else:
        print(f"Unknown command: {cmd}")
        print_help()
