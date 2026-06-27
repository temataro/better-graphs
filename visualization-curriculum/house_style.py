"""House style: one import, consistent charts. Grow this as you work through the modules."""
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.ticker import FuncFormatter

STYLE = Path(__file__).with_name("minerva.mplstyle")
FONTS_DIR = Path(__file__).with_name("fonts")


def _register_fonts() -> None:
    """Make the vendored League fonts available to matplotlib (idempotent).

    Run on import so any style that names 'League Spartan' (or 'Junction')
    resolves with zero system font install — the .otf files ship in fonts/.
    """
    if not FONTS_DIR.is_dir():
        return
    registered = {f.fname for f in fm.fontManager.ttflist}
    for path in sorted(FONTS_DIR.glob("*.[ot]tf")):
        if str(path) not in registered:
            fm.fontManager.addfont(str(path))


_register_fonts()

def apply_theme(mode: str = "detailed") -> None:
    """Apply the base style, then mode-specific overrides.
    mode='executive' → stripped, one-message;  mode='detailed' → denser, multi-panel.
    """
    plt.style.use(str(STYLE))
    if mode == "executive":
        plt.rcParams.update({"axes.grid": False, "axes.titlesize": 16, "figure.figsize": (8, 4.5)})
    elif mode == "detailed":
        plt.rcParams.update({"axes.grid": True, "figure.figsize": (9, 6)})
    # TODO (M7): add a 'print' mode — vector defaults, embedded fonts (pdf.fonttype=42).

def despine(ax, keep=("left", "bottom"), outward=8):
    """M5 polish: drop unused spines, offset the kept ones (range-frame look)."""
    for side, spine in ax.spines.items():
        spine.set_visible(side in keep)
        if side in keep and outward:
            spine.set_position(("outward", outward))
    return ax

def thousands(ax, axis="y"):
    """Unit-aware tick formatting you always forget to add."""
    fmt = FuncFormatter(lambda v, _: f"{v:,.0f}")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)
    return ax

def add_colorbar(fig, mappable, ax, **kw):
    """Colorbar pre-sized to the axes (the fraction/pad magic numbers)."""
    return fig.colorbar(mappable, ax=ax, fraction=0.046, pad=0.04, **kw)

def outlined_text(ax, x, y, s, fg="white", lw=3, **kw):
    """Label that stays legible over a busy background."""
    return ax.text(x, y, s, path_effects=[pe.Stroke(linewidth=lw, foreground=fg), pe.Normal()], **kw)

def takeaway_title(ax, message, sub=None):
    """Title = the message, not the variables. TODO: wire in highlight_text for colored series words."""
    ax.set_title(message, loc="left", pad=12)
    if sub:
        ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=10, color="#666666")
    return ax

# TODO (M7): chart builders — bar(), line(), slope(), dumbbell(), dist(), heatmap()
# each returning (fig, ax) with theme + polish already applied.
