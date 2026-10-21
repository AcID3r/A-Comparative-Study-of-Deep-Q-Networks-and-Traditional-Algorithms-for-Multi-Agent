"""Build CP-08 scientific manuscript from audited results; no typed result tables."""
import argparse
import json
import re
from pathlib import Path
from evaluation.final_protocol import digest
from evaluation.team_protocol import ROOT

TITLE='A Comparative Study of Deep Q-Networks and Traditional Algorithms for Multi-Agent Shortest-Path Search in Dynamic Graphs'


def build(analysis):
    analysis=Path(analysis).resolve(); report=json.loads((analysis/'report.json').read_text())
    if report['audit']['phase']!='final' or not report['audit']['all_decisions_replayed']:
        raise ValueError('Audited final results required')
    root=ROOT/'paper'; methods=(root/'methods_source.md').read_text(encoding='utf-8')
    methods=methods.split('## 1. Introduction',1)[1]; methods='## 1. Introduction'+methods
    references=json.loads((root/'references.json').read_text())
    author=json.loads((root/'author.json').read_text())
    overall={g['method']:g for g in report['groups']['overall']}
    astar,shared,solo=overall['astar'],overall['shared'],overall['solo']
    reliability=('Current-map prioritized A* completed a larger fraction of matched tasks than both frozen learned policy types under this protocol.'
        if astar['success_rate']>max(shared['success_rate'],solo['success_rate'])
        else 'Reliability differed between the evaluated methods and must be interpreted with the stratified results.')
    sharing=('Shared two-agent training did not improve pooled success over independent deployment of the solo-trained policy.'
        if shared['success_rate']<=solo['success_rate']
        else 'Shared two-agent training improved pooled success over independent deployment of the solo-trained policy, without establishing a causal effect of parameter sharing alone.')
    fmt=lambda x:'not defined' if x is None else f'{x:.3f}'
    pct=lambda x:f'{100*x:.2f}%'
    figures='../'+analysis.relative_to(ROOT).as_posix()+'/figures/'
    table=lambda name:(analysis/'tables'/f'{name}.md').read_text().strip()
    abstract=(f'This study compares prioritized breadth-first search, Dijkstra and A* with solo-trained and shared-policy deep Q-networks for navigation on static and changing unit-cost grids. Ten policies from five training seeds were frozen after static 5×5 training and evaluated without learning on 120 new geometries spanning 5×5, 10×10 and 15×15 sizes, one/two/four agents and two wall probabilities. The final protocol produced {report["unique_episodes"]:,} unique evaluation episodes; three fresh timing rollouts per episode were not treated as extra outcome samples. Across all conditions, replanning A* completed {astar["successes"]}/{astar["episodes"]} episodes ({pct(astar["success_rate"])}), shared DQN {shared["successes"]}/{shared["episodes"]} ({pct(shared["success_rate"])}), and solo DQN {solo["successes"]}/{solo["episodes"]} ({pct(solo["success_rate"])}). All recorded first trajectories passed replay auditing, and actual collisions were zero under the common rejection rules. Success-conditioned paths, matched comparisons and descriptive variation across model seeds are reported alongside failures. The findings apply to fixed small-map-trained policies and current-map prioritized planners under this protocol; they do not establish a universal algorithm ranking or a general reinforcement-learning adaptation advantage.')
    results=['## 6. Results','',
        '### 6.1 Collection, validation and sample denominators','',
        f'The sealed experiment completed {report["unique_episodes"]:,} unique episodes and {report["fresh_timing_rollouts"]:,} fresh timed rollouts on {report["scenarios"]["geometries"]} geometries. The saved audit replayed {report["audit"]["steps_replayed"]:,} first-trajectory steps with zero actual collisions. Empty dynamic schedules numbered {report["audit"]["empty_schedules"]}; any such cases remained in the denominator. Outcomes count only the first rollout per case; policy seeds reuse the same scenario sets. Each classical variant contributes 720 episodes, while each policy type contributes 3,600 across five models. These unequal totals represent equivalent matched scenarios, not extra distinct geometries for DQN.',
        '',f'Initially unreachable individual tasks occurred on {report["scenarios"]["initially_unreachable_by_agents"]["1"]}, {report["scenarios"]["initially_unreachable_by_agents"]["2"]}, and {report["scenarios"]["initially_unreachable_by_agents"]["4"]} of the 120 geometries for the nested one-, two-, and four-agent sets respectively. Such cases remain failures when they cannot be completed; reachability alone does not establish full team feasibility. Generation rejected {report["scenarios"]["rejected_candidates"]} candidates according to the predeclared geometry/free-endpoint rules, with reasons recorded in the bank.',
        '', '### 6.2 Success, agent scaling and map-size transfer','',
        'Table 1 summarizes all evaluated conditions, including frozen and untrained controls. Classical rows have no training-seed standard deviation. Learned seed standard deviations describe five frozen models on the same maps; they are not confidence intervals. Successful moves/makespan can favor a method that finishes only easy cases, so Table 1 must be read with its success denominators.',
        '', '**Table 1. Overall final outcomes; path/time means use successful episodes.**','',table('overall'),
        '', f'BFS completed {overall["bfs"]["successes"]}/{overall["bfs"]["episodes"]} episodes and Dijkstra completed {overall["dijkstra"]["successes"]}/{overall["dijkstra"]["episodes"]}; A* completed {astar["successes"]}/{astar["episodes"]}. Equal-cost BFS and Dijkstra use equivalent arrival-time objectives here. Any difference from A* team outcomes does not contradict admissible single-agent A*: fixed priorities and route choices can change later-agent feasibility. This experiment does not isolate tie-breaking as a causal factor.',
        '', 'Table 2 separates static and dynamic agent-count conditions. The full 648-stratum supplement preserves density, grid size, endpoint arrangement and agent count together. Figure 2 displays success and Figure 3 completed makespan; methods with no successes have missing completion means.',
        '', '**Table 2. Final outcomes by environment condition and agent count.**','',table('condition_agents'),
        '',f'![Figure 2. Success by agent count. Error bars for solo/shared show sample standard deviation across five model seeds; all failed episodes remain in denominators.]({figures}success_by_agents.png)',
        '',f'![Figure 3. Successful-episode makespan by agent count. These curves condition on different successful subsets and do not alone show paired superiority.]({figures}makespan_by_agents.png)',
        '', '**Table 3. Map-size transfer, pooled across agent counts and endpoint arrangements.**','',table('size_condition'),
        '',f'![Figure 4. Executed movement count by grid size among successful episodes. Success rates and matched comparisons are required to interpret these conditional averages.]({figures}moves_by_size.png)',
        '', '### 6.3 Matched static paths and dynamic completion','',
        'For H1, Table 4 compares each learned run with A* on exactly the same static task. Only jointly successful pairs contribute path differences; the same deterministic A* reference is reused for each learned seed. A positive movement difference means the learned policy used more moves. Team A* is prioritized arrival-time search, not a globally optimal movement reference.',
        '', '**Table 4. Learned-policy minus A* static movements on jointly successful pairs.**','',table('h1_paired'),
        '', 'The exact single-agent relative movement gap is additionally reported in Table 5. Its denominator is the exact spatial BFS distance, and its mean includes only successful static single-agent episodes. An absent gap for a failed episode is not treated as zero. Multi-agent and dynamic gaps remain undefined rather than using a misleading global optimum.',
        '', '**Table 5. Static single-agent exact relative movement gaps, (L - L*) / L*.**','',table('static_single_gap'),
        '', 'For H2, Table 6 restricts pairs to episodes in which both methods observed the scheduled addition. A positive completion-step difference means slower learned completion, and a negative success difference means lower learned success in that exposed subset. Both-exposed cases and jointly successful cases have different denominators; neither excludes failed episodes from the reported paired success difference. Replanning controls remain the main fair classical methods.',
        '', '**Table 6. Learned-policy minus frozen A* under dynamic addition exposure.**','',table('h2_exposed'),
        '', '### 6.4 Attempts, shared training and computational measurements','',
        'Figure 5 reports rejected-agent attempts per episode, including failures. These attempts indicate conflicting proposals; they are not realized physical collisions. Actual collisions were zero for every method because the common environment rejected unsafe proposals.',
        '',f'![Figure 5. Conflict attempts by requested wall probability, averaged over all episodes. These are rejected-agent counts per turn summed over a trip; actual collision count is zero.]({figures}attempts_by_density.png)',
        '', 'Table 7 pairs shared and solo policies using identical scenario and seed keys. Positive success differences favor shared training; path differences include only jointly successful pairs. Additional per-stratum paired differences are included in the machine-readable analysis.',
        '', '**Table 7. Shared-policy minus solo-policy matched effects.**','',table('h4_paired'),
        '', 'Table 8 separates recorded training budgets from inference. Task assignments were matched, while actual optimizer updates, transitions and reward timing were not. Figure 6 shows exploratory training returns from the original frozen-model training run; the curves are practice data, not final test results.',
        '', '**Table 8. Actual CPU training totals across five seeds per mode.**','',table('training'),
        '',f'![Figure 6. Training return per assigned task, trailing 100-cycle averages, for the frozen final solo/shared models. Curves are historical training data and do not select test checkpoints.]({figures}training_returns.png)',
        '', 'Table 9 uses per-case means from three fresh timing rollouts, averaged across static and dynamic cases. Planning, action-selection and complete-episode timers are separate; expanded space-time states sum over planning calls per episode and are missing for neural policies. Different success/horizon behavior changes how many decisions occur, so per-episode totals cannot establish a universal computational ranking. Figure 7 combines planning and selection only and retains those limitations.',
        '', '**Table 9. Repeated timing means in milliseconds and mean expanded states per episode.**','',table('runtime'),
        '',f'![Figure 7. Planning plus action-selection time per episode, with three fresh rollouts per unique case. Fixed method order, different completion lengths and logging overhead limit runtime claims.]({figures}runtime_by_agents.png)']
    h1=report['contrasts']['h1']; h2=report['contrasts']['h2']; h3=report['contrasts']['h3']; h4=report['contrasts']['h4']
    positive=sum(g['success_difference']>0 for g in h4); negative=sum(g['success_difference']<0 for g in h4); zero=6-positive-negative
    reducing=sum(g['success_difference']<0 for g in h3); increasing=sum(g['attempts_difference']>0 for g in h3)
    longer=sum(g['moves_difference'] is not None and g['moves_difference']>0 for g in h1)
    faster=sum(g['post_addition_steps_difference'] is not None and g['post_addition_steps_difference']<0 for g in h2)
    less_reliable=sum(g['success_difference'] is not None and g['success_difference']<0 for g in h2)
    discussion=['## 7. Discussion','',
        f'Replanning A* succeeded on {pct(astar["success_rate"])} of its evaluated cases. Shared and solo DQN reached {pct(shared["success_rate"])} and {pct(solo["success_rate"])} respectively. These averages combine conditions and should not replace the stratified tables. The main research question is answered for these implementations: the results quantify the reliability and path/timing tradeoffs of static-small-map-trained policies against current-map prioritized search. They are not a statement about the best attainable DQN, all reinforcement learning, or all MAPF planners.',
        '', f'The unpaired successful movement means are {fmt(astar["mean_successful_moves"])} for A*, {fmt(solo["mean_successful_moves"])} for solo and {fmt(shared["mean_successful_moves"])} for shared. These smaller learned-policy averages do not establish shorter routes: the methods complete different subsets of tasks. Table 4 instead holds the task fixed and retains only joint successes, where {longer} of the six mean learned-minus-A* static movement differences are positive in this final experiment. Most successful single-agent learned paths tie the exact distance, while occasional long detours increase the mean gap; the failures remain visible in Table 5.',
        '', '### 7.1 Hypothesis assessment','',
        f'H1 receives directional support in {longer} of six joint-success contrasts where learned mean movements exceed A*. The learned-minus-A* mean movement differences for solo with one/two/four agents are {", ".join(fmt(g["moves_difference"]) for g in h1[:3])}; shared differences are {", ".join(fmt(g["moves_difference"]) for g in h1[3:])}. Table 4 separates shorter paths and ties. A strict statement that A* always gives shorter paths is not justified by ties or any opposite-direction pairs. Static single-agent gaps have an exact reference; multi-agent prioritized paths do not. Joint-success conditioning and failures must remain visible when interpreting this conditional support for H1.',
        '', f'H2 is not established as a general advantage. In {faster} of six contrasts the learned policy has lower joint-success post-addition completion time, while in {less_reliable} it has lower exposed-pair success than frozen A*. Learned-minus-frozen-A* completion differences for solo are {", ".join(fmt(g["post_addition_steps_difference"]) for g in h2[:3])}; shared differences are {", ".join(fmt(g["post_addition_steps_difference"]) for g in h2[3:])}. Table 6 reports exposed-pair success as well. No online training occurred; reacting through a fixed policy is not learned adaptation during testing. Frozen routes can wait until tick 8 removal, while replanners seek another route. Mild changes and exposure/joint-success selection prevent a broad adaptation superiority claim.',
        '', f'H3 is not a uniform law for every method. Across the 20 main-method adjacent agent-count/condition comparisons, {reducing} show lower success and {increasing} show increased attempts. Classical reservations can keep attempted conflicts at zero, while adding an unreachable or blocked-goal task can reduce team success independently of learned coordination. Nested endpoints match the board but add tasks; they do not isolate congestion from feasibility.',
        '', f'H4 shows shared-policy success advantages in {positive} of six agent-count/condition summaries, disadvantages in {negative}, and ties in {zero}. The six paired seed-level differences and sample standard deviations are in Table 7, with 72 finer contrasts in the supplement. Thus any support is condition-specific; there is no significance test or claim of consistent superiority from pooled averages alone. Shared replay, delayed team bonuses and differing realized training updates all vary together.',
        '', '### 7.2 Mechanisms and interpretation','',
        'Current-map planners can search around newly blocked cells and reserve time-space for other agents; the learned policy can only choose from its compact current observation. The latter can alias different hidden situations and has no recurrent memory. Distribution shift also includes larger coordinate spans, longer routes and crossing endpoints. These are plausible explanations for observed patterns, not isolated causal mechanisms proved by ablations. Parameter sharing by itself does not prove cooperation or explicit information exchange.',
        '', f'The four-agent initial route-overlap proxy averages {fmt(report["scenarios"]["mean_overlap_by_arrangement"]["uniform"])} intersecting route pairs for uniform endpoints and {fmt(report["scenarios"]["mean_overlap_by_arrangement"]["crossing"])} for crossing endpoints. A route intersection has no time dimension and is not an actual collision. The endpoint arrangement therefore describes task structure rather than certifying a strict congestion ordering. Requested wall probabilities likewise differ from realized fractions recorded in each geometry.',
        '', '### 7.3 Reproducibility and practical scope','',
        'Run metadata, scenario banks, schedules, raw CSV, first trajectories, timer repetitions, model hashes and source snapshots are archived. Analysis tables/figures are generated from immutable measured outputs, and the manuscript provenance record maps text sections and tables to those files. Replaying first trajectories checks decisions and environment behavior; it does not reproduce wall-clock timers exactly. Independent external reproduction and evaluation on public warehouse benchmarks would strengthen this controlled local study.']
    limitations=['## 8. Limitations','',
        'This study uses small synthetic unit-cost grids, at most four agents and simplified synchronous moves; no real hardware validation is performed. Dynamic graphs contain only one safely scheduled addition/removal, not moving obstacles, changing costs or repeated adversarial changes. Some methods finish before exposure and some changes leave routes unaffected. Classical algorithms receive more map information than policies. A shared movement referee enforces zero actual collisions, so safety cannot be attributed to the learned networks.',
        '', 'Training is restricted to static 5×5 maps and a fixed budget with no final-test tuning. The observation is partially observable and the model has no memory, communication, demonstrations or graph embeddings. There are only five trained seeds and ten final geometries per size/density/arrangement stratum. Geometry rejection for boundary endpoint availability biases crossing cases, and route distance varies with the arrangement. Unreachable tasks are retained but full team solvability is not established by an exact solver.',
        '', 'Prioritized planning is incomplete and not globally optimal, with fixed priority and tie-breaking. Reward objectives differ from arrival-time search; waits and executed movement costs are distinct. Solo/shared training matches assigned tasks but not transition/update counts or reward timing. Path means condition on success, and matched completion means condition on joint success/exposure. Descriptive seed standard deviations are not confidence intervals. No universal speed ranking follows from timers with fixed ordering, no warm-up and shared-machine/logging effects.',
        '', 'The local experiment archive is provided; no public repository, independent third-party reproduction, external peer review or publication acceptance is claimed. This manuscript is a completed scientific source and readable review PDF. Venue-specific formatting and a separate reference-format Word deliverable remain the subsequent checkpoint.']
    conclusion=['## 9. Conclusion','',
        f'The study completed a frozen comparison of classical prioritized search and DQN policy transfer across matched static/dynamic grids. Replanning A*, shared DQN and solo DQN achieved overall success rates of {pct(astar["success_rate"])}, {pct(shared["success_rate"])} and {pct(solo["success_rate"])} respectively on their matched scenario sets. The results and paired tables answer the research question for the declared models and environments, with unsuccessful episodes retained. They do not justify a universal DQN advantage, learned collision-safety claim, or global multi-agent path optimum.',
        '', reliability+' '+sharing,
        '', 'The evidence supports evaluating reliability together with conditional path quality, separate training/inference budgets and explicit information access. Future work should add an information-matched baseline, multiple training sizes, recurrent or communicating policies, graph neural networks, expert imitation, stronger complete MAPF baselines and public warehouse tasks. PPO, QMIX and actor-critic methods are candidates for future comparisons, not methods evaluated here.']
    workflow=(f'![Figure 1. Shared-policy evaluation loop: current graph and positions produce local observations; frozen DQN weights propose actions; the movement referee resolves conflicts, then returns named rewards and the next observation.]({figures}workflow.png)')
    methods=methods.replace('### 4.2 Rewards and finite-horizon learning',workflow+'\n\n### 4.2 Rewards and finite-horizon learning')
    ref_lines=['## References','']+[f'[{r["id"]}] {r["authors"].rstrip(".")}. {r["title"]}. {r["venue"]}, {r["year"]}. [{r.get("doi","Primary source")}]({r["url"]}).' for r in references]
    manuscript='# '+TITLE+'\n\n**'+author['name']+'**\n\n'+author['affiliation']+'\n\n## Abstract\n\n'+abstract+'\n\n**Index terms:** graph search; deep Q-network; multi-agent pathfinding; dynamic grid; policy transfer.\n\n'+methods+'\n\n'+'\n\n'.join(results+discussion+limitations+conclusion+ref_lines)+'\n'
    (root/'paper.md').write_text(manuscript,encoding='utf-8')
    # Plain LaTeX source with the same text, tables, images, equations and bibliography.
    (root/'paper.tex').write_text(to_latex(manuscript),encoding='utf-8')
    claims=dict(overall={m:{k:overall[m][k] for k in ('episodes','successes','success_rate')} for m in ('astar','shared','solo')},
        unique_episodes=report['unique_episodes'],fresh_timing_rollouts=report['fresh_timing_rollouts'],audit=report['audit'],
        h1=report['contrasts']['h1'],h2=report['contrasts']['h2'],h3=report['contrasts']['h3'],h4=report['contrasts']['h4'],
        section_evidence={'Abstract':'report.json: groups.overall and audit','6.1':'report.json: audit/scenarios',
            '6.2':'tables/overall.md, condition_agents.md, size_condition.md','6.3':'tables/h1_paired.md, h2_exposed.md',
            '6.4':'tables/h4_paired.md, training.md, runtime.md','7':'report.json: contrasts/scenarios','9':'report.json: groups.overall'})
    (root/'claims.json').write_text(json.dumps(claims,indent=2)+'\n')
    inputs=[root/'methods_source.md',root/'references.json',root/'author.json',analysis/'report.json',analysis/'provenance.json']
    inputs += list((analysis/'tables').glob('*.md'))+list((analysis/'figures').glob('*.png'))
    provenance=dict(analysis=analysis.relative_to(ROOT).as_posix(),run=report['run'],
        builder_sha256=digest(Path(__file__)),input_sha256={p.relative_to(ROOT).as_posix():digest(p) for p in inputs},
        manuscript_sha256=digest(root/'paper.md'),latex_sha256=digest(root/'paper.tex'),claims_sha256=digest(root/'claims.json'),
        qenn_sha256=digest(ROOT/'references/QENN_Research_Paper_Madhav_Joshi (1).docx'),
        author_details=author,
        status='scientific manuscript generated; content/PDF review still required')
    (root/'manuscript_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(f'Manuscript generated: {root/"paper.md"}',flush=True)
    return root/'paper.md'


def tex_escape(text):
    substitutions={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
    return ''.join(substitutions.get(c,c) for c in text)


def to_latex(markdown):
    lines=markdown.splitlines(); body=[]; i=1
    while i<len(lines):
        line=lines[i]
        if line in ('**Madhav Joshi**','Marwadi University'): i+=1; continue
        if line.startswith('$$'): body.append('\\['+line.strip('$')+'\\]'); i+=1; continue
        match=re.fullmatch(r'!\[([^]]*)\]\(([^)]+)\)',line)
        if match:
            body.extend([r'\begin{figure}[htbp]',r'\centering',r'\includegraphics[width=\linewidth]{'+match[2]+'}',r'\caption{'+tex_escape(match[1])+'}',r'\end{figure}']); i+=1; continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                values=[v.strip() for v in lines[i].strip('|').split('|')]
                if not all(re.fullmatch(r'[:\- ]+',v) for v in values): rows.append(values)
                i+=1
            columns=(r'p{\dimexpr\linewidth/'+str(len(rows[0]))+r'-2\tabcolsep\relax}')*len(rows[0])
            body.append(r'{\footnotesize\begin{longtable}{'+columns+'}')
            for row in rows: body.append(' & '.join(tex_escape(v) for v in row)+r' \\')
            body.append(r'\end{longtable}}'); continue
        heading=re.match(r'^(#{2,4}) (.*)',line)
        if heading:
            command='section*' if len(heading[1])==2 else 'subsection*'
            body.append('\\'+command+'{'+tex_escape(heading[2])+'}'); i+=1; continue
        # Preserve link text and URLs; plain source remains independently readable.
        pieces=[]; last=0
        for link in re.finditer(r'\[([^]]+)\]\(([^)]+)\)',line):
            pieces.append(tex_escape(line[last:link.start()]))
            pieces.append(r'\href{'+link[2]+'}{'+tex_escape(link[1])+'}'); last=link.end()
        pieces.append(tex_escape(line[last:]))
        body.append(''.join(pieces).replace('**','').replace('`','')); i+=1
    return '\n'.join([r'\documentclass[10pt,a4paper]{article}',r'\usepackage[margin=18mm]{geometry}',
        r'\usepackage{fontspec,graphicx,amsmath,longtable,hyperref}',r'\setmainfont{Times New Roman}',
        r'\title{'+tex_escape(TITLE)+'}',r'\author{Madhav Joshi \\ Marwadi University}',r'\date{}',r'\begin{document}',r'\maketitle',*body,r'\end{document}'])+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('analysis',type=Path)
    args=parser.parse_args(); build(args.analysis)


if __name__=='__main__': main()
