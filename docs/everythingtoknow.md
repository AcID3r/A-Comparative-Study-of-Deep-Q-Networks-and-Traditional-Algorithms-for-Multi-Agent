# Everything to know about this project

Updated: **2026-10-07** | Checkpoint: **CP-09 complete; all planned work finished**

## The big idea

Imagine a robot on a board made of little squares. It needs to get from its
starting square to its goal. Some squares are walls. We also test several
robots together, with walls that change while they travel.

We want to compare ways to find a route. Three ways use rules to search the board.
Another way, called DQN, learns from practice. Our finished experiment found
that the rule-based finders reached more goals than these learned robots.
That tells us about this contest, not every possible robot or board.

The Word paper that was already in this folder talks about quantum computers.
That is a different project. We left it alone. This project's plan comes from
your graph-search brief.

## What works today

We made the board and three route finders. Now they tell us moves, cost, squares
checked, and search time. We can view their routes as text or pictures.
The full **142-test suite passed**, followed by three checks for the latest Word
preview fixes. Five fixed-board and five varied-board practice
runs finished. We tested their final models on 50 new boards, with and without
changing walls, and checked every saved test move by playing it again.
A seed lets us make the same supposedly random board again.

We also ran a real small measurement check on 30 boards. Each finder tried every
board, giving 90 saved answers: 84 successful answers and 6 with no route. We kept
failures instead of hiding them. This check does not tell us which method wins
in general. We checked the saved answers against the separate answer checker.

We have built and trained the learning robot on a fixed board. Now walls can
change during a trip, and the rule-based finders can plan again when that happens.
Two or four robots can now move together using planned or scripted moves.
Team learning is built and its full run and unseen-board checks are finished.
Changing walls while teams travel is built and tested. Its full comparison and
saved-answer checks are finished. The larger final experiment and scientific
paper are now finished. The separate Word paper is made too, but its real Word
page layout still needs the final check described below.

## How our board works

A square has an address like `(2, 3)`: row 2, column 3. Counting begins at zero.
A robot can move up, down, left, or right to a free square. It cannot move
diagonally, through a wall, or outside the board.

Usually a move costs one point. Some squares can cost more, like walking through
mud. Our cost is paid when entering the next square. Starting on a square is
free. We allow positive costs smaller than one too. We reject zero, negative,
and impossible number costs so our rules stay clear.

The board is fixed while a route finder searches. We copy the wall and cost lists
so someone changing their original lists cannot secretly change this board.

## The three route finders

**BFS** searches nearby squares first, then squares farther away. When every
move costs the same, it finds a route with the fewest moves. We refuse to use it
when move costs differ, because fewest moves could be expensive.

**Dijkstra** keeps looking at the cheapest route found so far. It can choose a
longer route if that route costs less. Imagine avoiding expensive mud by walking
around it.

**A*** also tracks cost, but guesses how much travel is left. On this board its
guess counts the row and column distance to the goal. If a move might cost less
than one, we make the guess smaller too. This stops the guess from pretending
the remaining trip must cost more than it really does.

Different finders can choose different routes that are equally good. The tests
check that a route is valid and has the right length or cost. They do not demand
one special drawing of the route.

## How we count a route

`[start, next_square, goal]` has three squares but **two moves**. This matters:
counting squares instead of moves would give the paper wrong numbers.

If the robot is already at its goal, there are zero moves. If a wall makes the
goal unreachable, the finder returns `None`, meaning no route. If the starting
square itself is outside the board or inside a wall, we raise an error: the
question was invalid, rather than a valid question with no solution.

Waiting is now allowed in the one-robot game. It takes time but is not a move.
We count moves and time separately. For several robots, makespan means how many
turns pass before the last robot arrives.

## How we checked the work

We tried an empty board where the answer is eight moves. We tried a wall that
forces a detour, a wall that blocks every route, and a robot already at its goal.
We tried bad coordinates and bad costs to make sure they are rejected.

We tried a muddy route where the short way costs 31 and a longer way costs 6.
Dijkstra and A* chose the cheaper way. We also tried cheap squares with costs
below one, which can expose a mistake in A*'s distance guess.

For the random boards, we used another little solver as an answer checker. It
repeatedly improves route costs instead of using the same search method as our
main code. We also check every step independently: it must stay on the board,
avoid walls, and move exactly one square. Using several kinds of checks helps
avoid trusting three programs that could all share the same mistake.

These checks help us trust the code. They do not tell us DQN is good, and they
are not the final paper experiments. We also checked that the documentation's
links work and its test count matches the actual test files.

## Which file does what?

