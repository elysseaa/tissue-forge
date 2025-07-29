from IPython.display import display
import ipywidgets as ipw
import tissue_forge as tf
import widgets as tfnw
import saveandscreenshot as sns
from IPython.display import display, HTML

"""
Labels
"""
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
LABELTEXT_CLIP_PLANES = "Clip Planes: "

# For boundary conditions
faces = [["x", "left", "right"], ["y", "bottom", "top"], ["z", "front", "back"]]
bcs = [("none", None), ("periodic", tf.BOUNDARY_PERIODIC), ("freeslip", tf.BOUNDARY_FREESLIP), ("noslip", tf.BOUNDARY_NO_SLIP), ("velocity", {"velocity": [0,0,0]}), ("potential", tf.BOUNDARY_POTENTIAL), ("reset", ('periodic', 'reset'))]

"""
Helper functions
"""
def _scalar_text(**kwargs):
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

def _vector_text(**kwargs):
    def_kwargs = dict(
        label="",
        numDims=3,
        initialValue=0,
        withCheckbox=True,
        dtype=int,
        disabled=True
    )
    def_kwargs.update(kwargs)

    data = []
    for i in range(def_kwargs["numDims"]):
        dataBox, dataWidget = _scalar_text(
            min=0,
            max=100,
            description=def_kwargs["label"] + " x: " if i == 0 else chr(i + 120) + ": ",
            initial_value=def_kwargs["initialValue"],
            dtype=def_kwargs["dtype"],
            disabled=def_kwargs["disabled"]
        )
        data.append(dataWidget)
    dataBox = ipw.HBox(data)
    if (def_kwargs["withCheckbox"]): 
        dim = ipw.HBox([_checkbox(dataBox), dataBox])
        return dim
    return dataBox

def _checkbox(widget, **kwargs):
    def_kwargs = dict(
        description=""
    )
    def_kwargs.update(kwargs)

    def set_default(change):
        def set_widget_state(widget, disabled_state):
            if hasattr(widget, 'disabled'):
                widget.disabled = disabled_state
            elif hasattr(widget, 'children'):
                for child in widget.children:
                    set_widget_state(child, disabled_state)
        
        set_widget_state(widget, not change["new"])

    checkbox = ipw.Checkbox(value=False, indent=False, layout = ipw.Layout(width='auto', margin='0'), **def_kwargs)
    checkbox.observe(set_default, names="value")

    return checkbox

"""
Tab Components
"""
def _set_settings(self):
    widgets = self.widgets

    dim = _vector_text(
        label = LABELTEXT_DIM, numDims = 3, initialValue = 10, withCheckbox = True, dtype = float
    )
    widgets["dim"] = dim

    cutoffBox, cutoffWidget = _scalar_text(
        min=0, max=100, description=LABELTEXT_CUTOFF, initial_value=1, dtype=float
    )
    cutoff = ipw.HBox([_checkbox(cutoffWidget), cutoffWidget])
    widgets["cutoff"] = cutoff

    dtBox, dtWidget = _scalar_text(
        min=0, max=1, description=LABELTEXT_DT, initial_value=0.01, dtype=float
    )
    dt = ipw.HBox([_checkbox(dtWidget), dtWidget])
    widgets["dt"] = dt

    title = ipw.Label("Settings", style=dict(font_weight="bold"))

    settings_widgets = [title, cutoff, dim, dt]

    return ipw.VBox(
        settings_widgets,
        layout=ipw.Layout(padding="0px 40px"),
    )


def _set_bc(self):
    widgets = self.widgets
    everywhereOptions = ipw.Dropdown(
        options=[(bc.name, bc.value) for bc in tf.BoundaryTypeFlags],
    )    

    def _dimension(face):
        def _is_velocity(change, hbox):
            widget = hbox.children[1]
            if isinstance(change["new"], dict):
                widget.layout.display = ""
            else:
                widget.layout.display = "none"

        data = []
        for key in face:
            velocity = _vector_text(
                label = "", numDims = 3, initialValue = 0, withCheckbox = False, dtype = float
            )
            velocity.layout = ipw.Layout(display="none", margin="0px 0px 10px 0px")

            faces = ipw.VBox([ipw.Dropdown(description=key, options=bcs, disabled=True), velocity])
            dropdown = faces.children[0]
            dropdown.observe(lambda change, hbox=faces: _is_velocity(change, hbox), names="value")
            
            facesCheckbox = ipw.HBox([_checkbox(faces), faces])
            data.append(facesCheckbox)

        return ipw.VBox(data)

    dimensionsList = [_dimension(face) for face in faces]
    dimensions = ipw.Tab()
    dimensions.children = dimensionsList
    dimensions.titles = [chr(i + 120) for i in range(3)]
    dimensions.layout = ipw.Layout(margin="10px 0px")

    isEverywhere = ipw.Checkbox(value=True, description="Apply Everywhere?", indent=False)
    everywhereBc = ipw.HBox(
        [               
            isEverywhere,
            everywhereOptions,
        ]
    )
    widgets["bc"] = everywhereBc

    def _set_settings(_):
        def _get_velocity(hbox):
            dropdown = hbox.children[0]
            velocity = hbox.children[1]
            data = []
            for dimension in velocity.children:
                data.append(dimension.value)
            return data
    
        if isEverywhere.value:
            widgets["bc"] = everywhereOptions
        else:
            data = {}
            for dimension in dimensionsList: # ipw.VBox[x, top, left]
                for face in dimension.children:
                    checkbox = face.children[0]
                    widget = face.children[1]
                    if checkbox.value == True:
                        dropdown = widget.children[0]
                        if isinstance(dropdown.value, dict):
                            data[dropdown.description] = {"velocity": _get_velocity(widget)}
                        else:
                            data[dropdown.description] = dropdown.value
            widgets["bc"] = data

        with self.out: print("Boundary condition settings saved!")
    
    save_settings = ipw.Button(
        description="Save Settings",
        disabled=False,
        tooltip="Save settings",
    )
    save_settings.on_click(_set_settings)

    title = ipw.Label("Boundary Conditions", style=dict(font_weight="bold"))
    return ipw.VBox(
        [title, everywhereBc, dimensions, save_settings],
        layout=ipw.Layout(padding="0px 40px"),
    )

def _set_advanced(self):
    widgets = self.widgets

    cells = _vector_text(
        label = LABELTEXT_CELLS, numDims = 3, initialValue = 4, withCheckbox = True, dtype = int
    )
    widgets["cells"] = cells

    threadsBox, threadsWidget = _scalar_text(
        min=0,
        max=100,
        description=LABELTEXT_THREADS,
        initial_value=20,
        dtype=int,
    )
    threads = ipw.HBox([_checkbox(threadsWidget), threadsWidget])
    widgets["threads"] = threads

    fluxBox, fluxWidget = _scalar_text(
        min=0, max=100, description=LABELTEXT_FLUX_STEPS, initial_value=1, dtype=int
    )
    flux = ipw.HBox([_checkbox(fluxWidget), fluxWidget])
    widgets["flux_steps"] = flux

    integratorWidget = ipw.Dropdown(
        options=[
            ("Foward Euler", tf.EngineIntegratorTypes.forward_euler.value),
            ("Runge Kutta", tf.EngineIntegratorTypes.runge_kutta4.value),
        ],
        value=tf.EngineIntegratorTypes.forward_euler.value,
        description=LABELTEXT_INTEGRATOR,
        disabled=True
    )
    integrator = ipw.HBox([_checkbox(integratorWidget), integratorWidget])
    widgets["integrator"] = integrator

    windowSize = _vector_text(
        label = LABELTEXT_WINDOW_SIZE, numDims = 2, initialValue = 700, withCheckbox = True, dtype = int
    )
    widgets["window_size"] = windowSize

    throwExcWidget = ipw.Checkbox(value=False, description=LABELTEXT_THROW_EXC, indent=False, disabled=True)
    throwExc = ipw.HBox([_checkbox(throwExcWidget), throwExcWidget])
    widgets["throw_exc"] = throwExc

    seedBox, seedWidget = _scalar_text(
        min=0, max=100, description=LABELTEXT_SEED, initial_value=0, dtype=int
    )
    seed = ipw.HBox([_checkbox(seedWidget), seedWidget])
    widgets["seed"] = seed

    loggerBox, loggerWidget = _scalar_text(
        min=0,
        max=100,
        description=LABELTEXT_LOGGER_LEVEL,
        initial_value=0,
        dtype=int,
    )
    logger = ipw.HBox([_checkbox(loggerWidget), loggerWidget])
    widgets["logger_level"] = logger

    clipPlanesList = ipw.VBox(layout=ipw.Layout(
        border='1px solid lightgray',
        padding='10px',
        margin='10px 0px',
        width='auto'
    ))

    clipPlanes = _set_clip_planes(self, widgets)

    title = ipw.Label("Advanced", style=dict(font_weight="bold"))
    return ipw.VBox(
        [
            title,
            cells,
            flux,
            integrator,
            logger,
            seed,
            threads,
            throwExc,
            windowSize,
            clipPlanes
        ],
        layout=ipw.Layout(padding="0px 40px"),
    )    


