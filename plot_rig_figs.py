from sys import argv
from typing import Any

import matplotlib.pyplot as plt  # type: ignore
import numpy as np

virus_sim_template = "data/viruses/r0={r0}/reduction_factor={rf}.txt"
xlim = [0.1 - 0.025, 0.525]
ylim = [-0.05, 1.05]
xticks = np.arange(0.1, 0.55, 0.1)


def load_cases(i_tsamp: int, **kwargs) -> np.ndarray:
    with open(virus_sim_template.format(**kwargs)) as data:
        cases = np.loadtxt(data, delimiter=",", dtype=int)
        return cases[:, i_tsamp]


def sample_total(
    cases: np.ndarray, n_rigs: int, n_years: int, n_samples: int
) -> np.ndarray:
    choices = np.random.choice(cases, size=(n_samples, n_years * n_rigs))
    return np.sum(choices, axis=1)


def power(
    test_stat_control: np.ndarray, test_stat_alt: np.ndarray, alpha: float = 0.05
) -> np.floating[Any]:
    t_thresh = np.quantile(test_stat_control, 1 - alpha, axis=-1)
    return np.mean(test_stat_alt > np.expand_dims(t_thresh, axis=(-1, -2)))


def power_from_cases(
    cases_control: np.ndarray,
    cases_uv: np.ndarray,
    n_rigs: int,
    n_years: int,
    n_samples: int,
) -> np.floating[Any]:
    samps_control = sample_total(
        cases_control,
        n_years,
        n_rigs,
        n_samples,
    )
    samps_uv = sample_total(
        cases_uv,
        n_years,
        n_rigs,
        n_samples,
    )
    return power(
        samps_control - np.random.permutation(samps_control), samps_control - samps_uv
    )


def s_if_plural(n: int) -> str:
    if n == 1:
        return ""
    else:
        return "s"


def format_ax(ax, x_pos: int, n_years: int, legend_title: str):
    if x_pos == 0:
        ax.set_ylabel("Power")
    if x_pos == 1:
        ax.legend(title=legend_title, frameon=False)
        ax.set_yticklabels([])
    ax.set_title(f"{n_years} winter{s_if_plural(n_years)}", fontsize=10)
    ax.set_ylim(ylim)
    ax.set_xlim(xlim)
    ax.set_xticks(xticks)


def plot_main_text_fig(
    n_samples: int,
    n_rigs: int,
    N_YEARS: list[int],
    R0: list[float],
    RF: list[float],
):
    fig, axes = plt.subplots(1, len(N_YEARS), layout="constrained", figsize=(5, 2))
    for j, n_years in enumerate(N_YEARS):
        ax = axes[j]
        for r0 in R0:
            powers = [
                power_from_cases(
                    load_cases(i_tsamp=2, r0=r0, rf=1.0),
                    load_cases(i_tsamp=2, r0=r0, rf=rf),
                    n_rigs,
                    n_years,
                    n_samples,
                )
                for rf in RF
            ]
            ax.plot([1 - rf for rf in RF], powers, "-", label=f"{r0}")
        format_ax(ax, j, n_years, legend_title="$R_0$")
    fig.text(0.5, -0.05, "Fraction of transmissions prevented", ha="center")
    return fig


def plot_appendix_fig(
    n_samples: int,
    n_rigs: int,
    N_YEARS: list[int],
    r0: float,
    RF: list[float],
):
    fig, axes = plt.subplots(2, len(N_YEARS), layout="constrained", figsize=(5, 4))
    for j, n_years in enumerate(N_YEARS):
        ax = axes[0, j]
        for i_tsamp, t_samp in [(1, 3), (2, 7)]:
            powers = [
                power_from_cases(
                    load_cases(i_tsamp=i_tsamp, r0=r0, rf=1.0),
                    load_cases(i_tsamp=i_tsamp, r0=r0, rf=rf),
                    n_rigs,
                    n_years,
                    n_samples,
                )
                for rf in RF
            ]
            if t_samp == 7:
                dash = "-"
            else:
                dash = "--"
            ax.plot([1 - rf for rf in RF], powers, dash, color="C0", label=f"{t_samp}")
        format_ax(ax, j, n_years, legend_title="Days between\nsamples")

    for j, n_years in enumerate(N_YEARS):
        ax = axes[1, j]
        for frac_missing in [0.0, 0.5, 0.9]:
            powers = [
                power_from_cases(
                    np.random.binomial(
                        n=load_cases(i_tsamp=2, r0=r0, rf=1.0), p=1 - frac_missing
                    ),
                    np.random.binomial(
                        n=load_cases(i_tsamp=2, r0=r0, rf=rf), p=1 - frac_missing
                    ),
                    n_rigs,
                    n_years,
                    n_samples,
                )
                for rf in RF
            ]
            ax.plot([1 - rf for rf in RF], powers, "-", label=f"{frac_missing}")
        format_ax(ax, j, n_years, legend_title="Fraction of\ntests missing")
    fig.text(0.5, -0.05, "Fraction of transmissions prevented", ha="center")
    return fig


def main():
    _, main_text_file, appendix_file = argv
    R0 = [1.25, 1.5, 1.75, 2.0]
    params = dict(
        n_samples=4000,
        n_rigs=2,
        N_YEARS=[1, 2],
        RF=[0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9],
    )
    np.random.seed(101)
    fig_main_text = plot_main_text_fig(R0=R0, **params)
    fig_main_text.savefig(main_text_file, bbox_inches="tight", dpi=300)
    fig_appendix = plot_appendix_fig(r0=1.5, **params)
    fig_appendix.savefig(appendix_file, bbox_inches="tight", dpi=300)


if __name__ == "__main__":
    main()
