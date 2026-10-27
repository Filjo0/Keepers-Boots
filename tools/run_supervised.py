"""Run one local Windows workload with resource checks and owned-tree cleanup."""
import argparse
from contextlib import contextmanager
import ctypes
from ctypes import wintypes
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
MUTEX_NAME = r"Global\KeepersBoots.SupervisedWorkload.v1"


class Deferred(RuntimeError):
    pass


@contextmanager
def workload_lock(name=MUTEX_NAME):
    """Share one mutex across checkouts/sessions; Windows releases abandoned locks."""
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    for function, args, result in (
        ("CreateMutexW", [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR], wintypes.HANDLE),
        ("WaitForSingleObject", [wintypes.HANDLE, wintypes.DWORD], wintypes.DWORD),
        ("ReleaseMutex", [wintypes.HANDLE], wintypes.BOOL),
        ("CloseHandle", [wintypes.HANDLE], wintypes.BOOL),
    ):
        getattr(api, function).argtypes, getattr(api, function).restype = args, result
    handle = api.CreateMutexW(None, False, name)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    acquired = False
    try:
        status = api.WaitForSingleObject(handle, 0)
        if status == 0x102:  # WAIT_TIMEOUT
            raise Deferred("Another supervised workload holds the machine lock.")
        if status not in (0, 0x80):  # WAIT_OBJECT_0 / WAIT_ABANDONED
            raise ctypes.WinError(ctypes.get_last_error())
        acquired = True
        yield
    finally:
        if acquired:
            api.ReleaseMutex(handle)
        api.CloseHandle(handle)


class BasicLimits(ctypes.Structure):
    _fields_ = [("process_time", ctypes.c_longlong), ("job_time", ctypes.c_longlong),
                ("flags", wintypes.DWORD), ("min_working_set", ctypes.c_size_t),
                ("max_working_set", ctypes.c_size_t), ("active_processes", wintypes.DWORD),
                ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD),
                ("scheduling", wintypes.DWORD)]


class ExtendedLimits(ctypes.Structure):
    _fields_ = [("basic", BasicLimits), ("io_counters", ctypes.c_ulonglong * 6),
                ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                ("peak_process_memory", ctypes.c_size_t), ("peak_job_memory", ctypes.c_size_t)]


