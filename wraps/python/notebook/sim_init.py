from IPython.display import display
import ipywidgets as ipw
import tissue_forge as tf
import numpy as np
import widgets as tfnw
import saveandscreenshot as sns
from ipyfilechooser import FileChooser
import os
from typing import Any, Dict, Optional

save_folder: Optional[str] = None

LABELTEXT_CUTOFF = "Cutoff: "
LABELTEXT_BC = "Boundaries: "
LABELTEXT_DT = "Time Discretization: "
LABELTEXT_DIM = "Dimensions: "
LABELTEXT_CELLS = "Cells: "
LABELTEXT_THREADS = "Threads: "
LABELTEXT_FLUX_STEPS = "Flux Steps: "
LABELTEXT_INTEGRATOR = "Integrator: "
LABELTEXT_WINDOW_SIZE = "Window Size: "
LABELTEXT_THROW_EXC = "Throw Errors? "
LABELTEXT_SEED = "Seed: "
LABELTEXT_LOAD_FILE = "Load File: "
LABELTEXT_LOGGER_LEVEL = "Logger Level: "

out = ipw.Output(layout={"border": "1px solid black"})


def _set_text(**kwargs):
    def_kwargs = dict(
        min=1,
        max=10,
        description="Value: ",
        disabled=True,
        continuous_update=False,
        orientation="horizontal",
        readout=True,
        readout_format=".1f",
    )
    def_kwargs.update(kwargs)
    if "step" not in def_kwargs:
        def_kwargs["step"] = (def_kwargs["max"] - def_kwargs["min"]) / 100

    box, widget = tfnw.scalar_text(
        kwargs.get("dtype", float),
        initial_value=kwargs.get("initial_value"),
        field_kwargs=def_kwargs,
    )
    return box, widget

def _set_dropdown(**kwargs):
    def_kwargs = dict(
        description="Value: ",
        disabled=True,
        continuous_update=False,
        orientation="horizontal",
        readout=True,
        readout_format=".1f",
    )
    def_kwargs.update(kwargs)

    widget = ipw.Dropdown(
        **def_kwargs,
    )
    return widget


# def _set_vector(
#     show=False,
#     label_kwargs: Dict[str, Any] = None,
#     field_kwargs: Dict[int, Dict[str, Any]] = None,
# ):
#     def_label_kwargs = dict(style=dict(description_width="initial"))
#     if label_kwargs is not None:
#         def_label_kwargs.update(label_kwargs)
#     def_field_kwargs = {i: dict(min=0.0, max=100, step=1) for i in range(3)}
#     if field_kwargs is not None:
#         for k, v in field_kwargs.items():
#             def_field_kwargs[k].update(v)
#     label = ipw.Label(LABELTEXT_DIM, **def_label_kwargs)
#     box, widgets = tfnw.vector_textb(
#         ndim=3,
#         dtype=float,
#         initial_values=[10, 10, 10],
#         label=label,
#         field_kwargs=def_field_kwargs,
#     )
#     if show:
#         display(box)
#     return box, *widgets

def _set_vector():
    data = []
    for i in range(3):
        dataBox, dataWidget = _set_text(
            min=0,
            max=100,
            description= chr(i + 120) + ": ",
            initial_value=0,
            dtype=float,
        )
        data.append(dataWidget)
    dimBox = ipw.HBox(data)
    return dimBox

def _checkbox(widget):
    def set_default(change):
        def set_widget_state(widget, disabled_state):
            if hasattr(widget, 'disabled'):
                widget.disabled = disabled_state
            elif hasattr(widget, 'children'):
                for child in widget.children:
                    set_widget_state(child, disabled_state)
        
        set_widget_state(widget, change["new"])

    checkbox = ipw.Checkbox(value=True, description="", indent=False, disabled=True)
    checkbox.observe(set_default, names="value")

    return checkbox


def _set_settings(self):
    widgets = self.widgets

    dim = []
    for i in range(3):
        dimBox, dimWidget = _set_text(
            min=0,
            max=100,
            description=LABELTEXT_DIM + " x: " if i == 0 else chr(i + 120) + ": ",
            initial_value=10,
            dtype=float,
        )
        dim.append(dimWidget)
    widgets["dim"] = dim
    dimBox = ipw.HBox(dim)

    cutoffBox, cutoffWidget = _set_text(
        min=0, max=100, description=LABELTEXT_CUTOFF, initial_value=1, dtype=float
    )
    widgets["cutoff"] = cutoffWidget
    dtBox, dtWidget = _set_text(
        min=0, max=1, description=LABELTEXT_DT, initial_value=0.01, dtype=float
    )
    widgets["dt"] = dtWidget

    title = ipw.Label("Settings", style=dict(font_weight="bold"))

    settings_widgets = [title, cutoffWidget, dimBox, dtWidget]

    return ipw.VBox(
        settings_widgets,
        layout=ipw.Layout(padding="0px 40px"),
    )