| File | Simple meaning |
|---|---|
| `README.md` | Front door: how to start and run the tests |
| `prd.md` | What we want to build and what counts as success |
| `implementationstrategy.md` | The order in which we will build it |
| `tdd.md` | Exact rules for the code and its tests |
| `task.md` | Our bookmark: done, unfinished, evidence, and next steps |
| `everythingtoknow.md` | This easy explanation of what and why |
| `AGENTS.md` | Instructions to keep the bookmark and explanation updated |
| `environments/grid_graph.py` | The board, walls, neighbors, and movement costs |
| `environments/single_agent_env.py` | One-robot game: actions, scores, observations, and turn limits |
| `algorithms/bfs.py` | Nearby-first route search and path reconstruction |
| `algorithms/dijkstra.py` | Cheapest-cost route search |
| `algorithms/astar.py` | Cost search with a remaining-distance guess |
| `algorithms/search_result.py` | A search report card: route, moves, cost, effort, and time |
| `algorithms/dqn.py` | Learning robot, practice memory, value guesses, and saved models |
| `evaluation/visualize.py` | Draws routes as text or SVG pictures |
| `experiments/run_static.py` | Gives matching boards to all finders and saves answers |
| `experiments/run_episode.py` | Plays three scripted games and can save every turn |
| `configs/static_smoke.json` | Chooses sizes, wall probabilities, seeds, and finders |
| `configs/dqn_fixed.json` | Frozen rules for the five fixed-board practice runs |
| `training/train_dqn.py` | Runs real practice and saves scores, losses, and models |
| `evaluation/evaluate_dqn.py` | Tests greedy learned choices with exploration off |
| `evaluation/plot_learning.py` | Draws learning charts from actual saved scores |
| `evaluation/audit_dqn_run.py` | Checks saved measurements and reproduces saved-model routes |
| `environments/random_maps.py` | Makes different boards and keeps practice and test piles separate |
| `environments/dynamic_env.py` | Adds or removes walls at planned turns |
| `evaluation/navigation.py` | Runs trips and lets rule-based finders plan again |
| `evaluation/varied_protocol.py` | Checks settings and saves exact boards and code copies |
| `configs/dqn_varied.json` | Frozen settings for different-board practice and tests |
| `training/train_varied.py` | Practices on many boards without using final test boards |
| `experiments/run_transfer.py` | Gives every method the same new boards and wall changes |
| `evaluation/audit_varied.py` | Checks practice records and plays every saved test trip again |
| `evaluation/summarize_transfer.py` | Makes comparison tables and pictures from saved answers |
| `test_baselines.py` | Automatic checks and a separate answer checker |
| `test_reporting.py` | Checks search report cards |
| `test_static_runner.py` | Checks pictures, repeated runs, and saved failure records |
| `test_single_agent_env.py` | Checks the one-robot game rules |
| `test_dqn.py` | Checks learning targets, memory, actions, and saved weights |
| `test_training.py` | Checks a tiny real training pipeline and repeatable outputs |
| `test_dynamic_maps.py` | Checks new boards, separate piles, wall changes and reset |
| `test_navigation.py` | Checks planning again, frozen routes, and failed trips |
| `test_varied_protocol.py` | Checks tiny real varied-board practice and test runs |
| `environments/multi_agent_env.py` | Team game and a referee that stops unsafe moves |
| `algorithms/prioritized.py` | Plans robots in order and reserves squares and turns |
| `experiments/run_team_episode.py` | Saves small team examples, including failures |
| `evaluation/audit_team_episode.py` | Plays saved team examples again and checks every score |
| `test_multi_agent_env.py` | Checks goals, team scores and unsafe moves |
| `test_prioritized.py` | Checks waiting, reservations and planning failures |
| `test_team_episode.py` | Checks saved examples and catches changed answers |
| `configs/dqn_team.json` | Frozen settings for solo and team practice |
| `evaluation/team_protocol.py` | Makes separate team boards, picks endpoints and runs trips |
| `training/train_team.py` | Teaches the shared and solo rulebooks on matching trips |
| `experiments/run_team_comparison.py` | Tests final rulebooks and planners on the same new boards |
| `evaluation/audit_team_run.py` | Replays every practice and final test trip to check answers |
| `evaluation/summarize_team.py` | Makes tables and charts from saved team answers |
| `test_team_learning.py` | Checks learning notes, later prizes, saved models and tiny real runs |
| `environments/dynamic_team_env.py` | Changes team walls while keeping goals and occupied squares safe |
| `evaluation/dynamic_team_protocol.py` | Plans again from current positions or retries frozen routes |
| `configs/dynamic_team.json` | Picks saved models and the turns for wall changes |
| `experiments/run_dynamic_team.py` | Gives matching fixed/changing boards to every method |
| `evaluation/audit_dynamic_team.py` | Replays decisions and checks shared wall changes |
| `evaluation/summarize_dynamic_team.py` | Builds changing-board tables and pictures from real answers |
| `test_dynamic_team.py` | Checks reset, walls, goals, collision rules and replanning |
| `test_dynamic_team_runner.py` | Checks real saved-policy runs and catches changed records |
| `requirements.txt` | Exact package versions needed for learning and charts |
| `.gitignore` | Tells future Git tracking to skip disposable Python files |
| `results/validation/CP-01.md` | Record of the actual first test run |
| `results/validation/CP-02.md` | Record of the new tests and real measurement check |
| `results/validation/CP-03.md` | Record of environment tests and scripted games |
| `results/validation/CP-03-episodes.json` | Saved turns and scores from those games |
| `results/validation/CP-04.md` | Real learning results and test evidence |
| `results/validation/CP-04-audit.json` | Saved audit of full learning outputs |
| `results/validation/CP-04-source/manifest.json` | Fingerprints of archived matching code and tests |
| `results/validation/CP-05.md` | Evidence for new-board learning and changing-wall tests |
| `results/analysis/CP-05-final/comparison.md` | Table made from actual new-board test answers |
| `results/validation/CP-06a.md` | Evidence for the team game and route planners |
| `results/validation/CP-06b.md` | Evidence for team practice and unseen-board comparison |
| `results/validation/CP-06c.md` | Evidence for changing team boards and original-paper preservation |

