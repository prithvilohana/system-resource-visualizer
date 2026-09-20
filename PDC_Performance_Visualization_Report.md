# Parallel and Distributed Computing
## Laptop Performance Visualization Report

**Group Members:**
1. Member 1: ____________________
2. Member 2: ____________________
3. Member 3: ____________________

**Course:** Parallel and Distributed Computing  
**Semester:** 6th  
**Instructor:** ____________________  
**Department/University:** ____________________  
**Submission Date:** ____________________

---

## Abstract

This report presents a graphical analysis of laptop and application performance using a live performance visualizer. The visualizer was used to observe CPU core utilization, overall CPU usage, RAM usage, selected application performance, scalability, inter-process communication latency, parallel efficiency, reliability, and fault tolerance. Each group member collected readings from their own laptop or selected application. The general procedure and analysis method are common to the group, while the measured readings and screenshots are reported separately for each member.

## 1. Introduction

Parallel and Distributed Computing studies how computational work can be divided among multiple processing units and how processes communicate and recover from failures. A laptop provides a practical environment for observing these concepts through CPU, memory, process, and communication measurements.

In this assignment, a live performance visualizer was used to graphically observe laptop performance. The purpose of the experiment was to collect and visualize readings, not to develop a new visualization framework. The same general experiment was performed by all three group members, while hardware conditions, selected applications, and measured values could differ.

## 2. Objectives

- To visualize overall CPU and RAM utilization.
- To observe the performance of individual logical CPU cores.
- To monitor the CPU and RAM usage of a selected application.
- To study scalability by changing the number of parallel workers.
- To calculate speedup and parallel efficiency.
- To measure communication latency between processes.
- To observe reliability and fault-tolerance behavior through task recovery.
- To visualize logical data flow between the CPU, system bus, RAM, and I/O devices.
- To compare performance readings collected by three group members.

## 3. Experimental Setup

The visualizer was executed on the laptops of all three group members. Each member selected an application and recorded the displayed readings separately. The common tools and procedure are described once in this report; hardware details and measured values are entered member-wise.

### 3.1 Member 1 Setup

**Member name:** ____________________  
**Selected application:** ____________________  
**Application activity used for testing:** ____________________

| Item | Member 1 value |
|---|---|
| Laptop/device | ____________________ |
| Operating system | ____________________ |
| Processor | ____________________ |
| Physical cores | ____________________ |
| Logical CPUs | ____________________ |
| Total RAM | ____________________ |
| Workload used | 650000 |

**How to fill this table:** copy the physical cores, logical CPUs, and total RAM from the dashboard. Get the processor and operating-system name from Windows Settings or Task Manager. Write the application name and the operation performed during monitoring.

### 3.2 Member 1 Screenshots

Add the screenshots after collecting the readings. Use clear captions and refer to each figure in the results discussion.

**Figure 1. Member 1 dashboard showing system resources and selected application.**

`[Insert Member 1 Live Monitor screenshot here]`

**Figure 2. Member 1 selected application CPU and RAM graph during the test.**

`[Insert Member 1 selected-application screenshot here]`

**Figure 3. Member 1 CPU core performance graph during the test.**

`[Insert Member 1 core-performance screenshot here]`

### 3.3 Common Tools Used

- Python
- Tkinter for the desktop interface
- Matplotlib for graphical plots
- psutil for CPU, RAM, and process readings
- multiprocessing and ProcessPoolExecutor for parallel experiments

## 4. Experimental Procedure

1. The visualizer was started on each laptop.
2. The selected application was opened and selected from the process list.
3. CPU, RAM, and logical-core activity were observed during normal and heavy application activity.
4. The scalability test was executed with different worker counts.
5. The communication test was executed using different message sizes.
6. The fault-tolerance test was executed and its recovery results were recorded.
7. Screenshots of the graphs and result logs were captured.
8. The Computer System Bus tab was observed during normal and heavy CPU activity.
9. Each member entered their own readings in the result tables below.

## 5. Concepts and Calculations

### 5.1 Core Performance and Resources

The live monitor displays overall CPU usage, total RAM usage, and utilization of each logical CPU. The selected application graph displays the CPU and RAM usage of the selected process.