# Helper function for _set_advanced
def _set_clip_planes(self, widgets):
    clipPlanesList = ipw.VBox()

    def _set_planes(_):
        def _get_dims(vector):
            data = []
            for dimension in vector.children:
                data.append(dimension.value)
            return data
        data = []

        for child in clipPlanesList.children[0].children: #VBox([planes, button]) planes = VBox([VBox[point, normal], VBox[point, normal]])
            point = _get_dims(child.children[0])
            normal = _get_dims(child.children[1])
            data.append((point, normal))

        with self.out: print("Clip plane settings saved!")
        widgets["clip_planes"] = data

    saveClipPlanes = ipw.Button(
        description="Save Settings",
        disabled=False,
        tooltip="Save settings",
    )
    saveClipPlanes.on_click(_set_planes)

    def _generate_planes(change):
        data = []
        planes = []
        for i in range (change["new"]):
            point = _vector_text(
                label = "Point: ", numDims = 3, initialValue = 0, withCheckbox = False, dtype = int, disabled=False
            )
            normal = _vector_text(
                label = "Normal Vector: ", numDims = 3, initialValue = 0, withCheckbox = False, dtype = int, disabled=False
            )
            plane = ipw.VBox([point, normal], layout=ipw.Layout(
                border='1px solid lightgray',
                padding='10px',
                margin='5px 0px',
                width='auto'
            ))
            planes.append(plane)
        data.append(ipw.VBox(planes))
        data.append(saveClipPlanes)
        clipPlanesList.children = data

    numClipPlanesBox, numClipPlanesWidget  = _scalar_text(
        min=0, max=100, description=LABELTEXT_CLIP_PLANES, initial_value=0, dtype=int
    )
    numClipPlanesWidget.observe(_generate_planes, names="value")

    clipPlanes = ipw.VBox([numClipPlanesWidget, clipPlanesList])
    clipPlanesCheckbox = ipw.HBox([_checkbox(clipPlanes), clipPlanes])

    return clipPlanesCheckbox

"""
Class for managing widget states
"""
class _SimInit:
    def __init__(self):
        self.out = ipw.Output(layout=ipw.Layout(
            border='1px solid lightgray',
            padding='20px',
            margin='10px 0px',
            width='auto'
        ))
        self.widgets = {};
        self.layout = self._layout()
    
    def _get_data(self):
        data = {}
        for key, value in self.widgets.items():
            if isinstance(value, dict) or isinstance(value, list):
                # This handles the bc and clip_planes params
                data[key] = value
                continue
            # All other data is stored as HBox[checkbox, widget]
            checkbox = value.children[0]
            widget = value.children[1]
            if checkbox.value == True:
                if hasattr(widget, 'children'):
                    data[key] = [w.value for w in widget.children]
                elif hasattr(widget, 'value'):
                    data[key] = widget.value
        return data

    def _on_init(self, _):
        with self.out: 
            print("Initializing...")
        data = self._get_data()     
        tf.init(**data)

        with self.out:
            if (tf.err_occurred()):
                for err in tf.err_get_all(): 
                    clean_msg = str(err).split("Msg: ", 1)[-1].strip()
                    display(HTML(f'''
                        <div style="
                            color: #ff0000; padding: 0px 8px;">
                            <strong>Error:</strong> {clean_msg}
                        </div>
                    '''))
                print("Please restart the kernel to reinitialize the simulation.")
            else:
                print("Successfully Initialized! Loaded Data:")
                if len(data) == 0: 
                    print("Loaded with default parameters")
                    return
                for param in data:
                    print("\t" + str(param) + ": " + str(data[param]))


    def _layout(self):
        initialize = ipw.Button(
            description="Initialize",
            disabled=False,
            button_style="info",
            tooltip="Initialize simulation",
        )

        initialize.on_click(self._on_init)
        save_settings, output = sns.save_widget()

        settings = _set_settings(self)
        bc = _set_bc(self)
        advanced = _set_advanced(self)

        children = [settings, bc, advanced]

        tabs = ipw.Tab()
        tabs.children = children
        tabs.titles = ["Settings", "Boundary Conditions", "Advanced"]

        buttons = ipw.HBox([initialize, save_settings], layout=ipw.Layout(width="100%"))
        widget = ipw.VBox([tabs, buttons, self.out])

        return widget

    def show(self):
        display(self.layout)


def init(show=True):
    simInit = _SimInit()
    if show:
        simInit.show()
    return simInit