The tiny `__init__.py` files mark folders as Python packages so imports work.

## Run it yourself

Open a terminal in this folder and type:

```powershell
python -m unittest discover -v
```

Today this prints the test names and finishes with `OK`. We used Python 3.12.6.
The learning checks use PyTorch and the charts use Matplotlib/NumPy. These were
already installed on this computer; the versions are saved in `requirements.txt`.

To display a fixed wall-detour example, then save the small measurement run:

```powershell
python -m experiments.run_static --demo
python -m experiments.run_static
```

The second command prints the new output folder. Read its `paths.txt`, or open
an `.svg` in its `paths` folder in a browser. SVG is made from shapes and stays
sharp when zoomed. S is start, G is goal, dark squares are walls, blue squares
show the route. Text routes use stars. B means start and goal are the same square.

## What the new report card means

Moves count steps along the route. Cost adds up those steps' costs. Expanded
nodes count squares the finder takes from its work list and checks, including
the goal. A three-square hallway takes three checks but only two moves. An old
work-list entry replaced by a cheaper entry does not count again.

Planning seconds include preparing and searching for the route, checking inputs,
and putting the route together. Drawing and saving happen afterwards. Computer
timing varies, so one quick measurement cannot prove which finder is faster.

## Why we save more than a score

Each run gets a new folder under `results/raw/static_smoke/`. We save the exact
boards, settings, answers, and computer details. Code hashes are little
fingerprints that help identify the code version that made the answers.
Wall probabilities do not guarantee exact wall counts, and endpoints stay free.

A CSV is a table you can open in a spreadsheet. An impossible route has empty
move and cost fields, not zero: zero would wrongly say the robot finished without
moving. Old runs stay untouched. `COMPLETE.json` is written last so we can tell
a finished run from one interrupted partway through.

## The new one-robot game

Call `reset` to put the robot back at its start and clear its score. Then use
`step` for up, down, left, right, or wait. Walls and board edges stop movement
but still use a turn. An unknown action is a programming error and uses no turn.

Every turn costs one point. Trying a wall costs ten extra; trying a boundary costs
five extra. Reaching the goal earns 100 extra once, so that turn earns 99. There
is no team bonus in this game. We save the score parts to explain every point.

Reaching the goal ends successfully; running out of turns ends unsuccessfully.
Arriving on the very last allowed turn still succeeds. Reset before stepping
again after either ending. Starting at the goal is already a zero-turn success
with zero reward; it does not create free points by repeatedly resetting.

The robot gets a 13-number note: position, goal direction, walls and boundaries
beside it, and remaining time. It does not see the whole board. The note has a
version number so a future saved learning model knows what its inputs mean.
These episodes use one-point movement costs; older route finders still handle
weighted boards. Reset records a seed but does not randomize this fixed game.

Run the scripted checks:

```powershell
python -m experiments.run_episode
```

Following the baseline route took 8 turns and 8 moves, score 92. Trying a boundary,
trying a wall, and waiting took 3 turns and zero moves, score -18, then timed out.
Starting at the goal took zero turns, score zero. We saved the turns and checked
their totals. These are programmed moves, not a trained robot.

## How the learning robot works

DQN keeps a little memory of moves, scores, and what happened next. It practices
from shuffled samples of that memory instead of only remembering the latest move.
Its neural network guesses a future score for each of five possible actions.
Sometimes it tries a random move to explore; later it explores less.

It has an online guesser that changes with practice and a target copy that changes
more slowly. Every 500 learning updates we copy the online guesser to the target.
Learning updates happen every four game steps after warm-up; those are different
counters. When a game ends or runs out of turns, there are no further future
points to add for that game. We checked these calculations with simple examples.

