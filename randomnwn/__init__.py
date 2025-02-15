"""
Random NWNs package.

Can be imported using either:

    >>> import randomnwn as rnwn

or:

    >>> from randomnwn import *

"""
from .version import __version__

from .nanowires import (
    create_NWN,
    convert_NWN_to_MNR,
    add_wires,
    add_electrodes,
    get_edge_indices,
    create_line_sections,
)

from .line_functions import (
    create_line,
    find_intersects,
    find_line_intersects,
    add_points_to_line,
)

from .calculations import (
    get_connected_nodes,
    create_matrix,
    solve_network,
    solve_drain_current,
    solve_nodal_current,
    solve_edge_current,
    scale_sol,
    get_section_current,
)

from .plotting import (
    plot_NWN,
    draw_NWN,
    plot_NWN_sections,
)

from .dynamics import (
    resist_func,
    solve_evolution,
    set_state_variables,
    get_evolution_current,
)

from .units import (
    get_units
)

from ._models import (
    set_chen_params,
)