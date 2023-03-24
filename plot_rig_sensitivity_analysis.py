import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def main():
    data = pd.read_csv("data/rig_sensitivity.csv")
    nunique = data.nunique()
    fig, axs = plt.subplots(nunique["crew_size"], nunique["prevalence"], figsize=(6, 6))
    facets = data.groupby(["crew_size", "prevalence"])
    for ax, ((crew_size, prevalence), subset) in zip(np.ravel(axs), facets):
        curves = subset.groupby("reduction_factor")
        for prev, d in curves:
            ax.plot(d["days"], d["power"], label=f"{1 - prev:.1f}")

    for i, row in enumerate(axs):
        for j, ax in enumerate(row):
            ax.set_ylim([0, 1])
            ax.set_xlim([0, 240])
            ax.set_xticks(list(range(0, 241, 60)))
            if i == 0 and j == 0:
                ax.legend(title="Transmission\nreduction", frameon=False)
            if i == 0:
                ax.set_title(
                    (
                        f"prev. = {data.prevalence.unique()[j]}\n"
                        f"crew = {data.crew_size.unique()[i]}"
                    ),
                    fontsize=10,
                )
            else:
                ax.set_title(f"crew = {data.crew_size.unique()[i]}", fontsize=10)
            if i < axs.shape[0] - 1:
                ax.set_xticklabels([])
            else:
                ax.set_xlabel("Days")
            if j == 0:
                ax.set_ylabel("Power")
            else:
                ax.set_yticklabels([])

    fig.savefig("fig/rig_power.png")


if __name__ == "__main__":
    main()