### 5.2 Scalability and Speedup

The scalability test performs a CPU-bound prime-number calculation with different numbers of worker processes.

$$
Speedup = \frac{T_1}{T_p}
$$

Here, $T_1$ is the execution time with one worker and $T_p$ is the execution time with multiple workers.

### 5.3 Parallel Efficiency

$$
Parallel\ Efficiency = \frac{Speedup}{Number\ of\ Workers} \times 100
$$

Efficiency may be below 100% because of process creation, scheduling, communication overhead, and other background tasks.

### 5.4 Communication

The communication test sends data from one process to another and receives it back. The complete send-and-receive duration is called round-trip latency.

$$
Average\ Latency = \frac{Total\ Communication\ Time}{Number\ of\ Rounds}
$$

### 5.5 Reliability and Fault Tolerance

The fault-tolerance experiment uses simulated task failures. Failed tasks are detected and retried.

$$
Reliability = \frac{Successfully\ Completed\ Tasks}{Total\ Tasks} \times 100
$$

$$
Recovery\ Rate = \frac{Recovered\ Tasks}{Failed\ Tasks} \times 100
$$

### 5.6 Computer System Bus Visualization

The Computer System Bus tab shows the logical relationship between the detected
CPU cores, system bus, RAM, and I/O devices. Animated packets represent live
resource activity. Their movement rate is influenced by the current CPU and RAM
readings, so the diagram responds to actual workload on the laptop. The exact
physical motherboard wiring is hardware-specific and is not exposed by standard
Windows Python APIs; therefore, the visualization presents the logical data,
address, and control-bus flow.

## 6. Results: Member 1

**Name:** ____________________  
**Selected application:** ____________________

### 6.1 Resource and Core Readings

| Activity | Overall CPU | RAM | Selected app CPU | Selected app RAM | Highest core usage |
|---|---:|---:|---:|---:|---:|
| Idle | ____% | ____% | ____% | ____% | ____% |
| Normal application use | ____% | ____% | ____% | ____% | ____% |
| Heavy operation | ____% | ____% | ____% | ____% | ____% |

### 6.2 Scalability Readings

| Workers | Time (s) | Speedup | Efficiency |
|---:|---:|---:|---:|
| 1 | ____ | ____x | ____% |
| 2 | ____ | ____x | ____% |
| 4 | ____ | ____x | ____% |
| 8 | ____ | ____x | ____% |

### 6.3 Communication Readings

| Message size | Latency (ms) |
|---:|---:|
| 1 KB | ____ |
| 10 KB | ____ |
| 100 KB | ____ |
| 1 MB | ____ |

### 6.4 Fault-Tolerance Readings

| Total tasks | Initial failed | Recovered | Unrecovered | Reliability | Recovery rate |
|---:|---:|---:|---:|---:|---:|
| 20 | ____ | ____ | ____ | ____% | ____% |

**Member 1 screenshots:**
- Figure 1. Live Monitor: ____________________
- Figure 2. Scalability and efficiency: ____________________
- Figure 3. Communication and fault-tolerance results: ____________________

## 7. Results: Member 2

**Name:** ____________________  
**Selected application:** ____________________

### 7.1 Resource and Core Readings

| Activity | Overall CPU | RAM | Selected app CPU | Selected app RAM | Highest core usage |
|---|---:|---:|---:|---:|---:|
| Idle | ____% | ____% | ____% | ____% | ____% |
| Normal application use | ____% | ____% | ____% | ____% | ____% |
| Heavy operation | ____% | ____% | ____% | ____% | ____% |

### 7.2 Scalability Readings

| Workers | Time (s) | Speedup | Efficiency |
|---:|---:|---:|---:|
| 1 | ____ | ____x | ____% |
| 2 | ____ | ____x | ____% |
| 4 | ____ | ____x | ____% |
| 8 | ____ | ____x | ____% |

### 7.3 Communication Readings

| Message size | Latency (ms) |
|---:|---:|
| 1 KB | ____ |
| 10 KB | ____ |
| 100 KB | ____ |
| 1 MB | ____ |

