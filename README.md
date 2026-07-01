# Reverberus: Resilient Edge-to-Cloud Emergency System

A smart, bandwidth-efficient monitoring system for rescue operators, powered by **Eclipse Zenoh**.

## Overview
Reverberus is an innovative IoT solution designed for rescue teams operating in challenging environments. By leveraging Zenoh’s high-performance, peer-to-peer communication, the system ensures real-time tracking and emergency detection even in disconnected areas. It acts as an "Edge-to-Cloud" bridge, where local Edge nodes (Rescuers) communicate with a Command Center, which intelligently filters and forwards only critical alerts to a national Cloud backend.

## System Architecture


## Key Features
* **Edge Intelligence**: Real-time position tracking and automatic "Man-Down" detection via sensor simulation.
* **Smart Filtering**: The Command Center acts as a Gateway, minimizing network noise by only forwarding critical data (e.g., emergencies) to the Cloud.
* **Store & Forward**: Localized data storage allows historical queries via `Z_GET` without constant cloud synchronization.
* **P2P Resiliency**: Uses Zenoh in peer-to-peer mode, ensuring system functionality even when internet connectivity is intermittent.

## Getting Started

### Prerequisites
* Python 3.10+
* [Eclipse Zenoh](https://zenoh.io/) (installed via `pip install zenoh`)

### Installation
1. Clone the repository:
```bash
git clone [https://github.com/yourusername/reverberus.git](https://github.com/yourusername/reverberus.git)
cd reverberus

```

2. Install dependencies:
```bash
pip install -r requirements.txt

```



### Running the Demo

1. **Start the Cloud Backend**:
```bash
python -m cloud_backend

```


2. **Start the Command Center**:
```bash
python -m main_cmd_center

```


3. **Start the Rescuer Node**:
```bash
python -m main_rescuer

```



## License

This project is licensed under the Apache License 2.0. See the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.

## Contributing

We welcome contributions! Please feel free to open a Pull Request or submit an issue if you have suggestions for new features or hardware integrations.

