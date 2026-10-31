import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

import app
import llm
import specialists


class WorkflowTests(unittest.TestCase):
    analysis = {
        "severity": "SEV3",
        "summary": "Elevated queue latency.",
        "proposed_action": "Inspect queue metrics.",
        "risk": "low",
        "rationale": "Read-only investigation.",
    }

    def test_specialists_reuse_shared_factory(self):
        self.assertIs(specialists.build_model, llm.build_model)

    def test_analyst_uses_tool_calling_and_returns_schema_dict(self):
        model = ChatOpenAI(model="test-model", api_key="offline")
        response = ChatResult(generations=[ChatGeneration(message=AIMessage(
            content="",
            tool_calls=[{
                "name": app.ANALYSIS_SCHEMA["title"],
                "args": self.analysis,
                "id": "analysis-call",
                "type": "tool_call",
            }],
        ))])
        with patch("app.build_model", return_value=model), patch.object(
            ChatOpenAI, "_generate", return_value=response
        ) as generate:
            result = app.build_analyst().invoke("Inspect the incident.")
        self.assertEqual(result, self.analysis)
        request = generate.call_args.kwargs
        self.assertEqual(request["tools"][0]["function"]["parameters"], {
            key: value for key, value in app.ANALYSIS_SCHEMA.items() if key != "title"
        })
        self.assertEqual(request["tool_choice"]["function"]["name"], "IncidentAnalysis")
        self.assertNotIn("response_format", request)

    def test_low_risk_publishes_without_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            runbooks = Path(directory) / "runbooks"
            analyst = Mock()
            analyst.invoke.return_value = self.analysis
            with patch("app.build_analyst", return_value=analyst), patch.object(
                app, "RUNBOOK_DIR", runbooks
            ), SqliteSaver.from_conn_string(str(Path(directory) / "checkpoints.db")) as saver:
                graph = app.build_graph(saver)
                result = graph.invoke({
                    "incident_id": "low-risk",
                    "incident": "Queue latency increased.",
                    "audit_log": [],
                }, {"configurable": {"thread_id": "low-risk"}})
            self.assertEqual(result["status"], "published")
            self.assertFalse(result["requires_approval"])
            self.assertEqual(result["analysis"], self.analysis)
            content = Path(result["runbook_path"]).read_text(encoding="utf-8")
            self.assertIn("Approval outcome: Not required by policy", content)
            self.assertIn(self.analysis["proposed_action"], content)
            analyst.invoke.assert_called_once()

    def test_high_risk_pauses_and_resumes_from_sqlite(self):
        for decision in ("approve", "reject"):
            with self.subTest(decision=decision), tempfile.TemporaryDirectory() as directory:
                runbooks = Path(directory) / "runbooks"
                database = str(Path(directory) / "checkpoints.db")
                config = {"configurable": {"thread_id": decision}}
                analyst = Mock()
                analyst.invoke.return_value = {
                    **self.analysis, "severity": "SEV1", "risk": "high"
                }
                with patch("app.build_analyst", return_value=analyst), patch.object(
                    app, "RUNBOOK_DIR", runbooks
                ):
                    with SqliteSaver.from_conn_string(database) as saver:
                        result = app.build_graph(saver).invoke({
                            "incident_id": decision,
                            "incident": "Queue latency increased.",
                            "audit_log": [],
                        }, config)
                    self.assertTrue(result["requires_approval"])
                    self.assertEqual(result["__interrupt__"][0].value["allowed_decisions"],
                                     ["approve", "reject"])
                    self.assertFalse(runbooks.exists())
                    with SqliteSaver.from_conn_string(database) as saver:
                        graph = app.build_graph(saver)
                        self.assertEqual(graph.get_state(config).next, ("approval_gate",))
                        result = graph.invoke(Command(resume=decision), config)
                    analyst.invoke.assert_called_once()
                if decision == "approve":
                    self.assertEqual(result["status"], "published")
                    content = Path(result["runbook_path"]).read_text(encoding="utf-8")
                    self.assertIn("Approval outcome: Approved", content)
                    self.assertIn("Human approved the proposal.", content)
                else:
                    self.assertEqual(result["status"], "rejected_without_publish")
                    self.assertNotIn("runbook_path", result)
                    self.assertFalse(runbooks.exists())
                    self.assertIn("Human rejected the proposal.", result["audit_log"])


if __name__ == "__main__":
    unittest.main()
