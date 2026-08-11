import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "deploy-private-vps-proxy" / "scripts" / "generate-routing-rules.rb"
POLICY = ROOT / "deploy-private-vps-proxy" / "assets" / "routing-policy.json"


class GenerateProxyRoutingRulesTest(unittest.TestCase):
    def run_generator(self, policy: Path, output: Path, server="203.0.113.10"):
        env = os.environ.copy()
        env["SOURCE_DATE_EPOCH"] = "0"
        return subprocess.run(
            [
                "ruby",
                str(SCRIPT),
                "--policy",
                str(policy),
                "--proxy-server",
                server,
                "--output",
                str(output),
            ],
            text=True,
            capture_output=True,
            env=env,
        )

    def test_generates_all_protected_formats_with_safe_ordering(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "rules"
            result = self.run_generator(POLICY, output)
            self.assertEqual(result.returncode, 0, result.stderr)

            expected = {
                "manifest.json",
                "mihomo-rules.yaml",
                "sing-box-route.json",
                "v2rayn-xray-routing.json",
            }
            self.assertEqual({path.name for path in output.iterdir()}, expected)
            for path in output.iterdir():
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

            sing_box = json.loads((output / "sing-box-route.json").read_text())
            rules = sing_box["route"]["rules"]
            self.assertEqual(rules[0], {"action": "sniff"})
            self.assertEqual(rules[1]["action"], "hijack-dns")
            self.assertEqual(rules[2]["outbound"], "direct")
            self.assertEqual(sing_box["route"]["final"], "proxy")

            xray = json.loads((output / "v2rayn-xray-routing.json").read_text())
            self.assertEqual(xray[0]["remarks"], "Proxy server bypass")
            self.assertEqual(xray[-1]["outboundTag"], "proxy")

            manifest = json.loads((output / "manifest.json").read_text())
            self.assertEqual(manifest["output_tags"]["sing_box"]["proxy"], "proxy")

            mihomo = (output / "mihomo-rules.yaml").read_text()
            self.assertIn("IP-CIDR,203.0.113.10/32,DIRECT,no-resolve", mihomo)
            self.assertTrue(mihomo.rstrip().endswith('"MATCH,PROXY"'))

    def test_rejects_conflicting_domain_actions(self):
        with tempfile.TemporaryDirectory() as temp:
            policy = json.loads(POLICY.read_text())
            policy["custom"]["direct_domains"] = ["openai.com"]
            policy_path = Path(temp) / "policy.json"
            policy_path.write_text(json.dumps(policy))
            result = self.run_generator(policy_path, Path(temp) / "rules")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Domain conflicts", result.stderr)

    def test_rejects_invalid_cidr(self):
        with tempfile.TemporaryDirectory() as temp:
            policy = json.loads(POLICY.read_text())
            policy["custom"]["direct_ip_cidrs"] = ["not-a-cidr"]
            policy_path = Path(temp) / "policy.json"
            policy_path.write_text(json.dumps(policy))
            result = self.run_generator(policy_path, Path(temp) / "rules")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Invalid CIDR", result.stderr)

    def test_refuses_to_overwrite_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "rules"
            first = self.run_generator(POLICY, output)
            second = self.run_generator(POLICY, output)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("Refusing to overwrite", second.stderr)


if __name__ == "__main__":
    unittest.main()
