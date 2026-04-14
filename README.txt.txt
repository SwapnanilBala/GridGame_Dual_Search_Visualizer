GridWorld Dual Search Visualizer

An interactive pathfinding tool to compare classic search algorithms on grid-based maps.

Overview:
This project allows running two search algorithms simultaneously on the same grid world, visualizing their behavior in real-time using Pygame and generating performance comparisons using Matplotlib.

Features:
- Side-by-side algorithm comparison
- Real-time visualization of node expansion and pathfinding
- Supports weighted terrain (Road=1, Mud=5, Water=10)
- Interactive UI for selecting maps, algorithms, and speed
- Automatic performance charts and summaries

Algorithms Implemented:
- A* (heuristic-based, optimal)
- BFS (shortest path for equal cost)
- DFS (depth-first exploration)
- DLS (depth-limited DFS)
- UCS (cost-aware optimal search)
- Bidirectional Search (faster BFS variant)

Tech Stack:
Python, Pygame, Matplotlib

Goal:
To demonstrate and compare how different search strategies behave in terms of efficiency, optimality, and exploration patterns.

Usage:
Run the launcher, select a map and algorithms, and visualize their behavior in real time.
