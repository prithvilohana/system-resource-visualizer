import os
import math
import time
import queue
import threading
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import deque

import psutil
import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


APP_TITLE = "PDC Live Laptop Performance Visualizer"
UPDATE_MS = 1000
HISTORY_POINTS = 60
DEFAULT_WORKLOAD = 650_000


# ============================================================
# CPU-BOUND WORKLOAD FOR SCALABILITY TEST
# ============================================================
def is_prime(n):
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False

    limit = int(math.sqrt(n)) + 1
    for divisor in range(3, limit, 2):
        if n % divisor == 0:
            return False
    return True


def count_primes_range(bounds):
    start, end = bounds
    count = 0
    for number in range(start, end):
        if is_prime(number):
            count += 1
    return count


def split_range(limit, workers):
    start = 2
    total = max(0, limit - start)
    chunk = math.ceil(total / workers)
    ranges = []

    for index in range(workers):
        a = start + index * chunk
        b = min(limit, a + chunk)
        if a < b:
            ranges.append((a, b))

    return ranges


def run_prime_benchmark(workers, workload):
    ranges = split_range(workload, workers)
    start = time.perf_counter()

    with ProcessPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(count_primes_range, ranges))

    elapsed = time.perf_counter() - start
    return elapsed, sum(results)


# ============================================================
# COMMUNICATION BENCHMARK
# ============================================================
def echo_process(connection):
    try:
        while True:
            payload = connection.recv_bytes()
            if payload == b"__STOP__":
                break
            connection.send_bytes(payload)
    finally:
        connection.close()


def measure_ipc_latency():
    parent_conn, child_conn = mp.Pipe(duplex=True)
    process = mp.Process(target=echo_process, args=(child_conn,))
    process.start()

    tests = [
        (1, 150),
        (10, 120),
        (100, 60),
        (1024, 20),
    ]
    results = []

    try:
        for size_kb, rounds in tests:
            payload = b"x" * (size_kb * 1024)

            parent_conn.send_bytes(payload)
            parent_conn.recv_bytes()

            start = time.perf_counter()
            for _ in range(rounds):
                parent_conn.send_bytes(payload)
                parent_conn.recv_bytes()

            elapsed = time.perf_counter() - start
            results.append((size_kb, (elapsed / rounds) * 1000))
    finally:
        try:
            parent_conn.send_bytes(b"__STOP__")
        except Exception:
            pass
        process.join(timeout=3)
        parent_conn.close()

    return results


# ============================================================
# FAULT-TOLERANCE DEMO
# ============================================================
def reliability_worker(task_id, fail_first_time=False):
    if fail_first_time:
        raise RuntimeError(f"Simulated failure in task {task_id}")

    value = 0
    for i in range(1, 45_000):
        value += (i * task_id) % 101
    return value


def run_fault_tolerance_test():
    total_tasks = 20
    planned_failures = {5, 10, 15, 20}
    failed_ids = []
    initial_success = 0

    with ProcessPoolExecutor(max_workers=min(4, os.cpu_count() or 2)) as executor:
        futures = {}
        for task_id in range(1, total_tasks + 1):
            future = executor.submit(
                reliability_worker,
                task_id,
                task_id in planned_failures,
            )
            futures[future] = task_id

        for future in as_completed(futures):
            task_id = futures[future]
            try:
                future.result()
                initial_success += 1
            except Exception:
                failed_ids.append(task_id)

    recovered = 0
    unrecovered = 0

    if failed_ids:
        with ProcessPoolExecutor(max_workers=min(4, os.cpu_count() or 2)) as executor:
            retries = {
                executor.submit(reliability_worker, task_id, False): task_id
                for task_id in failed_ids
            }

            for future in as_completed(retries):
                try:
                    future.result()
                    recovered += 1
                except Exception:
                    unrecovered += 1

    final_completed = initial_success + recovered
    reliability = (final_completed / total_tasks) * 100
    recovery_rate = (recovered / len(failed_ids) * 100) if failed_ids else 100.0

    return {
        "total": total_tasks,
        "initial_success": initial_success,
        "initial_failed": len(failed_ids),
        "recovered": recovered,
        "unrecovered": unrecovered,
        "reliability": reliability,
        "recovery_rate": recovery_rate,
    }


