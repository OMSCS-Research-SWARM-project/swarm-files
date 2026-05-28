# Event JSON Specification 
This document defines the structured JSON event format.

Students in the SWARM project will get 2 files 
1. events file with just the events array (the input for the malware analysis agent)
1.  sample classifications files with just the classifications array (for assessing accuracy)
    - Use the check_agent_output.py script to validate your local agent run vs the expected output

## 1. Top-Level Structure

The output is a JSON object with three primary arrays:

- `events`: A collection of extracted network conversations (sessions), each with a timestamp and optional scenario ID.
- `classifications`: Labels and metadata attached to those events.
- `mapped_cves`: A deduplicated quick-reference list of all CVEs assigned anywhere in the output.

```json
{
  "events": [],
  "classifications": [],
  "mapped_cves": []
}
```

## 2. Event Object Spec

Each entry in the `events` array represents a logical network conversation.

### Fields

- `id` (integer): A unique identifier for the event.
- `scenario_id` (integer | null): Optional identifier for grouping related DoS events into a shared attack scenario.
- `timestamp` (string): ISO 8601 UTC timestamp of the first packet that belongs to the emitted event (e.g., `"2026-03-20T01:29:00.700711Z"`).
- `protocol` (string): The detected protocol. Values: `"telnet"`, `"http"`, `"tcp"`, `"unknown"`.
- `tcp_ip` (object): Metadata about the transport layer.
    - `src_ip` (string): Source IP address.
    - `dst_ip` (string): Destination IP address.
    - `src_port` (integer): Source TCP port.
    - `dst_port` (integer): Destination TCP port.
    - `tcp_flag_flow` (array of arrays of strings): Ordered TCP flag lists for packets sent by the event source (`tcp_ip.src_ip` / `tcp_ip.src_port`) only. Values: `"fin"`, `"syn"`, `"rst"`, `"psh"`, `"ack"`, `"urg"`, `"ece"`, `"cwr"`.
- `protocol_data` (array of objects): Ordered sequence of data exchanged. The shape of objects in this array depends on the `protocol`.

#### Telnet `protocol_data`
When `protocol == "telnet"`, `protocol_data` contains an ordered sequence of payload snippets:
- `sender_ip` (string): IP address of the sender of this payload snippet.
- `payload` (string): The actual text content (UTF-8 decoded).

#### HTTP `protocol_data`
When `protocol == "http"`, `protocol_data` contains an ordered sequence of reconstructed HTTP transactions:
- `request` (string): Full reconstructed HTTP request text, including headers and body.
- `response` (string | null): Full reconstructed HTTP response text, including headers and body. May be `null` if no response was reconstructed.

### Example Event (Telnet)

```json
{
  "id": 1,
  "scenario_id": null,
  "timestamp": "2026-03-20T01:29:00.700711Z",
  "tcp_ip": {
    "src_ip": "10.42.1.108",
    "dst_ip": "10.42.1.230",
    "src_port": 24848,
    "dst_port": 2323,
    "tcp_flag_flow": [
      ["syn"],
      ["ack"],
      ["psh", "ack"]
    ]
  },
  "protocol": "telnet",
  "protocol_data": [
    {
      "sender_ip": "10.42.1.108",
      "payload": "root\r\n"
    },
    {
      "sender_ip": "10.42.1.230",
      "payload": "Password: "
    }
  ]
}
```

### Example Event (HTTP)

```json
{
  "id": 21,
  "scenario_id": null,
  "timestamp": "2026-03-20T01:34:10.104000Z",
  "tcp_ip": {
    "src_ip": "10.42.1.108",
    "dst_ip": "10.42.1.230",
    "src_port": 37226,
    "dst_port": 80,
    "tcp_flag_flow": [
      ["syn"],
      ["ack"],
      ["psh", "ack"]
    ]
  },
  "protocol": "http",
  "protocol_data": [
    {
      "request": "POST /videostream.cgi HTTP/1.1\r\nHost: 10.42.1.230\r\nContent-Length: 20\r\n\r\nuser=admin&pwd=admin",
      "response": "HTTP/1.1 200 OK\r\nServer: INetSim HTTP Server\r\nContent-Length: 0\r\n\r\n"
    }
  ]
}
```

### Example Event (HTTP - Grouped DoS)

```json
{
  "id": 61,
  "scenario_id": 1,
  "timestamp": "2026-03-20T01:35:00.104000Z",
  "tcp_ip": {
    "src_ip": "10.42.1.108",
    "dst_ip": "10.42.1.230",
    "src_port": 38000,
    "dst_port": 80,
    "tcp_flag_flow": [
      ["syn"],
      ["ack"],
      ["psh", "ack"]
    ]
  },
  "protocol": "http",
  "protocol_data": [
    {
      "request": "GET / HTTP/1.1\r\nHost: 10.42.1.230\r\n\r\n",
      "response": "HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n"
    }
  ]
}
```

## 3. Classification Object Spec

### Fields

- `event_id` (integer): Reference to the `id` of an event.
- `classification` (string): The behavioral label. Values:
    - `"telnet_bruteforce"`: Telnet sessions showing credential spray or post-login Mirai execution.
    - `"http_exploit"`: HTTP exploit or probe attempts.
    - `"http_dos"`: HTTP traffic on the non-scanner side of the dataset-specific binary split, including grouped HTTP DDoS activity.
    - `"tcp_dos"`: TCP traffic matching DDoS flood patterns.
    - `benign`: This is not extracted from the pcap, but it is synthetically created for the student data
- `scenario_id` (integer | null): Must match the `scenario_id` of the corresponding event for grouped DoS scenarios.
- `cve` (string | null): The single **best primary CVE** for the event, or `null`.

### Example Classification (Exploit)

```json
{
  "event_id": 21,
  "classification": "http_exploit",
  "scenario_id": null,
  "cve": "CVE-2025-34037"
}
```

### Example Classification (HTTP DoS)

```json
{
  "event_id": 61,
  "classification": "http_dos",
  "scenario_id": 1,
  "cve": null
}
```

### Semantics

- `cve` is the primary per-event CVE field.
- `mapped_cves` is the top-level deduplicated quick-reference list of matched CVEs.
- **Dataset-Specific HTTP Classification:** In this dataset, HTTP classification uses a binary split. HTTP sessions that match scanner/exploit behavior are labeled `http_exploit`. HTTP sessions that do not match scanner behavior are labeled `http_dos`.
- CVE mapping is optional enrichment for `http_exploit` events only.
- Under the current dataset rule, `http_dos` events normally use `cve: null`.
- HTTP exploit events with `cve: null` do not add anything to `mapped_cves`.

## 4. Scenario Grouping Rules

- **Applicability:** Scenario grouping is applied to `http_dos` and `tcp_dos` events.
- **Semantics:** For HTTP, `scenario_id` is used to link related `http_dos` events that belong to the same grouped burst or contiguous attack window.
- **Continuity:** Events are grouped if they share the same target (IP, Port, Protocol) and classification, and occur within a **5-second** gap of each other.
- **Scenario ID:** Shared between all events and classifications in the same contiguous attack window.