class OwnedJob:
    """Kill-on-close Windows job: only the waiting bootstrap and its descendants."""
    def __init__(self, max_memory_mib):
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        for name, args, result in (
            ("CreateJobObjectW", [ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
            ("SetInformationJobObject", [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL),
            ("QueryInformationJobObject", [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p], wintypes.BOOL),
            ("AssignProcessToJobObject", [wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
            ("CloseHandle", [wintypes.HANDLE], wintypes.BOOL),
        ):
            function = getattr(self.api, name)
            function.argtypes, function.restype = args, result
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000 | 0x200  # KILL_ON_JOB_CLOSE | JOB_MEMORY
        limits.job_memory = max_memory_mib * 1024 * 1024
        if not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            error = ctypes.WinError(ctypes.get_last_error())
            self.close()
            raise error

    def assign(self, process):
        if not self.api.AssignProcessToJobObject(self.handle, int(process._handle)):
            raise ctypes.WinError(ctypes.get_last_error())

    def report_memory(self):
        """Read peak job commitment before closing its handle; never infer an OOM."""
        limits = ExtendedLimits()
        if not self.api.QueryInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits), None):
            raise ctypes.WinError(ctypes.get_last_error())
        near_cap = bool(limits.job_memory and limits.peak_job_memory * 10 >= limits.job_memory * 9)
        print(json.dumps({"job_memory": {
            "peak_committed_mib": round(limits.peak_job_memory / 1024**2, 3),
            "cap_mib": round(limits.job_memory / 1024**2, 3),
            "near_cap": near_cap,
        }}), flush=True)
        if near_cap:
            print("Warning: job peak commitment reached at least 90% of its cap. "
                  "Allocation failures may be cap-related; this reading does not prove their cause.", flush=True)

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None


def check_resources(phase, gpu_required_mib=0, *, require_gpu=False):
    """Fail closed on timeout, missing metrics, malformed output or a failed gate."""
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-File",
         str(ROOT / "tools/check_resources.ps1"), "-Phase", phase,
         "-GpuRequiredMiB", str(gpu_required_mib)] + (["-RequireGpu"] if require_gpu or phase == "start" else []),
        capture_output=True, text=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW,
    )
    reading = json.loads(result.stdout)
    print(json.dumps({"resource_check": reading}), flush=True)
    metrics = [reading.get(key) for key in ("CpuLoadPercent", "RamAvailableGiB", "CommittedPercent", "DiskFreeGiB")]
    gpu = reading.get("Gpu") or {}
    if gpu or require_gpu or phase == "start" or reading.get("GpuMetricsRequired"):
        metrics += [gpu.get(key) for key in ("TotalMiB", "UsedMiB", "FreeMiB", "TemperatureC", "UtilizationPercent")]
    if any(type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in metrics):
        raise Deferred("Required resource metrics are unavailable.")
    if result.returncode != 0 or reading.get("Decision") != "within_task_limits":
        raise Deferred("Resource gate refused the workload.")


def supervise(command, *, model=False, gpu_required_mib=0, timeout=900, interval=30,
              max_memory_mib=None, checker=None, mutex_name=MUTEX_NAME):
    if os.name != "nt":
        raise Deferred("This supervisor requires Windows job objects.")
    if not command or timeout <= 0 or not 0 < interval <= 60:
        raise ValueError("A command, positive deadline and interval at most 60 seconds are required.")
    if gpu_required_mib < 0 or (model and gpu_required_mib == 0) or (gpu_required_mib and not model):
        raise ValueError("Model jobs require an explicit expected GPU allocation in MiB.")
    if model and max_memory_mib is None:
        raise ValueError("Model jobs require an explicit --max-memory-mib committed-memory budget.")
    memory_budget = 1024 if max_memory_mib is None else max_memory_mib
    if type(memory_budget) is not int or not 64 <= memory_budget <= 65536:
        raise ValueError("Committed-memory budget must be an integer between 64 and 65536 MiB.")
    if checker is None:
        checker = lambda phase, gpu: check_resources(phase, gpu, require_gpu=model)
    with workload_lock(mutex_name):
        checker("start" if model else "check", gpu_required_mib if model else 0)
        job = OwnedJob(memory_budget)
        child = None
        try:
            # The bootstrap cannot run the workload until assignment succeeds.
            # This also contains the virtual-environment launcher's child process.
            child = subprocess.Popen(
                # Direct base interpreter avoids the venv launcher's early child
                # escaping assignment. The workload command still uses its venv.
                [sys._base_executable, str(Path(__file__).resolve()), "--_child"],
                cwd=ROOT, stdin=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS,
            )
            job.assign(child)
            child.stdin.write(json.dumps(command) + "\n")
            child.stdin.close()
            started = time.monotonic()
            next_check = started + interval
            while child.poll() is None:
                now = time.monotonic()
                if now - started >= timeout:
                    raise Deferred("Workload deadline reached.")
                if now >= next_check:
                    checker("running", 0)  # Allocation is now included in measured usage.
                    next_check = time.monotonic() + interval
                time.sleep(0.2)
            return child.returncode
        finally:
            active_error = sys.exc_info()[0] is not None
            try:
                job.report_memory()
            except Exception as exc:
                try:
                    print("Job memory diagnostic unavailable: " + type(exc).__name__, flush=True)
                except OSError:
                    pass  # Broken output must not prevent owned-tree cleanup.
            finally:
                job.close()  # Includes descendants left after a parent exits normally.
            cleanup_failed = False
            if child is not None:
                try:
                    if child.stdin is not None and not child.stdin.closed:
                        child.stdin.close()  # Assignment failure: EOF, no workload started.
                    child.wait(timeout=10)
                except (OSError, subprocess.TimeoutExpired) as exc:
                    cleanup_failed = True
                    print("Owned workload cleanup: " + type(exc).__name__, flush=True)
            try:
                checker("check", 0)
            except Exception as exc:
                print("Post-job resource gate: " + type(exc).__name__, flush=True)
            if cleanup_failed and not active_error:
                raise Deferred("Owned workload cleanup did not finish in time.")


def main():
    if sys.argv[1:] == ["--_child"]:
        payload = sys.stdin.readline()
        return subprocess.call(json.loads(payload), stdin=subprocess.DEVNULL) if payload else 2
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", action="store_true", help="Use the stricter model-load gate")
    parser.add_argument("--gpu-required-mib", type=int, default=0, help="Expected model GPU allocation, excluding reserve")
    parser.add_argument("--max-memory-mib", type=int, help="Job committed-memory cap; default 1024 for non-model jobs, required for model jobs")
    parser.add_argument("--timeout", type=int, default=900, help="Maximum workload seconds")
    parser.add_argument("--interval", type=int, choices=range(5, 61), default=30, metavar="5..60")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command after --; runs without a shell")
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    try:
        return supervise(command, model=args.model, gpu_required_mib=args.gpu_required_mib,
                         max_memory_mib=args.max_memory_mib, timeout=args.timeout, interval=args.interval)
    except KeyboardInterrupt:
        print("Stopped the owned workload.", flush=True)
        return 130
    except Exception as exc:
        # Never print command arguments, environment values or captured stderr.
        print("Workload refused/stopped: " + type(exc).__name__ +
              (": " + str(exc) if isinstance(exc, (Deferred, ValueError)) else ""), flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