def _set_bc(self):
    widgets = self.widgets
    everywhereOptions = ipw.Dropdown(
        options=[(bc.name, bc.value) for bc in tf.BoundaryTypeFlags],
        disabled=True
    )    

    faces = [["x", "left", "right"], ["y", "bottom", "top"], ["z", "front", "back"]]
    bcs = [("none", None), ("periodic", tf.BOUNDARY_PERIODIC), ("freeslip", tf.BOUNDARY_FREESLIP), ("noslip", tf.BOUNDARY_NO_SLIP), ("velocity", {"velocity": [0,0,0]}), ("potential", tf.BOUNDARY_POTENTIAL), ("reset", ('periodic', 'reset'))]

    def is_velocity(change, hbox):
        widget = hbox.children[1]
        if isinstance(change["new"], dict):
            widget.layout.display = ""
        else:
            widget.layout.display = "none"

    def dimension(face):
        data = []
        for key in face:
            velocity = _set_vector()
            velocity.layout = ipw.Layout(display="none", margin="0px 0px 10px 0px")

            faces = ipw.VBox([_set_dropdown(description=key, options=bcs), velocity])
            dropdown = faces.children[0]

            dropdown.observe(lambda change, hbox=faces: is_velocity(change, hbox), names="value")
            data.append(faces)

        return ipw.VBox(data)

    items = [dimension(face) for face in faces]

    dimensions = ipw.Tab()
    dimensions.children = items
    dimensions.titles = [chr(i + 120) for i in range(3)]
    dimensions.layout = ipw.Layout(margin="10px 0px")

    def get_bcDict():
        data = {}
        for dimension in items: # vbox[x, top, left]
            for face in dimension.children:
                dropdown = face.children[0]
                data[dropdown.description] = dropdown.value

        return data
        
    def set_everywhere(change):
        def set_widget_state(widget, disabled_state):
            if hasattr(widget, 'disabled'):
                widget.disabled = disabled_state
            elif hasattr(widget, 'children'):
                for child in widget.children:
                    set_widget_state(child, disabled_state)
        
        set_widget_state(dimensions, change["new"])

    isEverywhere = ipw.Checkbox(value=True, description="Apply Everywhere?", indent=False, disabled=True)
    everywhereBc = ipw.HBox(
        [               
            isEverywhere,
            everywhereOptions,
        ]
    )
    widgets["bc"] = everywhereOptions
    isEverywhere.observe(set_everywhere, names="value")

    def get_velocity(hbox):
        dropdown = hbox.children[0]
        velocity = hbox.children[1]
        data = []
        for dimension in velocity.children:
            data.append(dimension.value)
        return data

    def set_settings(_):
        if isEverywhere.value:
            widgets["bc"] = everywhereOptions
        else:
            data = {}
            for dimension in items: # vbox[x, top, left]
                for face in dimension.children:
                    dropdown = face.children[0]
                    if isinstance(dropdown.value, dict):
                        data[dropdown.description] = {"velocity": get_velocity(face)}
                    else:
                        data[dropdown.description] = dropdown.value
            widgets["bc"] = data
        with self.out: print(widgets["bc"])
    
    save_settings = ipw.Button(
        description="Save Settings",
        disabled=False,
        tooltip="Save settings",
        clear_output=True,
    )

    save_settings.on_click(set_settings)
    
    title = ipw.Label("Boundary Conditions", style=dict(font_weight="bold"))
    return ipw.VBox(
        [title, everywhereBc, dimensions, save_settings],
        layout=ipw.Layout(padding="0px 40px"),
    )

