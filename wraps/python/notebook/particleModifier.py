from IPython.display import display
import ipywidgets as ipw
import tissue_forge as tf
import numpy as np
import widgets as tfnw
import json
from typing import Any, Dict, List

LABELTEXT_PTYPE_COLOR = 'Color for type '
LABELTEXT_PTYPE_MASS = 'Mass for type '
LABELTEXT_PTYPE_NUMBER = 'Particle # for type '
LABELTEXT_PTYPE_RADIUS = 'Radius for type '

feedback_output = ipw.Output()

def _safe_callback(_ptype: tf.ParticleType, _callback):
    name = _ptype.name
    def _inner(*args, **kwargs):
        _pt = tf.ParticleType_FindFromName(name)
        if _pt is not None:
            try:
                return _callback(_pt, *args, **kwargs)
            except Exception as e:
                with feedback_output:
                    print(f"[ERROR] {e}")
        else:
            with feedback_output:
                print(f"[WARNING] Particle type '{name}' not found.")
    return _inner

def _update_ptype_color(_ptype: tf.ParticleType, _color: tf.FVector3):
    _ptype.style.color = _color
    for p in _ptype:
        if p.style is not None:
            p.style.color = _color

def _update_ptype_mass(_ptype: tf.ParticleType, _mass: float):
    _ptype.mass = _mass
    for p in _ptype:
        p.mass = _mass

def _update_ptype_number(_ptype: tf.ParticleType, _number: int):
    current = len(_ptype.parts)
    delta_particles = _number - current
    if delta_particles > 0:
        _ptype.factory(nr_parts=delta_particles)
    elif delta_particles < 0:
        for i in reversed(range(min(-delta_particles, current))):
            _ptype[np.random.randint(0, i+1)].destroy()

def _update_ptype_radius(_ptype: tf.ParticleType, _radius: float):
    _ptype.radius = _radius
    for p in _ptype:
        p.radius = _radius

def set_ptype_color_picker(ptype: tf.ParticleType, show=False, **kwargs):
    def_kwargs = dict(
        description=LABELTEXT_PTYPE_COLOR + ptype.name,
        value=tfnw.color_inverter(*ptype.style.color.as_list())
    )
    def_kwargs.update(kwargs)
    widget = tfnw.color_picker(_safe_callback(ptype, _update_ptype_color), **def_kwargs)
    if show:
        display(widget)
    return widget

def set_ptype_mass_slider(ptype: tf.ParticleType, show=False, **kwargs):
    def_kwargs = dict(
        min=ptype.mass * 1E-1,
        max=ptype.mass * 1E1,
        description=LABELTEXT_PTYPE_MASS + ptype.name,
        disabled=False,
        continuous_update=False,
        orientation='horizontal',
        readout=True,
        readout_format='.1f'
    )
    def_kwargs.update(kwargs)
    if 'step' not in def_kwargs:
        def_kwargs['step'] = (def_kwargs['max'] - def_kwargs['min']) / 100
    box, widget = tfnw.scalar_slider(float, _safe_callback(ptype, _update_ptype_mass), initial_value=ptype.mass, field_kwargs=def_kwargs)
    if show:
        display(box)
    return box, widget

def set_ptype_number_slider(ptype: tf.ParticleType, show=False, **kwargs):
    def_kwargs = dict(
        min=0,
        max=10000,
        description=LABELTEXT_PTYPE_NUMBER + ptype.name,
        disabled=False,
        continuous_update=False,
        orientation='horizontal',
        readout=True,
        readout_format='.1f'
    )
    def_kwargs.update(kwargs)
    if 'step' not in def_kwargs:
        def_kwargs['step'] = int((def_kwargs['max'] - def_kwargs['min']) / 100)
    box, widget = tfnw.scalar_slider(int, _safe_callback(ptype, _update_ptype_number), initial_value=len(ptype.parts), field_kwargs=def_kwargs)
    if show:
        display(box)
    return box, widget

def set_ptype_radius_slider(ptype: tf.ParticleType, show=False, **kwargs):
    def_kwargs = dict(
        min=ptype.minimum_radius,
        max=min(tf.Universe.dim.as_list()),
        description=LABELTEXT_PTYPE_RADIUS + ptype.name,
        disabled=False,
        continuous_update=False,
        orientation='horizontal',
        readout=True,
        readout_format='.1f'
    )
    def_kwargs.update(kwargs)
    if 'step' not in def_kwargs:
        def_kwargs['step'] = (def_kwargs['max'] - def_kwargs['min']) / 100
    box, widget = tfnw.scalar_slider(float, _safe_callback(ptype, _update_ptype_radius), initial_value=ptype.radius, field_kwargs=def_kwargs)
    if show:
        display(box)
    return box, widget

def set_ptype_color_text(ptype: tf.ParticleType, show=False):
    text = ipw.Text(
        value=", ".join(map(str, ptype.style.color.as_list())),
        description=LABELTEXT_PTYPE_COLOR + ptype.name
    )
    def on_change(change):
        try:
            rgb = list(map(float, change['new'].split(",")))
            _update_ptype_color(ptype, tf.FVector3(*rgb))
        except Exception as e:
            with feedback_output:
                print(f"[ERROR] Invalid color input: {e}")
    text.observe(on_change, names="value")
    if show:
        display(text)
    return text, None

def set_ptype_mass_text(ptype: tf.ParticleType, show=False):
    text = ipw.FloatText(
        value=ptype.mass,
        description=LABELTEXT_PTYPE_MASS + ptype.name
    )
    text.observe(lambda change: _update_ptype_mass(ptype, change["new"]), names="value")
    if show:
        display(text)
    return text, None