### 7.4 Fault-Tolerance Readings

| Total tasks | Initial failed | Recovered | Unrecovered | Reliability | Recovery rate |
|---:|---:|---:|---:|---:|---:|
| 20 | ____ | ____ | ____ | ____% | ____% |

**Member 2 screenshots:**
- Figure 4. Live Monitor: ____________________
- Figure 5. Scalability and efficiency: ____________________
- Figure 6. Communication and fault-tolerance results: ____________________

## 8. Results: Member 3

**Name:** ____________________  
**Selected application:** ____________________

### 8.1 Resource and Core Readings

| Activity | Overall CPU | RAM | Selected app CPU | Selected app RAM | Highest core usage |
|---|---:|---:|---:|---:|---:|
| Idle | ____% | ____% | ____% | ____% | ____% |
| Normal application use | ____% | ____% | ____% | ____% | ____% |
| Heavy operation | ____% | ____% | ____% | ____% | ____% |

### 8.2 Scalability Readings

| Workers | Time (s) | Speedup | Efficiency |
|---:|---:|---:|---:|
| 1 | ____ | ____x | ____% |
| 2 | ____ | ____x | ____% |
| 4 | ____ | ____x | ____% |
| 8 | ____ | ____x | ____% |

### 8.3 Communication Readings

| Message size | Latency (ms) |
|---:|---:|
| 1 KB | ____ |
| 10 KB | ____ |
| 100 KB | ____ |
| 1 MB | ____ |

### 8.4 Fault-Tolerance Readings

| Total tasks | Initial failed | Recovered | Unrecovered | Reliability | Recovery rate |
|---:|---:|---:|---:|---:|---:|
| 20 | ____ | ____ | ____ | ____% | ____% |

**Member 3 screenshots:**
- Figure 7. Live Monitor: ____________________
- Figure 8. Scalability and efficiency: ____________________
- Figure 9. Communication and fault-tolerance results: ____________________

## 9. Comparative Analysis

### 9.1 Resource Comparison

| Measurement | Member 1 | Member 2 | Member 3 |
|---|---:|---:|---:|
| Idle CPU | ____% | ____% | ____% |
| Heavy-operation CPU | ____% | ____% | ____% |
| Heavy-operation RAM | ____% | ____% | ____% |
| Highest core usage | ____% | ____% | ____% |

### 9.2 Best Parallel Result

| Member | Fastest time | Highest speedup | Highest efficiency |
|---|---:|---:|---:|
| Member 1 | ____ s | ____x | ____% |
| Member 2 | ____ s | ____x | ____% |
| Member 3 | ____ s | ____x | ____% |

### 9.3 Discussion

The readings varied because the laptops had different processors, numbers of logical CPUs, RAM capacities, operating-system activity, and background processes. In general, increasing worker count can reduce execution time up to the point where process overhead and CPU limitations reduce the benefit. Communication latency generally increases with message size. The fault-tolerance experiment shows whether failed tasks can be recovered through retry.

Replace this paragraph with observations based on the actual three-member readings.

## 10. Limitations

- The fault-tolerance failures are simulated task failures.
- The selected external application is monitored but is not automatically terminated or restarted.
- The scalability benchmark uses a controlled prime-number workload; it does not parallelize the selected external application.
- Results can change because of laptop hardware, thermal conditions, Windows scheduling, and background processes.
- The experiment focuses on CPU, RAM, process, communication, and task-recovery readings. GPU, disk, and network utilization are not included.

## 11. Conclusion

The live performance visualizer was used to collect and graphically analyze laptop performance readings for three group members. The experiment covered core performance, resource usage, scalability, speedup, parallel efficiency, inter-process communication, reliability, and fault tolerance. The combined results show how hardware characteristics and workload conditions affect parallel performance. The visualizer provided a common measurement method, while separate member readings allowed comparison between different laptops and applications.

## References

1. Python Documentation: https://docs.python.org/3/
2. psutil Documentation: https://psutil.readthedocs.io/
3. Matplotlib Documentation: https://matplotlib.org/stable/
4. Course lectures and notes on Parallel and Distributed Computing.
