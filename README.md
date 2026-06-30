# Man-Down Rescue System (Zenoh P2P)

A decentralized IoT/Edge prototype designed for hackathons. This system provides real-time telemetry, "man-down" emergency alerts via Liveliness Tokens, and a Store & Forward mechanism using Distributed Queries.

Built entirely on a Pure P2P architecture using [Eclipse Zenoh](https://zenoh.io/).

## Repository Structure

The codebase is split into three main modules to allow parallel development without merge conflicts:
- `common/`: Shared configuration, data models, and network bootstrapping.
- `rescuer/`: Edge node logic (Telemetry, Local Storage, Queryables).
- `command_center/`: Backend logic (Subscribers, Liveliness Monitoring, Dashboards).

## Prerequisites

1. Install Python 3.9+
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt