"""
Atom = (
    Epsilon (J),
    Sigma (m),
    m (kg)
)
"""

kB = 1.38064852e-23 # Boltzmann constant
NA = 6.0221409e+23 # Avogadro number
m_nucleon = 1.674e-27 # mass of a nucleon

atoms = {
    "Lithium": (
        0.690/NA,
        1.51e-10,
        7*m_nucleon,
    ),
    "Argon": (
        1.65e-21,
        3.4e-10,
        6.69e-26,
    ),
    "Neon": (
        4.81e-22,
        2.7e-10,
        3.38e-26,
    ),
    "Krypton": (
        2.36e-21,
        3.6e-10,
        1.39e-25
    ),
    "Oxygen": (
        1.63e-21,
        3.46e-10,
        2.66e-26
    ),
}