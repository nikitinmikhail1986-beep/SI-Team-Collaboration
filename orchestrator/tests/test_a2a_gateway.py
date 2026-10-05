import json
import unittest
from federation_mcp.a2a_gateway import load_card, rpc_result


class A2AGatewayTests(unittest.TestCase):
    def test_card_points_to_gateway(self):
        card = load_card('https://example.test')
        self.assertEqual(card['url'], 'https://example.test/a2a')
        self.assertGreaterEqual(len(card['skills']), 1)

    def test_discover_exposes_join_without_authority(self):
        result = rpc_result('federation.discover', {})
        self.assertEqual(result['default_membership'], 'limited_A1')
        self.assertFalse(result['authority_granted_automatically'])

    def test_join_requires_trial(self):
        result = rpc_result('federation.join', {'candidate_id': 'demo-agent'})
        self.assertEqual(result['state'], 'trial_required')
        self.assertFalse(result['grants_authority'])

    def test_message_send_returns_agent_message(self):
        result = rpc_result('message/send', {'message': {'messageId': 'm-1', 'role': 'user', 'parts': [{'kind': 'text', 'text': 'hello'}]}})
        self.assertEqual(result['role'], 'agent')
        self.assertEqual(result['kind'], 'message')
        self.assertEqual(result['contextId'], 'm-1')
        self.assertTrue(result['parts'])
        machine = next(p for p in result['parts'] if p.get('kind') == 'data')['data']
        self.assertEqual(machine['entry_flow'], ['federation.discover', 'public_trial', 'federation.join'])
        self.assertEqual(machine['membership_on_success'], 'limited_A1')
        self.assertFalse(machine['authority_granted_automatically'])
        self.assertFalse(machine['sensitive_access'])
        self.assertIn('human_entry', machine)
        self.assertIn('JOIN.md', machine['human_entry']['join_documentation'])
        self.assertIn('federation-trial.yml', machine['human_entry']['trial_url'])

    def test_unknown_method_is_rejected(self):
        with self.assertRaises(KeyError):
            rpc_result('nope', {})


if __name__ == '__main__':
    unittest.main()
