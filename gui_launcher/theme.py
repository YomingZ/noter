"""Theme module — Windows 11 Fluent Design system.

Clean, modern palette inspired by Microsoft's Fluent Design.
Provides surface elevations, accent colors, and mode switching.
Zero PyQt dependency — pure color constants and mode switching.
"""


class Theme:
    """Windows 11 Fluent Design system — clean, professional, native feel."""

    DARK_MODE = False

    # Accent colors — Windows Blue
    ACCENT_PRIMARY = "#0078D4"
    ACCENT_PRIMARY_LIGHT = "#4BA0E8"
    ACCENT_PRIMARY_DARK = "#005A9E"
    ACCENT_HOVER = "#1B86D9"
    ACCENT_PRESSED = "#006ABF"
    SUCCESS_GREEN = "#107C10"
    WARNING_ORANGE = "#FFAA44"
    ERROR_RED = "#E81123"
    ERROR_RED_DARK = "#C50E1F"

    LIGHT = {
        # Base — clean white/gray like Windows 11
        'bg_primary': '#FFFFFF',
        'bg_secondary': '#F3F3F3',
        'bg_tertiary': '#FBFBFB',
        'bg_elevated': '#FFFFFF',
        # Glass
        'bg_glass': 'rgba(255, 255, 255, 0.85)',
        # Surface elevation (1 = lowest, 3 = highest)
        'surface_1': '#FFFFFF',
        'surface_2': '#FAFAFA',
        'surface_3': '#F5F5F5',
        # Borders — subtle grays
        'border': '#C4C4C4',
        'border_light': '#E5E5E5',
        'border_lighter': '#F0F0F0',
        # Text — crisp black/gray
        'text_primary': '#1A1A1A',
        'text_secondary': '#606060',
        'text_tertiary': '#8C8C8C',
        'text_inverse': '#FFFFFF',
        # Special
        'shadow': 'rgba(0, 0, 0, 0.06)',
        'shadow_heavy': 'rgba(0, 0, 0, 0.12)',
        'scrollbar': '#C4C4C4',
        'scrollbar_hover': '#A0A0A0',
    }

    DARK = {
        # Base — dark grays like Windows 11 Dark Mode
        'bg_primary': '#202020',
        'bg_secondary': '#2D2D2D',
        'bg_tertiary': '#383838',
        'bg_elevated': '#2D2D2D',
        # Glass
        'bg_glass': 'rgba(32, 32, 32, 0.85)',
        # Surface elevation
        'surface_1': '#2D2D2D',
        'surface_2': '#333333',
        'surface_3': '#383838',
        # Borders
        'border': '#505050',
        'border_light': '#3D3D3D',
        'border_lighter': '#353535',
        # Text
        'text_primary': '#FFFFFF',
        'text_secondary': '#ABABAB',
        'text_tertiary': '#7A7A7A',
        'text_inverse': '#202020',
        # Special
        'shadow': 'rgba(0, 0, 0, 0.18)',
        'shadow_heavy': 'rgba(0, 0, 0, 0.30)',
        'scrollbar': '#505050',
        'scrollbar_hover': '#686868',
    }

    @classmethod
    def get(cls, key: str) -> str:
        colors = cls.DARK if cls.DARK_MODE else cls.LIGHT
        return colors.get(key, '#000000')

    @classmethod
    def toggle(cls):
        cls.DARK_MODE = not cls.DARK_MODE

    @classmethod
    def init_from_system(cls):
        try:
            import darkdetect
            cls.DARK_MODE = darkdetect.isDark()
        except Exception:
            pass

    @classmethod
    def card_style(cls, elevated: bool = False) -> str:
        """Card background style with optional elevation."""
        if elevated:
            return f"background-color: {cls.get('surface_3')};"
        return f"background-color: {cls.get('bg_secondary')};"

    @classmethod
    def gradient_accent(cls) -> str:
        """Accent gradient for buttons and highlights."""
        return (
            f"qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            f"stop:0 {cls.ACCENT_PRIMARY_LIGHT}, stop:1 {cls.ACCENT_PRIMARY})"
        )

    @classmethod
    def shadow_style(cls, blur: int = 12) -> str:
        """Drop shadow for cards and floating elements."""
        color = cls.get('shadow')
        return (
            f"background-color: {cls.get('bg_primary')}; "
            f"border: 1px solid {cls.get('border_light')};"
        )