We chose all settings before the long run: one fixed 5×5 board, five different
training seeds, 2,000 practice games per seed, and checks every 100 games. The
robot only reads its 13-number note. It does not get a shortest route to copy or
extra rewards to guide it. Test moves use its best guess with random exploration
off. Testing on the practice board does not prove it knows new boards.

We save each game's score, success, wall attempts, and learning error, then let
a program draw the charts. Training-success charts include exploratory moves;
greedy checks are recorded separately. We time practice separately from choosing
an action. Saved model files keep the learned guesses. Reloading them must give
the same route. They do not include everything needed to resume the exact same
training history.

The short 20-game smoke run failed its final greedy goal test. That result is
kept. A small run checks that the machinery works; it does not promise good choices.
The full runs can also fail or get worse after doing well. We keep the final model
and the whole record rather than hiding bad checkpoints.

Try a short check or run the frozen full protocol:

```powershell
python -m training.train_dqn --smoke
python -m training.train_dqn
```

Both save new folders under `results/raw/dqn_fixed/`. The full command takes
longer. It prints real progress; the saved charts are in its `figures` folder.

## New boards and changing walls

A different random seed can accidentally make the same board. We check the whole
wall pattern before calling a board new. Our practice pile has 100 unique boards,
our check-up pile has 10, and our final test pile has 50. None repeats a board in
another pile or the old fixed practice board. Impossible boards stay in the test:
we must not hide hard cases to make scores look better.

During the changing-wall test, we add a wall before turn 3 and remove it before
turn 8. The chosen square is too far away for any robot to already be standing
there at turn 3. This gives every method the same real wall changes. In other
custom examples, trying to add a wall under the robot is rejected and recorded.

The rule-based finders can plan again from where they are after a change. A
frozen-route control keeps its original route and retries a blocked step until
it reopens. We checked an example where replanning arrives in 5 turns while the
frozen route takes 7. A wall placed on BFS's route might not affect A*'s route;
we must not pretend every scheduled change challenges every method equally.

The old fixed-board models succeeded on 80.0% of new static cases and 79.6% of
changing-wall cases. Each rule-based replanning method succeeded on 49 of the 50
boards. One board had no route initially. These are actual saved test results,
and every saved move was replayed to check them. The new varied-board models
finished 10,000 practice games altogether. They reached the goal in 226 of 250
static tests (90.4%) and 221 of 250 changing-wall tests (88.4%). That is more
successful trips than the old models here, but fewer than the rule-based finders.
It does not prove the new robot always wins or takes the shortest route.

Five robots each tried the same 50 test boards, so there were 250 tries per
condition. These are not 250 different boards. We kept the failures, including
the board that had no route. The printed table comes straight from saved answers;
we do not type nicer scores into it. Some robots reach the goal only after long
detours, so successful trips and short trips are different things.

The new models practice only on the practice pile. The check-up pile is used to
observe progress, not pick a best checkpoint. We keep the final model. The final
test pile never enters practice memory. During testing, learning is switched off.
Seeing a changed wall and choosing a different move is a reaction; it is not an
extra training session hidden inside the test.

## Fixed-board checkpoint history and upcoming work

The full run finished: all five final robots reached the goal on their practice
board. Their move counts were 12, 8, 12, 8, and 12. The rule-based finders need
8 moves on this board. Some robots waited, so the final arrival times were 12,
9, 15, 14, and 14 turns. Getting there is different from taking the best route.

The scores sometimes got better and then worse during practice. We kept those
records and final models. The saved models gave the same guesses and routes when
reloaded. We checked all 10,000 game records, 63,887 learning updates, and 115
greedy test records, then inspected the charts. We archived matching code and
settings so future edits do not erase the version that made these answers.

The fixed-board and varied-board runs are both audited. Each new run keeps a
copy of the code that made its answers, like keeping the recipe with a cake.
We checked 10,000 new practice records, 74,961 learning updates, and all 1,900
trips in the final comparison. The new-board checkpoint is finished.

DQN learns by practicing. It remembers past moves, guesses which move earns a
good future score, and improves its guesses. It also keeps a slower-changing copy
of its guesses to help training stay steady. Practice takes time; we will record
practice time separately from the time used to choose a move after learning.

We now have a game for two and four robots. They
must not stand on the same square or swap squares through each other in one
turn. A shared policy means they use the same learned rulebook. It does not mean
they talk to each other.

We will count unsafe moves robots **try** separately from collisions that really
happen. A referee stopping bad moves does not prove robots learned to cooperate.
For rule-based searches, we reserve squares and turns for earlier robots
before planning later robots. That simple planning order can fail even when a
better team solution exists; we must say so in the paper.

Finally, every method will face matching test boards, with repeated runs. We will
save real measurements and let a program build the tables from them. We will
write the results only after that, even if the learning method performs poorly.

