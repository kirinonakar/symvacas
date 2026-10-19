"""Parametric and height surfaces with row-local helper definitions."""
import math
import sympy as s
from calc_shared import require
from calc_graph_common import graph_expressions, graph_function, parameter_names, resolved_parameters, _finite_real


def parametric_surface_tree(tree):
    while tree.get('kind') == 'group':
        tree = tree['args'][0]
    if tree.get('kind') == 'relation' and tree.get('value') in ('=', '==') and tree['args'][0].get('kind') == 'call':
        tree = tree['args'][1]
        while tree.get('kind') == 'group':
            tree = tree['args'][0]
    return tree if tree.get('kind') in ('list', 'tuple') else None


def surface_definition_expressions(engine, tree):
    entries = tree.get('args', [])
    named = any(entry.get('kind') == 'relation' for entry in entries)
    definitions = {}
    if named:
        for entry in entries:
            args = entry.get('args', [])
            require(entry.get('kind') == 'relation' and entry.get('value') in ('=', '==') and
                    len(args) == 2 and args[0].get('kind') == 'symbol',
                    'Use [x=...,y=...,z=...] with optional local helper definitions')
            name = args[0]['value']
            require(name not in definitions and name not in ('u', 'v', 't'),
                    'Surface definitions must have unique names other than u, v or t')
            definitions[name] = args[1]
        parametric = 'x' in definitions or 'y' in definitions
        require(all(axis in definitions for axis in (('x', 'y', 'z') if parametric else ('z',))),
                'Define z for a height surface, or all three coordinates x, y and z')
    else:
        from calc_graph3d import space_coordinate_trees
        coordinates = space_coordinate_trees(tree)
        require(coordinates is not None, 'Enter a surface [x(u,v),y(u,v),z(u,v)]')

    previous = engine.bindings.copy()
    try:
        # Axis and local names shadow saved calculator variables for this row.
        engine.bindings.update({name: engine.symbol(name) for name in ('u', 'v', 'x', 'y', *definitions)})
        if named:
            values = graph_expressions(engine, list(definitions.values()), ('u', 'v'))
            require(all(isinstance(value, s.Expr) for value in values), 'Surface coordinates must be scalar expressions')
            raw = dict(zip(definitions, values))
            expanded = {}
            def resolve(name, active):
                require(name not in active, 'Circular local surface definition: ' + name)
                if name not in expanded:
                    value = raw[name]
                    replacements = {symbol: resolve(str(symbol), active | {name})
                                    for symbol in value.free_symbols if str(symbol) in raw}
                    expanded[name] = value.xreplace(replacements)
                return expanded[name]
            # Check unused helpers too, so circular definitions cannot disappear.
            for name in raw: resolve(name, set())
            expressions = tuple(expanded[axis] for axis in (('x', 'y', 'z') if parametric else ('z',)))
        else:
            expressions = graph_expressions(engine, coordinates, ('u', 'v'))
            require(all(isinstance(value, s.Expr) for value in expressions), 'Surface coordinates must be scalar expressions')
        return expressions
    finally:
        engine.bindings.clear()
        engine.bindings.update(previous)


def graph_parametric_surface(engine, request, expressions):
    axes = (engine.symbol('u'), engine.symbol('v'))
    sliders = resolved_parameters(engine, request, expressions, {'u', 'v'})
    function = graph_function(expressions, axes, sliders)
    names = sorted(parameter_names(expressions, {'u', 'v'}))
    ranges = [(float(request.get('surface' + axis + 'Min', 0)),
               float(request.get('surface' + axis + 'Max', 2 * math.pi))) for axis in ('U', 'V')]
    require(all(math.isfinite(low) and math.isfinite(high) and math.isfinite(high-low) and high > low
                for low, high in ranges), 'Enter finite increasing u and v ranges')
    count = max(12, min(96, int(request.get('surfaceSamples', 26))))
    from calc_graph_spatial import surface_coordinates
    us, vs = (surface_coordinates(low, high, count) for low, high in ranges)
    mesh = []
    heights = []
    for v in vs:
        row = []
        for u in us:
            try:
                point = [_finite_real(value) for value in function(u, v)]
                if len(point) != 3 or any(value is None for value in point): point = None
            except (TypeError, ValueError, ZeroDivisionError, OverflowError):
                point = None
            row.append(point)
            if point is not None: heights.append(point[2])
        mesh.append(row)
    require(heights, 'Surface has no finite values in this range')
    return {'surface': mesh, 'parametricSurface': True, 'surfaceSamples': count,
            'parameters': names, 'zMin': min(heights), 'zMax': max(heights)}
