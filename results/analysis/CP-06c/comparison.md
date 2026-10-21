# Paired static/dynamic team transfer

Generated from measured CSV. All failures/empty schedules are retained. Path/time means include successes only. Five model seeds reuse the same 20 geometries. Frozen controls retry independent original routes. Early completion stops later events. The static-trained policies receive no online updates.

| Method | Agents | Condition | Successes / episodes | Success | Successful makespan | Successful moves | Mean attempts | Mean plan calls | Mean plan failures | Episodes seeing addition |
|---|---|---|---|---|---|---|---|---|---|---|
| astar | 2 | static | 18 / 20 | 90.0% | 4.389 | 7.167 | 0.000 | 1.000 | 0.100 | 0 |
| astar | 4 | static | 16 / 20 | 80.0% | 6.125 | 15.438 | 0.000 | 1.000 | 0.200 | 0 |
| astar_frozen | 2 | static | 18 / 20 | 90.0% | 4.389 | 7.167 | 0.000 | 1.000 | 0.100 | 0 |
| astar_frozen | 4 | static | 16 / 20 | 80.0% | 6.125 | 15.438 | 0.000 | 1.000 | 0.200 | 0 |
| bfs | 2 | static | 18 / 20 | 90.0% | 4.389 | 7.167 | 0.000 | 1.000 | 0.100 | 0 |
| bfs | 4 | static | 16 / 20 | 80.0% | 6.125 | 15.312 | 0.000 | 1.000 | 0.200 | 0 |
| bfs_frozen | 2 | static | 18 / 20 | 90.0% | 4.389 | 7.167 | 0.000 | 1.000 | 0.100 | 0 |
| bfs_frozen | 4 | static | 16 / 20 | 80.0% | 6.125 | 15.312 | 0.000 | 1.000 | 0.200 | 0 |
| dijkstra | 2 | static | 18 / 20 | 90.0% | 4.389 | 7.167 | 0.000 | 1.000 | 0.100 | 0 |
| dijkstra | 4 | static | 16 / 20 | 80.0% | 6.125 | 15.312 | 0.000 | 1.000 | 0.200 | 0 |
| dijkstra_frozen | 2 | static | 18 / 20 | 90.0% | 4.389 | 7.167 | 0.000 | 1.000 | 0.100 | 0 |
| dijkstra_frozen | 4 | static | 16 / 20 | 80.0% | 6.125 | 15.312 | 0.000 | 1.000 | 0.200 | 0 |
| shared | 2 | static | 61 / 100 | 61.0% | 3.836 | 5.934 | 3.420 | 0.000 | 0.000 | 0 |
| shared | 4 | static | 25 / 100 | 25.0% | 6.760 | 12.680 | 27.280 | 0.000 | 0.000 | 0 |
| solo | 2 | static | 64 / 100 | 64.0% | 3.719 | 5.875 | 5.110 | 0.000 | 0.000 | 0 |
| solo | 4 | static | 27 / 100 | 27.0% | 5.148 | 12.630 | 32.580 | 0.000 | 0.000 | 0 |
| untrained | 2 | static | 1 / 100 | 1.0% | 1.000 | 2.000 | 0.740 | 0.000 | 0.000 | 0 |
| untrained | 4 | static | 0 / 100 | 0.0% | n/a | n/a | 13.800 | 0.000 | 0.000 | 0 |
| astar | 2 | dynamic | 18 / 20 | 90.0% | 5.833 | 8.611 | 0.000 | 2.250 | 0.350 | 19 |
| astar | 4 | dynamic | 16 / 20 | 80.0% | 7.562 | 18.812 | 0.000 | 2.600 | 0.600 | 20 |
| astar_frozen | 2 | dynamic | 18 / 20 | 90.0% | 7.722 | 7.167 | 0.650 | 1.000 | 0.100 | 19 |
| astar_frozen | 4 | dynamic | 13 / 20 | 65.0% | 10.308 | 14.615 | 9.600 | 1.000 | 0.200 | 20 |
| bfs | 2 | dynamic | 18 / 20 | 90.0% | 5.833 | 8.611 | 0.000 | 2.250 | 0.350 | 19 |
| bfs | 4 | dynamic | 16 / 20 | 80.0% | 7.688 | 18.812 | 0.000 | 2.600 | 0.600 | 20 |
| bfs_frozen | 2 | dynamic | 18 / 20 | 90.0% | 7.722 | 7.167 | 0.650 | 1.000 | 0.100 | 19 |
| bfs_frozen | 4 | dynamic | 14 / 20 | 70.0% | 10.286 | 14.857 | 7.350 | 1.000 | 0.200 | 20 |
| dijkstra | 2 | dynamic | 18 / 20 | 90.0% | 5.833 | 8.611 | 0.000 | 2.250 | 0.350 | 19 |
| dijkstra | 4 | dynamic | 16 / 20 | 80.0% | 7.688 | 18.812 | 0.000 | 2.600 | 0.600 | 20 |
| dijkstra_frozen | 2 | dynamic | 18 / 20 | 90.0% | 7.722 | 7.167 | 0.650 | 1.000 | 0.100 | 19 |
| dijkstra_frozen | 4 | dynamic | 14 / 20 | 70.0% | 10.286 | 14.857 | 7.350 | 1.000 | 0.200 | 20 |
| shared | 2 | dynamic | 58 / 100 | 58.0% | 4.914 | 6.534 | 3.420 | 0.000 | 0.000 | 95 |
| shared | 4 | dynamic | 25 / 100 | 25.0% | 8.360 | 12.600 | 27.100 | 0.000 | 0.000 | 100 |
| solo | 2 | dynamic | 61 / 100 | 61.0% | 4.754 | 6.443 | 5.100 | 0.000 | 0.000 | 95 |
| solo | 4 | dynamic | 28 / 100 | 28.0% | 7.321 | 13.107 | 31.690 | 0.000 | 0.000 | 100 |
| untrained | 2 | dynamic | 1 / 100 | 1.0% | 1.000 | 2.000 | 0.820 | 0.000 | 0.000 | 99 |
| untrained | 4 | dynamic | 0 / 100 | 0.0% | n/a | n/a | 13.870 | 0.000 | 0.000 | 100 |