## How the team game works

We now have a learning program for teams too. A finished robot stays still but
keeps recording what happens until the team finishes. This lets it receive the
later team prize rather than losing that prize from its practice memory.
In each practice round, the shared learner tries two robots together. A separate
control learner tries those same two trips one at a time. They get the same number
of trips to practice, but may use different numbers of turns and learning updates.
We save those counts so the comparison is honest.

Both new learners read the 17-number note. Old 13-number models still load and
give their old answers. We reloaded five older robots and checked every old move,
position and note. Nothing was secretly padded into their notes.

The long run is finished: ten robots practiced altogether, five solo and five
shared, with 2,000 assigned trips each. There are 15,000 saved practice games
because a team game contains two trips and a solo game contains one. We checked
every saved practice action and every one of the 720 final test trips.

On new boards with two robots, the shared rulebook finished 61 out of 100 tries;
the solo-trained rulebook finished 64. With four robots, shared finished 25 and
solo finished 27. The rule-based planners finished 18 out of 20 two-robot tries
and 16 out of 20 four-robot tries. So our shared robot did not win this test.
Five learned robots each tried the same 20 boards: 100 tries means repeated
boards, not 100 different boards. We kept impossible boards and failed trips.

Shared robots tried fewer unsafe moves than solo robots here, but still failed
many trips. The referee prevented real collisions. Less bumping does not always
mean reaching every goal. Some robots got stuck, and adding more robots made
these tests harder. We saved the disappointing results instead of changing the
rules after seeing the test answers.

Imagine each robot writes its next move on a card. The referee reads all cards
before moving anyone. If two robots want the same square, those moves stop. Two
robots cannot trade squares in one turn either. A robot can follow another if
that robot really leaves. If one blocked robot stops the robot behind it, the
referee checks the whole line again. Four robots may rotate around a square.

Robots that reach their goals stay there. Other robots must go around them.
Every unfinished robot loses one point per turn. Trying a wall loses ten extra,
trying the board edge loses five extra, and a rejected unsafe move loses 25 extra.
First arrival earns 100 points; everyone gets 100 more once the whole team finishes.
A robot already finished pays no turn cost. Starting on goals gives no free prizes.

We count attempted unsafe moves separately from real collisions. The examples
had no real collisions because the referee prevented them. This does not mean
the robots learned to be polite. One example tried two unsafe moves and still
failed to finish; we kept that failure.

Each robot gets a 17-number note. The old 13 numbers describe its position, goal,
walls, boundaries and time; four new numbers show robots beside it. The old
learning models expect 13 numbers, so we must teach compatible new models before
using the new notes. We trained compatible new models rather than pretending
old models understand the longer note.

The planners put reservations on squares for particular turns. Think of booking
a chair at a certain time. They also prevent opposite trips along an edge at the
same time. Goal chairs stay booked after arrival. A robot may wait for a square
to become free. Planning in a different order can change whether everyone gets
a route: our tests show one order failing and the reverse order succeeding.
That means this simple planner cannot promise to solve every possible team puzzle.

Team learning and changing walls passed their checks. We then froze the larger
experiment plan, tested new boards and wrote the scientific paper.

## What happens when team walls change?

We add a wall before turn 2 and remove it before turn 8. The square is far enough
from every starting robot that nobody can already be there at turn 2. Every method
gets the same planned change. Starts and goals are protected. In custom tests,
putting a wall under a robot is refused and written down.

Robots receive their new notes after the wall changes. Rule-based planners find
new routes from where the robots are now. If a route is impossible, the robots
wait until the board changes again. Finished robots stay on their goals, and their
original arrival times are kept. A frozen planner keeps its old route and retries
the blocked step; its delays can upset the other robots' original reservations.

The saved learning robots react to their notes without more practice. We checked
that their learned weights did not change. This is testing reactions after static
practice, not secretly teaching them during the test.

During CP-06c we ran 1,680 fixed/changing-board trips and replayed all 32,194 recorded turns.
All 123 test groups passed. The new fixed-board numbers match the earlier test,
and the old QENN Word file has the same fingerprint as before.

On changing boards, each replanning method finished 18 of 20 two-robot trips and
16 of 20 four-robot trips. Frozen four-robot routes finished only 13 or 14 of 20.
The shared learning rulebook finished 58 of 100 two-robot tries and 25 of 100
four-robot tries; the solo-trained control finished 61 and 28. Those 100 tries
reuse 20 boards with five trained rulebooks. We kept failed trips too.

A team that finishes early does not experience later wall changes. We check that
the changes match while teams are still playing, instead of pretending every
team saw a wall disappear after its game had ended. All 20 boards had a change
schedule; our code also tests what to do when no safe square can be changed.

