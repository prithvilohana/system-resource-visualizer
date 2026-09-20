PDC LIVE LAPTOP PERFORMANCE VISUALIZER
=======================================

WHAT THIS VERSION DOES
----------------------
This is a live GUI dashboard, not a static-image generator.

It continuously shows:
- Overall CPU usage
- RAM usage
- Per-core / logical CPU utilization
- CPU usage of a selected application such as Photoshop
- RAM usage of the selected application
- Moving graphs that update every second

It also contains PDC experiment buttons:
- Scalability Test
- Communication Test
- Fault-Tolerance Test

It also contains a Computer System Bus tab that demonstrates:
- Actual logical CPU core count detected from the laptop
- Actual total RAM capacity and live RAM utilization
- Live CPU-to-RAM and RAM-to-CPU data packet animation
- Data bus, address bus, control bus, and I/O device relationships

SETUP
-----
1. Install Python 3.
2. Put these files in one folder:
   pdc_live_performance_visualizer.py
   requirements_live.txt

3. Open CMD/PowerShell/VS Code terminal in that folder.

4. Install dependencies:
   python -m pip install -r requirements_live.txt

5. Run:
   python pdc_live_performance_visualizer.py

HOW TO DEMONSTRATE WITH PHOTOSHOP
---------------------------------
1. Open Photoshop.
2. Start this dashboard.
3. Click "Refresh Processes".
4. Select Photoshop.exe from the process dropdown.
5. In Photoshop, open a large image and apply filters, resize, export, blur,
   or another CPU-intensive operation.
6. Watch the Selected Application graph, overall CPU graph, and CPU core bars
   move in real time.

HOW TO DEMONSTRATE PARALLEL COMPUTING
-------------------------------------
1. Open the "PDC Tests" tab.
2. Click "Run Scalability Test".
3. Immediately click the "Live Monitor" tab.
4. You will see CPU usage and individual core bars increase while the test runs.
5. Go back to "PDC Tests" to see measured speedup and efficiency.

HOW TO DEMONSTRATE COMPUTER SYSTEM BUS
--------------------------------------
1. Open the "Computer System Bus" tab.
2. Point out the detected logical CPU cores and the total RAM capacity.
3. Run the Scalability Test while watching the animated packets and core usage.
4. Explain that the packets represent live resource activity flowing between CPU,
   RAM, and I/O; the values are read from the current laptop.
5. Use "Pause Animation" and "Resume Animation" to control the visualization.
6. Clarify that Windows does not expose the exact physical motherboard wiring
   through standard Python APIs, so the diagram shows logical system-bus flow.

NOTES
-----
- A process CPU value can exceed 100% on multi-core systems because one
  application may use more than one logical CPU.
- Results can vary because Windows and background applications also use CPU.
- Close unnecessary applications for a cleaner scalability experiment.
