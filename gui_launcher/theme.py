"""Theme module — "Scholarly Warmth" design system.

Warm-toned academic palette inspired by cream paper and Obsidian's deep indigo.
Provides surface elevations, glass effects, shadows, and gradient definitions.
Zero PyQt dependency — pure color constants and mode switching.
"""


class Theme:
    """Scholarly Warmth design system — warm neutrals meet deep indigo dark mode."""

    DARK_MODE = False

    # Accent colors — warm amber gold for scholarly feel
    ACCENT_AMBER = "#D4A047"
    ACCENT_AMBER_LIGHT = "#E8C47A"
    ACCENT_AMBER_DARK = "#B8863A"
    ACCENT_BLUE = "#4A6CF7"
    ACCENT_BLUE_DARK = "#3451DB"
    SUCCESS_GREEN = "#34C759"
    WARNING_ORANGE = "#FF9500"
    ERROR_RED = "#FF3B30"
    ERROR_RED_DARK = "#D32F2F"

    LIGHT = {
        # Base — warm cream tones like quality paper
        'bg_primary': '#FAF8F5',
        'bg_secondary': '#F2EFEB',
        'bg_tertiary': '#E8E4DD',
        'bg_elevated': '#FFFFFF',
        # Glass — frosted overlay
        'bg_glass': 'rgba(255, 255, 255, 0.72)',
        # Surface elevation (1 = lowest, 3 = highest)
        'surface_1': '#FFFFFF',
        'surface_2': '#FAFAFA',
        'surface_3': '#F5F5F0',
        # Borders — warm grays
        'border': '#D4CFC8',
        'border_light': '#E5E1DA',
        'border_lighter': '#F0EDE8',
        # Text — soft black
        'text_primary': '#2D2A24',
        'text_secondary': '#8B8580',
        'text_tertiary': '#B5AFA8',
        'text_inverse': '#FFFFFF',
        # Special
        'shadow': 'rgba(45, 42, 36, 0.08)',
        'shadow_heavy': 'rgba(45, 42, 36, 0.16)',
        'scrollbar': '#D4D0C9',
        'scrollbar_hover': '#BDB8B0',
    }

    DARK = {
        # Base — deep indigo, warmer than flat gray
        'bg_primary': '#1C1B2B',
        'bg_secondary': '#252438',
        'bg_tertiary': '#2F2E45',
        'bg_elevated': '#2A293E',
        # Glass
        'bg_glass': 'rgba(28, 27, 43, 0.78)',
        # Surface elevation
        'surface_1': '#2A293E',
        'surface_2': '#302F45',
        'surface_3': '#38374F',
        # Borders — purple-toned grays
        'border': '#3E3D55',
        'border_light': '#35344A',
        'border_lighter': '#2E2D42',
        # Text
        'text_primary': '#EEEDF2',
        'text_secondary': '#9695B0',
        'text_tertiary': '#6A6982',
        'text_inverse': '#1C1B2B',
        # Special
        'shadow': 'rgba(0, 0, 0, 0.24)',
        'shadow_heavy': 'rgba(0, 0, 0, 0.36)',
        'scrollbar': '#3E3D55',
        'scrollbar_hover': '#525170',
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
            f"stop:0 {cls.ACCENT_AMBER}, stop:1 {cls.ACCENT_AMBER_DARK})"
        )

    @classmethod
    def shadow_style(cls, blur: int = 12) -> str:
        """Drop shadow for cards and floating elements."""
        color = cls.get('shadow')
        return (
            f"background-color: {cls.get('bg_primary')}; "
            f"border: 1px solid {cls.get('border_light')};"
        )