These are small practice experiments, not proof that any method always wins.
Some walls do not block every selected route. The completed final study used new
boards, larger sizes, clear endpoint rules, and settings fixed before tests.

## The final checkpoints

CP-07a fixed and checked the final experiment rules. CP-07b finished those experiments and made
their tables and pictures. CP-08 finished and checked the scientific story. CP-09
makes the complete new Word paper look like the reference you chose and checks
every page. Think of CP-08 as finishing the story and CP-09 as making the finished
book. The old Word paper stays untouched. We used real checked results, even
when they showed that the learning robot lost. The scientific paper is saved;
the Word version is also saved. Its final page check is the remaining step.

## What the final contest tells us, in simple words

Across these trips, A* finished about 89 out of 100. The solo learning robot
finished about 24 out of 100, and the shared learning robot about 22 out of 100.
The exact report has the real counts and percentages. Five learned rulebooks
try the same boards, so those are not five separate piles of new boards.

Imagine one runner finishes only short races and another finishes almost every
race. The first runner's average race length might be shorter, but that does
not mean it found a better way around the same race. We therefore compared
matching trips too. On matching successful static trips, the learned robot's
average movement count was higher than A*'s, though many individual routes tied.

Sharing a rulebook helped a little in the four-robot success summaries, but did
not help overall. Some learning robots finished faster after a wall changed,
but many more of their trips failed. Our paper explains both parts instead of
calling the learning robot the winner.

No robots actually bumped into each other because the game's referee stopped
unsafe moves. We separately counted how often a robot tried an unsafe move.
That is like a teacher stopping a playground bump: the stop does not prove
that every child learned to avoid it alone.

The learned robots practiced only on small static boards. The route finders
can see the whole current board, while learned robots get a small note about
nearby squares. Bigger boards and limited sight make this contest hard for
these learned robots. These are possible explanations, not facts proved by
changing just one thing in a separate experiment.

The scientific paper is finished, checked and saved. It has not been accepted
by a journal or checked by an outside reviewer. The Word version has been made
and its numbers are checked. Its real Word page layout still needs review.
See `task.md` for exact commands.

## The Word paper and the last check

Open `paper/Graph_Search_Research_Paper.docx`. It is our full new paper, with
Madhav Joshi and Marwadi University on the front. It looks like the old paper's
page style: one wide opening, then two narrow columns. We copied the page style,
not the old quantum story. The old file has the same fingerprint as before.

Ten tables include the background comparison and the nine real-result tables.
We checked every table entry against the earlier paper. Seven pictures use the
same measured numbers but stack their panels so narrow columns are easier to
read. The two numbered equations are editable in Word. The source links work.

Think of our preview as drawing a picture of a book. Microsoft Word may place
some words on different pages. We made and checked a 12-page preview, but it
is not a real Word export. Word is installed here, yet this work session could
not start its automation service. We wrote down the error instead of pretending
we had checked Word's pages. That is why CP-09 is still partly finished.

All 142 test groups passed, and the three Word checks passed again after fixes.
One check changes a result on purpose and makes sure our checker catches it,
even if someone gives the changed file a new fingerprint. Preview checks also
make sure equation pictures stay on the page and their numbers stay together.

The last job is to open/export the new paper using Word in a normal Windows
session, check every real page and fix any layout problems. The commands are in
`paper/WORD_REVIEW.md`. No more robot training or new result numbers are needed.

## Our project diary

**2026-10-07, CP-09 partly finished:** Made the separate Word paper, checked its
text, tables, pictures and equations, and kept the old paper untouched. Made
a 12-page independent preview, fixed picture sizing and equation numbers, and
passed the full 142 tests plus the latest three Word checks. Word's own export
failed because this session could not start its service. We saved that error
and left the final Word-page check unfinished. No contest numbers were changed.

**2026-10-07, CP-08 finished:** Wrote the full paper using the checked contest
records. Its author is Madhav Joshi from Marwadi University, as you confirmed.
It has seven pictures, nine result tables and nine checked sources. The readable
PDF has 17 pages. We checked the pages and fixed a small caption problem with
the name A*. All 139 test groups passed again. We also saved an editable text
paper and a LaTeX source, but did not pretend that LaTeX had been compiled.
The next job, CP-09, makes a separate Word paper using the old paper's page style.
The old quantum paper stays exactly as it was.

**2026-10-07, CP-07b finished:** Ran 15,120 different contest cases on 120 new
boards. We timed each case three times, but did not count those repeats as new
answers. We played all 652,244 saved turns again and checked the records.
Another checker counted 837 groups of answers from the original files. We kept
the trips that failed and did not teach the robots again after seeing the scores.

**2026-10-07, working toward CP-07b and CP-08:** The user asked us to finish the
big experiment and the scientific paper. The contest is running with the locked
rules. We built tools to compare matching trips, make charts from records, and
turn the finished story into a readable PDF. Six new tool checks passed. We
checked nine real sources for the background. We have not called the big contest
or the paper finished yet; the results must first be checked. The final Word
formatting remains CP-09, and the old Word paper is unchanged.

