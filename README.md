# Distributed computing for Calculating N-grams

This project is developed by leveraging key distributed computing principles. It is designed with a focus on
dynamic host discovery to ensure seamless node integration and scalability as new hosts join the network. Moreover,
the system is implemented with fault tolerance mechanisms, such as heartbeat monitoring, to detect and mitigate
node failures swiftly, preventing disruptions in data processing. Using the Bully
algorithm, facilitates efficient leader election, enabling any node to assume leadership for data distribution and
result synchronisation. The adoption of ordered reliable multicast ensures consistent delivery and synchronisation of
n-gram results, enhancing reliability and maintaining data consistency across distributed nodes. Altogether, these
contribute to a scalable, reliable and consistent distributed computing environment, crucial for effective textual data
analysis in today's data driven landscape.

### Dynamic Host Discovery:
Efficiently adapts to network changes using broadcast communication, minimizing overhead. Utilizes UDP for lightweight, efficient discovery without persistent connections.

### Fault Tolerance:
Ensures system reliability with heartbeat monitoring, swiftly redistributing tasks upon node failures. Proactively elects new master nodes to maintain seamless operation.

### Voting:
Employs the Bully algorithm for leader election, allowing any node to become leader, ensuring decentralization and flexibility for efficient data distribution.

### Ordered Reliable Multicasting:
Facilitates orderly communication between nodes, essential for coordinating tasks. Implements FIFO queue strategy for fair message handling, streamlining data processing.