import os
import sys
from unittest.mock import mock_open, patch

from log_parser import parse_file

# Добавляем путь к корню проекта
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sample_log = """
192.168.1.1 - anna [17/Feb/2025:03:41:02 +0300] "PROPFIND /remote.php HTTP/1.1" 207 234 "-" "Nextcloud/3.6.4" "-"
192.168.1.1 - - [17/Feb/2025:03:41:07 +0300] "POST /api/v4/jobs/request HTTP/1.1" 502 24 "-" "gitlab-runner" "-"
81.171.3.204 - - [17/Feb/2025:03:41:44 +0300] "GET / HTTP/1.1" 502 166 "-" "Mozilla/5.0" "-"
"""


def test_parse_sample_log():
    with patch("builtins.open", mock_open(read_data=sample_log)):
        result = parse_file("fake.log")

    assert result["total_requests"] == 3
    assert ("PROPFIND", 1) in result["methods"]
    assert ("POST", 1) in result["methods"]
    assert ("GET", 1) in result["methods"]

    assert ("502", 2) in result["statuses"]
    assert ("207", 1) in result["statuses"]

    assert any("Nextcloud" in ua[0] for ua in result["top_user_agents"])
    assert any(ip[0] == "192.168.1.1" for ip in result["top_ip_addresses"])