**2026-10-07, CP-07a:** Wrote the final game rules before opening the final test
boards. Kept all ten learned rulebooks, even if some are weaker. Checked twelve
practice boards that cover every size, wall amount and start/goal arrangement.
Saved 1,512 trips and played all 63,386 turns again to check the records. All 133
test groups passed. One checker mixed up two ways of writing coordinates; we
fixed the checker without changing any scores. The old Word paper is unchanged.
Next we will run the real final test on 120 new boards; those are not opened yet.

### What the final experiment plan means

Think of a board-game contest. Before the contest, we must decide which boards,
players, rules and clocks we will use. Otherwise we might quietly change a rule
after seeing who wins. Our plan now says: three board sizes, two amounts of
walls, one/two/four robots and boards with fixed or changing walls.

We use two ways to place robots. In one, start and goal squares are random. In
the other, robots start along the left edge and their goals are along the right
edge in the opposite order. Their routes may cross, but that does not promise
traffic jams. We record when simple routes share squares rather than pretending
every crossing board is equally crowded.

The learned robots keep the same rulebooks they already practiced with. They
will not study the final boards first. This asks whether a rulebook learned on
a little board can work on bigger boards and with changing walls. We keep
unreachable boards and failed trips in the scores. The referee still stops
robots from crashing, so rejected crash attempts and real crashes are different.

For the final contest, each trip will be played three times to measure its
clocks. That is still one trip's answer, not three new independent successes.
We do not say a failed robot finished at the timeout. If nobody finishes, its
average finished-trip time is left blank. The pilot checks that these rules work;
it does not supply the final paper's results.

The new files have simple jobs: `final_experiment.json` lists the fixed choices;
`final_protocol.md` explains them; `final_protocol.py` makes boards and locks the
choices; `run_final.py` runs the contest; `audit_final.py` replays and checks it;
`summarize_final.py` makes tables from records; `test_final_protocol.py` checks
these tools. The lock stores fingerprints of code, models and settings. If a
locked file changes, the final run stops so we can explain and check the change.

**2026-10-07, new CP-09 plan:** After the research and writing steps, we will make
the full new paper look like the old Word paper. We looked at its page layout
without changing it. It has a wide title area, two text columns, and numbered
sections, pictures, tables and equations. Our new paper will use our graph-search
experiments and checked references, not the old paper's quantum results.

**2026-10-07, CP-06c:** Added changing team walls, replanning and frozen-route
controls. All 123 test groups passed. Saved 1,680 trips, replayed every recorded
turn, checked the chart and confirmed old fixed-board answers still match.
Learning weights and the QENN paper were unchanged. Next is the bigger final
experiment plan and fresh final boards for our graph-search research paper.

**2026-10-07, CP-06b:** Built compatible learning models and taught five solo and
five shared rulebooks. All 111 test groups passed. Checked 15,000 practice games,
25,084 learning updates, saved-model reloads and all 720 new-board tests. Made
charts from real records and checked them. Shared learning did not improve goal
success here, so we kept that finding. Next is changing walls for teams.

**2026-10-07, CP-06a:** Built the team game and planners. All 103 test groups
passed. Checked all 625 possible choices for four robots on a little board.
Saved 16 examples: nine successful trips, six planning failures and one timeout.
Played all 26 saved turns again and checked the scores. Next is team learning;
there is no trained team robot yet.

**2026-10-07, CP-05:** Made separate piles of new boards, added changing walls,
and taught the finders to plan again. Five new learning robots practiced for
2,000 games each. All 82 test groups passed. We saved and replayed 1,900 final
comparison trips, checked the charts, and kept failures. New-board learning
helped these robots reach more goals, but the rule-based finders still reached
more. Next is the team game and rules that stop robots bumping into one another.

**2026-10-06, CP-04:** Built and tested DQN, trained five robots for 2,000 games
each, saved their models and charts, and audited the files. All 68 test groups
passed. Every final robot reached the practice goal, but only two matched the
shortest move count. Next is testing new boards and changing obstacles.

**2026-10-06, CP-03:** Built the one-robot game, fixed its 13-number note format,
and checked actions, scores, waiting, reset, goals, and time limits. All 52 test
groups passed. Saved and checked three scripted games. Next is single-agent DQN;
no learning has happened yet.

**2026-10-06, CP-02:** Added search report cards, text and SVG pictures, and a
repeatable runner that saves real measurements. All 31 test groups passed.
The small run saved 90 answers and 90 pictures for 30 matching boards. We checked
the saved answers and kept failures. Next is the single-robot game environment.

