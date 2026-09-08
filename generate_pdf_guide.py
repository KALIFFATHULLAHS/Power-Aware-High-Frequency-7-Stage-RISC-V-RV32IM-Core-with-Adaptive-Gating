import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and render total page numbers,
    running headers, and running footers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            # First page cover styling header/footer skipped
            return
        
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#4A5568"))
        
        # Header
        self.drawString(54, 11 * 72 - 36, "RISC-V RV32IM CORE — TECHNICAL INTERVIEW & ARCHITECTURE MASTERCLASS")
        self.setStrokeColor(colors.HexColor("#CBD5E0"))
        self.setLineWidth(0.75)
        self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)
        
        # Footer
        self.setFont("Helvetica", 8)
        self.line(54, 48, 8.5 * 72 - 54, 48)
        self.drawString(54, 34, "CONFIDENTIAL & PROPRIETARY — POWER-AWARE HIGH-FREQUENCY CORE STUDY GUIDE")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * 72 - 54, 34, page_str)
        self.restoreState()

def create_pdf(filename="RISC_V_RV32IM_Core_Interview_Guide.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY = colors.HexColor("#0F2942")     # Deep Navy
    SECONDARY = colors.HexColor("#1D63B8")   # Royal Blue
    ACCENT = colors.HexColor("#D97706")      # Amber Gold
    DARK_TEXT = colors.HexColor("#1F2937")   # Charcoal Text
    LIGHT_BG = colors.HexColor("#F8FAFC")    # Cool Grey Background
    BORDER_COLOR = colors.HexColor("#E2E8F0")# Light Border
    CODE_BG = colors.HexColor("#0F172A")     # Slate Dark for Code
    CODE_TEXT = colors.HexColor("#38BDF8")   # Cyan Code Text
    CALLOUT_BG = colors.HexColor("#FEF3C7")  # Warm Light Yellow Callout
    CALLOUT_BORDER = colors.HexColor("#F59E0B")

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=30,
        textColor=PRIMARY,
        alignment=0,
        spaceAfter=12
    )

    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=SECONDARY,
        spaceAfter=16
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=PRIMARY,
        spaceBefore=16,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=SECONDARY,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'Heading3_Custom',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=DARK_TEXT,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13.5,
        textColor=DARK_TEXT,
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=7.5,
        leading=10.5,
        textColor=CODE_TEXT,
        backColor=CODE_BG,
        borderColor=colors.HexColor("#334155"),
        borderWidth=1,
        borderPadding=6,
        spaceAfter=8,
        spaceBefore=6
    )

    callout_style = ParagraphStyle(
        'Callout_Custom',
        parent=body_style,
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=13,
        textColor=colors.HexColor("#78350F"),
        backColor=CALLOUT_BG,
        borderColor=CALLOUT_BORDER,
        borderWidth=1,
        borderPadding=8,
        spaceBefore=8,
        spaceAfter=10
    )

    q_title_style = ParagraphStyle(
        'QTitle_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=PRIMARY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    a_body_style = ParagraphStyle(
        'ABody_Custom',
        parent=body_style,
        fontSize=8.5,
        leading=13,
        textColor=DARK_TEXT,
        spaceAfter=8
    )

    story = []

    # =========================================================================
    # COVER PAGE / TITLE BANNER
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("POWER-AWARE HIGH-FREQUENCY 7-STAGE RISC-V RV32IM CORE WITH ADAPTIVE GATING", title_style))
    story.append(Paragraph("Complete RTL Microarchitecture Analysis, FPGA Power Synthesis Breakdown & Staff-Level Interview Preparation Guide", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2.5, color=PRIMARY, spaceBefore=0, spaceAfter=12))

    # Meta Table
    meta_data = [
        [Paragraph("<b>Target Architecture:</b> RISC-V RV32IM", body_style), Paragraph("<b>Target Device:</b> Xilinx 7-Series FPGA (XC7A100T)", body_style)],
        [Paragraph("<b>Pipeline Depth:</b> 7 Stages (IF1-IF2-ID-EX1-EX2-MEM-WB)", body_style), Paragraph("<b>Clock Management:</b> MMCM (50 MHz) + 12x BUFGCE Gated Clocks", body_style)],
        [Paragraph("<b>Power Savings:</b> Dynamic Stage Gating + WFI Sleep + Approx ALU", body_style), Paragraph("<b>Synthesis Results:</b> 0.251 W Total Power (0.153 W Dynamic)", body_style)],
    ]
    t_meta = Table(meta_data, colWidths=[250, 250])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 12))

    # Executive Overview
    story.append(Paragraph("Executive Summary & Core Value Proposition", h2_style))
    story.append(Paragraph(
        "This project implements an advanced, industrial-grade 32-bit RISC-V processor core optimized for low-power high-frequency execution on Xilinx 7-Series FPGAs. "
        "By extending traditional 5-stage classic RISC pipelines to a deeply pipelined <b>7-stage microarchitecture</b> (split instruction fetch IF1/IF2 and dual execution stages EX1/EX2), "
        "the core achieves higher maximum operating frequencies (Fmax) while maintaining low dynamic power through central dynamic clock gating using hardware <code>BUFGCE</code> buffers, "
        "Wait-For-Interrupt (WFI) sleep shutdown, and an energy-saving Approximate Arithmetic mode.", body_style
    ))
    story.append(Spacer(1, 8))

    # Table of Contents Summary
    story.append(Paragraph("Guide Table of Contents", h2_style))
    toc_data = [
        [Paragraph("<b>Chapter</b>", h3_style), Paragraph("<b>Technical Scope & Focus Areas</b>", h3_style)],
        [Paragraph("Chapter 1", body_style), Paragraph("Executive Summary & System Architecture Specifications", body_style)],
        [Paragraph("Chapter 2", body_style), Paragraph("7-Stage Deep Pipeline Microarchitecture & Signal Flow", body_style)],
        [Paragraph("Chapter 3", body_style), Paragraph("Adaptive Stage Clock Gating & FPGA Power Management", body_style)],
        [Paragraph("Chapter 4", body_style), Paragraph("Approximate Arithmetic Unit (4-LSB Operand Truncation)", body_style)],
        [Paragraph("Chapter 5", body_style), Paragraph("Pipeline Hazard Resolution, Stalls & Forwarding Network", body_style)],
        [Paragraph("Chapter 6", body_style), Paragraph("Hardware Arithmetic Extensions (DSP Multiplier & Restoring Divider)", body_style)],
        [Paragraph("Chapter 7", body_style), Paragraph("Hardware Branch Prediction Unit (64-entry BHT + BTB Tag Match)", body_style)],
        [Paragraph("Chapter 8", body_style), Paragraph("Control & Status Register (CSR) Subsystem & Power Modes", body_style)],
        [Paragraph("Chapter 9", body_style), Paragraph("Dual-Port BRAM Memory System & UART In-Circuit Bootloader", body_style)],
        [Paragraph("Chapter 10", body_style), Paragraph("Masterclass Technical Interview Q&A (25 Model Answers)", body_style)],
    ]
    t_toc = Table(toc_data, colWidths=[80, 420])
    t_toc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 4.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG])
    ]))
    story.append(t_toc)

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 1: SYSTEM ARCHITECTURE SPECIFICATIONS
    # =========================================================================
    story.append(Paragraph("Chapter 1: Microarchitectural System Specifications", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("Key Microarchitectural Parameters", h2_style))
    spec_table_data = [
        [Paragraph("<b>Parameter</b>", h3_style), Paragraph("<b>Specification / Value</b>", h3_style), Paragraph("<b>Implementation Details</b>", h3_style)],
        [Paragraph("Instruction Set Architecture", body_style), Paragraph("RISC-V RV32IM + Custom CSRs", body_style), Paragraph("Base 32-bit Integer + M Extension (Mul/Div) + Power/Approx CSRs", body_style)],
        [Paragraph("Pipeline Depth", body_style), Paragraph("7 Stages", body_style), Paragraph("IF1 → IF2 → ID → EX1 → EX2 → MEM → WB", body_style)],
        [Paragraph("Target Frequency", body_style), Paragraph("50 MHz (20.0 ns period)", body_style), Paragraph("Generated via MMCME2_BASE primitive on Xilinx 7-Series", body_style)],
        [Paragraph("Branch Predictor", body_style), Paragraph("Dynamic BHT + BTB", body_style), Paragraph("64-entry 2-bit saturating counter array + 32-bit target & tag match", body_style)],
        [Paragraph("Multiplier Core", body_style), Paragraph("1-Cycle Combinational DSP", body_style), Paragraph("Maps to FPGA DSP48E1 slices ($signed, unsigned products)", body_style)],
        [Paragraph("Divider Core", body_style), Paragraph("32-Cycle Iterative Restoring", body_style), Paragraph("Sequenced state machine; holds pipeline stall via stall_ex2", body_style)],
        [Paragraph("Clock Gating Architecture", body_style), Paragraph("12 Gated Clock Domains", body_style), Paragraph("BUFGCE primitives controlled by stage_gating_controller & mpower CSR", body_style)],
        [Paragraph("Approximate Mode", body_style), Paragraph("4-LSB Truncated Addition", body_style), Paragraph("Enabled via mapprox CSR (0x800); reduces ALU switching power", body_style)],
        [Paragraph("Memory Architecture", body_style), Paragraph("16KB IMEM / 16KB DMEM", body_style), Paragraph("Dual-Port BRAM blocks with integrated UART bootloader at reset", body_style)],
        [Paragraph("MMIO Peripherals", body_style), Paragraph("UART TX & LED Array", body_style), Paragraph("Mapped at 0xFFFF0000 (UART TX byte) & 0xFFFF0004 (LED state)", body_style)]
    ]
    t_spec = Table(spec_table_data, colWidths=[120, 150, 230])
    t_spec.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 4.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG])
    ]))
    story.append(t_spec)
    story.append(Spacer(1, 8))

    story.append(Paragraph("FPGA Synthesis & Utilization Breakdown (XC7A100T-2FTG256C)", h2_style))
    story.append(Paragraph("The design has been synthesized and fully routed in Xilinx Vivado v2025.1. Total on-chip power is measured at <b>0.251 W</b> (0.153 W Dynamic, 0.098 W Static).", body_style))

    power_data = [
        [Paragraph("<b>Resource Type</b>", h3_style), Paragraph("<b>Used</b>", h3_style), Paragraph("<b>Available</b>", h3_style), Paragraph("<b>Utilization %</b>", h3_style), Paragraph("<b>Power Contribution</b>", h3_style)],
        [Paragraph("Slice LUTs (Logic)", body_style), Paragraph("3,767", body_style), Paragraph("63,400", body_style), Paragraph("5.94%", body_style), Paragraph("0.008 W", body_style)],
        [Paragraph("Slice Registers (FFs)", body_style), Paragraph("5,520", body_style), Paragraph("126,800", body_style), Paragraph("4.35%", body_style), Paragraph("< 0.001 W", body_style)],
        [Paragraph("Block RAM (RAMB36)", body_style), Paragraph("8", body_style), Paragraph("135", body_style), Paragraph("5.93%", body_style), Paragraph("0.009 W", body_style)],
        [Paragraph("DSP Slices (DSP48E1)", body_style), Paragraph("12", body_style), Paragraph("240", body_style), Paragraph("5.00%", body_style), Paragraph("0.005 W", body_style)],
        [Paragraph("Clocking (MMCME2)", body_style), Paragraph("1 MMCM", body_style), Paragraph("6", body_style), Paragraph("16.67%", body_style), Paragraph("0.105 W", body_style)],
        [Paragraph("Signals & Routing", body_style), Paragraph("8,827 nets", body_style), Paragraph("—", body_style), Paragraph("—", body_style), Paragraph("0.014 W", body_style)],
        [Paragraph("Gated Clock Trees", body_style), Paragraph("12 BUFGCE", body_style), Paragraph("32 BUFG", body_style), Paragraph("37.5%", body_style), Paragraph("0.012 W", body_style)],
    ]
    t_pow = Table(power_data, colWidths=[120, 70, 80, 90, 140])
    t_pow.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), SECONDARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG])
    ]))
    story.append(t_pow)

    story.append(Spacer(1, 8))

    # =========================================================================
    # CHAPTER 2: 7-STAGE PIPELINE MICROARCHITECTURE
    # =========================================================================
    story.append(Paragraph("Chapter 2: 7-Stage Deep Pipeline Architecture", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("Why a 7-Stage Pipeline?", h2_style))
    story.append(Paragraph(
        "Standard 5-stage RISC-V processors combine instruction fetch into 1 cycle and execution into 1 cycle. "
        "In modern high-frequency FPGA designs, BRAM address-to-data read latency and complex multi-operand ALU/branch calculations create critical path bottlenecks. "
        "This architecture splits fetch into <b>IF1</b> and <b>IF2</b>, and splits execution into <b>EX1</b> (branch resolution & target calculation) and <b>EX2</b> (ALU, CSR, Multiplication, Division).", body_style
    ))

    pipeline_stages_data = [
        [Paragraph("<b>Stage</b>", h3_style), Paragraph("<b>Module Name</b>", h3_style), Paragraph("<b>Key Functions & Operations Performed</b>", h3_style)],
        [Paragraph("<b>1. IF1</b><br/>Fetch 1", body_style), Paragraph("<code>if1.v</code>", body_style), Paragraph("Program Counter (PC) register update, speculative next-PC target selection, BHT/BTB branch predictor lookup, output BRAM read address.", body_style)],
        [Paragraph("<b>2. IF2</b><br/>Fetch 2", body_style), Paragraph("<code>if2.v</code>", body_style), Paragraph("Registers 32-bit instruction returned from synchronous Dual-Port BRAM (imem). Holds instruction during IF stalls and pipeline flushes.", body_style)],
        [Paragraph("<b>3. ID</b><br/>Decode", body_style), Paragraph("<code>id.v</code>", body_style), Paragraph("Decodes RISC-V opcode, funct3, funct7. Generates 24-bit control bus. Reads GPR registers rs1/rs2. Generates immediates. Asserts stage gating class flags.", body_style)],
        [Paragraph("<b>4. EX1</b><br/>Execute 1", body_style), Paragraph("<code>ex1.v</code>", body_style), Paragraph("Receives forwarded operands. Computes branch condition and jump target (JAL/JALR). Compares predicted PC with actual target to trigger 2-cycle mispredict flush. Starts MUL/DIV pulses.", body_style)],
        [Paragraph("<b>5. EX2</b><br/>Execute 2", body_style), Paragraph("<code>ex2.v</code>", body_style), Paragraph("Executes exact or 4-LSB approximate ALU ops, DSP 32x32 multiplication, multi-cycle division, CSR read/write access. Evaluates MMIO UART TX busy stalls.", body_style)],
        [Paragraph("<b>6. MEM</b><br/>Memory", body_style), Paragraph("<code>mem.v</code>", body_style), Paragraph("Drives Data BRAM (dmem). Packs store data and byte-enable strobes (SB, SH, SW). Performs sign-extension and zero-extension on loaded byte/halfword data (LB, LH, LW, LBU, LHU).", body_style)],
        [Paragraph("<b>7. WB</b><br/>Writeback", body_style), Paragraph("<code>wb.v</code>", body_style), Paragraph("Writes ALU or Load result back to General Purpose Register File (R1-R31). Detects <code>WFI</code> instruction to trigger low-power idle sleep state.", body_style)]
    ]
    t_pipe = Table(pipeline_stages_data, colWidths=[80, 80, 340])
    t_pipe.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 4.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG])
    ]))
    story.append(t_pipe)

    story.append(Spacer(1, 8))
    story.append(Paragraph("24-Bit Pipeline Control Bus Structure", h3_style))
    story.append(Paragraph(
        "Control signals generated in <code>id.v</code> travel down the pipeline inside a packed 24-bit bus <code>ctrl_bus[23:0]</code>:<br/>"
        "• <code>ctrl_bus[23]</code>: Is M-Extension instruction (MUL/DIV)<br/>"
        "• <code>ctrl_bus[22:20]</code>: Load/Store sub-type (funct3)<br/>"
        "• <code>ctrl_bus[19:16]</code>: M-Extension sub-type<br/>"
        "• <code>ctrl_bus[15]</code>: Register File Write Enable (reg_write)<br/>"
        "• <code>ctrl_bus[14]</code>: Data Memory Read Enable (mem_read)<br/>"
        "• <code>ctrl_bus[13]</code>: Data Memory Write Enable (mem_write)<br/>"
        "• <code>ctrl_bus[12]</code>: Is Branch instruction<br/>"
        "• <code>ctrl_bus[11]</code>: Is JAL Jump instruction<br/>"
        "• <code>ctrl_bus[10]</code>: Is JALR Indirect Jump instruction<br/>"
        "• <code>ctrl_bus[9]</code>: Is CSR Operation<br/>"
        "• <code>ctrl_bus[8]</code>: ALU Source B Select (0 = rs2, 1 = immediate)<br/>"
        "• <code>ctrl_bus[7:4]</code>: ALU Operation Select Code", body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 3: ADAPTIVE STAGE CLOCK GATING & POWER
    # =========================================================================
    story.append(Paragraph("Chapter 3: Adaptive Stage Clock Gating & Power Management", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("Dynamic Hardware Clock Tree Architecture", h2_style))
    story.append(Paragraph(
        "To achieve maximum power reduction without compromising timing performance, the core replaces global un-gated clocks with a dynamic 12-domain gated clock distribution tree. "
        "The module <code>stage_gating_controller.v</code> evaluates stage classification signals, hazard stalls, CSR power masks, and WFI states to generate individual stage clock enables <code>ce_if1...ce_wb</code>.", body_style
    ))

    story.append(Paragraph("Synthesis Gated Clock Buffer (BUFGCE Primitive)", h3_style))
    story.append(Paragraph(
        "In FPGA Synthesis mode (<code>`ifdef SYNTHESIS</code> inside <code>clock_manager.v</code>), clock enables are registered on the falling edge / rising edge of the MMCM clock and supplied directly to Xilinx <b>BUFGCE</b> primitives. "
        "This completely disables the clock tree toggle activity to unused pipeline registers and functional blocks.", body_style
    ))

    story.append(Paragraph("""
// Xilinx 7-Series BUFGCE Gated Clock Primitive Instantiation in clock_manager.v
BUFGCE #(.SIM_DEVICE("7SERIES")) buf_if1 (.I(clk_mmcm_out), .CE(ce_if1_r), .O(clk_if1));
BUFGCE #(.SIM_DEVICE("7SERIES")) buf_if2 (.I(clk_mmcm_out), .CE(ce_if2_r), .O(clk_if2));
BUFGCE #(.SIM_DEVICE("7SERIES")) buf_id  (.I(clk_mmcm_out), .CE(ce_id_r ), .O(clk_id ));
BUFGCE #(.SIM_DEVICE("7SERIES")) buf_ex1 (.I(clk_mmcm_out), .CE(ce_ex1_r), .O(clk_ex1));
BUFGCE #(.SIM_DEVICE("7SERIES")) buf_ex2 (.I(clk_mmcm_out), .CE(ce_ex2_r), .O(clk_ex2));
BUFGCE #(.SIM_DEVICE("7SERIES")) buf_mem (.I(clk_mmcm_out), .CE(ce_mem_r), .O(clk_mem));
BUFGCE #(.SIM_DEVICE("7SERIES")) buf_wb  (.I(clk_mmcm_out), .CE(ce_wb_r ), .O(clk_wb ));
    """, code_style))

    story.append(Paragraph("Simulation Glitch-Free Negative-Latch Integrated Clock Gating (ICG)", h3_style))
    story.append(Paragraph(
        "Standard RTL AND-gating (<code>clk & ce</code>) causes dangerous clock glitches if <code>ce</code> changes while <code>clk</code> is HIGH. "
        "In RTL Behavioral Simulation mode (<code>`ifndef SYNTHESIS</code>), <code>clock_manager.v</code> models a negative-level latch ICG circuit. "
        "The clock enable signal is sampled only when <code>clk_in</code> is LOW, guaranteeing zero glitching on gated clock outputs.", body_style
    ))

    story.append(Paragraph("""
// Glitch-Free Negative-Latch ICG Model for RTL Simulation (clock_manager.v)
reg ce_if1_latch, ce_if2_latch, ce_id_latch, ce_ex1_latch, ce_ex2_latch;

always @(*) begin
    if (!clk_in) begin  // Transparent ONLY during low half-cycle of clock
        ce_if1_latch = ce_if1;
        ce_if2_latch = ce_if2;
        ce_id_latch  = ce_id;
        ce_ex1_latch = ce_ex1;
        ce_ex2_latch = ce_ex2;
    end
end
assign clk_if1 = clk_in & ce_if1_latch; // Zero-glitch output clock
    """, code_style))

    story.append(Paragraph("Wait-For-Interrupt (WFI) Deep Idle Shutdown", h2_style))
    story.append(Paragraph(
        "When the core executes a <code>wfi</code> instruction (SYSTEM opcode <code>0x73</code> with imm <code>0x105</code>), the writeback stage asserts <code>wfi_active = 1</code>. "
        "The stage gating controller immediately forces <code>ce_if1 = ce_if2 = ce_id = ce_ex1 = ce_ex2 = ce_mem = ce_wb = 0</code>, turning off all pipeline clocks. "
        "Only <code>clk_csr</code> remains active to allow external hardware interrupts or system reset to wake the processor.", body_style
    ))

    story.append(Spacer(1, 8))

    # =========================================================================
    # CHAPTER 4: APPROXIMATE ARITHMETIC UNIT
    # =========================================================================
    story.append(Paragraph("Chapter 4: Energy-Efficient Approximate Arithmetic Unit", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("4-LSB Truncated Arithmetic Logic Architecture", h2_style))
    story.append(Paragraph(
        "For error-tolerant workloads such as quantum-inspired QUBO optimization, image processing, neural network inference, and matrix operations, exact 32-bit addition produces unnecessary carry-propagation switching power in lower bits. "
        "The core implements a hardware-selectable Approximate Arithmetic Mode controlled by the custom CSR <code>mapprox</code> (Address <code>0x800</code>).", body_style
    ))

    story.append(Paragraph("""
// Exact vs Approximate ALU Logic in ex2.v
// 1. Exact ALU Addition
alu_exact = ex2_op_a_in + ex2_op_b_in;

// 2. Approximate ALU Addition (Truncating 4 LSBs to zero)
alu_approx = { (ex2_op_a_in[31:4] + ex2_op_b_in[31:4]), 4'b0000 };

// 3. Mode Multiplexing based on mapprox CSR bit 0
wire [31:0] alu_final = (approx_enable && !ex2_ctrl_bus_in[8]) ? alu_approx : alu_exact;
    """, code_style))

    story.append(Paragraph("Error Analysis & Power Savings Trade-Off", h3_style))
    story.append(Paragraph(
        "<b>Mathematical Error Bound:</b> The maximum absolute error introduced by truncating 4 LSBs during addition is <code>2^4 - 1 = 15</code>. "
        "For 32-bit values exceeding 1,000,000, the relative computational error is under <b>0.0015%</b>.<br/>"
        "<b>Dynamic Power Impact:</b> Eliminating carry propagation across bits [3:0] reduces net switching activity in the internal CARRY4 primitives by up to <b>18%</b> during continuous arithmetic loop execution.", body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 5: HAZARD RESOLUTION & FORWARDING
    # =========================================================================
    story.append(Paragraph("Chapter 5: Hazard Resolution & Forwarding Network", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("Pipeline Hazard Classification & Handling Strategy", h2_style))
    story.append(Paragraph(
        "Because the pipeline is 7 stages deep, data dependency penalties could be severe without aggressive forwarding. "
        "The core integrates a centralized <code>hazard_unit.v</code> and <code>forwarding_unit.v</code> to maintain maximum throughput.", body_style
    ))

    hazard_summary_data = [
        [Paragraph("<b>Hazard Type</b>", h3_style), Paragraph("<b>Detection Condition</b>", h3_style), Paragraph("<b>Pipeline Resolution Mechanism</b>", h3_style), Paragraph("<b>Penalty</b>", h3_style)],
        [Paragraph("RAW Data Hazard (ALU → ALU)", body_style), Paragraph("ID rs1/rs2 matches EX2_rd, MEM_rd, or WB_rd", body_style), Paragraph("Forwarding network bypasses result directly to EX1 operands in 0 cycles.", body_style), Paragraph("0 Cycles (No Stall)", body_style)],
        [Paragraph("RAW Load-Use Hazard", body_style), Paragraph("Instruction in EX1/EX2/MEM is LOAD and rd matches ID rs1/rs2", body_style), Paragraph("Hazard unit stalls IF1, IF2, ID, and EX1 for 1 cycle until data loaded from BRAM.", body_style), Paragraph("1 Cycle Stall", body_style)],
        [Paragraph("Multi-cycle DIV Structural Hazard", body_style), Paragraph("Iterative divider active (<code>div_busy = 1</code>)", body_style), Paragraph("Holds <code>stall_ex2 = 1</code>, freezing IF1, IF2, ID, EX1 registers for 32 cycles.", body_style), Paragraph("32 Cycles Stall", body_style)],
        [Paragraph("Branch Misprediction Hazard", body_style), Paragraph("EX1 actual branch result ≠ predicted PC in IF1", body_style), Paragraph("Asserts <code>flush_id = 1</code> and <code>flush_ex1 = 1</code>. Redirects IF1 PC to correct target.", body_style), Paragraph("2 Cycle Flush", body_style)]
    ]
    t_haz = Table(hazard_summary_data, colWidths=[100, 150, 180, 70])
    t_haz.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 4.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG])
    ]))
    story.append(t_haz)

    story.append(Spacer(1, 8))
    story.append(Paragraph("4-Level Priority Forwarding Network Matrix", h2_style))
    story.append(Paragraph(
        "Forwarding is evaluated combinationally in <code>forwarding_unit.v</code> for both operand 1 (<code>rs1</code>) and operand 2 (<code>rs2</code>) with strict age priority (newest pipeline stage first):", body_style
    ))

    story.append(Paragraph("""
// Operands Forwarding Logic (forwarding_unit.v)
if (ex2_valid && ex2_rd != 0 && ex2_rd == id_rs1)
    fwd_rs1_val = ex2_result;                  // Priority 1: EX2 Stage Bypass
else if (mem_valid && mem_rd != 0 && mem_rd == id_rs1)
    fwd_rs1_val = mem_result;                  // Priority 2: MEM Stage Bypass
else if (wb_valid && wb_rd != 0 && wb_rd == id_rs1)
    fwd_rs1_val = wb_result;                   // Priority 3: WB Stage Bypass
else if (rf_we && rf_waddr != 0 && rf_waddr == id_rs1)
    fwd_rs1_val = rf_wdata;                    // Priority 4: RF Write Port Bypass
else
    fwd_rs1_val = original_rs1;                // Default: Register File Async Read
    """, code_style))

    story.append(Spacer(1, 8))

    # =========================================================================
    # CHAPTER 6: ARITHMETIC HARDWARE EXTENSIONS (MUL / DIV)
    # =========================================================================
    story.append(Paragraph("Chapter 6: Hardware Arithmetic Extensions (RV32M)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("DSP-Optimized Hardware Multiplier (mul_unit.v)", h2_style))
    story.append(Paragraph(
        "The multiplier unit implements full 32-bit x 32-bit multiplication producing a 64-bit full product. "
        "By utilizing Verilog signed multiplication operators (<code>$signed(op_a) * $signed(op_b)</code>), Xilinx Vivado infers dedicated <b>DSP48E1 hard slices</b>. "
        "Multiplication executes combinationally within the EX2 stage (busy = 0), introducing zero stall cycles.", body_style
    ))

    story.append(Paragraph("32-Cycle Iterative Restoring Divider (div_unit.v)", h2_style))
    story.append(Paragraph(
        "Division cannot be efficiently completed in a single high-frequency clock cycle without massive delay penalties. "
        "The core implements a 32-cycle sequential radix-2 restoring division algorithm:<br/>"
        "1. <b>Start Phase:</b> EX1 issues <code>div_start</code> pulse. Divider captures dividend/divisor and computes absolute values for signed operations (<code>DIV</code>, <code>REM</code>).<br/>"
        "2. <b>Compute Phase:</b> Over 32 clock cycles, <code>dividend[62:31]</code> is compared against <code>divisor</code>. If greater, subtraction occurs and quotient bit 1 is shifted in.<br/>"
        "3. <b>Completion Phase:</b> Quotient or remainder sign corrections are applied based on operand original sign bits (<code>neg_q = op_a[31] ^ op_b[31]</code>, <code>neg_r = op_a[31]</code>).", body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 7: BRANCH PREDICTION UNIT
    # =========================================================================
    story.append(Paragraph("Chapter 7: Hardware Branch Prediction Unit (BPU)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("BHT + BTB + Tag Matching Architecture", h2_style))
    story.append(Paragraph(
        "Branch instruction execution penalties in deep 7-stage pipelines can severely impact CPI (Cycles Per Instruction). "
        "The core incorporates a hardware <b>Branch Prediction Unit (BPU)</b> in <code>branch_predictor.v</code> that runs speculatively during the IF1 stage.", body_style
    ))

    bpu_table_data = [
        [Paragraph("<b>BPU Component</b>", h3_style), Paragraph("<b>Structure & Size</b>", h3_style), Paragraph("<b>Functional Description</b>", h3_style)],
        [Paragraph("Branch History Table (BHT)", body_style), Paragraph("64 Entries x 2-bit", body_style), Paragraph("2-bit Saturating Counter State Machine (00: Strongly Not Taken, 01: Weakly Not Taken, 10: Weakly Taken, 11: Strongly Taken).", body_style)],
        [Paragraph("Branch Target Buffer (BTB)", body_style), Paragraph("64 Entries x 32-bit", body_style), Paragraph("Stores the target branch address computed during previous executions of the branch.", body_style)],
        [Paragraph("Tag Comparison Array", body_style), Paragraph("64 Entries x 32-bit", body_style), Paragraph("Stores full PC tag address to ensure BTB hits only occur for exact matching branch instruction addresses.", body_style)]
    ]
    t_bpu = Table(bpu_table_data, colWidths=[130, 110, 260])
    t_bpu.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 4.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG])
    ]))
    story.append(t_bpu)

    story.append(Spacer(1, 8))

    # =========================================================================
    # CHAPTER 8: CONTROL & STATUS REGISTERS (CSR)
    # =========================================================================
    story.append(Paragraph("Chapter 8: Control & Status Register (CSR) Subsystem", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("CSR Address Map & Privilege Architecture", h2_style))
    story.append(Paragraph(
        "The module <code>csr_unit.v</code> handles machine-mode performance counters and custom power-management registers. "
        "CSR operations support <code>CSRRW</code> (Atomic Read/Write), <code>CSRRS</code> (Atomic Read & Set Bits), and <code>CSRRC</code> (Atomic Read & Clear Bits).", body_style
    ))

    csr_table_data = [
        [Paragraph("<b>CSR Address</b>", h3_style), Paragraph("<b>CSR Name</b>", h3_style), Paragraph("<b>Access</b>", h3_style), Paragraph("<b>Description & Power Control Function</b>", h3_style)],
        [Paragraph("<code>0xC00</code>", body_style), Paragraph("<code>mcycle</code>", body_style), Paragraph("Read-Only", body_style), Paragraph("Lower 32 bits of 64-bit cycle counter (increments every active clock cycle).", body_style)],
        [Paragraph("<code>0xC80</code>", body_style), Paragraph("<code>mcycleh</code>", body_style), Paragraph("Read-Only", body_style), Paragraph("Upper 32 bits of 64-bit cycle counter.", body_style)],
        [Paragraph("<code>0xC02</code>", body_style), Paragraph("<code>minstret</code>", body_style), Paragraph("Read-Only", body_style), Paragraph("Lower 32 bits of 64-bit retired instruction counter (increments on WB valid).", body_style)],
        [Paragraph("<code>0xC82</code>", body_style), Paragraph("<code>minstreth</code>", body_style), Paragraph("Read-Only", body_style), Paragraph("Upper 32 bits of 64-bit retired instruction counter.", body_style)],
        [Paragraph("<code>0x800</code>", body_style), Paragraph("<code>mapprox</code>", body_style), Paragraph("Read/Write", body_style), Paragraph("Custom Approx Register. Bit [0] = 1 enables 4-LSB ALU truncation mode.", body_style)],
        [Paragraph("<code>0x801</code>", body_style), Paragraph("<code>mpower</code>", body_style), Paragraph("Read/Write", body_style), Paragraph("Custom Power Gating Register. 8-bit mask enabling stage clocks [6:0] and UART [7]. Default 0xFF.", body_style)]
    ]
    t_csr = Table(csr_table_data, colWidths=[70, 70, 70, 290])
    t_csr.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), SECONDARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 4.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG])
    ]))
    story.append(t_csr)

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 9: MEMORY LAYOUT & UART BOOTLOADER
    # =========================================================================
    story.append(Paragraph("Chapter 9: Memory Layout & UART In-Circuit Bootloader", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("System Memory Address Map", h2_style))
    mem_map_data = [
        [Paragraph("<b>Address Range</b>", h3_style), Paragraph("<b>Target Device / Peripheral</b>", h3_style), Paragraph("<b>Access Type</b>", h3_style), Paragraph("<b>Description</b>", h3_style)],
        [Paragraph("<code>0x0000_0000 - 0x0000_3FFF</code>", body_style), Paragraph("Instruction BRAM (IMEM)", body_style), Paragraph("Read-Only (CPU)<br/>Write (UART Loader)", body_style), Paragraph("16KB Dual-Port Block RAM. Holds application binary instructions.", body_style)],
        [Paragraph("<code>0x0000_4000 - 0x0000_7FFF</code>", body_style), Paragraph("Data BRAM (DMEM)", body_style), Paragraph("Read / Write", body_style), Paragraph("16KB Dual-Port Block RAM. Holds application stack, heap, and static data.", body_style)],
        [Paragraph("<code>0xFFFF_0000</code>", body_style), Paragraph("MMIO UART TX Register", body_style), Paragraph("Write-Only", body_style), Paragraph("Writing a byte to this address transmits serial character over UART pin at 115200 Baud.", body_style)],
        [Paragraph("<code>0xFFFF_0004</code>", body_style), Paragraph("MMIO LED Output Register", body_style), Paragraph("Write-Only", body_style), Paragraph("Writing an 8-bit value directly updates physical FPGA LED pin state.", body_style)]
    ]
    t_mmap = Table(mem_map_data, colWidths=[120, 110, 90, 180])
    t_mmap.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 4.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG])
    ]))
    story.append(t_mmap)

    story.append(Spacer(1, 8))
    story.append(Paragraph("UART Hardware Bootloader Protocol (bram_imem.v)", h2_style))
    story.append(Paragraph(
        "To allow rapid application binary deployment on physical FPGA hardware without triggering lengthy Vivado synthesis runs, "
        "the instruction memory module <code>bram_imem.v</code> integrates an in-circuit UART bootloader.<br/>"
        "• <b>Active Reset Mode:</b> When physical reset button <code>M14</code> is pressed, the CPU is held in reset, while <code>u_rx</code> listens on the serial port (115200 Baud).<br/>"
        "• <b>Word Reassembly:</b> Bytes arrive Little-Endian. Once 4 bytes arrive (<code>byte_cnt == 3</code>), a complete 32-bit RISC-V instruction word is written into <code>mem[load_addr]</code>.<br/>"
        "• <b>Execution Handover:</b> Upon releasing button <code>M14</code>, the core begins fetching instructions from address <code>0x00000000</code>.", body_style
    ))

    story.append(Spacer(1, 8))

    # =========================================================================
    # CHAPTER 10: MASTERCLASS INTERVIEW Q&A (25 QUESTIONS)
    # =========================================================================
    story.append(Paragraph("Chapter 10: Masterclass Technical Interview Questions & Answers", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=2, spaceAfter=8))
    story.append(Paragraph("This chapter presents 25 deep technical interview questions covering RTL microarchitecture, FPGA synthesis, timing analysis, hazard handling, power optimization, and debugging.", body_style))
    story.append(Spacer(1, 6))

    qa_list = [
        ("Q1: Why did you choose a 7-stage pipeline instead of the classic 5-stage RISC-V pipeline?",
         "In FPGA implementations (such as Xilinx 7-Series), Block RAM memory access requires a clock cycle for address-to-data output latency. A 5-stage pipeline forces instruction memory read and decode into a tight cycle, limiting maximum operating frequency. By splitting Fetch into IF1 (address generation & BPU lookup) and IF2 (BRAM data register), and splitting Execution into EX1 (branch target/condition calculation) and EX2 (ALU/MUL/DIV), we significantly shorten the critical path, enabling a 50 MHz+ target Fmax."),

        ("Q2: How does dynamic stage clock gating work in your verilog design, and why is BUFGCE required on Xilinx FPGAs?",
         "Central stage clock gating is managed by stage_gating_controller.v and clock_manager.v. On Xilinx FPGAs, simply using combinational logic (clk & enable) causes clock skew, glitching, and violates global clock routing constraints. We instantiate 12 BUFGCE primitives (gated global clock buffers). The stage_gating_controller outputs enable signals (ce_if1..ce_wb) which are registered on clk_mmcm_out to drive BUFGCE primitives cleanly, toggling clock trees off when pipeline stages are idle or masked out by the mpower CSR."),

        ("Q3: How do you prevent clock glitches during behavioral simulation when BUFGCE primitives are bypassed?",
         "In simulation mode (`ifndef SYNTHESIS`), clock_manager.v models a glitch-free Negative-Latch Integrated Clock Gating (ICG) circuit. It latches the stage enable signal during the LOW half-cycle of clk_in (if (!clk_in)). This guarantees that enable transitions never occur while the clock line is HIGH, completely eliminating artificial clock glitches in Icarus Verilog or Vivado XSIM."),

        ("Q4: What happens during a Wait-For-Interrupt (WFI) instruction, and how does the core wake up?",
         "When a WFI instruction (opcode 0x73, imm 0x105) reaches the Writeback (WB) stage, wb.v asserts wfi_active = 1. The stage gating controller detects wfi_active and immediately deasserts ce_if1 through ce_wb, turning off all 7 pipeline stage clocks. Dynamic core power drops to near zero. Only clk_csr remains active so that an incoming external hardware interrupt or system reset can clear wfi_active and resume clocking."),

        ("Q5: Explain the Approximate Arithmetic Mode and its impact on computational power and precision.",
         "The custom CSR mapprox (0x800) bit 0 enables approximate addition in EX2 (ex2.v). Instead of exact 32-bit addition, the ALU calculates alu_approx = { (op_a[31:4] + op_b[31:4]), 4'b0000 }, truncating the 4 least significant bits. This reduces switching activity in lower CARRY4 FPGA primitives by up to 18%. For noise-tolerant tasks like QUBO quantum stress loops or image processing, the maximum absolute error is bounded by 15, yielding a negligible relative error (<0.0015%)."),

        ("Q6: How does your core handle RAW (Read-After-Write) data hazards without introducing unnecessary stall cycles?",
         "RAW hazards are resolved in 0 stall cycles using a 4-level priority forwarding network in forwarding_unit.v. Forwarded values are combinationally bypassed to EX1 operands (fwd_rs1_val / fwd_rs2_val) from EX2 result, MEM result, WB result, or RF write port in order of priority. Only Load-Use dependencies require a 1-cycle stall because memory load data is not ready until the MEM stage."),

        ("Q7: How is a Load-Use hazard detected and resolved in your hazard unit?",
         "A Load-Use hazard occurs when an instruction in EX1, EX2, or MEM is a LOAD (mem_read = 1) and its destination register rd matches rs1 or rs2 of the instruction currently in ID. hazard_unit.v detects this condition and asserts stall_if = 1, stall_id = 1, and stall_ex1 = 1 for 1 cycle. This freezes the front pipeline while inserting a bubble into EX2."),

        ("Q8: Describe the operation of your 32-cycle iterative restoring hardware divider (div_unit.v).",
         "The hardware divider uses a sequential radix-2 restoring division algorithm. When EX1 detects a DIV/REM opcode, it issues a 1-cycle div_start pulse. The divider sets busy = 1 for 32 clock cycles, holding stall_ex2 = 1 to freeze EX1 and earlier pipeline stages. Each cycle, dividend[62:31] is compared with divisor; if greater, divisor is subtracted and a 1 bit is shifted in. Signed quotient and remainder sign corrections are applied on cycle 32."),

        ("Q9: Why does the multiplier (mul_unit.v) execute in 1 cycle while division takes 32 cycles?",
         "The multiplier infers DSP48E1 hard blocks on Xilinx FPGAs. DSP48E1 slices contain fast 25x18 hardware multipliers capable of performing 32x32 signed/unsigned products combinationally within the EX2 clock period (20 ns). Division algorithms require iterative comparison and shift-subtraction steps that cannot fit in a single 50 MHz clock period without severely violating setup time, necessitating a multi-cycle state machine."),

        ("Q10: How does the Branch Prediction Unit (BPU) handle branch resolution and misprediction recovery?",
         "The BPU (branch_predictor.v) uses a 64-entry BHT (2-bit saturating counters), BTB (target addresses), and tag array. In IF1, if BHT >= 2'b10 and tag matches if_pc, predicted_valid = 1 and PC jumps to BTB address. In EX1, the actual branch condition and target are evaluated. If prediction was wrong, ex1.v asserts branch_mispredict = 1, driving flush_id = 1 and flush_ex1 = 1 to clear speculatively fetched instructions, while redirecting IF1 to the correct branch target."),

        ("Q11: What is the penalty for a branch misprediction in this 7-stage core?",
         "The branch misprediction penalty is exactly 2 clock cycles. Because branches are resolved in EX1, two speculatively fetched instructions reside in IF2 and ID. Asserting flush_id and flush_ex1 converts these 2 stages into bubble NOPs while reloading the correct PC into IF1."),

        ("Q12: How does the internal register file (register_file.v) support asynchronous reads with write-first bypass?",
         "The register file contains 32 registers of 32 bits. Reads are combinational (asynchronous). To prevent stale reads when an instruction writes to rd in WB while the next instruction reads the same register in ID, an internal bypass is implemented: assign rdata1 = (we && waddr != 0 && waddr == raddr1) ? wdata : regs[raddr1]. Register R0 is hardwired to 0."),

        ("Q13: Explain how the UART In-Circuit Bootloader operates during FPGA reset.",
         "The instruction BRAM (bram_imem.v) integrates a UART RX module (u_rx) running at 115200 Baud. While the physical reset button M14 is held DOWN, the CPU is held in reset, but uart_clk remains active. Arriving serial bytes are assembled in little-endian order (4 bytes = 1 word). Once byte_cnt == 3, the complete 32-bit instruction word is written into mem[load_addr]. Releasing button M14 allows the core to boot the newly uploaded program instantly."),

        ("Q14: How is Memory-Mapped I/O (MMIO) implemented in this RISC-V core?",
         "MMIO is decoded in EX2 and MEM stages based on memory addresses. Address 0xFFFF0000 is mapped to the MMIO UART TX transmitter (uart_tx_minimal.v). Writing a byte to 0xFFFF0000 triggers UART serial transmission; if the UART TX line is busy, stall_uart asserts stall_ex2 to freeze the pipeline. Address 0xFFFF0004 is mapped directly to the FPGA 8-bit LED array."),

        ("Q15: What custom CSRs were added to this core and what are their addresses?",
         "Two custom machine-mode CSRs were added: 1) mapprox at address 0x800 (bit [0] enables 4-LSB truncated approximate ALU mode), and 2) mpower at address 0x801 (8-bit stage mask controlling dynamic clock enable outputs in stage_gating_controller.v). Standard CSRs include mcycle (0xC00/0xC80) and minstret (0xC02/0xC82)."),

        ("Q16: How do CSR instructions (CSRRW, CSRRS, CSRRC) modify system registers?",
         "CSR instructions pass down to EX2 with is_csr = 1. In csr_unit.v, CSRRW (funct3 01) overwrites the target CSR with rs1 data. CSRRS (funct3 10) sets bits using rs1 as a bitmask (csr | wdata). CSRRC (funct3 11) clears bits using rs1 as a mask (csr & ~wdata). Updated CSR values take effect immediately on the next clock cycle."),

        ("Q17: What are the main sources of power dissipation reported in power_report.txt?",
         "According to Vivado report_power on routed fpga_top, Total Power is 0.251 W (Dynamic: 0.153 W, Static: 0.098 W). The largest dynamic power contributor is the MMCM clock generator (0.105 W, 68.6% of dynamic power). Core signals consume 0.014 W, gated clock trees consume 0.012 W, Slice LUT logic consumes 0.008 W, and BRAM blocks consume 0.009 W."),

        ("Q18: What clock constraint was used in synthesis and how is the 50 MHz system clock generated?",
         "The input FPGA clock clk_in is constrained to 20.0 ns (50 MHz) in risc_v.xdc. An MMCME2_BASE primitive in clock_manager.v multiplies the 50 MHz input by 20 (VCO = 1000 MHz) and divides by 20 to output a jitter-filtered 50 MHz clk_mmcm_out system clock."),

        ("Q19: How do you handle store byte enables (SB, SH, SW) in mem.v?",
         "In mem.v, store data and 4-bit write strobes (mem_wstrb) are calculated combinationally based on address bits [1:0] and funct3: SB (Store Byte) shifts 8-bit data and asserts 1 strobe bit (4'b0001 << addr[1:0]); SH (Store Halfword) replicates 16-bit data and asserts 2 strobe bits (4'b0011 or 4'b1100); SW (Store Word) asserts all 4 strobe bits (4'b1111)."),

        ("Q20: How are sign-extension and zero-extension handled for Load instructions in mem.v?",
         "When reading BRAM data (mem_rdata), mem.v inspects funct3 and address bits [1:0]: LB (Load Byte) sign-extends bit 7 ({{24{data[7]}}, data[7:0]}); LBU (Load Byte Unsigned) zero-extends (24'd0, data[7:0]); LH sign-extends 16 bits; LHU zero-extends 16 bits; LW passes the full 32-bit word directly."),

        ("Q21: What is the purpose of the pulse latch (div_started) in ex1.v?",
         "When a division instruction starts, ex1.v generates a 1-cycle div_start pulse. Because division stalls the pipeline for 32 cycles, EX1 holds its register values. Without div_started pulse latching, EX1 would re-trigger div_start on every stalled cycle. div_started ensures div_start pulses exactly once."),

        ("Q22: How does the pipeline recover from a multi-stage stall triggered by UART TX busy?",
         "When an MMIO store writes to 0xFFFF0000 while uart_tx_minimal.v is transmitting (busy = 1), ex2.v asserts stall_uart = 1, driving stall_ex2 = 1. The hazard unit propagates stall_ex2 to freeze IF1, IF2, ID, and EX1. Once the UART transmission completes (busy = 0), stall_ex2 deasserts and normal pipeline flow resumes smoothly."),

        ("Q23: How would you debug a silent hang in hardware when executing an assembly loop on the FPGA?",
         "1) Check physical LEDs bound to dbg_led and dbg_wfi_active to see if core entered WFI or reset stall. 2) Connect Vivado Integrated Logic Analyzer (ILA) core to sample pc_out, stall_ex2, and wfi_active signals in real time. 3) Inspect UART bootloader logs using diagnostic scripts (upload_edge_cases.py) to verify complete byte stream reception."),

        ("Q24: What timing path in this 7-stage RISC-V core is most likely to become the critical path at higher frequencies (e.g., > 100 MHz)?",
         "The most critical timing path is the Forwarding Mux → EX1 Branch Condition Evaluation → EX1 Mispredict Detection → IF1 Next-PC Mux loop. Because branch resolution in EX1 depends on forwarded ALU results from EX2 or MEM, this combinational logic chain spans across stage boundaries and represents the primary Fmax limiting path."),

        ("Q25: If you were to add an L1 Instruction Cache to this core, how would miss stalls integrate into the existing hazard unit?",
         "An I-Cache miss signal (icache_miss) would be connected directly to hazard_unit.v as a high-priority stall input. On a miss, hazard_unit.v would assert stall_if = 1 and stall_id = 1 while inserting a bubble flush into EX1 (flush_ex1 = 1). Once the BRAM/DRAM line fill completes, icache_miss deasserts, allowing IF1 to resume fetching instructions.")
    ]

    for q_text, a_text in qa_list:
        story.append(Paragraph(q_text, q_title_style))
        story.append(Paragraph(a_text, a_body_style))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated {filename}")

if __name__ == "__main__":
    create_pdf()
