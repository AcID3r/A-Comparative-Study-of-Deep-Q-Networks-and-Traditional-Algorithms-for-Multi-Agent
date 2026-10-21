# Held-out transfer comparison

Generated from measured CSV. Success uses all test maps, including initially unreachable ones. Means of moves/arrival are successful episodes only. Seed standard deviation describes variation across trained models, not independent map uncertainty.

| Method | Condition | Successes / episodes | Mean seed success | Seed std | Successful mean moves | Successful mean arrival |
|---|---|---|---|---|---|---|
| astar | static | 49 / 50 | 98.0% | n/a | 8.000 | 8.000 |
| astar | dynamic | 49 / 50 | 98.0% | n/a | 8.000 | 8.510 |
| astar_frozen | static | 49 / 50 | 98.0% | n/a | 8.000 | 8.000 |
| astar_frozen | dynamic | 49 / 50 | 98.0% | n/a | 8.000 | 8.510 |
| bfs | static | 49 / 50 | 98.0% | n/a | 8.000 | 8.000 |
| bfs | dynamic | 49 / 50 | 98.0% | n/a | 8.653 | 9.163 |
| dijkstra | static | 49 / 50 | 98.0% | n/a | 8.000 | 8.000 |
| dijkstra | dynamic | 49 / 50 | 98.0% | n/a | 8.000 | 8.510 |
| dqn_fixed | static | 200 / 250 | 80.0% | 0.082 | 10.810 | 18.985 |
| dqn_fixed | dynamic | 199 / 250 | 79.6% | 0.074 | 11.146 | 19.196 |
| dqn_untrained | static | 0 / 250 | 0.0% | 0.000 | n/a | n/a |
| dqn_untrained | dynamic | 0 / 250 | 0.0% | 0.000 | n/a | n/a |