**2026-10-06, CP-01:** Started the graph-search project. Wrote the plans, built a
fixed grid and three route finders, and ran the checks. All 15 groups passed.
No learning models or final research measurements exist yet. The next step is
baseline reporting and visualization.

Every later change must update this explanation and `task.md`. These files do
not magically update themselves. Whoever changes the project must write what
changed, why it changed, what was checked, and what is still unfinished.


**2026-10-07, CP-09 page review and table fix:** Your terminal made a real
11-page Word PDF. We looked at every page. The story, pictures and equations
were there, but some table boxes were cramped: a number like 89.17 put its last
digit on another line. We made the empty space inside each box smaller. The
numbers stayed the same. All three Word tests passed again in 9.418 seconds.
We kept the old version so we can compare them.

The new Word file needs a new real page check. Run the same three commands again
in your terminal. Your terminal can open Word; the assistant's terminal still
cannot. Once the new pages look right, we can finish CP-09. The old 11-page PDF
belongs to the first version, so it cannot prove the new version looks right.


**2026-10-07, checking the longer numbers:** We looked at all 11 pages from
your second Word export. Most numbers fit, but a long time such as 123.251 still
split across lines. We now measure how much space each complete number needs
and give its table column at least that much room. The table still fits inside
the page column. We added this rule to a test so the same mistake is caught.
All three Word tests passed in 10.980 seconds; no experiment numbers changed.

We saved both old versions. The newest Word file needs another real Word export
from your terminal. We must check its pages before calling CP-09 complete.
Your earlier successful export belongs to the previous version of the paper.


**2026-10-07, CP-09 finished:** Your terminal made the newest paper into a
real 11-page Word PDF. We looked at every page. The long table numbers now stay
on one line, and the pictures, equations and references are readable. The
checker also confirmed that no words or pictures leave the page. Every table
number still matches the real experiment. The old quantum paper is untouched.

Our agreed project is finished: working programs, tested experiments, honest
results and the new paper in Word and PDF. We saved the checks and fingerprints
so we know which version passed. Earlier mistakes remain in the diary, because
that shows how we found and fixed them. You do not need to repeat the export
commands for this saved version.

Next, read the paper yourself and choose where to send it. A journal may ask for
its own page style or a shorter paper. A supervisor can help review the research.
Finishing our project does not mean a journal has accepted it.


**2026-10-07, tidying the project for GitHub:** Think of our project as a
school bag. We put the instructions in the `docs` pocket, the tests in `tests`,
and the old paper in `references`. The programs already had good pockets, so
we kept them there. We updated the directions so everything can still find
what it needs. All 142 tests passed after tidying, in 46.351 seconds.

Some old papers and one test stay in their original places. They are sealed
proof of our experiment, like a teacher's signed worksheet. Moving or rewriting
those would break the proof. The front README and AGENTS instructions also stay
at the front so GitHub and coding tools find them.

Three robot travel diaries were too big for an ordinary Git upload. We kept the
real diaries on this computer and packed exact copies into a 51.4 MiB ZIP in
`dist`. We checked every copy's fingerprint. Git ignores those big files, but it
keeps the numbers, pictures, models and smaller diaries. Upload the ZIP separately
as a Release asset; people can unpack it to check the complete trips.

The finished Word/PDF and the old quantum paper have exactly the same bytes as
before. No scores changed. `docs/GITHUB.md` explains how to upload. We have not
uploaded anything or made a GitHub repository for you. That is the next step.


**2026-10-07, final submission folder:** We copied the finished Word paper and
PDF into `final submission`. It is like putting two copies of your finished
homework in an envelope. We checked their fingerprints: each copy is exactly
the same as the accepted paper. The originals remain in `paper`. No numbers or
words changed. You can open the new folder to find the two files together.


**2026-10-07, getting ready for Zenodo:** Your edited Word paper added your
programme and email. The old PDF did not have them, so they were different.
We made a new pair in `final submission/zenodo`: a Word file and a PDF with the
same author details. Your name is centered and bold. We kept your university,
programme and email exactly as you provided them.

The numbers and pictures still match the real experiment. We also restored the
checked equation symbols after Word changed a few of their shapes. We looked
at all 12 pages of the new PDF. Everything fits on the pages, and five paper
tests passed. The old papers and the old quantum paper are safe and unchanged.

Our terminal could not open Microsoft Word, so a different printing tool made
the new PDF. It has different page breaks from Word, but the checked story and
numbers are the same. Use this reviewed PDF as the main Zenodo upload; the Word
file is optional. The older PDF in the parent folder still has the old header.

Choose `Publication / Preprint`: that means sharing a paper before journal peer
review. Code belongs in a separate Software record if you share it that way.
`docs/ZENODO_UPLOAD.md` gives every form field and the abstract to copy. Zenodo
can give the paper a DOI. We did not reserve one or publish anything. You still
choose your license and review the upload form before clicking Publish.
