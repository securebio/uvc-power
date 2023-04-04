import numpy as np
import matplotlib.pyplot as plt  # type: ignore
from typing import Any

virus_sim_template = "data/viruses/r0={r0}/reduction_factor={rf}.txt"
xlim = [0.1 - 0.025, 0.525]
ylim = [-0.05, 1.05]
xticks = np.arange(0.1, 0.55, 0.1)


def load_multivirus(
    i_control: int = 3, i_uv: int = 7, **kwargs
) -> tuple[np.ndarray, np.ndarray]:
    with open(virus_sim_template.format(**kwargs)) as data:
        cases = np.loadtxt(data, delimiter=",", dtype=int)
        return cases[:, i_control], cases[:, i_uv]


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
                    *load_multivirus(r0=r0, rf=rf),
                    n_rigs,
                    n_years,
                    n_samples,
                )
                for rf in RF
            ]
            ax.plot([1 - rf for rf in RF], powers, "-", label=f"{r0}")
        if j == 1:
            ax.legend(title="$R_0$", frameon=False)
            ax.set_yticklabels([])
        if j == 0:
            ax.set_ylabel("Power")
        ax.set_title(f"{n_years} winter{s_if_plural(n_years)}", fontsize=10)
        ax.set_ylim(ylim)
        ax.set_xlim(xlim)
        ax.set_xticks(xticks)
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
        for i_control, i_uv, t_samp in [(2, 6, 3), (3, 7, 7)]:
            powers = [
                power_from_cases(
                    *load_multivirus(i_control=i_control, i_uv=i_uv, r0=r0, rf=rf),
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
        if j == 1:
            ax.legend(title="Days between\nsamples", frameon=False)
            ax.set_yticklabels([])
        if j == 0:
            ax.set_ylabel("Power")
        ax.set_title(f"{n_years} winter{s_if_plural(n_years)}", fontsize=10)
        ax.set_ylim([-0.05, 1.05])
        ax.set_xticks([0.1, 0.2, 0.3, 0.4, 0.5])
        ax.set_xlim([0.05, 0.55])

    for j, n_years in enumerate(N_YEARS):
        ax = axes[1, j]
        for frac_missing in [0.0, 0.5, 0.9]:
            data = [load_multivirus(r0=r0, rf=rf) for rf in RF]
            powers = [
                power_from_cases(
                    np.random.binomial(n=cases_control, p=1 - frac_missing),
                    np.random.binomial(n=cases_uv, p=1 - frac_missing),
                    n_rigs,
                    n_years,
                    n_samples,
                )
                for cases_control, cases_uv in data
            ]
            ax.plot([1 - rf for rf in RF], powers, "-", label=f"{frac_missing}")
        if j == 1:
            ax.legend(title="Fraction of\ntests missing", frameon=False)
            ax.set_yticklabels([])
        if j == 0:
            ax.set_ylabel("Power")
        ax.set_title(f"{n_years} winter{s_if_plural(n_years)}", fontsize=10)
        ax.set_ylim(ylim)
        ax.set_xlim(xlim)
        ax.set_xticks(xticks)
    fig.text(0.5, -0.05, "Fraction of transmissions prevented", ha="center")
    return fig


def main():
    R0 = [1.25, 1.5, 1.75, 2.0]
    params = dict(
        n_samples=4000,
        n_rigs=2,
        N_YEARS=[1, 2],
        RF=[0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9],
    )
    np.random.seed(101)
    fig_main_text = plot_main_text_fig(R0=R0, **params)
    fig_main_text.savefig("fig/main_text.png", bbox_inches="tight", dpi=300)
    fig_appendix = plot_appendix_fig(r0=1.5, **params)
    fig_appendix.savefig("fig/appendix.png", bbox_inches="tight", dpi=300)


if __name__ == "__main__":
    main()
