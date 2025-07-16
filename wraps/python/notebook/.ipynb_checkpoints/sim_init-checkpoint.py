from IPython.display import display
import ipywidgets as ipw
import tissue_forge as tf
import numpy as np
import widgets as tfnw
from typing import Any, Dict, Optional

LABELTEXT_CUTOFF = "Cutoff: "
LABELTEXT_DT = "Time Discretization: "
LABELTEXT_DIM = "Dimensions: "

def set_float(**kwargs):
    def_kwargs = dict(
        min=1,
        max=10,
        description="Value: ",
        disabled=False,
        continuous_update=False,
        orientation="horizontal",
        readout=True,
        readout_format=".1f",
    )
    def_kwargs.update(kwargs)
    if "step" not in def_kwargs:
        def_kwargs["step"] = (def_kwargs["max"] - def_kwargs["min"]) / 100

    box, widget = tfnw.scalar_text(
        float,
        initial_value=kwargs.get("initial_value"),
        field_kwargs=def_kwargs,
    )
    return box, widget


def init(show=False, **kwargs):
    def set_settings(*args, **kwargs):
        dim = []
        for i in range(3):
            dimBox, dimWidget = set_float(
                min=0, max=100, description=LABELTEXT_DIM + " x: "if i == 0 else chr(i + 120), initial_value=10
            )
            dim.append(dimWidget)

        cutoffBox, cutoffWidget = set_float(
            min=0, max=100, description=LABELTEXT_CUTOFF, initial_value=1
        )
        dtBox, dtWidget = set_float(
            min=0, max=1, description=LABELTEXT_DT, initial_value=0.01
        )
        title = ipw.Label("Settings", style=dict(font_weight='bold'))
        return ipw.VBox([title, cutoffWidget, dtWidget, ipw.HBox(dim)])

    def boundary_conditions(*args, **kwargs):
        
        return

    def advanced(*args, **kwargs):
        return

    settings = set_settings()

    tab_contents = ["Settings", "Boundary Conditions", "Advanced"]
    children = [settings, settings, settings]

    tabs = ipw.Tab()
    tabs.children = children
    tabs.titles = ["Settings", "Boundary Conditions", "Advanced"]

    def initialize_load(*args, **kwargs):
        initialize = ipw.Button(
            description="Initialize",
            disabled=False,
            button_style="info",
            tooltip="Initialize simulation",
            clear_output=True,
        )

        load_settings = ipw.Button(
            description="Load Settings",
            disabled=False,
            tooltip="Load settings from JSON file",
            clear_output=True,
        )
        return ipw.HBox([initialize, load_settings], layout=ipw.Layout(width="100%"))

    buttons = initialize_load()
    widget = ipw.VBox([tabs, buttons])

    # if show:
    #     display(widget)
    return widget