# ============================================================
# GUI APPLICATION
# ============================================================
class PerformanceVisualizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1320x860")
        self.minsize(1050, 700)

        self.event_queue = queue.Queue()
        self.monitoring = True
        self.test_running = False

        self.time_counter = 0
        self.time_history = deque(maxlen=HISTORY_POINTS)
        self.cpu_history = deque(maxlen=HISTORY_POINTS)
        self.ram_history = deque(maxlen=HISTORY_POINTS)
        self.process_cpu_history = deque(maxlen=HISTORY_POINTS)
        self.process_ram_history = deque(maxlen=HISTORY_POINTS)

        self.process_map = {}
        self.selected_process = None

        self.benchmark_workers = []
        self.benchmark_times = []
        self.benchmark_speedups = []
        self.benchmark_efficiencies = []
        self.communication_sizes = []
        self.communication_latencies = []
        self.selected_process_failures = 0
        self.selected_process_display = ""

        self.system_bus_running = True
        self.system_bus_phase = 0.0
        self.system_bus_speed = tk.DoubleVar(value=1.0)
        self.current_cpu_usage = 0.0
        self.current_ram_usage = 0.0

        self._build_style()
        self._build_ui()
        self._prime_cpu_measurement()
        self.refresh_processes()
        self.after(200, self._poll_event_queue)
        self.after(300, self._update_live_data)
        self.after(200, self._update_system_bus)

    def _build_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("CardValue.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("CardText.TLabel", font=("Segoe UI", 9))
        style.configure("Section.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("TButton", padding=7)

    def _build_ui(self):
        header = ttk.Frame(self, padding=(14, 12, 14, 6))
        header.pack(fill="x")

        ttk.Label(header, text="Live Parallel Computing Performance Dashboard",
                  style="Title.TLabel").pack(side="left")

        self.status_var = tk.StringVar(value="Live monitoring active")
        ttk.Label(header, textvariable=self.status_var).pack(side="right")

        cards = ttk.Frame(self, padding=(14, 4, 14, 8))
        cards.pack(fill="x")

        physical = psutil.cpu_count(logical=False) or "N/A"
        logical = psutil.cpu_count(logical=True) or "N/A"
        ram_gb = psutil.virtual_memory().total / (1024 ** 3)

        self.cpu_value = tk.StringVar(value="0.0%")
        self.ram_value = tk.StringVar(value="0.0%")
        self.process_cpu_value = tk.StringVar(value="0.0%")
        self.process_ram_value = tk.StringVar(value="0.0%")

        card_data = [
            ("Physical Cores", str(physical), None),
            ("Logical CPUs", str(logical), None),
            ("Total RAM", f"{ram_gb:.1f} GB", None),
            ("Live CPU", None, self.cpu_value),
            ("Live RAM", None, self.ram_value),
            ("Selected Process CPU", None, self.process_cpu_value),
            ("Selected Process RAM", None, self.process_ram_value),
        ]

        for index, (label, fixed_value, variable) in enumerate(card_data):
            frame = ttk.LabelFrame(cards, text=label, padding=8)
            frame.grid(row=0, column=index, padx=4, sticky="nsew")
            cards.columnconfigure(index, weight=1)

            if variable is not None:
                ttk.Label(frame, textvariable=variable,
                          style="CardValue.TLabel").pack()
            else:
                ttk.Label(frame, text=fixed_value,
                          style="CardValue.TLabel").pack()

        process_row = ttk.Frame(self, padding=(14, 2, 14, 8))
        process_row.pack(fill="x")

        ttk.Label(process_row, text="Monitor application/process:",
                  style="Section.TLabel").pack(side="left", padx=(0, 8))

        self.process_combo = ttk.Combobox(process_row, state="readonly", width=48)
        self.process_combo.pack(side="left", padx=(0, 8))
        self.process_combo.bind("<<ComboboxSelected>>", self._on_process_selected)

        ttk.Button(process_row, text="Refresh Processes",
                   command=self.refresh_processes).pack(side="left")

        ttk.Label(
            process_row,
            text="Tip: open Photoshop first, then Refresh Processes and select Photoshop.exe",
        ).pack(side="left", padx=12)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self.live_tab = ttk.Frame(notebook)
        self.tests_tab = ttk.Frame(notebook)
        self.bus_tab = ttk.Frame(notebook)
        notebook.add(self.live_tab, text="Live Monitor")
        notebook.add(self.tests_tab, text="PDC Tests")
        notebook.add(self.bus_tab, text="Computer System Bus")

        self._build_live_tab()
        self._build_tests_tab()
        self._build_system_bus_tab()

    def _build_live_tab(self):
        self.live_tab.columnconfigure(0, weight=1)
        self.live_tab.columnconfigure(1, weight=1)
        self.live_tab.rowconfigure(0, weight=1)
        self.live_tab.rowconfigure(1, weight=1)

        # CPU + RAM live history
        frame1 = ttk.LabelFrame(self.live_tab, text="Overall CPU & RAM — Live", padding=6)
        frame1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.fig_system = Figure(figsize=(6, 3.2), dpi=100)
        self.ax_system = self.fig_system.add_subplot(111)
        self.line_cpu, = self.ax_system.plot([], [], label="CPU %")
        self.line_ram, = self.ax_system.plot([], [], label="RAM %")
        self.ax_system.set_ylim(0, 100)
        self.ax_system.set_xlabel("Last 60 seconds")
        self.ax_system.set_ylabel("Usage (%)")
        self.ax_system.legend(loc="upper left")
        self.ax_system.grid(True, alpha=0.25)
        self.canvas_system = FigureCanvasTkAgg(self.fig_system, master=frame1)
        self.canvas_system.get_tk_widget().pack(fill="both", expand=True)

        # Per-core bars
        frame2 = ttk.LabelFrame(self.live_tab, text="CPU Core Performance — Live", padding=6)
        frame2.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.fig_cores = Figure(figsize=(6, 3.2), dpi=100)
        self.ax_cores = self.fig_cores.add_subplot(111)
        core_count = psutil.cpu_count(logical=True) or 1
        initial = [0] * core_count
        self.core_bars = self.ax_cores.bar(range(1, core_count + 1), initial)
        self.ax_cores.set_ylim(0, 100)
        self.ax_cores.set_xlabel("Logical CPU / Core")
        self.ax_cores.set_ylabel("Usage (%)")
        self.ax_cores.grid(True, axis="y", alpha=0.25)
        self.canvas_cores = FigureCanvasTkAgg(self.fig_cores, master=frame2)
        self.canvas_cores.get_tk_widget().pack(fill="both", expand=True)

        # Process usage
        frame3 = ttk.LabelFrame(self.live_tab, text="Selected Application — Live", padding=6)
        frame3.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        self.fig_process = Figure(figsize=(12, 3.2), dpi=100)
        self.ax_process = self.fig_process.add_subplot(111)
        self.line_proc_cpu, = self.ax_process.plot([], [], label="Process CPU %")
        self.line_proc_ram, = self.ax_process.plot([], [], label="Process RAM %")
        self.ax_process.set_xlabel("Last 60 seconds")
        self.ax_process.set_ylabel("Usage (%)")
        self.ax_process.set_ylim(0, 100)
        self.ax_process.legend(loc="upper left")
        self.ax_process.grid(True, alpha=0.25)
        self.canvas_process = FigureCanvasTkAgg(self.fig_process, master=frame3)
        self.canvas_process.get_tk_widget().pack(fill="both", expand=True)

    def _build_tests_tab(self):
        controls = ttk.Frame(self.tests_tab, padding=10)
        controls.pack(fill="x")

        ttk.Label(controls, text="CPU workload upper limit:").pack(side="left")
        self.workload_var = tk.StringVar(value=str(DEFAULT_WORKLOAD))
        ttk.Entry(controls, textvariable=self.workload_var, width=12).pack(side="left", padx=(6, 14))

        self.benchmark_button = ttk.Button(
            controls,
            text="Run Scalability Test",
            command=self.start_scalability_test,
        )
        self.benchmark_button.pack(side="left", padx=4)

        self.communication_button = ttk.Button(
            controls,
            text="Run Communication Test",
            command=self.start_communication_test,
        )
        self.communication_button.pack(side="left", padx=4)

        self.fault_button = ttk.Button(
            controls,
            text="Run Fault-Tolerance Test",
            command=self.start_fault_test,
        )
        self.fault_button.pack(side="left", padx=4)

        ttk.Label(
            controls,
            text="Run these tests while watching the Live Monitor tab to see CPU graphs move in real time.",
        ).pack(side="left", padx=12)

        middle = ttk.Frame(self.tests_tab, padding=(10, 0, 10, 6))
        middle.pack(fill="x", expand=False)
        middle.columnconfigure(0, weight=1)
        middle.columnconfigure(1, weight=1)
        middle.rowconfigure(0, weight=1)
        middle.rowconfigure(1, weight=1)

        speed_frame = ttk.LabelFrame(middle, text="Scalability / Speedup", padding=6)
        speed_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.fig_speedup = Figure(figsize=(5.5, 2.0), dpi=100)
        self.ax_speedup = self.fig_speedup.add_subplot(111)
        self.speed_line, = self.ax_speedup.plot([], [], marker="o", label="Measured Speedup")
        self.ideal_line, = self.ax_speedup.plot([], [], linestyle="--", label="Ideal Speedup")
        self.ax_speedup.set_xlabel("Workers")
        self.ax_speedup.set_ylabel("Speedup (x)")
        self.ax_speedup.grid(True, alpha=0.25)
        self.ax_speedup.legend()
        self.canvas_speedup = FigureCanvasTkAgg(self.fig_speedup, master=speed_frame)
        self.canvas_speedup.get_tk_widget().pack(fill="both", expand=True)

        efficiency_frame = ttk.LabelFrame(middle, text="Parallel Efficiency", padding=6)
        efficiency_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.fig_eff = Figure(figsize=(5.5, 2.0), dpi=100)
        self.ax_eff = self.fig_eff.add_subplot(111)
        self.eff_line, = self.ax_eff.plot([], [], marker="o", label="Efficiency %")
        self.ax_eff.set_ylim(0, 110)
        self.ax_eff.set_xlabel("Workers")
        self.ax_eff.set_ylabel("Efficiency (%)")
        self.ax_eff.grid(True, alpha=0.25)
        self.ax_eff.legend()
        self.canvas_eff = FigureCanvasTkAgg(self.fig_eff, master=efficiency_frame)
        self.canvas_eff.get_tk_widget().pack(fill="both", expand=True)

        communication_frame = ttk.LabelFrame(
            middle, text="Inter-Process Communication Latency", padding=6
        )
        communication_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.fig_communication = Figure(figsize=(5.5, 2.0), dpi=100)
        self.ax_communication = self.fig_communication.add_subplot(111)
        self.communication_line, = self.ax_communication.plot(
            [], [], marker="o", label="Average latency"
        )
        self.ax_communication.set_xlabel("Message size (KB)")
        self.ax_communication.set_ylabel("Round-trip latency (ms)")
        self.ax_communication.grid(True, alpha=0.25)
        self.ax_communication.legend()
        self.canvas_communication = FigureCanvasTkAgg(
            self.fig_communication, master=communication_frame
        )
        self.canvas_communication.get_tk_widget().pack(fill="both", expand=True)

        fault_frame = ttk.LabelFrame(
            middle, text="Fault-Tolerance Summary", padding=12
        )
        fault_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        fault_frame.columnconfigure(1, weight=1)

        self.fault_total_value = tk.StringVar(value="Not run")
        self.fault_initial_failed_value = tk.StringVar(value="Not run")
        self.fault_recovered_value = tk.StringVar(value="Not run")
        self.fault_unrecovered_value = tk.StringVar(value="Not run")
        self.fault_reliability_value = tk.StringVar(value="Not run")
        self.fault_recovery_rate_value = tk.StringVar(value="Not run")

        fault_rows = [
            ("Total tasks", self.fault_total_value),
            ("Initial failures", self.fault_initial_failed_value),
            ("Recovered", self.fault_recovered_value),
            ("Unrecovered", self.fault_unrecovered_value),
            ("Reliability", self.fault_reliability_value),
            ("Recovery rate", self.fault_recovery_rate_value),
        ]
        for row, (label, variable) in enumerate(fault_rows):
            ttk.Label(fault_frame, text=f"{label}:").grid(
                row=row, column=0, sticky="w", padx=(0, 16), pady=4
            )
            ttk.Label(fault_frame, textvariable=variable,
                      style="CardValue.TLabel").grid(
                row=row, column=1, sticky="w", pady=4
            )

        log_frame = ttk.LabelFrame(self.tests_tab, text="Test Results / Event Log", padding=6)
        log_frame.pack(fill="both", padx=15, pady=(0, 10))

        self.log_text = tk.Text(log_frame, height=7, wrap="word")
        self.log_text.pack(fill="both", expand=True)
        self._log("Dashboard ready. Live monitoring is running.")

    def _build_system_bus_tab(self):
        self.bus_tab.columnconfigure(0, weight=3)
        self.bus_tab.columnconfigure(1, weight=1)
        self.bus_tab.rowconfigure(0, weight=1)

        diagram_frame = ttk.LabelFrame(
            self.bus_tab, text="Live Computer System Bus", padding=6
        )
        diagram_frame.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)

        self.fig_bus = Figure(figsize=(8, 5), dpi=100)
        self.ax_bus = self.fig_bus.add_subplot(111)
        self.ax_bus.set_xlim(0, 10)
        self.ax_bus.set_ylim(0, 10)
        self.ax_bus.axis("off")

        self.ax_bus.text(1.0, 8.7, "CPU / Cores", ha="center", va="center",
                         fontsize=13, fontweight="bold")
        self.ax_bus.text(5.0, 8.7, "SYSTEM BUS", ha="center", va="center",
                         fontsize=13, fontweight="bold", color="#1d5d8f")
        self.ax_bus.text(8.6, 8.7, "RAM", ha="center", va="center",
                         fontsize=13, fontweight="bold")
        self.ax_bus.text(8.6, 3.0, "I/O Devices", ha="center", va="center",
                         fontsize=12, fontweight="bold")

        self.ax_bus.add_patch(Rectangle(
            (0.2, 1.0), 1.6, 7.0, facecolor="#e8f1f8", edgecolor="#2878b5", linewidth=2
        ))
        self.ax_bus.add_patch(Rectangle(
            (3.0, 4.0), 4.0, 1.5, facecolor="#dcecf7", edgecolor="#2878b5", linewidth=2
        ))
        self.ax_bus.add_patch(Rectangle(
            (7.6, 5.5), 1.8, 2.5, facecolor="#e9f5e9", edgecolor="#2a9d8f", linewidth=2
        ))
        self.ax_bus.add_patch(Rectangle(
            (7.6, 1.0), 1.8, 1.8, facecolor="#fff1d6", edgecolor="#d98b2b", linewidth=2
        ))

        self.cpu_core_labels = []
        logical_count = psutil.cpu_count(logical=True) or 1
        shown_cores = min(logical_count, 8)
        for index in range(shown_cores):
            y_pos = 7.5 - index * (5.8 / max(1, shown_cores - 1))
            self.ax_bus.text(1.0, y_pos, f"Core {index + 1}", ha="center", va="center", fontsize=9)
            self.cpu_core_labels.append(self.ax_bus.text(1.0, y_pos - 0.27, "0%",
                                                         ha="center", va="center", fontsize=8))

        self.ax_bus.text(5.0, 4.72, "Data Bus   |   Address Bus   |   Control Bus",
                         ha="center", va="center", fontsize=9)
        self.ax_bus.text(8.5, 6.45, f"{psutil.virtual_memory().total / (1024 ** 3):.1f} GB total",
                         ha="center", va="center", fontsize=10)
        self.ax_bus.text(8.5, 1.9, "Storage / Network", ha="center", va="center", fontsize=9)

        for y_pos in (7.0, 5.9, 4.7, 3.5, 2.3):
            self.ax_bus.plot([1.8, 3.0], [y_pos, 4.75], color="#9aa4b2", linewidth=1.5)
        self.ax_bus.plot([7.0, 7.6], [4.75, 6.75], color="#9aa4b2", linewidth=2)
        self.ax_bus.plot([7.0, 7.6], [4.25, 2.0], color="#9aa4b2", linewidth=2)

        self.bus_forward_marker, = self.ax_bus.plot([], [], "o", color="#d94f4f", markersize=9)
        self.bus_return_marker, = self.ax_bus.plot([], [], "o", color="#2a9d8f", markersize=9)
        self.canvas_bus = FigureCanvasTkAgg(self.fig_bus, master=diagram_frame)
        self.canvas_bus.get_tk_widget().pack(fill="both", expand=True)

        side = ttk.Frame(self.bus_tab, padding=(4, 8, 8, 8))
        side.grid(row=0, column=1, sticky="nsew")
        ttk.Label(side, text="System Bus Status", style="Section.TLabel").pack(anchor="w")
        self.system_bus_status_var = tk.StringVar(value="Monitoring actual resources")
        ttk.Label(side, textvariable=self.system_bus_status_var, wraplength=230).pack(anchor="w", pady=(4, 12))

        self.system_cpu_var = tk.StringVar(value="CPU activity: 0.0%")
        self.system_ram_var = tk.StringVar(value="RAM activity: 0.0%")
        self.system_core_var = tk.StringVar(value=f"Logical cores: {logical_count}")
        self.system_memory_var = tk.StringVar(value=f"RAM: {psutil.virtual_memory().total / (1024 ** 3):.1f} GB")
        for variable in (self.system_cpu_var, self.system_ram_var,
                         self.system_core_var, self.system_memory_var):
            ttk.Label(side, textvariable=variable).pack(anchor="w", pady=4)

        ttk.Label(side, text="Packet animation speed").pack(anchor="w", pady=(16, 2))
        ttk.Scale(side, from_=0.25, to=2.5, variable=self.system_bus_speed,
                  orient="horizontal").pack(fill="x")
        self.system_bus_button = ttk.Button(
            side, text="Pause Animation", command=self._toggle_system_bus
        )
        self.system_bus_button.pack(anchor="w", pady=14)
        ttk.Label(
            side,
            text="Packets show live resource activity moving between CPU, RAM, and I/O. "
                 "The physical motherboard bus layout is not exposed by standard Windows APIs.",
            wraplength=230,
        ).pack(anchor="w")

    def _update_system_bus(self):
        if not self.monitoring:
            return

        cpu_usage = self.current_cpu_usage
        ram_usage = self.current_ram_usage
        if self.system_bus_running:
            activity = max(0.2, (cpu_usage + ram_usage) / 100)
            self.system_bus_phase = (self.system_bus_phase +
                                     0.025 * self.system_bus_speed.get() * activity) % 1.0

        forward_x = 1.8 + 5.8 * self.system_bus_phase
        forward_y = 4.25 + 0.5 * self.system_bus_phase
        return_x = 7.6 - 5.8 * self.system_bus_phase
        return_y = 4.75 - 0.5 * self.system_bus_phase
        self.bus_forward_marker.set_data([forward_x], [forward_y])
        self.bus_return_marker.set_data([return_x], [return_y])

        self.system_cpu_var.set(f"CPU activity: {cpu_usage:.1f}%")
        self.system_ram_var.set(f"RAM activity: {ram_usage:.1f}%")
        self.system_bus_status_var.set(
            "System bus animation running" if self.system_bus_running else "System bus animation paused"
        )
        self.canvas_bus.draw_idle()
        self.after(200, self._update_system_bus)

    def _toggle_system_bus(self):
        self.system_bus_running = not self.system_bus_running
        self.system_bus_button.configure(
            text="Pause Animation" if self.system_bus_running else "Resume Animation"
        )

    def _prime_cpu_measurement(self):
        psutil.cpu_percent(interval=None, percpu=True)
        psutil.cpu_percent(interval=None)

    def _log(self, message):
        stamp = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{stamp}] {message}\n")
        self.log_text.see("end")

    def refresh_processes(self):
        current = self.process_combo.get()
        items = []
        mapping = {}

        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = proc.info.get("name") or "Unknown"
                pid = proc.info["pid"]
                display = f"{name}  (PID {pid})"
                items.append(display)
                mapping[display] = pid
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        items.sort(key=str.lower)
        self.process_map = mapping
        self.process_combo["values"] = items

        selected = None

        if current in mapping:
            selected = current
        else:
            photoshop_candidates = [
                item for item in items
                if "photoshop" in item.lower()
            ]
            if photoshop_candidates:
                selected = photoshop_candidates[0]

        if selected:
            self.process_combo.set(selected)
            self._select_process_by_display(selected)
        elif items:
            self.process_combo.set(items[0])
            self._select_process_by_display(items[0])

    def _on_process_selected(self, _event=None):
        self._select_process_by_display(self.process_combo.get())

    def _select_process_by_display(self, display):
        pid = self.process_map.get(display)
        if not pid:
            self.selected_process = None
            return

        try:
            proc = psutil.Process(pid)
            proc.cpu_percent(interval=None)
            self.selected_process = proc
            self.selected_process_display = display
            self.process_cpu_history.clear()
            self.process_ram_history.clear()
            self._log(f"Monitoring process: {display}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self.selected_process = None

    def _update_live_data(self):
        if not self.monitoring:
            return

        try:
            overall_cpu = psutil.cpu_percent(interval=None)
            per_core = psutil.cpu_percent(interval=None, percpu=True)
            ram = psutil.virtual_memory().percent
            self.current_cpu_usage = overall_cpu
            self.current_ram_usage = ram

            for label, value in zip(self.cpu_core_labels, per_core):
                label.set_text(f"{value:.0f}%")

            self.time_counter += 1
            self.time_history.append(self.time_counter)
            self.cpu_history.append(overall_cpu)
            self.ram_history.append(ram)

            proc_cpu = 0.0
            proc_ram = 0.0

            if self.selected_process is not None:
                try:
                    proc_cpu = self.selected_process.cpu_percent(interval=None)
                    proc_ram = self.selected_process.memory_percent()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    self.selected_process = None
                    self.status_var.set("Selected process closed or access denied")
                    self.selected_process_failures += 1
                    self._log(
                        f"Selected process unavailable: {self.selected_process_display} "
                        f"(failure #{self.selected_process_failures})"
                    )

            self.process_cpu_history.append(proc_cpu)
            self.process_ram_history.append(proc_ram)

            self.cpu_value.set(f"{overall_cpu:.1f}%")
            self.ram_value.set(f"{ram:.1f}%")
            self.process_cpu_value.set(f"{proc_cpu:.1f}%")
            self.process_ram_value.set(f"{proc_ram:.2f}%")

            # Overall CPU/RAM chart
            x = list(range(-len(self.cpu_history) + 1, 1))
            self.line_cpu.set_data(x, list(self.cpu_history))
            self.line_ram.set_data(x, list(self.ram_history))
            self.ax_system.set_xlim(min(-59, x[0] if x else -59), 0)
            self.canvas_system.draw_idle()

            # Per-core bars
            for bar, value in zip(self.core_bars, per_core):
                bar.set_height(value)
            self.canvas_cores.draw_idle()

            # Selected process chart
            px = list(range(-len(self.process_cpu_history) + 1, 1))
            self.line_proc_cpu.set_data(px, list(self.process_cpu_history))
            self.line_proc_ram.set_data(px, list(self.process_ram_history))

            max_proc_cpu = max(list(self.process_cpu_history) + [100])
            self.ax_process.set_ylim(0, max(100, max_proc_cpu * 1.15))
            self.ax_process.set_xlim(min(-59, px[0] if px else -59), 0)
            self.canvas_process.draw_idle()

        except Exception as exc:
            self.status_var.set(f"Monitor error: {exc}")

        self.after(UPDATE_MS, self._update_live_data)

    def _worker_counts(self):
        logical = os.cpu_count() or 2
        maximum = min(logical, 8)

        counts = [1]
        value = 2
        while value <= maximum:
            counts.append(value)
            value *= 2

        if maximum not in counts:
            counts.append(maximum)

        return sorted(set(counts))

    def start_scalability_test(self):
        if self.test_running:
            messagebox.showinfo("Test Running", "Another PDC test is already running.")
            return

        try:
            workload = int(self.workload_var.get().replace(",", "").strip())
            if workload < 50_000:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid Workload",
                "Enter an integer workload of at least 50000.",
            )
            return

        self.test_running = True
        self._set_test_buttons(False)
        self.status_var.set("Scalability test running — watch the live graphs")
        self._log("Starting scalability test...")

        self.benchmark_workers = []
        self.benchmark_times = []
        self.benchmark_speedups = []
        self.benchmark_efficiencies = []
        self.communication_sizes = []
        self.communication_latencies = []
        self._refresh_benchmark_charts()
        self._refresh_communication_chart()

        threading.Thread(
            target=self._scalability_thread,
            args=(workload,),
            daemon=True,
        ).start()

    def _scalability_thread(self, workload):
        try:
            baseline = None

            for workers in self._worker_counts():
                self.event_queue.put(("log", f"Running CPU benchmark with {workers} worker(s)..."))
                elapsed, prime_count = run_prime_benchmark(workers, workload)

                if baseline is None:
                    baseline = elapsed

                speedup = baseline / elapsed if elapsed > 0 else 0
                efficiency = (speedup / workers) * 100 if workers else 0

                self.event_queue.put((
                    "benchmark_point",
                    {
                        "workers": workers,
                        "time": elapsed,
                        "speedup": speedup,
                        "efficiency": efficiency,
                        "primes": prime_count,
                    },
                ))

            self.event_queue.put(("done", "Scalability test completed."))
        except Exception as exc:
            self.event_queue.put(("error", f"Scalability test failed: {exc}"))

    def start_communication_test(self):
        if self.test_running:
            messagebox.showinfo("Test Running", "Another PDC test is already running.")
            return

        self.test_running = True
        self._set_test_buttons(False)
        self.status_var.set("Communication test running")
        self._log("Starting inter-process communication test...")

        threading.Thread(
            target=self._communication_thread,
            daemon=True,
        ).start()

    def _communication_thread(self):
        try:
            results = measure_ipc_latency()
            self.event_queue.put(("communication", results))
            self.event_queue.put(("done", "Communication test completed."))
        except Exception as exc:
            self.event_queue.put(("error", f"Communication test failed: {exc}"))

    def start_fault_test(self):
        if self.test_running:
            messagebox.showinfo("Test Running", "Another PDC test is already running.")
            return

        self.test_running = True
        self._set_test_buttons(False)
        self.status_var.set("Fault-tolerance test running")
        self._log("Starting simulated reliability/fault-tolerance test...")

        threading.Thread(
            target=self._fault_thread,
            daemon=True,
        ).start()

    def _fault_thread(self):
        try:
            results = run_fault_tolerance_test()
            self.event_queue.put(("fault", results))
            self.event_queue.put(("done", "Fault-tolerance test completed."))
        except Exception as exc:
            self.event_queue.put(("error", f"Fault-tolerance test failed: {exc}"))

    def _poll_event_queue(self):
        try:
            while True:
                event, payload = self.event_queue.get_nowait()

                if event == "log":
                    self._log(payload)

                elif event == "benchmark_point":
                    self.benchmark_workers.append(payload["workers"])
                    self.benchmark_times.append(payload["time"])
                    self.benchmark_speedups.append(payload["speedup"])
                    self.benchmark_efficiencies.append(payload["efficiency"])

                    self._log(
                        f'Workers={payload["workers"]} | '
                        f'Time={payload["time"]:.3f}s | '
                        f'Speedup={payload["speedup"]:.2f}x | '
                        f'Efficiency={payload["efficiency"]:.1f}% | '
                        f'Prime count={payload["primes"]}'
                    )
                    self._refresh_benchmark_charts()

                elif event == "communication":
                    self.communication_sizes = [size for size, _ in payload]
                    self.communication_latencies = [latency for _, latency in payload]
                    self._refresh_communication_chart()
                    self._log("Communication results:")
                    for size_kb, latency_ms in payload:
                        label = "1 MB" if size_kb == 1024 else f"{size_kb} KB"
                        self._log(f"  {label}: {latency_ms:.3f} ms average round-trip latency")

                elif event == "fault":
                    self._update_fault_summary(payload)
                    self._log(
                        "Fault tolerance: "
                        f'Total={payload["total"]}, '
                        f'Initial Success={payload["initial_success"]}, '
                        f'Initial Failed={payload["initial_failed"]}, '
                        f'Recovered={payload["recovered"]}, '
                        f'Unrecovered={payload["unrecovered"]}'
                    )
                    self._log(
                        f'Reliability={payload["reliability"]:.1f}% | '
                        f'Recovery Rate={payload["recovery_rate"]:.1f}%'
                    )

                elif event == "done":
                    self.test_running = False
                    self._set_test_buttons(True)
                    self.status_var.set(payload)
                    self._log(payload)

                elif event == "error":
                    self.test_running = False
                    self._set_test_buttons(True)
                    self.status_var.set(payload)
                    self._log(payload)
                    messagebox.showerror("Test Error", payload)

        except queue.Empty:
            pass

        self.after(150, self._poll_event_queue)

    def _refresh_benchmark_charts(self):
        workers = self.benchmark_workers
        speedups = self.benchmark_speedups
        efficiencies = self.benchmark_efficiencies

        self.speed_line.set_data(workers, speedups)
        self.ideal_line.set_data(workers, workers)

        if workers:
            self.ax_speedup.set_xlim(0.5, max(workers) + 0.5)
            max_y = max(max(speedups + [1]), max(workers))
            self.ax_speedup.set_ylim(0, max_y * 1.15)
        else:
            self.ax_speedup.set_xlim(0, 2)
            self.ax_speedup.set_ylim(0, 2)

        self.eff_line.set_data(workers, efficiencies)

        if workers:
            self.ax_eff.set_xlim(0.5, max(workers) + 0.5)
        else:
            self.ax_eff.set_xlim(0, 2)

        self.canvas_speedup.draw_idle()
        self.canvas_eff.draw_idle()

    def _refresh_communication_chart(self):
        self.communication_line.set_data(
            self.communication_sizes, self.communication_latencies
        )

        if self.communication_sizes:
            self.ax_communication.set_xlim(
                0, max(self.communication_sizes) * 1.1
            )
            maximum_latency = max(self.communication_latencies + [1])
            self.ax_communication.set_ylim(0, maximum_latency * 1.2)
        else:
            self.ax_communication.set_xlim(0, 1100)
            self.ax_communication.set_ylim(0, 1)

        self.canvas_communication.draw_idle()

    def _update_fault_summary(self, results):
        self.fault_total_value.set(str(results["total"]))
        self.fault_initial_failed_value.set(str(results["initial_failed"]))
        self.fault_recovered_value.set(str(results["recovered"]))
        self.fault_unrecovered_value.set(str(results["unrecovered"]))
        self.fault_reliability_value.set(f'{results["reliability"]:.1f}%')
        self.fault_recovery_rate_value.set(f'{results["recovery_rate"]:.1f}%')

    def _set_test_buttons(self, enabled):
        state = "normal" if enabled else "disabled"
        self.benchmark_button.config(state=state)
        self.communication_button.config(state=state)
        self.fault_button.config(state=state)

    def destroy(self):
        self.monitoring = False
        super().destroy()


def main():
    mp.freeze_support()
    app = PerformanceVisualizer()
    app.mainloop()


if __name__ == "__main__":
    main()
