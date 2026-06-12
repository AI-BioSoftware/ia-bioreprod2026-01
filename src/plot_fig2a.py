"""Reproduce Fig 2A heatmap (S. cerevisiae periodic cell-cycle genes) from raw data.

This script allows the user to generate the heatmap in Fig 2A by providing the path to
the original Excel file containing the periodic gene expression data.
The output figure is automatically saved in the 'plots' directory.
"""

import warnings
from pathlib import Path

import click
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm


def load_periodic_genes(xlsx_path: str) -> pd.DataFrame:
    """Load and order the 1246 S. cerevisiae periodic genes from S1 Table.

    Parameters
    ----------
    xlsx_path : str
        Path to an Excel file containing the periodic gene data.

    Returns
    -------
    pd.DataFrame
        Genes × time-points, minutes as columns, sorted by peak-time order.
    """
    logger.info(f"Loading periodic gene data from {xlsx_path}...")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df = pd.read_excel(xlsx_path, skiprows=2)
    except FileNotFoundError:
        print(f"Error: The file '{xlsx_path}' was not found.")
        raise
    except Exception as e:
        print(f"Error reading the Excel file: {e}")
        raise
    # Filter out columns that represent time-points (numeric columns)
    time_cols = [c for c in df.columns if isinstance(c, (int, float))]
    periodic = (
        df[(df["LS_cutoff"] == "Yes") & df["Figure2A_order_peaktime"].notna()]
        .sort_values("Figure2A_order_peaktime")
        .set_index("gene_ID")[time_cols]
    )
    logger.success(
        f"Loaded {len(periodic)} periodic genes with {len(time_cols)} time-points each."
    )
    return periodic


def zscore(df: pd.DataFrame) -> pd.DataFrame:
    """Z-score normalize each row (gene) independently.

    Parameters
    ----------
    df : pd.DataFrame
        Genes × time-points FPKM matrix.

    Returns
    -------
    pd.DataFrame
        Z-scored DataFrame clipped to [-2, 2].
    """
    mu, sigma = df.mean(axis=1), df.std(axis=1)
    return df.sub(mu, axis=0).div(sigma.replace(0, np.nan), axis=0).clip(-2, 2)


def plot_heatmap(zdf: pd.DataFrame, output_path: Path) -> None:
    """Render and save the heatmap matching Fig 2A style.

    Parameters
    ----------
    zdf : pd.DataFrame
        Z-scored genes × time-points matrix, genes ordered by peak time.
    output_path : Path
        Output file path where the figure will be saved.
    """
    logger.info("Plotting the heatmap...")
    fig, ax = plt.subplots(figsize=(4.5, 6))
    # 1. Custom colormap to match Kelliher et al. style (Blue -> Black -> Yellow)
    colors = ["#04e8e8", "#000000", "#FFFF00"]
    custom_cmap = LinearSegmentedColormap.from_list("BlueBlackYellow", colors, N=256)
    norm = TwoSlopeNorm(vmin=-2, vcenter=0, vmax=2)
    # 2. Added origin="lower" to prevent the vertical inversion of genes
    im = ax.imshow(
        zdf.values,
        aspect="auto",
        cmap=custom_cmap,
        norm=norm,
        interpolation="none",
        origin="lower",
    )
    # x-axis: time in minutes (show every 50 min)
    times = list(zdf.columns)
    tick_idx = [i for i, t in enumerate(times) if t % 50 == 0]
    ax.set_xticks(tick_idx)
    ax.set_xticklabels([str(times[i]) for i in tick_idx], fontsize=7)
    ax.set_xlabel("time (minutes)", fontsize=8)
    # y-axis label
    ax.set_yticks([])
    ax.set_ylabel(f"Top Periodic Genes ({len(zdf)})", fontsize=8)
    # colorbar
    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02, ticks=[-2, -1, 0, 1, 2])
    cbar.ax.tick_params(labelsize=7)
    cbar.set_label("z-score", fontsize=7)
    ax.set_title("Saccharomyces cerevisiae", fontstyle="italic", fontsize=9)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    logger.success(f"Saved to {output_path} successfully!")


@click.command()
@click.option(
    "--xlsx_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to the Excel file containing the periodic gene data.",
)
@click.option(
    "--output",
    required=True,
    type=click.Path(file_okay=True, dir_okay=False),
    help="Output figure filename.",
)
def main(xlsx_path: str, output: str) -> None:
    """Generate Fig 2A heatmap of S. cerevisiae cell-cycle periodic genes."""
    logger.info("Generating the heatmap of S. cerevisiae cell-cycle periodic genes...")
    # Create the folder if it doesn't exist
    plots_dir = Path("plots")
    plots_dir.mkdir(exist_ok=True)
    output_path = plots_dir / output
    # Load the data
    dataframe = load_periodic_genes(xlsx_path)
    # Compute
    zdf = zscore(dataframe)
    logger.success(
        "Successfully computed z-scores for the periodic gene expression data."
    )
    # Plot
    plot_heatmap(zdf, output_path)


if __name__ == "__main__":
    main()
