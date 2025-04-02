import re
from collections import Counter
from typing import Dict

LOG_PATTERN = re.compile(
    r"(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "
    r'"(?P<method>\S+) (?P<url>\S+) (?P<protocol>[^"]+)" '
    r"(?P<status>\d{3}) (?P<size>\d+) "
    r'"(?P<referrer>[^"]*)" "(?P<user_agent>[^"]*)" "(?P<extra>[^"]*)"'
)


def parse_file(file_path: str) -> Dict[str, any]:
    methods = Counter()
    statuses = Counter()
    user_agents = Counter()
    ip_addresses = Counter()
    total = 0

    with open(file_path, encoding="utf-8") as f:
        for line in f:
            match = LOG_PATTERN.match(line)
            if match:
                data = match.groupdict()
                total += 1
                methods[data["method"]] += 1
                statuses[data["status"]] += 1
                user_agents[data["user_agent"]] += 1
                ip_addresses[data["ip"]] += 1

    return {
        "total_requests": total,
        "methods": methods.most_common(),
        "statuses": statuses.most_common(),
        "top_user_agents": user_agents.most_common(5),
        "top_ip_addresses": ip_addresses.most_common(5),
    }
