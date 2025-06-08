# Keywords for auto-scoring (updated for all 60 questions)
ANSWER_KEYWORDS = {
    "floorplanning": {
        # Set 1 keywords (questions 0-14)
        0: ["macro placement", "timing", "power", "utilization", "power delivery", "IR drop", "blockage", "pins", "orientation", "dataflow"],
        1: ["setup violations", "timing paths", "floorplan", "critical paths", "placement", "buffers", "repeaters", "pipeline", "hierarchy", "partition"],
        2: ["congestion", "routing", "density", "spreading", "blockages", "channels", "utilization", "cell density", "padding", "keep-out"],
        3: ["voltage domains", "level shifter", "power grid", "isolation", "domain crossing", "power planning", "multi-voltage", "always-on", "shutdown", "interface"],
        4: ["clock domains", "clock tree", "skew", "latency", "synchronization", "CDC", "metastability", "clock gating", "mesh", "H-tree"],
        5: ["memory placement", "access time", "pin alignment", "data flow", "power straps", "decap", "timing critical", "bus routing", "periphery", "clustering"],
        6: ["IR drop", "power grid", "mesh density", "via pillars", "current density", "electromigration", "power straps", "decap cells", "voltage", "resistance"],
        7: ["die area", "utilization", "aspect ratio", "channel width", "macro spacing", "standard cell", "optimization", "timing margin", "risk", "iterations"],
        8: ["mixed-signal", "noise isolation", "guard rings", "substrate", "digital noise", "analog", "shielding", "separate supplies", "deep n-well", "distance"],
        9: ["congestion map", "global route", "heat map", "trial route", "density screens", "fly lines", "pin density", "track utilization", "gcell", "overflow"],
        10: ["hierarchical", "partition", "interface logic", "feedthrough", "pin assignment", "budgeting", "black box", "timing model", "boundary", "repeaters"],
        11: ["scan chains", "DFT", "test mode", "scan flops", "compression", "test time", "wire length", "shift power", "launch capture", "scan routing"],
        12: ["power gating", "retention", "isolation cells", "power switches", "sleep mode", "MTCMOS", "header footer", "rush current", "wake-up", "domains"],
        13: ["ECO", "spare cells", "flexibility", "metal layers", "gate array", "filler cells", "keep-out", "reserve", "incremental", "freeze"],
        14: ["validation", "quality checks", "congestion", "timing", "utilization", "connectivity", "DRC", "pin access", "aspect ratio", "metrics"],
        # Set 2 keywords (questions 15-29)
        15: ["voltage domains", "power sequencing", "domain crossing", "level shifters", "isolation", "retention", "always-on", "power-up", "interface", "complexity"],
        16: ["mesh clock", "distribution", "skew", "jitter", "drivers", "leaf cells", "grid", "redundancy", "short circuit", "analysis"],
        17: ["datapath", "multipliers", "ALU", "pipeline", "bit-slice", "regularity", "bus routing", "critical path", "placement", "hierarchy"],
        18: ["analog digital", "substrate", "noise coupling", "guard rings", "isolation", "separate supplies", "shielding", "distance", "deep n-well", "seal ring"],
        19: ["power grid", "IR drop", "current density", "mesh", "straps", "via arrays", "decap", "analysis", "electromigration", "optimization"],
        20: ["hard IP", "macro placement", "puzzle", "utilization", "channels", "aspect ratio", "orientation", "pins", "blockages", "dataflow"],
        21: ["DVFS", "voltage scaling", "frequency", "domains", "level shifters", "headers", "retention", "transition", "power states", "floorplan"],
        22: ["SerDes", "high-speed", "differential", "termination", "power noise", "isolation", "bumps", "escape routing", "shielding", "placement rules"],
        23: ["thermal", "hotspots", "heat dissipation", "power density", "spreading", "package", "thermal vias", "gradient", "placement", "monitors"],
        24: ["variants", "high-performance", "low-power", "common floorplan", "flexibility", "constraints", "trade-offs", "parameterized", "derivatives", "reuse"],
        25: ["security", "hardware", "isolation", "shielding", "tamper", "side-channel", "physical attacks", "sensors", "mesh", "boundaries"],
        26: ["test modes", "BIST", "scan", "access", "TAP", "compression", "controllers", "routing", "multiplexing", "coverage"],
        27: ["chiplet", "die-to-die", "interface", "micro-bumps", "alignment", "pitch", "PHY placement", "signal integrity", "power delivery", "yield"],
        28: ["repeater", "buffer", "planning", "stages", "delay", "slew", "placement", "resources", "prediction", "optimization"],
        29: ["aspect ratio", "pin placement", "package", "constraints", "IO planning", "bump map", "escape", "redistribution", "signal groups", "power"],
        # Set 3 keywords (questions 30-44)
        30: ["multi-core", "cache", "latency", "coherency", "mesh", "ring", "placement", "distance", "bandwidth", "arbitration"],
        31: ["reconfiguration", "partial", "regions", "boundaries", "static logic", "isolation", "clocking", "routing", "constraints", "bitstream"],
        32: ["hard macro", "timing models", "uncertainty", "margins", "interface", "budgeting", "constraints", "abstraction", "black box", "validation"],
        33: ["HBM", "memory interface", "PHY", "channels", "bump planning", "signal integrity", "power",# app.py - Physical Design Interview System (3 Questions Version)
import os
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'pd-secret-2024')

# In-memory storage
users = {}
assignments = {}
notifications = {}
assignment_counter = 0

# Initialize default users
def init_users():
    # Admin with new password
    users['admin'] = {
        'id': 'admin',
        'username': 'admin',
        'password': generate_password_hash('Vibhuaya@3006'),
        'is_admin': True,
        'experience_years': 3
    }
    
    # 5 Students
    for i in range(1, 6):  # Changed to 6 for 5 engineers
        user_id = f'eng00{i}'
        users[user_id] = {
            'id': user_id,
            'username': user_id,
            'password': generate_password_hash('password123'),
            'is_admin': False,
            'experience_years': 3
        }

# 4 Sets of Questions per topic (3+ Years Experience) - 15 questions each
# Set 1
QUESTIONS_SET1 = {
    "floorplanning": [
        "You have a 5mm x 5mm die with 4 hard macros (each 1mm x 0.8mm) and need to achieve 70% utilization. Describe your macro placement strategy considering timing and power delivery.",
        "Your design has setup timing violations on paths crossing from left to right. The floorplan has macros placed randomly. How would you reorganize the floorplan to improve timing?",
        "During floorplan, you notice routing congestion in the center region. What are 3 specific techniques you would use to reduce congestion without major timing impact?",
        "You're working with a design that has 2 voltage domains (0.9V core, 1.2V IO). Explain how you would plan the floorplan to minimize level shifter count and power grid complexity.",
        "Your design has 3 clock domains running at 800MHz, 400MHz, and 100MHz. How would you approach floorplanning to minimize clock tree power and skew?",
        "You need to place 8 memory instances in your design. What factors would you consider for their placement, and how would you verify the floorplan quality?",
        "Your floorplan review shows IR drop violations in certain regions. Describe your approach to fix this through floorplan changes and power grid improvements.",
        "You're told to reduce die area by 10% while maintaining timing. What floorplan modifications would you make and what risks would you monitor?",
        "Your design has mixed-signal blocks that need isolation from digital switching noise. How would you handle their placement and what guard techniques would you use?",
        "During early floorplan, how would you estimate routing congestion and what tools/techniques help predict routability issues?",
        "You have a hierarchical design with 3 major blocks. Explain your approach to partition-level floorplanning and interface planning between blocks.",
        "Your design requires scan chains for testing. How does DFT impact your floorplan decisions and what considerations are important for scan routing?",
        "You're working on a power-sensitive design. Describe floorplan techniques to enable effective power gating and retention strategies.",
        "Your floorplan needs to accommodate late ECOs (Engineering Change Orders). How would you plan for flexibility and what areas would you keep available?",
        "Explain your methodology for floorplan validation - what checks would you run and what metrics indicate a good floorplan ready for placement?"
    ],
    "placement": [
        "Your placement run shows timing violations on 20 critical paths with negative slack up to -50ps. Describe your systematic approach to fix these violations.",
        "You're seeing routing congestion hotspots after placement in 2-3 regions. What placement adjustments would you make to improve routability?",
        "Your design has high-fanout nets (>500 fanout) causing placement issues. How would you handle these nets during placement optimization?",
        "Compare global placement vs detailed placement - what specific problems does each solve and when would you iterate between them?",
        "Your placement shows leakage power higher than target. What placement techniques would you use to reduce power while maintaining timing?",
        "You have a multi-voltage design with voltage islands. Describe your placement strategy for cells near domain boundaries and level shifter placement.",
        "Your timing report shows hold violations scattered across the design. How would you address this through placement without affecting setup timing?",
        "During placement, you notice that certain instances are creating long routes. What tools and techniques help identify and fix such placement issues?",
        "Your design has clock gating cells. Explain their optimal placement strategy and impact on both power and timing.",
        "You're working with a design that has both high-performance and low-power modes. How does this affect your placement strategy?",
        "Your placement review shows uneven cell density distribution. Why is this problematic and how would you achieve better density distribution?",
        "Describe your approach to placement optimization for designs with multiple timing corners (SS, FF, TT). How do you ensure all corners meet timing?",
        "Your design has redundant logic for reliability. How would you place redundant instances to avoid common-mode failures?",
        "You need to optimize placement for both area and timing. Describe the trade-offs and how you would balance these competing requirements.",
        "Explain how placement impacts signal integrity. What placement techniques help minimize crosstalk and noise issues?"
    ],
    "routing": [
        "After global routing, you have 500 DRC violations (spacing, via, width). Describe your systematic approach to resolve these violations efficiently.",
        "Your design has 10 differential pairs for high-speed signals. Explain your routing strategy to maintain 100-ohm impedance and minimize skew.",
        "You're seeing timing degradation after detailed routing compared to placement timing. What causes this and how would you recover the timing?",
        "Your router is struggling with congestion in certain regions leading to routing non-completion. What techniques would you use to achieve 100% routing?",
        "Describe your approach to power/ground routing. How do you ensure adequate current carrying capacity and low IR drop?",
        "Your design has specific layer constraints (e.g., no routing on M1 except for local connections). How does this impact your routing strategy?",
        "You have crosstalk violations on critical nets. Explain your routing techniques to minimize crosstalk and meet noise requirements.",
        "Your clock nets require special routing with controlled skew. Describe clock routing methodology and skew optimization techniques.",
        "During routing, some nets are showing electromigration violations. How would you address current density issues through routing changes?",
        "You need to route in a design with double patterning constraints. Explain the challenges and your approach to handle decomposition issues.",
        "Your design has antenna violations after routing. What causes these and what routing techniques help prevent antenna issues?",
        "Describe your ECO (Engineering Change Order) routing strategy. How do you minimize disruption to existing clean routing?",
        "Your timing closure requires specific net delays. How do you control routing parasitics to meet timing targets?",
        "You're working with advanced technology nodes (7nm/5nm). What routing challenges are specific to these nodes and how do you address them?",
        "Explain your routing verification methodology. What checks ensure your routing is manufacturable and reliable?"
    ]
}

# Set 2
QUESTIONS_SET2 = {
    "floorplanning": [
        "Your design contains 6 voltage domains with complex power sequencing requirements. How would you organize the floorplan to minimize domain crossings and simplify power grid design?",
        "You're implementing a mesh clock distribution for a high-frequency design. Describe your floorplan strategy to support mesh clock architecture effectively.",
        "Explain how you would handle floorplanning for a design with heavy datapath components (multipliers, ALUs). What placement strategies optimize timing and area?",
        "Your chip has both digital and analog sections sharing the same substrate. Detail your floorplanning approach for noise isolation and substrate coupling prevention.",
        "Describe your methodology for power grid planning in the floorplan stage. How do you ensure robust power delivery while minimizing resources?",
        "You have a design with multiple hard IP blocks of different sizes. How would you approach the macro placement puzzle to maximize utilization?",
        "Your floorplan must support dynamic voltage and frequency scaling (DVFS). What special considerations are needed in the floorplan?",
        "Explain your approach to handling high-speed serial interfaces (SerDes) in the floorplan. What placement rules would you follow?",
        "Your design has stringent thermal requirements. How would you modify the floorplan to improve heat dissipation and avoid hotspots?",
        "Describe the floorplan considerations for a design targeting both high-performance and low-power variants from the same RTL.",
        "You need to implement hardware security features. How does this impact your floorplanning decisions regarding isolation and shielding?",
        "Your floorplan must accommodate multiple test modes including BIST and scan. Explain your planning for test access and routing.",
        "How would you approach floorplanning for a chiplet-based design with die-to-die interfaces? What are the key considerations?",
        "Describe your strategy for handling repeater planning during the floorplan stage. How do you predict and allocate repeater resources?",
        "Your design requires specific aspect ratio and pin placement for package constraints. How do you balance these requirements with optimal floorplan?"
    ],
    "placement": [
        "Your placement engine reports severe congestion despite low utilization. What investigation steps and fixes would you apply?",
        "Describe your approach to timing-driven placement when dealing with multiple clock domains and false paths.",
        "You have a datapath with regular structure. How would you leverage structured placement techniques for better QoR?",
        "Explain your methodology for handling macro blockages and halos. How do you determine optimal spacing values?",
        "Your design has critical nets requiring special attention. Describe net weighting strategies and their impact on placement.",
        "How would you approach placement optimization for a design with significant on-chip variation (OCV) effects?",
        "Your placement shows clustering of high-switching cells. What techniques would you use to distribute power consumption?",
        "Describe your approach to placement when dealing with multiple power domains and always-on logic requirements.",
        "You need to achieve specific timing for memory interfaces. How would you use placement constraints and techniques?",
        "Explain how you would handle placement for cells with special requirements like antenna diodes or decap cells.",
        "Your design has both timing-critical and power-critical paths. How do you balance placement optimization between these objectives?",
        "Describe your methodology for incremental placement during ECO implementation. How do you minimize perturbation?",
        "How would you optimize placement for better clock tree synthesis results? What placement preparation helps CTS?",
        "Your placement must consider package-level constraints like bump locations. Explain your approach to this co-optimization.",
        "Describe techniques for achieving uniform power rail utilization through placement optimization."
    ],
    "routing": [
        "Your design fails routing due to severe congestion in specific layers. Describe layer-aware routing strategies to resolve this.",
        "Explain your approach to shielding critical signals. When would you use coaxial shielding vs adjacent track shielding?",
        "You have buses requiring matched delays. Describe techniques for achieving tight skew control during routing.",
        "How would you handle routing for a design with restrictive DRC rules in advanced nodes? What strategies help convergence?",
        "Your routing must meet strict electromagnetic interference (EMI) requirements. What routing techniques help minimize EMI?",
        "Describe your approach to via optimization. How do you balance via count, resistance, and reliability concerns?",
        "You need to route power meshes with IR drop constraints. Explain your methodology for power routing optimization.",
        "How would you handle routing in the presence of pre-routed IP blocks? What are common integration challenges?",
        "Your design has analog signals requiring special routing. Describe techniques for routing sensitive analog nets in a digital environment.",
        "Explain your approach to handling crosstalk-induced delay variations. What routing techniques minimize timing uncertainty?",
        "Describe routing strategies for designs with multiple metal stacks and different resistivity metals.",
        "How would you approach routing optimization for manufacturing yield? What DFM rules impact routing decisions?",
        "Your routing must consider stress effects and device performance. Explain stress-aware routing techniques.",
        "Describe your methodology for achieving routing closure with minimum iterations. What metrics guide optimization?",
        "How would you handle special routing requirements for power gating switches and isolation cells?"
    ]
}

# Set 3
QUESTIONS_SET3 = {
    "floorplanning": [
        "You're designing a multi-core processor with shared cache. Describe your floorplan strategy for minimizing cache access latency across cores.",
        "Your floorplan must support partial reconfiguration regions. How would you partition and constrain the floorplan for this requirement?",
        "Explain your approach to floorplanning when dealing with hard macro timing models that have significant uncertainty margins.",
        "Your design includes high-bandwidth memory (HBM) interfaces. Describe floorplan considerations for HBM integration and signal routing.",
        "How would you handle floorplanning for a design with stringent jitter requirements on multiple clock domains?",
        "Your chip requires redundancy for yield improvement. Explain how redundancy requirements impact your floorplanning decisions.",
        "Describe your methodology for creating a pin placement that optimizes both internal routing and package escape routing.",
        "You need to floorplan a design with aggressive power targets using extensive power gating. How do you organize power domains?",
        "Your floorplan must accommodate on-chip voltage regulators. What placement and isolation strategies would you employ?",
        "Explain how you would approach floorplanning for testability, including placement of test compression logic and TAP controllers.",
        "Your design has performance monitors and debug infrastructure. How do you integrate these into your floorplan efficiently?",
        "Describe floorplan strategies for designs requiring radiation hardening or single-event upset (SEU) protection.",
        "How would you optimize the floorplan for a design with multiple high-speed transceivers requiring careful power supply isolation?",
        "Your floorplan needs to support both flip-chip and wire-bond package options. Explain your approach to this flexibility.",
        "Describe considerations for floorplanning a design that will undergo metal-only ECOs. How do you prepare for changes?"
    ],
    "placement": [
        "Your placement results show timing violations only in specific voltage-temperature corners. Describe your corner-specific optimization approach.",
        "Explain how you would handle placement for a design with extensive clock domain crossing (CDC) logic. What clustering strategies help?",
        "You need to optimize placement for routability while maintaining timing. Describe metrics and techniques to balance these goals.",
        "Your design has memory arrays with strict access timing. How would you approach placement of memory interface logic?",
        "Describe your methodology for placing spare cells for ECO purposes. How do you determine quantity and distribution?",
        "How would you handle placement optimization when dealing with coupling-critical nets that affect functionality?",
        "Your placement must consider electromigration rules from early stages. Explain how EM impacts placement decisions.",
        "Describe techniques for achieving better placement QoR through floorplan feedback. What metrics drive floorplan updates?",
        "You have a design with multiple test modes affecting timing. How do you ensure placement works across all modes?",
        "Explain your approach to placing level shifters and isolation cells in a multi-voltage design for optimal area and timing.",
        "Your placement shows local congestion around certain macros. Describe techniques to relieve congestion without impacting timing.",
        "How would you optimize placement for designs with significant useful skew requirements? What constraints and techniques apply?",
        "Describe your approach to placement when dealing with substrate noise-sensitive analog blocks integrated with digital logic.",
        "Your design requires specific placement for security features. How do you balance security requirements with PPA goals?",
        "Explain placement strategies for achieving uniform dynamic IR drop across the design. What factors do you consider?"
    ],
    "routing": [
        "Your routing faces severe congestion with multiple hotspots. Describe a systematic approach using global route guides and modifications.",
        "Explain advanced techniques for routing differential signals in the presence of obstacles while maintaining signal integrity.",
        "You need to achieve specific impedance targets for high-speed interfaces. Describe your routing methodology and verification approach.",
        "How would you handle routing for a design with extensive bus structures requiring length matching within 1% tolerance?",
        "Your design has power delivery network (PDN) resonance issues. Describe routing techniques to improve PDN impedance.",
        "Explain your approach to routing clock networks with non-default rules while managing transition times and duty cycle.",
        "Describe techniques for routing in designs with triple or quadruple patterning requirements. How do you handle coloring conflicts?",
        "You have nets switching simultaneously causing power integrity issues. How would you modify routing to reduce simultaneous switching?",
        "Your routing must meet reliability requirements including antenna and via reliability. Describe comprehensive checking methodology.",
        "How would you approach routing optimization for thermal management? What routing strategies help spread heat generation?",
        "Explain routing techniques for designs with embedded FPGA or programmable logic blocks requiring special interconnect.",
        "Your design has strict requirements for matched propagation delays on buses. Describe routing techniques beyond length matching.",
        "How would you handle routing challenges in 3D-IC or interposer-based designs? What special considerations apply?",
        "Describe your approach to routing optimization when dealing with process variation effects on different metal layers.",
        "Explain strategies for achieving routing closure when facing manufacturing constraints like via pillars or metal density rules."
    ]
}

# Set 4
QUESTIONS_SET4 = {
    "floorplanning": [
        "Your design requires integration of third-party encrypted IP. How does this impact your floorplanning approach and optimization capabilities?",
        "Describe your methodology for floorplanning a network-on-chip (NoC) based design. How do you optimize for latency and throughput?",
        "You're working on an AI accelerator with large systolic arrays. Explain your floorplan strategy for dataflow optimization.",
        "How would you approach floorplanning for a design with multiple asynchronous clock domains and metastability concerns?",
        "Your floorplan must support in-field diagnostic capabilities. What considerations are needed for access and isolation?",
        "Describe floorplanning challenges and solutions when dealing with ultra-low power designs using aggressive voltage scaling.",
        "You need to create a floorplan supporting both performance and area-optimized versions. Explain your parameterizable approach.",
        "How would you handle floorplanning for designs with significant repeater and buffer requirements? Describe resource planning.",
        "Your design includes custom analog blocks with specific orientation requirements. How do you accommodate these in digital floorplan?",
        "Explain your approach to floorplanning when dealing with hard macros that have multiple power domains internally.",
        "Describe methodology for creating floorplans that are portable across different technology nodes with minimal changes.",
        "Your floorplan must accommodate future derivative designs. How do you build flexibility while meeting current targets?",
        "How would you approach floorplanning for designs requiring hardware root-of-trust and secure enclaves?",
        "Explain floorplan optimization techniques when dealing with designs having multiple voltage regulators and power switches.",
        "Describe your approach to validating floorplan quality early using virtual prototypes before detailed implementation."
    ],
    "placement": [
        "Your placement optimization is limited by long runtime. Describe techniques to improve placement efficiency without sacrificing QoR.",
        "Explain how machine learning techniques can be applied to placement optimization. What features and models are effective?",
        "You're dealing with a sea-of-gates style placement with minimal structure. How do you guide placement for optimal results?",
        "Describe your approach to placement when handling designs with dynamic power management and multiple operating modes.",
        "How would you optimize placement for designs with significant IR drop concerns? What early analysis guides placement?",
        "Your placement must consider package and board-level constraints. Explain co-design considerations affecting placement.",
        "Describe techniques for achieving placement closure when dealing with conflicting constraints from multiple design teams.",
        "How would you handle placement for designs with embedded test structures like memory BIST and logic BIST?",
        "Explain your methodology for placing designs with fine-grained power gating. How do you handle sleep transistor placement?",
        "Your placement faces challenges from irregular floorplans. Describe techniques to achieve good QoR despite constraints.",
        "How would you approach placement optimization for designs targeting multiple process corners with different characteristics?",
        "Describe placement strategies when dealing with soft error rate (SER) requirements. How do you optimize for reliability?",
        "Your design has placement restrictions due to export control requirements. How do you handle security-driven constraints?",
        "Explain techniques for incremental placement optimization late in the design cycle without full re-placement.",
        "How would you validate placement quality using static analysis before moving to routing? What checks are critical?"
    ],
    "routing": [
        "Your routing is failing due to complex pin access issues in advanced nodes. Describe systematic approaches to improve pin access.",
        "Explain your methodology for routing power networks in designs with hundreds of power domains. How do you manage complexity?",
        "You need to implement redundant routing for critical nets. Describe techniques and trade-offs for redundancy implementation.",
        "How would you approach routing optimization for designs with extensive use of via ladders and stacked vias?",
        "Your routing must meet stringent coupling capacitance targets. Describe extraction and optimization techniques for coupling reduction.",
        "Explain routing strategies for designs with non-Manhattan geometries. When are 45-degree routes beneficial?",
        "Describe your approach to routing when dealing with designs having IP blocks with different routing track definitions.",
        "How would you handle routing optimization for multi-die integration using silicon interposers or bridges?",
        "Your design requires specific routing for security features like shields and guards. Explain implementation strategies.",
        "Describe techniques for achieving routing closure with multiple metal layer options having different RC characteristics.",
        "How would you optimize routing for designs with critical electrostatic discharge (ESD) protection requirements?",
        "Explain your methodology for routing verification including LVS, antenna, and reliability checks. What tools and flows are used?",
        "Your routing must consider future metal layer reduction for cost. How do you prepare for layer reduction ECOs?",
        "Describe approaches to routing optimization when dealing with statistical timing analysis and variation-aware timing.",
        "How would you handle routing challenges in designs with extensive use of low-power techniques like MTCMOS and power gating?"
    ]
}

# Combine all question sets
QUESTION_SETS = [QUESTIONS_SET1, QUESTIONS_SET2, QUESTIONS_SET3, QUESTIONS_SET4]

# Track which set each engineer gets
engineer_question_sets = {}

# Keywords for auto-scoring (updated for all 4 sets)
ANSWER_KEYWORDS = {
    "floorplanning": {
        # Set 1 keywords
        0: ["macro placement", "timing", "power", "utilization", "power delivery", "IR drop", "blockage", "pins", "orientation", "dataflow"],
        1: ["setup violations", "timing paths", "floorplan", "critical paths", "placement", "buffers", "repeaters", "pipeline", "hierarchy", "partition"],
        2: ["congestion", "routing", "density", "spreading", "blockages", "channels", "utilization", "cell density", "padding", "keep-out"],
        # Set 2 keywords
        3: ["voltage domains", "level shifter", "power grid", "isolation", "domain crossing", "power planning", "multi-voltage", "always-on", "shutdown", "interface"],
        4: ["clock domains", "clock tree", "skew", "latency", "synchronization", "CDC", "metastability", "clock gating", "mesh", "H-tree"],
        5: ["memory placement", "access time", "pin alignment", "data flow", "power straps", "decap", "timing critical", "bus routing", "periphery", "clustering"],
        # Set 3 keywords
        6: ["IR drop", "power grid", "mesh density", "via pillars", "current density", "electromigration", "power straps", "decap cells", "voltage", "resistance"],
        7: ["die area", "utilization", "aspect ratio", "channel width", "macro spacing", "standard cell", "optimization", "timing margin", "risk", "iterations"],
        8: ["mixed-signal", "noise isolation", "guard rings", "substrate", "digital noise", "analog", "shielding", "separate supplies", "deep n-well", "distance"],
        # Set 4 keywords
        9: ["congestion map", "global route", "heat map", "trial route", "density screens", "fly lines", "pin density", "track utilization", "gcell", "overflow"],
        10: ["hierarchical", "partition", "interface logic", "feedthrough", "pin assignment", "budgeting", "black box", "timing model", "boundary", "repeaters"],
        11: ["scan chains", "DFT", "test mode", "scan flops", "compression", "test time", "wire length", "shift power", "launch capture", "scan routing"]
    },
    "placement": {
        # Set 1 keywords
        0: ["timing violations", "negative slack", "optimization", "critical paths", "placement", "setup", "hold", "clock", "incremental", "ECO"],
        1: ["congestion", "hotspots", "spreading", "density", "padding", "blockages", "magnet placement", "guides", "regions", "utilization"],
        2: ["high-fanout", "buffer tree", "cloning", "load splitting", "placement", "clustering", "net weights", "timing", "physical synthesis", "optimization"],
        # Set 2 keywords
        3: ["global placement", "detailed placement", "legalization", "optimization", "wirelength", "timing driven", "congestion driven", "overlap removal", "spreading", "refinement"],
        4: ["leakage power", "LVT", "HVT", "threshold voltage", "cell swapping", "power optimization", "clustering", "activity", "temperature", "multi-Vt"],
        5: ["voltage islands", "level shifters", "isolation cells", "retention", "power domains", "always-on", "interface", "power state", "boundary", "crossing"],
        # Set 3 keywords
        6: ["hold violations", "buffer insertion", "min delay", "clock skew", "useful skew", "hold margin", "corner analysis", "multi-corner", "OCV", "CPPR"],
        7: ["long routes", "path analysis", "net viewer", "flight lines", "placement density", "spreading", "guides", "soft blockages", "net weights", "critical nets"],
        8: ["clock gating", "enable timing", "placement", "clock tree", "activity", "power savings", "setup check", "glitch", "ICG", "proximity"],
        # Set 4 keywords
        9: ["multi-mode", "scenario", "performance mode", "low power mode", "DVFS", "placement strategy", "optimization", "constraints", "cell selection", "operating points"],
        10: ["cell density", "utilization", "hot spots", "spreading", "target density", "overflow", "legalization", "detailed placement", "uniformity", "gradients"],
        11: ["multi-corner", "MCMM", "setup timing", "hold timing", "worst corner", "optimization", "scenario merging", "common path", "margin", "sign-off"]
    },
    "routing": {
        # Set 1 keywords
        0: ["DRC violations", "spacing", "via", "width", "metal", "tracks", "reroute", "ECO", "search repair", "manual fixes"],
        1: ["differential pairs", "impedance", "matching", "shielding", "spacing", "length matching", "skew", "routing", "symmetry", "guard rings"],
        2: ["timing degradation", "parasitics", "RC delay", "crosstalk", "coupling", "optimization", "layer assignment", "via optimization", "buffer", "sizing"],
        # Set 2 keywords
        3: ["routing congestion", "detour", "layer assignment", "track utilization", "global route", "detailed route", "spreading", "guides", "overflow", "iterations"],
        4: ["power routing", "IR drop", "EM rules", "via arrays", "width", "current density", "mesh", "straps", "star route", "trunk routing"],
        5: ["layer constraints", "preferred direction", "track offset", "via stack", "routing resources", "metal stack", "NDR", "shielding", "keep-out", "blockages"],
        # Set 3 keywords
        6: ["crosstalk", "coupling capacitance", "aggressor", "victim", "shielding", "spacing", "NDR", "switching window", "noise margin", "parallel run"],
        7: ["clock routing", "skew", "latency", "NDR rules", "shielding", "spine", "mesh", "H-tree", "balanced", "buffer placement"],
        8: ["electromigration", "current density", "wire width", "via count", "temperature", "lifetime", "redundant vias", "tapering", "EM rules", "stress"],
        # Set 4 keywords
        9: ["double patterning", "coloring", "decomposition", "odd cycle", "conflict", "stitching", "mask assignment", "spacing", "litho", "manufacturing"],
        10: ["antenna violations", "PAE", "CAR", "diode insertion", "metal jumping", "layer hopping", "gate oxide", "charge accumulation", "ratio", "process antenna"],
        11: ["ECO routing", "minimal impact", "preserve routing", "incremental", "freeze silicon", "metal fix", "spare cells", "rip-up", "reroute", "timing"]
    }
}

# Helper function to get questions for an engineer
def get_questions_for_engineer(engineer_id, topic):
    """Get unique question set for engineer"""
    if engineer_id not in engineer_question_sets:
        # Assign a question set (rotate through sets)
        engineer_num = int(engineer_id[-3:]) - 1  # Extract number from eng001, eng002, etc.
        set_index = engineer_num % len(QUESTION_SETS)
        engineer_question_sets[engineer_id] = set_index
    
    set_index = engineer_question_sets[engineer_id]
    return QUESTION_SETS[set_index][topic]

# Helper function to get keyword index for auto-scoring
def get_keyword_index(engineer_id, question_index):
    """Get the correct keyword index based on engineer's question set"""
    set_index = engineer_question_sets.get(engineer_id, 0)
    return set_index * 15 + question_index  # Each set has 15 questions

# Scoring rubric
SCORING_RUBRIC = {
    10: "Excellent - Comprehensive answer with deep understanding",
    8: "Very Good - Covers most key points with good detail",
    6: "Good - Basic understanding with some key points",
    4: "Fair - Limited understanding, missing key concepts",
    2: "Poor - Minimal understanding shown",
    0: "No answer or completely incorrect"
}

# Helper functions
def calculate_auto_score(answer, topic, question_index, engineer_id):
    """Calculate auto-score based on keywords"""
    if not answer:
        return 0
    
    answer_lower = answer.lower()
    keywords_found = 0
    
    # Get correct keyword index based on engineer's question set
    keyword_index = get_keyword_index(engineer_id, question_index)
    
    if topic in ANSWER_KEYWORDS and keyword_index < len(ANSWER_KEYWORDS[topic]):
        keywords = ANSWER_KEYWORDS[topic][keyword_index]
        for keyword in keywords:
            if keyword.lower() in answer_lower:
                keywords_found += 1
    
    # 2 points per keyword, max 10 points
    return min(keywords_found * 2, 10)

def create_assignment(engineer_id, topic):
    global assignment_counter
    
    user = users.get(engineer_id)
    if not user or topic not in QUESTIONS_SET1:
        return None
    
    assignment_counter += 1
    assignment_id = f"PD_{topic.upper()}_{engineer_id}_{assignment_counter}"
    
    # Get unique questions for this engineer
    questions = get_questions_for_engineer(engineer_id, topic)
    
    assignment = {
        'id': assignment_id,
        'engineer_id': engineer_id,
        'topic': topic,
        'questions': questions,
        'answers': {},
        'auto_scores': {},  # Auto-calculated scores
        'final_scores': {},  # Admin's final scores
        'status': 'pending',  # pending -> submitted -> under_review -> published
        'created_date': datetime.now().isoformat(),
        'due_date': (datetime.now() + timedelta(days=3)).isoformat(),
        'total_score': None,
        'scored_by': None,
        'scored_date': None,
        'published_date': None
    }
    
    assignments[assignment_id] = assignment
    
    # Create notification
    if engineer_id not in notifications:
        notifications[engineer_id] = []
    
    notifications[engineer_id].append({
        'title': f'New {topic} Assignment',
        'message': f'15 questions for 3+ years experience, due in 3 days',
        'created_at': datetime.now().isoformat()
    })
    
    return assignment

# HTML Templates
def get_base_html():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>VT - Physical Design Interview System</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #0a0a0a;
                color: #e0e0e0;
                line-height: 1.6;
            }
            
            /* Header Styles */
            .header { 
                background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 100%);
                color: white; 
                padding: 20px 0;
                box-shadow: 0 4px 20px rgba(0,0,0,0.5);
                border-bottom: 2px solid #2196F3;
            }
            
            .header-content { 
                max-width: 1200px; 
                margin: 0 auto;
                padding: 0 20px;
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
            }
            
            .logo-section {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .logo {
                width: 50px;
                height: 50px;
                background: linear-gradient(135deg, #2196F3 0%, #64B5F6 100%);
                clip-path: polygon(0 0, 100% 0, 50% 100%);
                position: relative;
            }
            
            .logo::after {
                content: 'VT';
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                font-weight: bold;
                font-size: 18px;
                color: white;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            
            .header h1 { 
                font-size: 1.8rem;
                font-weight: 300;
                letter-spacing: 1px;
            }
            
            .user-info { 
                display: flex; 
                align-items: center; 
                gap: 20px; 
            }
            
            .logout-btn { 
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                color: white; 
                text-decoration: none; 
                padding: 10px 20px; 
                border-radius: 25px;
                border: 1px solid rgba(255,255,255,0.2);
                transition: all 0.3s ease;
                font-weight: 500;
            }
            
            .logout-btn:hover { 
                background: rgba(255,255,255,0.2);
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            }
            
            /* Container */
            .container { 
                max-width: 1200px; 
                margin: 2rem auto; 
                padding: 0 2rem; 
            }
            
            /* Cards */
            .card { 
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                padding: 2rem; 
                margin: 2rem 0; 
                border-radius: 15px; 
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                border: 1px solid rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            
            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 12px 40px rgba(33,150,243,0.2);
            }
            
            /* Stats Grid */
            .stats { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 2rem; 
                margin-bottom: 3rem;
            }
            
            .stat-card { 
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                text-align: center;
                padding: 2rem;
                border-radius: 15px;
                border: 1px solid rgba(255,255,255,0.1);
                transition: all 0.3s ease;
            }
            
            .stat-card:hover {
                transform: translateY(-10px) scale(1.02);
                box-shadow: 0 15px 35px rgba(33,150,243,0.3);
            }
            
            .stat-value { 
                font-size: 3rem; 
                font-weight: bold; 
                color: #64B5F6;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                margin-bottom: 0.5rem;
            }
            
            .stat-label { 
                color: #B0BEC5;
                font-size: 1rem; 
                text-transform: uppercase; 
                letter-spacing: 2px;
                font-weight: 300;
            }
            
            /* Forms */
            .form-group { 
                margin: 1.5rem 0; 
            }
            
            label { 
                display: block; 
                margin-bottom: 0.5rem; 
                font-weight: 500; 
                color: #64B5F6;
                font-size: 0.9rem;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            input, select, textarea { 
                width: 100%; 
                padding: 12px 16px; 
                border: 2px solid rgba(255,255,255,0.1);
                background: rgba(255,255,255,0.05);
                border-radius: 8px;
                color: #e0e0e0;
                font-size: 1rem;
                transition: all 0.3s ease;
            }
            
            input:focus, select:focus, textarea:focus { 
                outline: none; 
                border-color: #2196F3;
                background: rgba(255,255,255,0.08);
                box-shadow: 0 0 20px rgba(33,150,243,0.2);
            }
            
            textarea { 
                min-height: 120px; 
                resize: vertical; 
                font-family: inherit;
            }
            
            /* Buttons */
            button, .btn { 
                background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
                color: white; 
                padding: 12px 30px; 
                border: none; 
                border-radius: 25px; 
                font-size: 1rem; 
                font-weight: 500;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(33,150,243,0.3);
                text-transform: uppercase;
                letter-spacing: 1px;
                display: inline-block;
                text-decoration: none;
            }
            
            button:hover, .btn:hover { 
                transform: translateY(-2px);
                box-shadow: 0 6px 25px rgba(33,150,243,0.4);
                background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%);
            }
            
            /* Tables */
            table { 
                width: 100%; 
                border-collapse: collapse;
                margin-top: 1rem;
                background: rgba(255,255,255,0.02);
                border-radius: 10px;
                overflow: hidden;
            }
            
            th, td { 
                padding: 15px; 
                text-align: left; 
                border-bottom: 1px solid rgba(255,255,255,0.05);
            }
            
            th { 
                background: rgba(33,150,243,0.1);
                font-weight: 600; 
                color: #64B5F6;
                text-transform: uppercase;
                font-size: 0.85rem;
                letter-spacing: 1px;
            }
            
            tr:hover {
                background: rgba(255,255,255,0.03);
            }
            
            /* Questions */
            .question { 
                background: linear-gradient(135deg, rgba(33,150,243,0.1) 0%, rgba(33,150,243,0.05) 100%);
                padding: 1.5rem; 
                margin: 1.5rem 0; 
                border-left: 4px solid #2196F3;
                border-radius: 8px;
                transition: all 0.3s ease;
            }
            
            .question:hover {
                transform: translateX(5px);
                box-shadow: 0 5px 20px rgba(33,150,243,0.2);
            }
            
            .question-number { 
                font-weight: 600; 
                color: #64B5F6;
                margin-bottom: 0.5rem;
                font-size: 1.1rem;
            }
            
            .answer-box { 
                margin-top: 1rem;
                background: rgba(0,0,0,0.3);
                padding: 1rem;
                border-radius: 8px;
                border: 1px solid rgba(255,255,255,0.05);
            }
            
            /* Badges */
            .badge { 
                display: inline-block; 
                padding: 6px 16px; 
                border-radius: 20px; 
                font-size: 0.85rem;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .badge-pending { 
                background: linear-gradient(135deg, #FFC107 0%, #FFB300 100%);
                color: #000;
            }
            
            .badge-submitted { 
                background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
                color: white;
            }
            
            .badge-under_review { 
                background: linear-gradient(135deg, #FF5722 0%, #E64A19 100%);
                color: white;
            }
            
            .badge-published { 
                background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%);
                color: white;
            }
            
            /* Messages */
            .error { 
                color: #FF5252;
                background: rgba(255,82,82,0.1);
                padding: 1rem;
                border-radius: 8px;
                border: 1px solid rgba(255,82,82,0.3);
                margin: 1rem 0;
            }
            
            .success { 
                color: #69F0AE;
                background: rgba(105,240,174,0.1);
                padding: 1rem;
                border-radius: 8px;
                border: 1px solid rgba(105,240,174,0.3);
                margin: 1rem 0;
            }
            
            /* Score Box */
            .score-box { 
                display: flex; 
                align-items: center; 
                gap: 20px; 
                margin: 1rem 0;
                flex-wrap: wrap;
            }
            
            .auto-score { 
                background: linear-gradient(135deg, rgba(33,150,243,0.2) 0%, rgba(33,150,243,0.1) 100%);
                padding: 8px 16px; 
                border-radius: 20px;
                font-weight: 500;
                border: 1px solid rgba(33,150,243,0.3);
            }
            
            .rubric { 
                background: rgba(255,255,255,0.03);
                padding: 1rem; 
                margin: 1rem 0; 
                border-radius: 8px; 
                font-size: 0.9rem;
                border: 1px solid rgba(255,255,255,0.05);
            }
            
            /* Login Page */
            .login-container { 
                min-height: 100vh; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #0f3460 100%);
                position: relative;
                overflow: hidden;
            }
            
            .login-container::before {
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(33,150,243,0.1) 0%, transparent 70%);
                animation: pulse 10s ease-in-out infinite;
            }
            
            @keyframes pulse {
                0%, 100% { transform: scale(1); opacity: 0.5; }
                50% { transform: scale(1.1); opacity: 0.3; }
            }
            
            .login-box { 
                background: rgba(26,26,46,0.9);
                backdrop-filter: blur(20px);
                padding: 3rem; 
                border-radius: 20px; 
                box-shadow: 0 20px 60px rgba(0,0,0,0.5);
                width: 100%; 
                max-width: 450px;
                border: 1px solid rgba(255,255,255,0.1);
                position: relative;
                z-index: 1;
            }
            
            .login-logo {
                text-align: center;
                margin-bottom: 2rem;
            }
            
            .login-logo .logo {
                width: 80px;
                height: 80px;
                margin: 0 auto;
                font-size: 24px;
            }
            
            .login-title {
                text-align: center;
                margin-bottom: 2rem;
                color: #e0e0e0;
                font-weight: 300;
                font-size: 1.8rem;
            }
            
            .info-box {
                background: rgba(33,150,243,0.1);
                border: 1px solid rgba(33,150,243,0.3);
                padding: 1rem;
                border-radius: 10px;
                margin-bottom: 1.5rem;
                font-size: 0.9rem;
            }
            
            /* Animations */
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .card, .stat-card {
                animation: fadeIn 0.6s ease-out;
            }
            
            /* Responsive */
            @media (max-width: 768px) {
                .header h1 { font-size: 1.2rem; }
                .stats { grid-template-columns: 1fr; }
                .container { padding: 0 1rem; }
                .stat-value { font-size: 2rem; }
            }
        </style>
    </head>
    <body>
    '''

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        if session.get('is_admin'):
            return redirect('/admin')
        else:
            return redirect('/student')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = users.get(username)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user.get('is_admin', False)
            
            if user.get('is_admin'):
                return redirect('/admin')
            else:
                return redirect('/student')
        else:
            error = 'Invalid credentials'
    
    html = get_base_html() + f'''
        <div class="login-container">
            <div class="login-box">
                <div class="login-logo">
                    <div class="logo"></div>
                </div>
                <h1 class="login-title">Physical Design Interview System</h1>
                <p style="text-align: center; color: #64B5F6; margin-bottom: 2rem;">3+ Years Experience Assessment</p>
                <div class="info-box">
                    <strong style="color: #64B5F6;">Demo Credentials:</strong><br>
                    Admin: admin / Vibhuaya@3006<br>
                    Student: eng001-eng005 / password123
                </div>
                {f'<p class="error">{error}</p>' if error else ''}
                <form method="POST">
                    <div class="form-group">
                        <label>Username</label>
                        <input type="text" name="username" required placeholder="Enter your username">
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" name="password" required placeholder="Enter your password">
                    </div>
                    <button type="submit" style="width: 100%; margin-top: 1rem;">LOGIN</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect('/login')
    
    engineers = [u for u in users.values() if not u.get('is_admin')]
    all_assignments = list(assignments.values())
    
    # Count assignments by status
    submitted = [a for a in all_assignments if a['status'] == 'submitted']
    under_review = [a for a in all_assignments if a['status'] == 'under_review']
    published = [a for a in all_assignments if a['status'] == 'published']
    
    html = get_base_html() + f'''
        <div class="header">
            <div class="header-content">
                <div class="logo-section">
                    <div class="logo"></div>
                    <h1>Admin Dashboard</h1>
                </div>
                <div class="user-info">
                    <span style="color: #64B5F6;">Welcome, {session["username"]}</span>
                    <a href="/logout" class="logout-btn">LOGOUT</a>
                </div>
            </div>
        </div>
        
        <div class="container">
            <div class="stats">
                <div class="stat card">
                    <h2>{len(engineers)}</h2>
                    <p>Engineers</p>
                </div>
                <div class="stat card">
                    <h2>{len(submitted)}</h2>
                    <p>Submitted</p>
                </div>
                <div class="stat card">
                    <h2>{len(under_review)}</h2>
                    <p>Under Review</p>
                </div>
                <div class="stat card">
                    <h2>{len(published)}</h2>
                    <p>Published</p>
                </div>
            </div>
            
            <div class="card">
                <h2>Create Assignment</h2>
                <form method="POST" action="/admin/create">
                    <div class="form-group">
                        <label>Engineer</label>
                        <select name="engineer_id" required>
                            <option value="">Select...</option>
    '''
    
    for eng in engineers:
        html += f'<option value="{eng["id"]}">{eng["username"]}</option>'
    
    html += '''
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Topic</label>
                        <select name="topic" required>
                            <option value="">Select...</option>
                            <option value="floorplanning">Floorplanning</option>
                            <option value="placement">Placement</option>
                            <option value="routing">Routing</option>
                        </select>
                    </div>
                    <button type="submit">Create Assignment</button>
                </form>
            </div>
            
            <div class="card">
                <h2>Submitted Assignments (Ready for Review)</h2>
    '''
    
    if submitted:
        for a in submitted:
            html += f'''
                <div style="border: 1px solid #ddd; padding: 10px; margin: 10px 0;">
                    <h4>{a["id"]} - {a["engineer_id"]} - {a["topic"].title()}</h4>
                    <p>Submitted: All 15 answers | Auto-score calculated</p>
                    <a href="/admin/review/{a["id"]}"><button>Review & Score</button></a>
                </div>
            '''
    else:
        html += '<p>No assignments ready for review</p>'
    
    html += '''
            </div>
            
            <div class="card">
                <h2>All Assignments</h2>
                <table>
                    <tr>
                        <th>ID</th>
                        <th>Engineer</th>
                        <th>Topic</th>
                        <th>Status</th>
                        <th>Score</th>
                        <th>Action</th>
                    </tr>
    '''
    
    for a in all_assignments[-10:]:  # Last 10
        action = ""
        if a['status'] == 'under_review':
            action = f'<a href="/admin/publish/{a["id"]}"><button>Publish</button></a>'
        elif a['status'] == 'published':
            action = "Published ✓"
            
        html += f'''
            <tr>
                <td>{a["id"]}</td>
                <td>{a["engineer_id"]}</td>
                <td>{a["topic"]}</td>
                <td><span class="badge badge-{a["status"]}">{a["status"]}</span></td>
                <td>{a.get("total_score", "-")}/150</td>
                <td>{action}</td>
            </tr>
        '''
    
    html += '''
                </table>
            </div>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/admin/create', methods=['POST'])
def admin_create():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect('/login')
    
    engineer_id = request.form.get('engineer_id')
    topic = request.form.get('topic')
    
    if engineer_id and topic:
        create_assignment(engineer_id, topic)
    
    return redirect('/admin')

@app.route('/admin/review/<assignment_id>', methods=['GET', 'POST'])
def admin_review(assignment_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect('/login')
    
    assignment = assignments.get(assignment_id)
    if not assignment or assignment['status'] != 'submitted':
        return redirect('/admin')
    
    if request.method == 'POST':
        # Save final scores
        total_score = 0
        for i in range(15):  # 15 questions
            score = request.form.get(f'score_{i}', '0')
            try:
                final_score = int(score)
                assignment['final_scores'][str(i)] = final_score
                total_score += final_score
            except:
                pass
        
        assignment['total_score'] = total_score
        assignment['scored_by'] = session['username']
        assignment['scored_date'] = datetime.now().isoformat()
        assignment['status'] = 'under_review'
        
        return redirect('/admin')
    
    # Calculate auto-scores if not done
    if not assignment.get('auto_scores'):
        for i, question in enumerate(assignment['questions']):
            answer = assignment.get('answers', {}).get(str(i), '')
            assignment['auto_scores'][str(i)] = calculate_auto_score(answer, assignment['topic'], i, assignment['engineer_id'])
    
    # Show review form
    html = get_base_html() + f'''
        <div class="header">
            <div class="header-content">
                <div class="logo-section">
                    <div class="logo"></div>
                    <h1>Review Assignment</h1>
                </div>
                <div class="user-info">
                    <span style="color: #64B5F6;">Assignment: {assignment_id}</span>
                </div>
            </div>
        </div>
        
        <div class="container">
            <div class="card">
                <h3>Engineer: {assignment["engineer_id"]} | Topic: {assignment["topic"].title()}</h3>
                
                <div class="rubric">
                    <strong>Scoring Rubric:</strong><br>
    '''
    
    for score, desc in SCORING_RUBRIC.items():
        html += f'{score}: {desc}<br>'
    
    html += '''
                </div>
                
                <form method="POST">
    '''
    
    for i, question in enumerate(assignment['questions']):
        answer = assignment.get('answers', {}).get(str(i), 'No answer provided')
        auto_score = assignment.get('auto_scores', {}).get(str(i), 0)
        
        html += f'''
            <div class="question">
                <strong>Q{i+1}:</strong> {question}
                <div class="answer-box">
                    <strong>Student's Answer:</strong><br>
                    {answer}
                </div>
                <div class="score-box">
                    <div class="auto-score">
                        Auto-score (Keywords): {auto_score}/10
                    </div>
                    <div>
                        <label>Final Score (0-10):</label>
                        <input type="number" name="score_{i}" min="0" max="10" value="{auto_score}" style="width: 60px;">
                    </div>
                </div>
            </div>
        '''
    
    html += '''
                    <button type="submit" style="margin-top: 20px;">Save Scores (Next: Publish)</button>
                    <a href="/admin"><button type="button">Cancel</button></a>
                </form>
            </div>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/admin/publish/<assignment_id>')
def admin_publish(assignment_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect('/login')
    
    assignment = assignments.get(assignment_id)
    if not assignment or assignment['status'] != 'under_review':
        return redirect('/admin')
    
    # Publish the assignment
    assignment['status'] = 'published'
    assignment['published_date'] = datetime.now().isoformat()
    
    # Notify student
    engineer_id = assignment['engineer_id']
    if engineer_id not in notifications:
        notifications[engineer_id] = []
    
    notifications[engineer_id].append({
        'title': f'{assignment["topic"].title()} Assignment Scored',
        'message': f'Your assignment has been evaluated. Score: {assignment["total_score"]}/150',
        'created_at': datetime.now().isoformat()
    })
    
    return redirect('/admin')

@app.route('/student')
def student_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    my_assignments = [a for a in assignments.values() if a['engineer_id'] == user_id]
    my_notifications = notifications.get(user_id, [])[-5:]
    
    html = get_base_html() + f'''
        <div class="header">
            <div class="header-content">
                <div class="logo-section">
                    <div class="logo"></div>
                    <h1>Student Dashboard</h1>
                </div>
                <div class="user-info">
                    <span style="color: #64B5F6;">{session["username"]} • 3+ Years Experience</span>
                    <a href="/logout" class="logout-btn">LOGOUT</a>
                </div>
            </div>
        </div>
        
        <div class="container">
    '''
    
    if my_notifications:
        html += '<div class="card"><h2>Notifications</h2>'
        for n in my_notifications:
            html += f'<p><strong>{n["title"]}</strong><br>{n["message"]}<br><small>{n["created_at"][:16]}</small></p>'
        html += '</div>'
    
    html += '<h2>My Assignments</h2>'
    
    if my_assignments:
        for a in my_assignments:
            html += f'''
                <div class="card">
                    <h3>{a["topic"].title()} Assignment 
                        <span class="badge badge-{a["status"]}">{a["status"]}</span>
                    </h3>
                    <p>Due: {a["due_date"][:10]}</p>
            '''
            
            if a['status'] == 'published':
                html += f'<p><strong>Score: {a["total_score"]}/150</strong> (Scored by: {a.get("scored_by", "Admin")})</p>'
                html += f'<a href="/student/assignment/{a["id"]}"><button>View Results</button></a>'
            elif a['status'] in ['submitted', 'under_review']:
                html += '<p>Your submission is being reviewed...</p>'
            else:
                html += f'<a href="/student/assignment/{a["id"]}"><button>Answer Questions</button></a>'
            
            html += '</div>'
    else:
        html += '<div class="card"><p>No assignments yet.</p></div>'
    
    html += '''
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/student/assignment/<assignment_id>', methods=['GET', 'POST'])
def student_assignment(assignment_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    assignment = assignments.get(assignment_id)
    if not assignment or assignment['engineer_id'] != session['user_id']:
        return redirect('/student')
    
    if request.method == 'POST' and assignment['status'] == 'pending':
        # Save answers
        answers = {}
        for i in range(15):  # 15 questions
            answer = request.form.get(f'answer_{i}', '').strip()
            if answer:
                answers[str(i)] = answer
        
        if len(answers) == 15:  # All questions answered
            assignment['answers'] = answers
            assignment['status'] = 'submitted'
            
            # Calculate auto-scores
            for i in range(15):
                answer = answers.get(str(i), '')
                assignment['auto_scores'][str(i)] = calculate_auto_score(answer, assignment['topic'], i, engineer_id)
        
        return redirect('/student')
    
    # Show assignment
    html = get_base_html() + f'''
        <div class="header">
            <div class="header-content">
                <div class="logo-section">
                    <div class="logo"></div>
                    <h1>{assignment["topic"].title()} Assignment</h1>
                </div>
                <div class="user-info">
                    <span style="color: #64B5F6;">Due: {assignment["due_date"][:10]}</span>
                </div>
            </div>
        </div>
        
        <div class="container">
            <div class="card">
                <p>Status: <span class="badge badge-{assignment["status"]}">{assignment["status"]}</span> | Due: {assignment["due_date"][:10]}</p>
    '''
    
    if assignment['status'] == 'published':
        html += f'<p><strong>Total Score: {assignment["total_score"]}/150</strong></p>'
    
    if assignment['status'] == 'pending':
        html += '<form method="POST">'
    
    for i, question in enumerate(assignment['questions']):
        html += f'''
            <div class="question">
                <strong>Q{i+1}:</strong> {question}
        '''
        
        if assignment['status'] == 'pending':
            html += f'''
                <div class="answer-box">
                    <textarea name="answer_{i}" placeholder="Type your answer here..." required></textarea>
                </div>
            '''
        elif assignment['status'] in ['submitted', 'under_review', 'published']:
            answer = assignment.get('answers', {}).get(str(i), '')
            html += f'''
                <div class="answer-box">
                    <strong>Your Answer:</strong><br>
                    {answer}
                </div>
            '''
            
            if assignment['status'] == 'published':
                final_score = assignment.get('final_scores', {}).get(str(i), 0)
                html += f'<p><strong>Score: {final_score}/10</strong></p>'
        
        html += '</div>'
    
    if assignment['status'] == 'pending':
        html += '''
            <button type="submit" style="margin-top: 20px;">Submit All Answers</button>
            </form>
        '''
    
    html += '''
                <a href="/student"><button type="button">Back to Dashboard</button></a>
            </div>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'users': len(users), 'assignments': len(assignments)})

# Initialize
init_users()

# Create demo assignment
if len(assignments) == 0:
    create_assignment('eng001', 'floorplanning')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
