from tom_bench.batch import plan_batch, run_batch
from tom_bench.clients.mock import MockClient
from tom_bench.generator import generate_pair


class StatefulFailThenSucceedClient:
    """Fails the first `fail_times` calls with a non-retryable error, then
    succeeds. Used to simulate a mid-batch API failure that requires a
    later, separate run_batch invocation to resolve (the "resumable across
    days" scenario from PRD test plan §13)."""

    def __init__(self, name: str, fail_times: int):
        self.name = name
        self.min_interval_seconds = 0.0
        self.fail_times = fail_times
        self.calls = 0

    def generate(self, prompt: str) -> str:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("500 Internal Server Error (simulated, non-retryable)")
        return '{"assist_location": "unknown"}'


def test_dry_run_does_not_write_files_and_counts_correctly(tmp_path):
    pairs = [generate_pair(seed=1), generate_pair(seed=2)]
    clients = {"mock-a": MockClient(name="mock-a")}
    trials_dir = tmp_path / "trials"
    plan = run_batch(pairs, clients, ["interactive", "quiz"], trials_dir=trials_dir, dry_run=True)
    assert not trials_dir.exists() or not any(trials_dir.glob("*.json"))
    # 2 pairs * 2 conditions * 1 client * 2 task types = 8 calls
    assert plan.total_calls == 8
    assert plan.already_done == 0


def test_plan_batch_accounts_for_existing_trials(tmp_path):
    pairs = [generate_pair(seed=3)]
    clients = {"mock-a": MockClient(name="mock-a")}
    trials_dir = tmp_path / "trials"
    run_batch(pairs, clients, ["interactive"], trials_dir=trials_dir)
    plan = plan_batch(pairs, clients, ["interactive"], trials_dir=trials_dir)
    assert plan.already_done == 2  # F + T
    assert plan.total_calls == 0


def test_batch_preserves_partial_results_and_is_resumable(tmp_path):
    pairs = [generate_pair(seed=9)]
    client = StatefulFailThenSucceedClient(name="flaky", fail_times=1)
    clients = {client.name: client}
    trials_dir = tmp_path / "trials"

    run_batch(pairs, clients, ["interactive"], trials_dir=trials_dir, max_retries=0)
    files_after_first_run = list(trials_dir.glob("*.json"))
    assert len(files_after_first_run) == 1  # the F-trial call failed, T-trial call succeeded

    run_batch(pairs, clients, ["interactive"], trials_dir=trials_dir, max_retries=0)
    files_after_second_run = list(trials_dir.glob("*.json"))
    assert len(files_after_second_run) == 2  # resumed run filled in the missing trial


def test_batch_on_trial_callback_fires_for_every_attempt(tmp_path):
    pairs = [generate_pair(seed=4)]
    clients = {"mock-a": MockClient(name="mock-a")}
    trials_dir = tmp_path / "trials"
    seen = []
    run_batch(pairs, clients, ["interactive", "quiz"], trials_dir=trials_dir, on_trial=seen.append)
    assert len(seen) == 4  # 2 conditions * 2 task types
