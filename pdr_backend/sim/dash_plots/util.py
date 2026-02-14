from __future__ import annotations

import concurrent.futures
from typing import Callable, TypeVar

import plotly.graph_objects as go

from pdr_backend.aimodel import aimodel_plotter
from pdr_backend.sim.dash_plots.view_elements import figure_names
from pdr_backend.sim.sim_plotter import SimPlotter

T = TypeVar("T")


def call_with_timeout(timeout_s: float, fn: Callable[[], T]) -> T:
    ex = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    fut = ex.submit(fn)
    try:
        return fut.result(timeout=timeout_s)
    except concurrent.futures.TimeoutError as e:
        fut.cancel()
        raise TimeoutError(f"Timed out after {timeout_s} seconds") from e
    finally:
        ex.shutdown(wait=False)


def get_figures_by_state(
    sim_plotter: SimPlotter,
    selected_vars: list[str],
    timeout: float = 2,
) -> dict[str, go.Figure]:
    figures: dict[str, go.Figure] = {}

    for key in figure_names:
        if not key.startswith("aimodel"):

            def _work(k: str = key) -> go.Figure:
                return getattr(sim_plotter, f"plot_{k}")()

            try:
                fig = call_with_timeout(timeout, _work)
            except TimeoutError:
                fig = go.Figure()

        else:

            def _work(k: str = key) -> go.Figure:
                if k in ("aimodel_response", "aimodel_varimps"):
                    sim_plotter.aimodel_plotdata.sweep_vars = [
                        sim_plotter.aimodel_plotdata.colnames.index(var)
                        for var in selected_vars
                    ]

                func_name = getattr(aimodel_plotter, f"plot_{k}")
                return func_name(sim_plotter.aimodel_plotdata)

            try:
                fig = call_with_timeout(timeout, _work)
            except TimeoutError:
                fig = go.Figure()

        figures[key] = fig

    return figures
