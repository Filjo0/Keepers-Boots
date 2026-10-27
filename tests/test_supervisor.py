from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from uuid import uuid4
from unittest.mock import Mock, call, patch

from tools.run_supervised import Deferred, ExtendedLimits, MUTEX_NAME, OwnedJob, ROOT, check_resources, supervise, workload_lock


@unittest.skipUnless(os.name == "nt", "Windows job objects and mutexes")
class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.mutex_name = r"Global\KeepersBoots.Test." + uuid4().hex

    def test_refused_preflight_never_starts_workload(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary) / "started"
            with self.assertRaises(Deferred):
                supervise([sys.executable, "-c", f"open({str(marker)!r},'w').close()"],
                          checker=lambda *_: (_ for _ in ()).throw(Deferred("pressure")),
                          mutex_name=self.mutex_name)
            self.assertFalse(marker.exists())

    def test_another_process_cannot_hold_same_lock_and_lock_is_reusable(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.mutex_name
            code = (f"import sys; sys.path.insert(0, {str(ROOT)!r}); "
                    "from tools.run_supervised import workload_lock; "
                    f"\nwith workload_lock({path!r}): pass")
            with workload_lock(path):
                blocked = subprocess.run([sys.executable, "-c", code], capture_output=True, cwd=temporary)
                self.assertNotEqual(blocked.returncode, 0)
                self.assertIn(b"Another supervised workload holds the machine lock.", blocked.stderr)
            with workload_lock(path):
                pass

    def test_exit_code_and_model_allocation_gates(self):
        phases = []
        with tempfile.TemporaryDirectory() as temporary, redirect_stdout(io.StringIO()) as output:
            self.assertEqual(supervise([sys.executable, "-c", "raise SystemExit(7)"],
                                      checker=lambda *args: phases.append(args), model=True,
                                      gpu_required_mib=100, max_memory_mib=128, mutex_name=self.mutex_name), 7)
        self.assertEqual(phases, [("start", 100), ("check", 0)])
        memory = json.loads(output.getvalue().splitlines()[0])["job_memory"]
        self.assertGreater(memory["peak_committed_mib"], 0)
        self.assertEqual(memory["cap_mib"], 128.0)
        with self.assertRaises(ValueError):
            supervise([sys.executable], model=True)
        with self.assertRaises(ValueError):
            supervise([sys.executable], gpu_required_mib=100)
        with self.assertRaisesRegex(ValueError, "committed-memory budget"):
            supervise([sys.executable], model=True, gpu_required_mib=100)
        for budget in (0, 63, 65537, True):
            with self.assertRaises(ValueError):
                supervise([sys.executable], max_memory_mib=budget)

    def test_pressure_stops_descendant_but_leaves_unrelated_process(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            heartbeat = root / "heartbeat"
            tick = f"from pathlib import Path; import time\nwhile True: Path({str(heartbeat)!r}).write_text(str(time.time())); time.sleep(.05)"
            code = f"import subprocess,sys,time; subprocess.Popen([sys.executable,'-c',{tick!r}]); time.sleep(30)"
            phases = []

            def pressure(phase, gpu):
                phases.append((phase, gpu))
                if phase == "running":
                    self.assertTrue(heartbeat.exists(), "Descendant actually ran before stop")
                    raise Deferred("simulated memory pressure")

            unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
            try:
                with self.assertRaisesRegex(Deferred, "memory pressure"):
                    supervise([sys.executable, "-c", code], checker=pressure, interval=2,
                              mutex_name=self.mutex_name)
                before = heartbeat.read_text()
                import time
                time.sleep(.3)
                self.assertEqual(heartbeat.read_text(), before)
                self.assertIsNone(unrelated.poll())
                self.assertEqual(phases, [("check", 0), ("running", 0), ("check", 0)])
            finally:
                unrelated.terminate()
                unrelated.wait(timeout=5)

    def test_deadline_cleans_up_and_releases_lock(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.mutex_name
            with self.assertRaisesRegex(Deferred, "deadline"):
                supervise([sys.executable, "-c", "import time; time.sleep(30)"],
                          timeout=.5, checker=lambda *_: None, mutex_name=self.mutex_name)
            with workload_lock(path):
                pass

    def test_metrics_failure_and_timeout_fail_closed(self):
        bad = subprocess.CompletedProcess([], 0, json.dumps({"Decision": "defer_heavy_work"}), "")
        with patch("tools.run_supervised.subprocess.run", return_value=bad):
            with self.assertRaises(Deferred):
                check_resources("check")
        with patch("tools.run_supervised.subprocess.run", side_effect=subprocess.TimeoutExpired([], 20)):
            with self.assertRaises(subprocess.TimeoutExpired):
                check_resources("check")
        missing = subprocess.CompletedProcess([], 0, '{"Decision":"within_task_limits"}', "")
        with patch("tools.run_supervised.subprocess.run", return_value=missing):
            with self.assertRaisesRegex(Deferred, "metrics"):
                check_resources("check")

    def test_job_memory_cap_is_applied_by_windows_without_large_allocations(self):
        import ctypes
        from ctypes import wintypes
        job = OwnedJob(64)
        try:
            query = job.api.QueryInformationJobObject
            query.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p]
            query.restype = wintypes.BOOL
            limits = ExtendedLimits()
            self.assertTrue(query(job.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits), None))
            self.assertEqual(limits.job_memory, 64 * 1024 * 1024)
            self.assertTrue(limits.basic.flags & 0x200)
            self.assertTrue(limits.basic.flags & 0x2000)
            with redirect_stdout(io.StringIO()) as output:
                job.report_memory()
            report = json.loads(output.getvalue())["job_memory"]
            self.assertEqual(report, {"peak_committed_mib": 0.0, "cap_mib": 64.0, "near_cap": False})
        finally:
            job.close()

    def test_peak_diagnostic_warns_at_ninety_percent_without_allocating_memory(self):
        import ctypes
        job = OwnedJob(64)
        try:
            for peak, near in ((89, False), (90, True), (100, True)):
                def query(_handle, _kind, destination, _size, _returned):
                    limits = ctypes.cast(destination, ctypes.POINTER(ExtendedLimits)).contents
                    limits.job_memory = 100 * 1024**2
                    limits.peak_job_memory = peak * 1024**2
                    return True
                with self.subTest(peak=peak), patch.object(job.api, "QueryInformationJobObject", side_effect=query):
                    with redirect_stdout(io.StringIO()) as output:
                        job.report_memory()
                    lines = output.getvalue().splitlines()
                    self.assertEqual(json.loads(lines[0])["job_memory"], {
                        "peak_committed_mib": float(peak), "cap_mib": 100.0, "near_cap": near})
                    self.assertEqual(len(lines), 2 if near else 1)
                    if near:
                        self.assertIn("does not prove", lines[1])
        finally:
            job.close()

    def test_failed_memory_query_preserves_cleanup_and_primary_stop(self):
        phases = []
        child = Mock()
        child.stdin.closed = True
        original = Deferred("original stop")
        child.poll.side_effect = original
        with patch("tools.run_supervised.OwnedJob") as job, patch("tools.run_supervised.subprocess.Popen", return_value=child):
            job.return_value.report_memory.side_effect = OSError("query failed")
            with self.assertRaises(Deferred) as caught, redirect_stdout(io.StringIO()) as output:
                supervise(["not-started"], checker=lambda *args: phases.append(args), mutex_name=self.mutex_name)
            self.assertIs(caught.exception, original)
            self.assertEqual(job.return_value.method_calls, [
                call.assign(child), call.report_memory(), call.close()])
            self.assertIn("diagnostic unavailable", output.getvalue())
        self.assertEqual(phases, [("check", 0), ("check", 0)])

    def test_assignment_failure_never_releases_workload_and_still_checks_afterwards(self):
        phases = []
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary) / "must-not-exist"
            with patch.object(OwnedJob, "assign", side_effect=OSError("assignment refused")):
                with self.assertRaisesRegex(OSError, "assignment refused"):
                    supervise([sys.executable, "-c", f"open({str(marker)!r},'w').close()"],
                              checker=lambda *args: phases.append(args), mutex_name=self.mutex_name)
            self.assertFalse(marker.exists())
        self.assertEqual(phases, [("check", 0), ("check", 0)])
        with workload_lock(self.mutex_name):
            pass

    def test_cleanup_timeout_preserves_interrupt_or_primary_error_and_post_check(self):
        for original in (KeyboardInterrupt(), Deferred("primary stop")):
            with self.subTest(error=type(original).__name__):
                phases = []
                child = Mock()
                child.stdin.closed = True
                child.poll.side_effect = original
                child.wait.side_effect = subprocess.TimeoutExpired("owned-child", 10)
                with patch("tools.run_supervised.OwnedJob") as job, patch("tools.run_supervised.subprocess.Popen", return_value=child):
                    with self.assertRaises(type(original)) as caught:
                        supervise(["not-started"], checker=lambda *args: phases.append(args), mutex_name=self.mutex_name)
                    self.assertIs(caught.exception, original)
                    job.return_value.close.assert_called_once()
                self.assertEqual(phases, [("check", 0), ("check", 0)])
                with workload_lock(self.mutex_name):
                    pass

    def test_real_powershell_output_without_nvidia_accepts_cpu_job_but_refuses_model(self):
        # Execute the real checker using fixture providers, not the host's load.
        # This tests PS->JSON->Python and never allocates a model or queries CIM.
        providers = """
function Get-CimInstance {
    param($ClassName)
    switch ($ClassName) {
        'Win32_Processor' { [pscustomobject]@{ LoadPercentage = 10 } }
        'Win32_OperatingSystem' { [pscustomobject]@{ FreePhysicalMemory = 4 * 1MB } }
        'Win32_PerfFormattedData_PerfOS_Memory' { [pscustomobject]@{ PercentCommittedBytesInUse = 50 } }
        default { throw 'Unexpected metric provider' }
    }
}
function Get-PSDrive { param($Name) [pscustomobject]@{ Free = 20 * 1GB } }
function Get-Command { param($Name, $ErrorAction) $null }
"""
        script = str(ROOT / "tools/check_resources.ps1").replace("'", "''")
        for model in (False, True):
            with self.subTest(model=model):
                result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                                         providers + f"\n& '{script}' -Phase check" + (" -RequireGpu" if model else "") + "; exit $LASTEXITCODE"],
                                        capture_output=True, text=True, timeout=20,
                                        creationflags=subprocess.CREATE_NO_WINDOW)
                reading = json.loads(result.stdout)
                self.assertIsNone(reading["Gpu"])
                self.assertEqual(result.returncode, 2 if model else 0, result.stderr)
                with patch("tools.run_supervised.subprocess.run", return_value=result):
                    if model:
                        with self.assertRaises(Deferred):
                            check_resources("check", require_gpu=True)
                    else:
                        check_resources("check")
