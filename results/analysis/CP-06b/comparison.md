# Static held-out team comparison

Generated from raw CSV. All maps and planning/time-limit failures are included in success denominators. Makespan/moves means include successes only. Seed std describes variation across five models, not independent map uncertainty. Attempts are rejected agents per tick; actual collisions are checked separately.

| Method | Agents | Successes / episodes | Success rate | Seed std | Successful makespan | Successful moves | Mean attempts | Planning failures | Actual collisions |
|---|---|---|---|---|---|---|---|---|---|
| astar | 2 | 18 / 20 | 90.0% | n/a | 4.389 | 7.167 | 0.000 | 2 | 0 |
| astar | 4 | 16 / 20 | 80.0% | n/a | 6.125 | 15.438 | 0.000 | 4 | 0 |
| bfs | 2 | 18 / 20 | 90.0% | n/a | 4.389 | 7.167 | 0.000 | 2 | 0 |
| bfs | 4 | 16 / 20 | 80.0% | n/a | 6.125 | 15.312 | 0.000 | 4 | 0 |
| dijkstra | 2 | 18 / 20 | 90.0% | n/a | 4.389 | 7.167 | 0.000 | 2 | 0 |
| dijkstra | 4 | 16 / 20 | 80.0% | n/a | 6.125 | 15.312 | 0.000 | 4 | 0 |
| shared | 2 | 61 / 100 | 61.0% | 0.065 | 3.836 | 5.934 | 3.420 | 0 | 0 |
| shared | 4 | 25 / 100 | 25.0% | 0.035 | 6.760 | 12.680 | 27.280 | 0 | 0 |
| solo | 2 | 64 / 100 | 64.0% | 0.042 | 3.719 | 5.875 | 5.110 | 0 | 0 |
| solo | 4 | 27 / 100 | 27.0% | 0.027 | 5.148 | 12.630 | 32.580 | 0 | 0 |
| untrained | 2 | 1 / 100 | 1.0% | 0.022 | 1.000 | 2.000 | 0.740 | 0 | 0 |
| untrained | 4 | 0 / 100 | 0.0% | 0.000 | n/a | n/a | 13.800 | 0 | 0 |