def _set_advanced(self):
    widgets = self.widgets
    cells = []
    for i in range(3):
        cellBox, cellWidget = _set_text(
            min=0,
            max=100,
            description=LABELTEXT_CELLS + " x: " if i == 0 else chr(i + 120) + ": ",
            initial_value=4,
            dtype=int,
        )
        cells.append(cellWidget)
    widgets["cells"] = cells

    threadsBox, threadsWidget = _set_text(
        min=0,
        max=100,
        description=LABELTEXT_THREADS,
        initial_value=20,
        dtype=int,
    )
    widgets["threads"] = threadsWidget

    fluxBox, fluxWidget = _set_text(
        min=0, max=100, description=LABELTEXT_FLUX_STEPS, initial_value=1, dtype=int
    )
    widgets["flux_steps"] = fluxWidget

    integratorWidget = ipw.Dropdown(
        options=[
            ("Foward Euler", tf.EngineIntegratorTypes.forward_euler.value),
            ("Runge Kutta", tf.EngineIntegratorTypes.runge_kutta4.value),
        ],
        value=tf.EngineIntegratorTypes.forward_euler.value,
        description=LABELTEXT_INTEGRATOR,
        disabled=True
    )
    widgets["integrator"] = integratorWidget

    windowSize = []
    for i in range(2):
        windowSizeBox, windowSizeWidget = _set_text(
            min=0,
            max=1000,
            description=(
                LABELTEXT_WINDOW_SIZE + " x: " if i == 0 else chr(i + 120) + ": "
            ),
            initial_value=800 if i == 0 else 600,
            dtype=int,
        )
        windowSize.append(windowSizeWidget)
    widgets["window_size"] = windowSize

    throwExcWidget = ipw.HBox(
        [
            ipw.Label(LABELTEXT_THROW_EXC),
            ipw.Checkbox(value=False, description="", indent=False),
        ]
    )
    widgets["throw_exc"] = throwExcWidget

    seedBox, seedWidget = _set_text(
        min=0, max=100, description=LABELTEXT_SEED, initial_value=0, dtype=int
    )
    widgets["seed"] = seedWidget

    loadWidget = ipw.Text(
        placeholder="Load File Name",
        description=LABELTEXT_LOAD_FILE,
        disabled=True
    )
    widgets["load_file"] = loadWidget

    loggerBox, loggerWidget = _set_text(
        min=0,
        max=100,
        description=LABELTEXT_LOGGER_LEVEL,
        initial_value=0,
        dtype=int,
    )
    widgets["logger_level"] = loggerWidget

    title = ipw.Label("Advanced", style=dict(font_weight="bold"))
    return ipw.VBox(
        [
            title,
            ipw.HBox(cells),
            fluxWidget,
            integratorWidget,
            loadWidget,
            loggerWidget,
            seedWidget,
            threadsWidget,
            throwExcWidget,
            ipw.HBox(windowSize),
        ],
        layout=ipw.Layout(padding="0px 40px"),
    )    

class _SimInit:
    def __init__(self):
        self.out = ipw.Output(layout={'border': '1px solid black'})
        self.widgets = {};
        self.settings = _set_settings(self)
        self.bc = _set_bc(self)
        self.advanced = _set_advanced(self)
        self.tabs = self._tabs()
        self.layout = self._layout()

    def _tabs(self):
        settings = self.settings
        bc = self.bc
        advanced = self.advanced

        def set_default(change):
            def set_widget_state(widget, disabled_state):
                if hasattr(widget, 'disabled'):
                    widget.disabled = disabled_state
                elif hasattr(widget, 'children'):
                    for child in widget.children:
                        set_widget_state(child, disabled_state)
            
            for container in [settings, bc, advanced]:
                set_widget_state(container, change["new"])

        useDefault = ipw.Checkbox(
            value=True, description="Use Default Values?", disabled=False, indent=False
        )
        useDefault.observe(set_default, names="value")
        defaultSettings = ipw.VBox(
            [useDefault, settings],
        )
        defaultBc = ipw.VBox(
            [useDefault, bc],
        )
        defaultAdvanced = ipw.VBox(
            [useDefault, advanced],
        )

        children = [defaultSettings, defaultBc, defaultAdvanced]

        tabs = ipw.Tab()
        tabs.children = children
        tabs.titles = ["Settings", "Boundary Conditions", "Advanced"]
        return tabs
    
    def _get_data(self):
        data = {}
        for key, value in self.widgets.items():
            if isinstance(value, list):
                data[key] = [w.value for w in value]
            elif isinstance(value, dict):
                data[key] = value
            elif hasattr(value, 'value'):
                data[key] = value.value
        return data

    def _on_init(self, _):
        useDefault = self.tabs.children[0].children[0].value
        if useDefault:
            with self.out: print("Using default values")
            tf.init()

        else:
            data = self._get_data()
            data = {'dim': [7.0, 13.0, 6.0], 'cutoff': 1.0, 'dt': 0.01, 'bc': 0, 'cells': [4, 4, 4], 'threads': 20, 'flux_steps': 1, 'integrator': 0, 'window_size': [800, 600], 'seed': 0, 'logger_level': 0}
            with self.out: 
                print("Using edited values!!")
                print(data)
            tf.init(**data)

    def _layout(self):
        initialize = ipw.Button(
            description="Initialize",
            disabled=False,
            button_style="info",
            tooltip="Initialize simulation",
        )

        initialize.on_click(self._on_init)

        load_settings = ipw.Button(
            description="Load Settings",
            disabled=False,
            tooltip="Load settings from JSON file",
            clear_output=True,
        )
        
        save_settings , output = sns.save_widget()

        buttons = ipw.HBox([initialize, load_settings, save_settings], layout=ipw.Layout(width="100%"))
        widget = ipw.VBox([self.tabs, buttons, self.out])

        return widget

    def show(self):
        display(self.layout)


def init(show=True):
    simInit = _SimInit()
    if show:
        simInit.show()
    return simInit
