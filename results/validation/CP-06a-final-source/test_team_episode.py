import json
import tempfile
import unittest
from pathlib import Path
from experiments.run_team_episode import generate
from evaluation.audit_team_episode import audit


class TeamTraceTests(unittest.TestCase):
    def test_real_trace_replay_and_reward_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'trace.json'
            data = generate()
            path.write_text(json.dumps(data))
            result = audit(path)
            self.assertEqual(result['cases'],16)
            self.assertEqual(result['successful_episodes'],9)
            self.assertEqual(result['planning_failures'],6)
            self.assertEqual(result['steps_replayed'],26)
            self.assertEqual(result['actual_collisions'],0)
            rewards = list(data['cases'][0]['steps'][0]['rewards'])
            rewards[0] = 999
            data['cases'][0]['steps'][0]['rewards'] = rewards
            path.write_text(json.dumps(data))
            with self.assertRaises(AssertionError): audit(path)

    def test_planning_failure_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'trace.json'
            data = generate()
            failed = next(c for c in data['cases'] if c.get('planning_success') is False)
            failed['failed_agent'] = 99
            path.write_text(json.dumps(data))
            with self.assertRaises(AssertionError): audit(path)


if __name__ == '__main__': unittest.main()
