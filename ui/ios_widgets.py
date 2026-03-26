"""
ui/ios_widgets.py
Shared iOS-style widget helpers for all tabs.
Provides consistent card, button, and layout styling.
"""
import customtkinter as ctk

# iOS Design Tokens
FONT = "Segoe UI"
BLUE = "#007AFF"
GREEN = "#34C759"
RED = "#FF3B30"
ORANGE = "#FF9500"
PURPLE = "#AF52DE"
TEAL = "#5AC8FA"
INDIGO = "#5856D6"

CARD_BG = ("#FFFFFF", "#1C1C1E")
CARD_BORDER = ("#E5E5EA", "#38383A")
BG = ("#F2F2F7", "#000000")
FILL = ("#E5E5EA", "#3A3A3C")
FILL_SEC = ("#D1D1D6", "#48484A")
LABEL = ("#000000", "#FFFFFF")
LABEL_SEC = ("#3C3C43", "#EBEBF5")
LABEL_TER = ("#8E8E93", "#8E8E93")
SEPARATOR = ("#C6C6C8", "#38383A")
LOG_BG = ("#F2F2F7", "#000000")


def ios_card(parent, title, subtitle=None):
    """Create an iOS-style grouped card with title."""
    card = ctk.CTkFrame(
        parent, fg_color=CARD_BG, corner_radius=12,
        border_width=1, border_color=CARD_BORDER
    )
    card.pack(fill="x", pady=(0, 10))

    ctk.CTkLabel(
        card, text=title,
        font=ctk.CTkFont(family=FONT, size=15, weight="bold"),
        text_color=LABEL, anchor="w"
    ).pack(fill="x", padx=18, pady=(14, 2))

    if subtitle:
        ctk.CTkLabel(
            card, text=subtitle,
            font=ctk.CTkFont(family=FONT, size=12),
            text_color=LABEL_TER, anchor="w"
        ).pack(fill="x", padx=18, pady=(0, 6))

    return card


def ios_button(parent, text, command, color=BLUE, width=130, height=34):
    """Create an iOS-style tinted button."""
    # Lighter version of color for hover
    return ctk.CTkButton(
        parent, text=text,
        font=ctk.CTkFont(family=FONT, size=13, weight="bold"),
        height=height, width=width, corner_radius=8,
        fg_color=color, hover_color=_lighter(color),
        text_color="#FFFFFF",
        command=command
    )


def ios_process_btn(parent, command):
    """iOS blue Process button."""
    return ios_button(parent, "Process", command, BLUE)


def ios_save_btn(parent, command):
    """iOS green Save button — initially hidden."""
    btn = ios_button(parent, "Save", command, GREEN, width=110)
    btn.pack(side="left", padx=5, pady=(0, 12))
    btn.pack_forget()
    return btn


def ios_cancel_btn(parent, command):
    """iOS red Cancel button — initially hidden."""
    btn = ios_button(parent, "Cancel", command, RED, width=110)
    btn.pack(side="left", padx=5, pady=(0, 12))
    btn.pack_forget()
    return btn


def ios_select_btn(parent, text, command):
    """iOS-style file select button (tinted outline)."""
    return ctk.CTkButton(
        parent, text=text,
        font=ctk.CTkFont(family=FONT, size=12),
        height=32, width=130, corner_radius=8,
        fg_color="transparent",
        border_width=1, border_color=BLUE,
        text_color=BLUE,
        hover_color=("#E8F0FE", "#1a1a2e"),
        command=command
    )


def ios_entry(parent, width=180, placeholder=""):
    """iOS-style text entry."""
    return ctk.CTkEntry(
        parent, width=width,
        font=ctk.CTkFont(family=FONT, size=12),
        corner_radius=8,
        border_color=CARD_BORDER,
        fg_color=CARD_BG,
        placeholder_text=placeholder
    )


def ios_option_menu(parent, values, variable, width=180):
    """iOS-style option menu."""
    return ctk.CTkOptionMenu(
        parent, values=values, variable=variable,
        font=ctk.CTkFont(family=FONT, size=12),
        width=width, corner_radius=8,
        fg_color=FILL,
        button_color=BLUE,
        button_hover_color=_lighter(BLUE),
        text_color=LABEL
    )


def ios_slider(parent, from_, to, variable, width=180):
    """iOS-style slider."""
    return ctk.CTkSlider(
        parent, from_=from_, to=to, variable=variable,
        width=width,
        progress_color=BLUE,
        button_color=("#FFFFFF", "#FFFFFF"),
        button_hover_color=("#E5E5EA", "#E5E5EA"),
        fg_color=FILL
    )


def ios_checkbox(parent, text):
    """iOS-style checkbox (toggle)."""
    return ctk.CTkCheckBox(
        parent, text=text,
        font=ctk.CTkFont(family=FONT, size=12),
        fg_color=BLUE, hover_color=_lighter(BLUE),
        text_color=LABEL
    )


def ios_scrollable(parent):
    """Scrollable container matching iOS background."""
    return ctk.CTkScrollableFrame(parent, fg_color=BG)


def ios_log_box(parent, height=100):
    """iOS-style log textbox."""
    return ctk.CTkTextbox(
        parent, height=height,
        font=ctk.CTkFont(family="Consolas", size=11),
        fg_color=LOG_BG,
        corner_radius=10
    )


def ios_section_label(parent, text):
    """Section header label."""
    ctk.CTkLabel(
        parent, text=text,
        font=ctk.CTkFont(family=FONT, size=13, weight="bold"),
        text_color=LABEL_TER, anchor="w"
    ).pack(fill="x", pady=(12, 5))


def ios_label(parent, text, size=12, color=LABEL, weight="normal"):
    """Standard iOS label."""
    return ctk.CTkLabel(
        parent, text=text,
        font=ctk.CTkFont(family=FONT, size=size, weight=weight),
        text_color=color
    )


def _lighter(hex_color):
    """Lighten a hex color by ~20%."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = min(255, r + 40)
    g = min(255, g + 40)
    b = min(255, b + 40)
    return f"#{r:02x}{g:02x}{b:02x}"
