"""
Image Transfer Corruption Detector - Dashboard Edition
-------------------------------------------------------
A Tkinter desktop dashboard for verifying image integrity using CRC-32.

Features:
- Modern dashboard layout with sidebar navigation
- Single image comparison with previews, file size and CRC-32
- Corruption simulation
- Multiple-image checking matched by filename
- Folder batch verification
- Verification history/report table
- CSV report export
- Reset controls

Requires:
    pip install pillow
"""

import os
import csv
import zlib
import random
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from PIL import Image, ImageTk
except ImportError:
    raise SystemExit(
        "This application requires Pillow.\n"
        "Install it with: pip install pillow"
    )


# ============================================================
# COLORS / FONTS
# ============================================================

BG = "#F5F9FF"
SIDEBAR = "#FFFFFF"
CARD = "#FFFFFF"
CARD_2 = "#EFF6FF"
BORDER = "#E2E8F0"
TEXT = "#172033"
MUTED = "#64748B"
BLUE = "#2563EB"
BLUE_DARK = "#1D4ED8"
GREEN = "#16A34A"
GREEN_BG = "#ECFDF3"
RED = "#DC2626"
RED_BG = "#FEF2F2"
PURPLE = "#2563EB"
CYAN = "#2563EB"
WHITE = "#FFFFFF"

FONT_TITLE = ("Segoe UI", 24, "bold")
FONT_SUBTITLE = ("Segoe UI", 10)
FONT_HEADING = ("Segoe UI", 15, "bold")
FONT_BODY = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_BUTTON = ("Segoe UI", 10, "bold")
FONT_MONO = ("Consolas", 11, "bold")

PREVIEW_SIZE = (330, 230)


def compute_crc32(path):
    """Return an 8-character uppercase CRC-32 and file size."""
    with open(path, "rb") as f:
        data = f.read()
    return format(zlib.crc32(data) & 0xFFFFFFFF, "08X"), len(data)


class ImageSlot:
    def __init__(self, name):
        self.name = name
        self.path = None
        self.crc = None
        self.size_bytes = None
        self.photo = None
        self.preview_widget = None
        self.info_label = None
        self.size_label = None
        self.crc_label = None


class CorruptionDetectorDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Transfer Corruption Detector")
        self.root.geometry("1280x820")
        self.root.minsize(1050, 700)
        self.root.configure(bg=BG)

        self.original = ImageSlot("Original")
        self.received = ImageSlot("Received")

        self.multiple_original_paths = []
        self.multiple_received_paths = []
        self.report_rows = []

        self.current_page = "Dashboard"
        self.nav_buttons = {}
        self.pages = {}

        self._configure_styles()
        self._build_layout()
        self.show_page("Dashboard")

    # ========================================================
    # STYLE
    # ========================================================

    def _configure_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Dashboard.Treeview",
            background=CARD,
            fieldbackground=CARD,
            foreground=TEXT,
            rowheight=32,
            borderwidth=0,
            font=FONT_SMALL
        )
        style.map(
            "Dashboard.Treeview",
            background=[("selected", BLUE_DARK)],
            foreground=[("selected", WHITE)]
        )
        style.configure(
            "Dashboard.Treeview.Heading",
            background=CARD_2,
            foreground=TEXT,
            font=("Segoe UI", 9, "bold"),
            padding=(8, 8),
            relief="flat"
        )
        style.map(
            "Dashboard.Treeview.Heading",
            background=[("active", CARD_2)]
        )

        style.configure(
            "Vertical.TScrollbar",
            background=BORDER,
            troughcolor=SIDEBAR,
            borderwidth=0,
            arrowsize=12
        )

    # ========================================================
    # MAIN LAYOUT
    # ========================================================

    def _build_layout(self):
        self.sidebar = tk.Frame(self.root, bg=SIDEBAR, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.main = tk.Frame(self.root, bg=BG)
        self.main.pack(side="right", fill="both", expand=True)

        self._build_sidebar()
        self._build_pages()

        self.status_bar = tk.Label(
            self.main,
            text="Ready.",
            bg="#EAF2FF",
            fg=MUTED,
            anchor="w",
            padx=18,
            pady=6,
            font=FONT_SMALL
        )
        self.status_bar.pack(side="bottom", fill="x")

    def _build_sidebar(self):
        top = tk.Frame(self.sidebar, bg=SIDEBAR)
        top.pack(fill="x", padx=20, pady=(24, 28))

        icon = tk.Label(
            top,
            text="🛡",
            bg=SIDEBAR,
            fg=CYAN,
            font=("Segoe UI Emoji", 25)
        )
        icon.pack(anchor="w")

        tk.Label(
            top,
            text="IMAGE TRANSFER",
            bg=SIDEBAR,
            fg=TEXT,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(8, 0))

        tk.Label(
            top,
            text="CORRUPTION DETECTOR",
            bg=SIDEBAR,
            fg=BLUE,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        tk.Label(
            self.sidebar,
            text="VERIFICATION",
            bg=SIDEBAR,
            fg="#64748B",
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w", padx=20, pady=(0, 8))

        items = [
            ("▣", "Dashboard"),
            ("▧", "Single Image"),
            ("▤", "Batch / Multiple"),
            ("≡", "Reports"),
            ("⚙", "Settings"),
        ]

        for symbol, name in items:
            self._make_nav_button(symbol, name)

        bottom = tk.Frame(self.sidebar, bg=SIDEBAR)
        bottom.pack(side="bottom", fill="x", padx=20, pady=22)

        tk.Frame(bottom, bg=BORDER, height=1).pack(fill="x", pady=(0, 15))

        tk.Label(
            bottom,
            text="DATA INTEGRITY",
            bg=SIDEBAR,
            fg=GREEN,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        tk.Label(
            bottom,
            text="Check  •  Compare  •  Verify",
            bg=SIDEBAR,
            fg=MUTED,
            font=FONT_SMALL
        ).pack(anchor="w", pady=(4, 0))

    def _make_nav_button(self, symbol, name):
        button = tk.Button(
            self.sidebar,
            text=f"  {symbol}    {name}",
            command=lambda n=name: self.show_page(n),
            bg=SIDEBAR,
            fg=MUTED,
            activebackground="#EFF6FF",
            activeforeground=WHITE,
            relief="flat",
            bd=0,
            anchor="w",
            padx=16,
            pady=12,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2"
        )
        button.pack(fill="x", padx=10, pady=2)
        self.nav_buttons[name] = button

    # ========================================================
    # PAGE SYSTEM
    # ========================================================

    def _build_pages(self):
        self.page_container = tk.Frame(self.main, bg=BG)
        self.page_container.pack(fill="both", expand=True)

        self._build_dashboard_page()
        self._build_single_page()
        self._build_batch_page()
        self._build_reports_page()
        self._build_settings_page()

    def _new_page(self):
        page = tk.Frame(self.page_container, bg=BG)
        page.place(relx=0, rely=0, relwidth=1, relheight=1)
        return page

    def _build_page_header(self, parent, title, subtitle):
        header = tk.Frame(parent, bg=BG)
        header.pack(fill="x", padx=28, pady=(24, 16))

        left = tk.Frame(header, bg=BG)
        left.pack(side="left")

        tk.Label(
            left, text=title, bg=BG, fg=TEXT, font=FONT_TITLE
        ).pack(anchor="w")

        tk.Label(
            left, text=subtitle, bg=BG, fg=MUTED, font=FONT_SUBTITLE
        ).pack(anchor="w", pady=(5, 0))

        return header

    def show_page(self, name):
        self.current_page = name

        for page in self.pages.values():
            page.lower()

        self.pages[name].lift()

        for nav_name, button in self.nav_buttons.items():
            if nav_name == name:
                button.configure(bg=BLUE, fg=WHITE)
            else:
                button.configure(bg=SIDEBAR, fg=MUTED)

        if name == "Dashboard":
            self.refresh_dashboard()
        elif name == "Reports":
            self.refresh_report_table()
        elif name == "Batch / Multiple":
            self._refresh_multiple_lists()

    # ========================================================
    # DASHBOARD PAGE
    # ========================================================

    def _build_dashboard_page(self):
        page = self._new_page()
        self.pages["Dashboard"] = page

        header = self._build_page_header(
            page,
            "Image Transfer Corruption Detector",
            "Verify image integrity using CRC-32 checksums"
        )

        status = tk.Frame(header, bg="#ECFDF3")
        status.pack(side="right", pady=4)

        tk.Label(
            status, text="●  SYSTEM READY", bg="#ECFDF3",
            fg=GREEN, font=("Segoe UI", 10, "bold"),
            padx=15, pady=9
        ).pack()

        body = tk.Frame(page, bg=BG)
        body.pack(fill="both", expand=True, padx=28, pady=(0, 20))

        # Statistic cards
        stats = tk.Frame(body, bg=BG)
        stats.pack(fill="x", pady=(0, 18))

        self.stat_total = self._stat_card(
            stats, "TOTAL IMAGES", "0", "Images checked so far", BLUE
        )
        self.stat_total.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.stat_good = self._stat_card(
            stats, "VERIFIED IMAGES", "0", "No corruption detected", GREEN
        )
        self.stat_good.pack(side="left", fill="both", expand=True, padx=8)

        self.stat_bad = self._stat_card(
            stats, "CORRUPTED IMAGES", "0", "Integrity check failed", RED
        )
        self.stat_bad.pack(side="left", fill="both", expand=True, padx=8)

        self.stat_unmatched = self._stat_card(
            stats, "UNMATCHED / MISSING", "0", "Extra or missing files", PURPLE
        )
        self.stat_unmatched.pack(side="left", fill="both", expand=True, padx=8)

        self.stat_last = self._stat_card(
            stats, "LAST CHECKED", "—", "No checks yet", PURPLE
        )
        self.stat_last.pack(side="left", fill="both", expand=True, padx=(8, 0))

        middle = tk.Frame(body, bg=BG)
        middle.pack(fill="both", expand=True)

        # Recent checks
        recent = self._card(middle)
        recent.pack(side="left", fill="both", expand=True, padx=(0, 9))

        top = tk.Frame(recent, bg=CARD)
        top.pack(fill="x", padx=18, pady=(16, 8))

        tk.Label(
            top, text="Recent Checks", bg=CARD, fg=TEXT,
            font=FONT_HEADING
        ).pack(side="left")

        tk.Button(
            top, text="View All →", command=lambda: self.show_page("Reports"),
            bg=CARD, fg=CYAN, activebackground=CARD,
            activeforeground=WHITE, relief="flat", bd=0,
            font=FONT_SMALL, cursor="hand2"
        ).pack(side="right")

        columns = ("file", "status", "time")
        self.recent_tree = ttk.Treeview(
            recent, columns=columns, show="headings",
            style="Dashboard.Treeview", height=7
        )
        self.recent_tree.heading("file", text="FILE NAME")
        self.recent_tree.heading("status", text="RESULT")
        self.recent_tree.heading("time", text="DATE & TIME")
        self.recent_tree.column("file", width=260)
        self.recent_tree.column("status", width=100)
        self.recent_tree.column("time", width=160)
        self.recent_tree.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        self.recent_tree.tag_configure("good", foreground=GREEN)
        self.recent_tree.tag_configure("bad", foreground=RED)

        # Quick actions
        quick = self._card(middle, width=360)
        quick.pack(side="right", fill="y", padx=(9, 0))

        tk.Label(
            quick, text="Quick Actions", bg=CARD, fg=TEXT,
            font=FONT_HEADING
        ).pack(anchor="w", padx=18, pady=(16, 14))

        self._dashboard_action(
            quick, "▧", "Single Image Check",
            "Compare original and received images",
            lambda: self.show_page("Single Image")
        )
        self._dashboard_action(
            quick, "▤", "Batch Verification",
            "Check a complete pair of folders",
            lambda: self.show_page("Batch / Multiple")
        )
        self._dashboard_action(
            quick, "↥", "Export Report",
            "Save verification history as CSV",
            self.export_report
        )

        self.refresh_dashboard()

    def _stat_card(self, parent, title, value, subtitle, accent):
        frame = tk.Frame(parent, bg=CARD, highlightbackground=BORDER,
                         highlightthickness=1, padx=16, pady=14)

        tk.Frame(frame, bg=accent, width=4).pack(
            side="left", fill="y", padx=(0, 13)
        )

        inner = tk.Frame(frame, bg=CARD)
        inner.pack(side="left", fill="both", expand=True)

        tk.Label(
            inner, text=title, bg=CARD, fg=MUTED,
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w")

        value_label = tk.Label(
            inner, text=value, bg=CARD, fg=TEXT,
            font=("Segoe UI", 21, "bold")
        )
        value_label.pack(anchor="w", pady=(5, 0))

        tk.Label(
            inner, text=subtitle, bg=CARD, fg=MUTED,
            font=FONT_SMALL
        ).pack(anchor="w", pady=(2, 0))

        frame.value_label = value_label
        return frame

    def _card(self, parent, width=None):
        frame = tk.Frame(
            parent, bg=CARD, highlightbackground=BORDER,
            highlightthickness=1
        )
        if width:
            frame.configure(width=width)
            frame.pack_propagate(False)
        return frame

    def _dashboard_action(self, parent, icon, title, subtitle, command):
        box = tk.Frame(parent, bg=CARD_2, cursor="hand2")
        box.pack(fill="x", padx=16, pady=6)

        tk.Label(
            box, text=icon, bg=CARD_2, fg=CYAN,
            font=("Segoe UI", 17, "bold")
        ).pack(side="left", padx=12)

        text = tk.Frame(box, bg=CARD_2)
        text.pack(side="left", fill="x", expand=True, pady=10)

        tk.Label(
            text, text=title, bg=CARD_2, fg=TEXT,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        tk.Label(
            text, text=subtitle, bg=CARD_2, fg=MUTED,
            font=("Segoe UI", 8)
        ).pack(anchor="w", pady=(2, 0))

        for widget in (box, text):
            widget.bind("<Button-1>", lambda e: command())

    def refresh_dashboard(self):
        total = len(self.report_rows)
        good = sum(r["status"] == "INTACT" for r in self.report_rows)
        bad = sum(r["status"] == "CORRUPTED" for r in self.report_rows)
        unmatched = sum(
            r["status"] in ("UNMATCHED/EXTRA", "MISSING RECEIVED")
            for r in self.report_rows
        )

        self.stat_total.value_label.configure(text=str(total))
        self.stat_good.value_label.configure(text=str(good))
        self.stat_bad.value_label.configure(text=str(bad))
        self.stat_unmatched.value_label.configure(text=str(unmatched))

        if self.report_rows:
            last = self.report_rows[-1]["timestamp"]
            self.stat_last.value_label.configure(text=last[0:10])
            self.stat_last.value_label.configure(font=("Segoe UI", 12, "bold"))
            self.stat_last.winfo_children()[-1].configure(text=last[11:])
        else:
            self.stat_last.value_label.configure(text="—")

        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)

        for row in reversed(self.report_rows[-7:]):
            tag = "good" if row["status"] == "INTACT" else "bad"
            self.recent_tree.insert(
                "", "end",
                values=(
                    row["original"],
                    "✓ Verified" if tag == "good" else "✕ Corrupted",
                    row["timestamp"]
                ),
                tags=(tag,)
            )

    # ========================================================
    # SINGLE IMAGE PAGE
    # ========================================================

    def _build_single_page(self):
        page = self._new_page()
        self.pages["Single Image"] = page

        self._build_page_header(
            page,
            "Single Image Verification",
            "Compare an original image with its received copy"
        )

        outer = tk.Frame(page, bg=BG)
        outer.pack(fill="both", expand=True, padx=28, pady=(0, 20))

        comparison = tk.Frame(outer, bg=BG)
        comparison.pack(fill="both", expand=True)

        self.original_panel = self._make_image_panel(
            comparison, self.original, self.load_original
        )
        self.original_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.received_panel = self._make_image_panel(
            comparison, self.received, self.load_received
        )
        self.received_panel.pack(side="left", fill="both", expand=True, padx=(8, 0))

        bottom = tk.Frame(outer, bg=BG)
        bottom.pack(fill="x", pady=(14, 0))

        self.single_status = tk.Label(
            bottom,
            text="Load both images, then check for corruption.",
            bg=CARD_2, fg=MUTED,
            font=("Segoe UI", 11, "bold"),
            padx=18, pady=13
        )
        self.single_status.pack(side="left", fill="x", expand=True)

        actions = tk.Frame(bottom, bg=BG)
        actions.pack(side="right", padx=(12, 0))

        self._button(
            actions, "✓  Check for Corruption",
            self.check_corruption, BLUE
        ).pack(side="left", padx=4)

        self._button(
            actions, "⚡  Simulate Corruption",
            self.simulate_corruption, BLUE
        ).pack(side="left", padx=4)

        self._button(
            actions, "↻  Reset",
            self.reset_all, CARD_2
        ).pack(side="left", padx=4)

    def _make_image_panel(self, parent, slot, load_command):
        panel = tk.Frame(
            parent, bg=CARD, highlightbackground=BORDER,
            highlightthickness=1
        )

        header = tk.Frame(panel, bg=CARD)
        header.pack(fill="x", padx=18, pady=(16, 10))

        tk.Label(
            header, text=f"●  {slot.name.upper()} IMAGE",
            bg=CARD, fg=TEXT, font=FONT_HEADING
        ).pack(side="left")

        preview = tk.Label(
            panel, text="No image loaded",
            bg="#F8FAFC", fg=MUTED,
            font=FONT_BODY,
            relief="flat"
        )
        preview.pack(fill="both", expand=True, padx=18, pady=4)
        slot.preview_widget = preview

        info = tk.Frame(panel, bg=CARD)
        info.pack(fill="x", padx=18, pady=(12, 0))

        info_label = tk.Label(
            info, text="File: —", bg=CARD, fg=TEXT,
            font=FONT_BODY, anchor="w"
        )
        info_label.pack(fill="x")
        slot.info_label = info_label

        size_label = tk.Label(
            info, text="Size: —", bg=CARD, fg=MUTED,
            font=FONT_SMALL, anchor="w"
        )
        size_label.pack(fill="x", pady=(3, 0))
        slot.size_label = size_label

        crc_row = tk.Frame(panel, bg=CARD)
        crc_row.pack(fill="x", padx=18, pady=12)

        tk.Label(
            crc_row, text="CRC-32", bg=CARD, fg=MUTED,
            font=FONT_SMALL
        ).pack(side="left")

        crc_label = tk.Label(
            crc_row, text="—", bg="#EFF6FF", fg=CYAN,
            font=FONT_MONO, padx=12, pady=6
        )
        crc_label.pack(side="left", padx=(10, 0))
        slot.crc_label = crc_label

        self._button(
            panel, f"▣  Browse {slot.name} Image",
            load_command, BLUE_DARK
        ).pack(fill="x", padx=18, pady=(0, 18))

        return panel

    # ========================================================
    # BATCH / MULTIPLE PAGE
    # ========================================================

    def _build_batch_page(self):
        page = self._new_page()
        self.pages["Batch / Multiple"] = page

        self._build_page_header(
            page,
            "Batch / Multiple Image Verification",
            "Compare multiple files or complete folders by matching filenames"
        )

        outer = tk.Frame(page, bg=BG)
        outer.pack(fill="both", expand=True, padx=28, pady=(0, 20))

        lists = tk.Frame(outer, bg=BG)
        lists.pack(fill="both", expand=True)

        self.original_batch_card = self._make_batch_card(
            lists, "ORIGINAL IMAGES", BLUE,
            lambda: self.add_multiple_original(),
            lambda: self.clear_multiple_original()
        )
        self.original_batch_card.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.received_batch_card = self._make_batch_card(
            lists, "RECEIVED IMAGES", PURPLE,
            lambda: self.add_multiple_received(),
            lambda: self.clear_multiple_received()
        )
        self.received_batch_card.pack(side="left", fill="both", expand=True, padx=(8, 0))

        actions = tk.Frame(outer, bg=BG)
        actions.pack(fill="x", pady=(14, 0))

        self._button(
            actions, "＋  Add Original Images",
            self.add_multiple_original, BLUE
        ).pack(side="left", padx=4)

        self._button(
            actions, "＋  Add Received Images",
            self.add_multiple_received, BLUE
        ).pack(side="left", padx=4)

        self._button(
            actions, "✓  Check All Multiple Images",
            self.check_multiple_images, GREEN
        ).pack(side="left", padx=4)

        self._button(
            actions, "▣  Batch Check Folders",
            self.batch_check, CARD_2
        ).pack(side="left", padx=4)

        self._button(
            actions, "↻  Clear All",
            self.clear_all_multiple, CARD_2
        ).pack(side="right", padx=4)

        note = tk.Label(
            outer,
            text="Files are matched by filename before CRC-32 comparison.",
            bg=BG, fg=MUTED, font=FONT_SMALL
        )
        note.pack(anchor="w", padx=5, pady=(8, 0))

    def _make_batch_card(self, parent, title, accent, add_command, clear_command):
        card = tk.Frame(
            parent, bg=CARD, highlightbackground=BORDER,
            highlightthickness=1
        )

        header = tk.Frame(card, bg=CARD)
        header.pack(fill="x", padx=16, pady=(15, 8))

        tk.Label(
            header, text=title, bg=CARD, fg=TEXT,
            font=FONT_HEADING
        ).pack(side="left")

        count = tk.Label(
            header, text="0 selected", bg=CARD_2, fg=accent,
            font=("Segoe UI", 8, "bold"), padx=9, pady=4
        )
        count.pack(side="right")

        listbox = tk.Listbox(
            card, height=14,
            bg="#F8FAFC", fg=TEXT,
            selectbackground=BLUE_DARK,
            selectforeground=WHITE,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=BORDER,
            font=FONT_BODY
        )
        listbox.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        buttons = tk.Frame(card, bg=CARD)
        buttons.pack(fill="x", padx=16, pady=(0, 15))

        self._button(buttons, "Add", add_command, accent).pack(side="left")
        self._button(buttons, "Clear", clear_command, CARD_2).pack(side="left", padx=8)

        card.listbox = listbox
        card.count_label = count
        return card

    # ========================================================
    # REPORTS PAGE
    # ========================================================

    def _build_reports_page(self):
        page = self._new_page()
        self.pages["Reports"] = page

        header = self._build_page_header(
            page,
            "Verification Reports",
            "Review all CRC-32 checks performed during this session"
        )

        self._button(
            header, "↓  Export CSV",
            self.export_report, BLUE
        ).pack(side="right", pady=4)

        body = tk.Frame(page, bg=BG)
        body.pack(fill="both", expand=True, padx=28, pady=(0, 22))

        table_card = self._card(body)
        table_card.pack(fill="both", expand=True)

        tk.Label(
            table_card, text="Verification History",
            bg=CARD, fg=TEXT, font=FONT_HEADING
        ).pack(anchor="w", padx=18, pady=(16, 10))

        frame = tk.Frame(table_card, bg=CARD)
        frame.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        columns = (
            "timestamp", "original", "received",
            "orig_crc", "recv_crc", "status"
        )

        self.report_tree = ttk.Treeview(
            frame, columns=columns, show="headings",
            style="Dashboard.Treeview"
        )

        headings = {
            "timestamp": "Timestamp",
            "original": "Original File",
            "received": "Received File",
            "orig_crc": "Original CRC",
            "recv_crc": "Received CRC",
            "status": "Status"
        }

        widths = {
            "timestamp": 155,
            "original": 190,
            "received": 190,
            "orig_crc": 110,
            "recv_crc": 110,
            "status": 110
        }

        for col in columns:
            self.report_tree.heading(col, text=headings[col])
            self.report_tree.column(col, width=widths[col], anchor="w")

        self.report_tree.tag_configure("good", foreground=GREEN)
        self.report_tree.tag_configure("bad", foreground=RED)
        self.report_tree.tag_configure("neutral", foreground=MUTED)

        scrollbar = ttk.Scrollbar(
            frame, orient="vertical",
            command=self.report_tree.yview
        )
        self.report_tree.configure(yscrollcommand=scrollbar.set)

        self.report_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def refresh_report_table(self):
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)

        for row in self.report_rows:
            if row["status"] == "INTACT":
                tag = "good"
                display_status = "✓ INTACT"
            elif row["status"] == "CORRUPTED":
                tag = "bad"
                display_status = "✕ CORRUPTED"
            else:
                tag = "neutral"
                display_status = row["status"]

            self.report_tree.insert(
                "", "end",
                values=(
                    row["timestamp"],
                    row["original"],
                    row["received"],
                    row["orig_crc"],
                    row["recv_crc"],
                    display_status
                ),
                tags=(tag,)
            )

    # ========================================================
    # SETTINGS / ABOUT
    # ========================================================

    def _build_settings_page(self):
        page = self._new_page()
        self.pages["Settings"] = page

        self._build_page_header(
            page,
            "Settings & About",
            "Application information and verification details"
        )

        body = tk.Frame(page, bg=BG)
        body.pack(fill="both", expand=True, padx=28)

        info = self._card(body)
        info.pack(fill="x", pady=(0, 14))

        tk.Label(
            info, text="About the Project", bg=CARD,
            fg=TEXT, font=FONT_HEADING
        ).pack(anchor="w", padx=20, pady=(18, 10))

        text = (
            "Image Transfer Corruption Detector\n\n"
            "This application compares CRC-32 checksums of an original "
            "and received image file to detect accidental changes during "
            "storage or transfer.\n\n"
            "Technology: Python + Tkinter + Pillow + zlib\n"
            "Reporting: CSV verification history\n"
            "Matching: Multiple files are matched by filename."
        )

        tk.Label(
            info, text=text, bg=CARD, fg=MUTED,
            justify="left", anchor="w",
            font=FONT_BODY
        ).pack(fill="x", padx=20, pady=(0, 20))

        reset = self._card(body)
        reset.pack(fill="x")

        tk.Label(
            reset, text="Session Controls", bg=CARD,
            fg=TEXT, font=FONT_HEADING
        ).pack(anchor="w", padx=20, pady=(18, 10))

        tk.Label(
            reset,
            text="Reset clears the currently loaded images, multiple-image selections and report history.",
            bg=CARD, fg=MUTED, font=FONT_SMALL
        ).pack(anchor="w", padx=20)

        self._button(
            reset, "↻  Reset Application",
            self.reset_all, BLUE
        ).pack(anchor="w", padx=20, pady=16)

    # ========================================================
    # BUTTON HELPER
    # ========================================================

    def _button(self, parent, text, command, color):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg=WHITE,
            activebackground=BLUE_DARK if color != CARD_2 else BORDER,
            activeforeground=WHITE,
            relief="flat",
            bd=0,
            padx=14,
            pady=9,
            font=FONT_BUTTON,
            cursor="hand2"
        )

    # ========================================================
    # STATUS
    # ========================================================

    def _set_status(self, text):
        self.status_bar.configure(text=text)

    def _set_single_status(self, text, good=None):
        if good is True:
            self.single_status.configure(
                text=text, bg=GREEN_BG, fg=GREEN
            )
        elif good is False:
            self.single_status.configure(
                text=text, bg=RED_BG, fg=RED
            )
        else:
            self.single_status.configure(
                text=text, bg=CARD_2, fg=MUTED
            )

    # ========================================================
    # IMAGE LOADING
    # ========================================================

    def load_original(self):
        self._load_into_slot(self.original)

    def load_received(self):
        self._load_into_slot(self.received)

    def _load_into_slot(self, slot):
        path = filedialog.askopenfilename(
            title=f"Select {slot.name} Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        self._apply_image_to_slot(slot, path)
        self._set_status(
            f"Loaded {slot.name.lower()} image: {os.path.basename(path)}"
        )

        self.show_page("Single Image")

    def _apply_image_to_slot(self, slot, path):
        try:
            crc, size_bytes = compute_crc32(path)
        except Exception as e:
            messagebox.showerror(
                "Error Reading File",
                f"Could not read this file:\n{e}"
            )
            return

        slot.path = path
        slot.crc = crc
        slot.size_bytes = size_bytes

        try:
            img = Image.open(path).convert("RGB")
            img.thumbnail(PREVIEW_SIZE)
            photo = ImageTk.PhotoImage(img)
            slot.photo = photo
            slot.preview_widget.configure(image=photo, text="")
        except Exception:
            slot.preview_widget.configure(
                image="", text="Preview unavailable"
            )

        slot.info_label.configure(
            text=f"File: {os.path.basename(path)}"
        )
        slot.size_label.configure(
            text=f"Size: {size_bytes:,} bytes"
        )
        slot.crc_label.configure(text=crc)

        self._set_single_status(
            "Images changed. Run a new CRC-32 comparison.",
            None
        )

    # ========================================================
    # SINGLE CORRUPTION CHECK
    # ========================================================

    def check_corruption(self):
        if not self.original.path or not self.received.path:
            messagebox.showwarning(
                "Missing Images",
                "Please load both the original and received images first."
            )
            return

        match = self.original.crc == self.received.crc
        status = "INTACT" if match else "CORRUPTED"

        if match:
            self._set_single_status(
                "✓  INTACT — no corruption detected; CRC-32 values match.",
                True
            )
        else:
            self._set_single_status(
                "✕  CORRUPTED — received image does not match the original.",
                False
            )

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        row = {
            "timestamp": timestamp,
            "original": os.path.basename(self.original.path),
            "received": os.path.basename(self.received.path),
            "orig_crc": self.original.crc,
            "recv_crc": self.received.crc,
            "status": status
        }

        self.report_rows.append(row)

        self._set_status(f"Check complete: {status}")
        self.refresh_dashboard()

    # ========================================================
    # MULTIPLE IMAGE FUNCTIONS
    # ========================================================

    def add_multiple_original(self):
        paths = filedialog.askopenfilenames(
            title="Select Multiple Original Images",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),
                ("All files", "*.*")
            ]
        )

        if not paths:
            return

        for path in paths:
            if path not in self.multiple_original_paths:
                self.multiple_original_paths.append(path)

        self._refresh_multiple_lists()
        self._set_status(f"Added {len(paths)} original image(s).")

    def add_multiple_received(self):
        paths = filedialog.askopenfilenames(
            title="Select Multiple Received Images",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),
                ("All files", "*.*")
            ]
        )

        if not paths:
            return

        for path in paths:
            if path not in self.multiple_received_paths:
                self.multiple_received_paths.append(path)

        self._refresh_multiple_lists()
        self._set_status(f"Added {len(paths)} received image(s).")

    def _refresh_multiple_lists(self):
        if not hasattr(self, "original_batch_card"):
            return

        original_list = self.original_batch_card.listbox
        received_list = self.received_batch_card.listbox

        original_list.delete(0, tk.END)
        received_list.delete(0, tk.END)

        for path in self.multiple_original_paths:
            original_list.insert(tk.END, os.path.basename(path))

        for path in self.multiple_received_paths:
            received_list.insert(tk.END, os.path.basename(path))

        self.original_batch_card.count_label.configure(
            text=f"{len(self.multiple_original_paths)} selected"
        )
        self.received_batch_card.count_label.configure(
            text=f"{len(self.multiple_received_paths)} selected"
        )

    def clear_multiple_original(self):
        self.multiple_original_paths.clear()
        self._refresh_multiple_lists()

    def clear_multiple_received(self):
        self.multiple_received_paths.clear()
        self._refresh_multiple_lists()

    def clear_all_multiple(self):
        self.multiple_original_paths.clear()
        self.multiple_received_paths.clear()
        self._refresh_multiple_lists()
        self._set_status("Multiple-image selections cleared.")

    def check_multiple_images(self):
        if not self.multiple_original_paths or not self.multiple_received_paths:
            messagebox.showwarning(
                "Missing Images",
                "Please add both Original and Received images first."
            )
            return

        original_by_name = {
            os.path.basename(p).lower(): p
            for p in self.multiple_original_paths
        }

        received_by_name = {
            os.path.basename(p).lower(): p
            for p in self.multiple_received_paths
        }

        original_names = set(original_by_name)
        received_names = set(received_by_name)

        common = sorted(original_names & received_names)
        extra_received = sorted(received_names - original_names)
        missing_received = sorted(original_names - received_names)

        intact_count = 0
        corrupted_count = 0
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Only files with the same filename are CRC-compared.
        # A file with no corresponding filename is NOT called corrupted.
        for key in common:
            orig_path = original_by_name[key]
            recv_path = received_by_name[key]

            try:
                orig_crc, _ = compute_crc32(orig_path)
                recv_crc, _ = compute_crc32(recv_path)
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Could not read {key}:\n{e}"
                )
                continue

            status = "INTACT" if orig_crc == recv_crc else "CORRUPTED"

            if status == "INTACT":
                intact_count += 1
            else:
                corrupted_count += 1

            self.report_rows.append({
                "timestamp": timestamp,
                "original": os.path.basename(orig_path),
                "received": os.path.basename(recv_path),
                "orig_crc": orig_crc,
                "recv_crc": recv_crc,
                "status": status
            })

        # Received files that have no original counterpart.
        for key in extra_received:
            recv_path = received_by_name[key]
            self.report_rows.append({
                "timestamp": timestamp,
                "original": "—",
                "received": os.path.basename(recv_path),
                "orig_crc": "—",
                "recv_crc": "—",
                "status": "UNMATCHED/EXTRA"
            })

        # Original files that have no received counterpart.
        for key in missing_received:
            orig_path = original_by_name[key]
            self.report_rows.append({
                "timestamp": timestamp,
                "original": os.path.basename(orig_path),
                "received": "—",
                "orig_crc": "—",
                "recv_crc": "—",
                "status": "MISSING RECEIVED"
            })

        matching_count = len(common)
        total_received = len(received_names)
        total_original = len(original_names)

        if matching_count == 0:
            message = (
                "⚠  No Matching Images\n"
                f"Received: {total_received} extra/unmatched | "
                f"Missing received: {len(missing_received)}"
            )
            good = None
        elif corrupted_count > 0:
            message = (
                f"✕  Batch result: {intact_count} intact, "
                f"{corrupted_count} corrupted, "
                f"{len(extra_received)} extra, "
                f"{len(missing_received)} missing received."
            )
            good = False
        elif extra_received or missing_received:
            message = (
                f"✓  CRC check complete: {intact_count} intact. "
                f"{len(extra_received)} extra, "
                f"{len(missing_received)} missing received."
            )
            good = None
        else:
            message = (
                f"✓  Batch result: all {intact_count} matching image(s) are intact."
            )
            good = True

        self._set_status(
            f"Multiple-image check complete: "
            f"Matching {matching_count}, Intact {intact_count}, "
            f"Corrupted {corrupted_count}, "
            f"Extra {len(extra_received)}, "
            f"Missing Received {len(missing_received)}"
        )
        self._set_single_status(message, good)
        self.refresh_dashboard()
        self.refresh_report_table()

        messagebox.showinfo(
            "Multiple Image Check Complete",
            f"Original images: {total_original}\n"
            f"Received images: {total_received}\n"
            f"Matching filenames: {matching_count}\n\n"
            f"✓ Intact: {intact_count}\n"
            f"✕ Corrupted: {corrupted_count}\n"
            f"＋ Unmatched/Extra received: {len(extra_received)}\n"
            f"− Missing received: {len(missing_received)}"
        )

    # ========================================================
    # FOLDER BATCH CHECK
    # ========================================================

    def batch_check(self):
        original_dir = filedialog.askdirectory(
            title="Select Folder of Original Images"
        )
        if not original_dir:
            return

        received_dir = filedialog.askdirectory(
            title="Select Folder of Received Images"
        )
        if not received_dir:
            return

        image_exts = {
            ".png", ".jpg", ".jpeg", ".bmp",
            ".gif", ".tiff", ".webp"
        }

        def list_images(folder):
            try:
                return {
                    f for f in os.listdir(folder)
                    if os.path.splitext(f)[1].lower() in image_exts
                }
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Could not read folder:\n{folder}\n\n{e}"
                )
                return None

        original_files = list_images(original_dir)
        received_files = list_images(received_dir)

        if original_files is None or received_files is None:
            return

        common = sorted(original_files & received_files)

        if not common:
            messagebox.showwarning(
                "No Matching Files",
                "No image filenames were found in common between the folders."
            )
            return

        intact_count = 0
        corrupted_count = 0
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for filename in common:
            orig_path = os.path.join(original_dir, filename)
            recv_path = os.path.join(received_dir, filename)

            try:
                orig_crc, _ = compute_crc32(orig_path)
                recv_crc, _ = compute_crc32(recv_path)
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Could not read {filename}:\n{e}"
                )
                continue

            status = "INTACT" if orig_crc == recv_crc else "CORRUPTED"

            if status == "INTACT":
                intact_count += 1
            else:
                corrupted_count += 1

            self.report_rows.append({
                "timestamp": timestamp,
                "original": filename,
                "received": filename,
                "orig_crc": orig_crc,
                "recv_crc": recv_crc,
                "status": status
            })

        total = intact_count + corrupted_count

        self._set_status(
            f"Batch check complete: {intact_count} intact, "
            f"{corrupted_count} corrupted"
        )
        self.refresh_dashboard()

        if corrupted_count:
            messagebox.showwarning(
                "Batch Check Complete",
                f"Checked {total} matching image(s).\n\n"
                f"✓ Intact: {intact_count}\n"
                f"✕ Corrupted: {corrupted_count}"
            )
        else:
            messagebox.showinfo(
                "Batch Check Complete",
                f"Checked {total} matching image(s).\n\n"
                f"✓ All {intact_count} image(s) are intact."
            )

    # ========================================================
    # CORRUPTION SIMULATION
    # ========================================================

    def simulate_corruption(self):
        if not self.received.path:
            messagebox.showwarning(
                "No Received Image",
                "Load a received image first, then simulate corruption on it."
            )
            return

        try:
            with open(self.received.path, "rb") as f:
                data = bytearray(f.read())
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not read the received image:\n{e}"
            )
            return

        if not data:
            messagebox.showwarning("Empty File", "The received image is empty.")
            return

        num_flips = max(1, len(data) // 5000)

        for _ in range(num_flips):
            idx = random.randrange(len(data))
            data[idx] ^= 0xFF

        base, ext = os.path.splitext(self.received.path)
        corrupted_path = f"{base}_corrupted{ext}"

        try:
            with open(corrupted_path, "wb") as f:
                f.write(data)
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not write the simulated file:\n{e}"
            )
            return

        self._apply_image_to_slot(self.received, corrupted_path)
        self._set_status(
            f"Simulated corruption saved as "
            f"{os.path.basename(corrupted_path)}"
        )

        messagebox.showinfo(
            "Corruption Simulated",
            f"{num_flips} byte(s) were flipped.\n\n"
            f"Saved as: {os.path.basename(corrupted_path)}\n\n"
            "Run Check for Corruption to verify the change."
        )

    # ========================================================
    # EXPORT REPORT
    # ========================================================

    def export_report(self):
        if not self.report_rows:
            messagebox.showinfo(
                "Nothing to Export",
                "No checks have been logged yet."
            )
            return

        path = filedialog.asksaveasfilename(
            title="Save Verification Report",
            defaultextension=".csv",
            initialfile="image_corruption_report.csv",
            filetypes=[("CSV files", "*.csv")]
        )

        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "timestamp", "original", "received",
                        "orig_crc", "recv_crc", "status"
                    ]
                )
                writer.writeheader()
                writer.writerows(self.report_rows)
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not save the report:\n{e}"
            )
            return

        self._set_status(f"Report saved to {path}")
        messagebox.showinfo(
            "Report Saved",
            f"The verification report was saved to:\n{path}"
        )

    # ========================================================
    # RESET
    # ========================================================

    def reset_all(self):
        self.multiple_original_paths.clear()
        self.multiple_received_paths.clear()

        self.original.path = None
        self.original.crc = None
        self.original.size_bytes = None
        self.original.photo = None

        self.received.path = None
        self.received.crc = None
        self.received.size_bytes = None
        self.received.photo = None

        for slot in (self.original, self.received):
            slot.preview_widget.configure(
                image="", text="No image loaded"
            )
            slot.info_label.configure(text="File: —")
            slot.size_label.configure(text="Size: —")
            slot.crc_label.configure(text="—")

        self.report_rows.clear()

        self._refresh_multiple_lists()
        self._set_single_status(
            "Load both images, then check for corruption.",
            None
        )
        self._set_status("Application reset. Ready for a new comparison.")

        self.refresh_dashboard()
        self.refresh_report_table()

    # ========================================================
    # START
    # ========================================================


def main():
    root = tk.Tk()
    app = CorruptionDetectorDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
