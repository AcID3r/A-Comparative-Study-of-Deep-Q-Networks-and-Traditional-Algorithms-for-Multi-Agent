import json
import tempfile
import unittest
from pathlib import Path
from evaluation.team_protocol import ROOT
from experiments.run_dynamic_team import evaluate
from evaluation.audit_dynamic_team import audit


class DynamicTeamRunnerTests(unittest.TestCase):
    def profile(self):
        profile=json.loads((ROOT/'configs/dynamic_team.json').read_text())
        profile['purpose']='dynamic_team_smoke'
        return profile

    def test_real_saved_policy_pipeline_audit_and_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            run=evaluate(self.profile(),Path(temp)/'runs')
            result=audit(run)
            self.assertEqual(result['episodes'],168)
            self.assertTrue(result['identical_active_event_prefixes'])
            path=run/'trajectories.jsonl'
            lines=path.read_text().splitlines()
            data=json.loads(lines[0]); data['rollout']['final_info']['total_moves']=999
            lines[0]=json.dumps(data); path.write_text('\n'.join(lines)+'\n')
            with self.assertRaises(AssertionError): audit(run)

    def test_invalid_profile_creates_no_output(self):
        profile=self.profile(); profile['remove_tick']=1
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'runs'
            with self.assertRaises(ValueError): evaluate(profile,output)
            self.assertFalse(output.exists())


if __name__=='__main__': unittest.main()