def set_ptype_number_text(ptype: tf.ParticleType, show=False):
    text = ipw.IntText(
        value=len(ptype.parts),
        description=LABELTEXT_PTYPE_NUMBER + ptype.name
    )
    text.observe(lambda change: _update_ptype_number(ptype, change["new"]), names="value")
    if show:
        display(text)
    return text, None

def set_ptype_radius_text(ptype: tf.ParticleType, show=False):
    text = ipw.FloatText(
        value=ptype.radius,
        description=LABELTEXT_PTYPE_RADIUS + ptype.name
    )
    text.observe(lambda change: _update_ptype_radius(ptype, change["new"]), names="value")
    if show:
        display(text)
    return text, None

def batch_edit_ptypes(ptypes: List[tf.ParticleType]):
    boxes = []
    for pt in ptypes:
        color_widget = set_ptype_color_picker(pt)
        mass_box, _ = set_ptype_mass_slider(pt)
        number_box, _ = set_ptype_number_slider(pt)
        radius_box, _ = set_ptype_radius_slider(pt)
        boxes.extend([color_widget, mass_box, number_box, radius_box])
    display(ipw.VBox(boxes))
    display(feedback_output)

def export_ptypes_config(ptypes: List[tf.ParticleType], filename="ptypes.json"):
    try:
        data = [{
            "name": pt.name,
            "mass": pt.mass,
            "radius": pt.radius,
            "color": pt.style.color.as_list()
        } for pt in ptypes]
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        with feedback_output:
            print(f"[SUCCESS] Exported to {filename}")
    except Exception as e:
        with feedback_output:
            print(f"[ERROR] Export failed: {e}")

def import_ptypes_config(filename="ptypes.json"):
    try:
        with open(filename, "r") as f:
            data = json.load(f)
        for d in data:
            pt = tf.ParticleType_FindFromName(d["name"])
            if pt is not None:
                pt.mass = d["mass"]
                pt.radius = d["radius"]
                pt.style.color = tf.FVector3(*d["color"])
        with feedback_output:
            print(f"[SUCCESS] Imported from {filename}")
    except Exception as e:
        with feedback_output:
            print(f"[ERROR] Import failed: {e}")

def add_export_import_buttons(ptypes):
    export_btn = ipw.Button(description="Export Config")
    import_btn = ipw.Button(description="Import Config")
    export_btn.on_click(lambda _: export_ptypes_config(ptypes))
    import_btn.on_click(lambda _: import_ptypes_config())
    display(ipw.HBox([export_btn, import_btn]))
    display(feedback_output)

def add_reset_button(ptypes: List[tf.ParticleType]):
    def reset_all(_):
        for pt in ptypes:
            pt.mass = 1.0
            pt.radius = 1.0
            pt.style.color = tf.FVector3(0.5, 0.5, 0.5)
            current = len(pt.parts)
            for i in reversed(range(current)):
                pt.parts[i].destroy()
            pt.factory(nr_parts=10)
        with feedback_output:
            print("[INFO] Reset all properties to default.")
    reset_btn = ipw.Button(description="Reset Properties", button_style="warning")
    reset_btn.on_click(reset_all)
    display(reset_btn)

def show_particle_counts(ptypes: List[tf.ParticleType]):
    items = [f"{pt.name}: {len(pt.parts)} particles" for pt in ptypes]
    summary = ipw.HTML("<br>".join(items))
    display(ipw.HTML("<b>Current Particle Counts</b>"))
    display(summary)

def toggle_visibility_widget(ptypes: List[tf.ParticleType]):
    dropdown = ipw.Dropdown(options=[pt.name for pt in ptypes], description='Select Type:')
    checkbox = ipw.Checkbox(value=True, description='Visible?')

    def toggle_visibility(change):
        selected = dropdown.value
        visible = checkbox.value
        pt = tf.ParticleType_FindFromName(selected)
        if pt:
            pt.style.visible = visible
            for p in pt.parts:
                if p.style is not None:
                    p.style.visible = visible

    checkbox.observe(toggle_visibility, names='value')
    display(ipw.HTML("<b>Toggle Particle Visibility</b>"))
    display(ipw.VBox([dropdown, checkbox]))

def show_ptype_summary_table(ptypes: List[tf.ParticleType]):
    rows = []
    for pt in ptypes:
        color_str = ", ".join(f"{c:.2f}" for c in pt.style.color.as_list())
        rows.append(f"<tr><td>{pt.name}</td><td>{pt.mass:.2f}</td><td>{pt.radius:.2f}</td><td>{len(pt.parts)}</td><td>{color_str}</td></tr>")
    table = f"""
    <table border="1">
        <tr><th>Name</th><th>Mass</th><th>Radius</th><th>Particles</th><th>Color</th></tr>
        {''.join(rows)}
    </table>
    """
    display(ipw.HTML("<b>Particle Summary Table</b>"))
    display(ipw.HTML(table))

def add_random_colorizer_button(ptypes: List[tf.ParticleType]):
    btn = ipw.Button(description="Randomize Colors", button_style="info")
    def on_click(_):
        for pt in ptypes:
            color = tf.FVector3(np.random.rand(), np.random.rand(), np.random.rand())
            pt.style.color = color
            for p in pt.parts:
                if p.style:
                    p.style.color = color
        with feedback_output:
            print("[INFO] Colors randomized.")
    btn.on_click(on_click)
    display(btn)


