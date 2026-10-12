export const unitGroups = {
  "Length": [
    "m",
    "km",
    "cm",
    "mm",
    "in",
    "ft",
    "yd",
    "mi"
  ],
  "Area": [
    "m2",
    "cm2",
    "km2",
    "ha",
    "acre"
  ],
  "Volume": [
    "L",
    "mL",
    "m3",
    "galUS"
  ],
  "Mass": [
    "kg",
    "g",
    "mg",
    "lb",
    "oz"
  ],
  "Temperature": [
    "degC",
    "degF",
    "K"
  ],
  "Speed": [
    "mps",
    "kph",
    "mph",
    "knot"
  ],
  "Acceleration": [
    "mps2",
    "g0"
  ],
  "Pressure": [
    "Pa",
    "kPa",
    "bar",
    "atm"
  ],
  "Force": [
    "N",
    "kN",
    "lbf"
  ],
  "Energy": [
    "J",
    "kJ",
    "cal",
    "kWh",
    "eV"
  ],
  "Power": [
    "W",
    "kW"
  ],
  "Time": [
    "s",
    "min",
    "h",
    "day",
    "ms"
  ],
  "Frequency": [
    "Hz",
    "kHz",
    "MHz"
  ],
  "Angle": [
    "rad",
    "deg",
    "grad"
  ],
  "Data": [
    "bit",
    "byte",
    "kB",
    "KiB",
    "MB",
    "MiB",
    "GB"
  ],
  "Current": [
    "A",
    "mA",
    "uA"
  ],
  "Charge": [
    "C",
    "mC",
    "uC"
  ],
  "Voltage": [
    "V",
    "mV",
    "kV"
  ],
  "Resistance": [
    "ohm",
    "kohm",
    "Mohm",
    "Ω"
  ],
  "Conductance": [
    "S",
    "mS"
  ],
  "Capacitance": [
    "F",
    "uF",
    "nF",
    "pF"
  ],
  "Inductance": [
    "H",
    "mH",
    "uH"
  ],
  "Magnetic flux": [
    "Wb",
    "Vs"
  ],
  "Magnetic flux density": [
    "T",
    "mT",
    "uT"
  ],
  "Amount": [
    "mol",
    "mmol",
    "umol"
  ]
};

export const unitNames = {
  "m": "meter",
  "km": "kilometer",
  "cm": "centimeter",
  "mm": "millimeter",
  "in": "inch",
  "inch": "inch",
  "ft": "foot",
  "yd": "yard",
  "mi": "mile",
  "m2": "square meter",
  "cm2": "square centimeter",
  "km2": "square kilometer",
  "ha": "hectare",
  "acre": "acre",
  "m3": "cubic meter",
  "L": "liter",
  "mL": "milliliter",
  "galUS": "US gallon",
  "kg": "kilogram",
  "g": "gram",
  "mg": "milligram",
  "lb": "pound",
  "oz": "ounce",
  "K": "kelvin",
  "degC": "degrees Celsius",
  "degF": "degrees Fahrenheit",
  "s": "second",
  "sec": "second",
  "min": "minute",
  "h": "hour",
  "hr": "hour",
  "day": "day",
  "ms": "millisecond",
  "mps": "meters per second",
  "kph": "kilometers per hour",
  "mph": "miles per hour",
  "knot": "nautical miles per hour",
  "mps2": "meters per second squared",
  "g0": "standard gravity, 9.80665 meters per second squared",
  "Pa": "pascal",
  "kPa": "kilopascal",
  "bar": "bar",
  "atm": "standard atmosphere",
  "N": "newton",
  "kN": "kilonewton",
  "lbf": "pound-force",
  "J": "joule",
  "kJ": "kilojoule",
  "cal": "calorie",
  "kWh": "kilowatt-hour",
  "eV": "electronvolt",
  "W": "watt",
  "kW": "kilowatt",
  "Hz": "hertz",
  "kHz": "kilohertz",
  "MHz": "megahertz",
  "A": "ampere",
  "amp": "ampere",
  "ampere": "ampere",
  "mA": "milliampere",
  "uA": "microampere",
  "C": "coulomb",
  "coulomb": "coulomb",
  "mC": "millicoulomb",
  "uC": "microcoulomb",
  "V": "volt",
  "volt": "volt",
  "mV": "millivolt",
  "kV": "kilovolt",
  "ohm": "ohm",
  "Ω": "ohm",
  "kohm": "kiloohm",
  "kΩ": "kiloohm",
  "Mohm": "megaohm",
  "MΩ": "megaohm",
  "S": "siemens",
  "siemens": "siemens",
  "mS": "millisiemens",
  "F": "farad",
  "farad": "farad",
  "uF": "microfarad",
  "nF": "nanofarad",
  "pF": "picofarad",
  "H": "henry",
  "henry": "henry",
  "mH": "millihenry",
  "uH": "microhenry",
  "Wb": "weber",
  "weber": "weber",
  "Vs": "volt-second",
  "T": "tesla",
  "tesla": "tesla",
  "mT": "millitesla",
  "uT": "microtesla",
  "mol": "mole",
  "mole": "mole",
  "mmol": "millimole",
  "umol": "micromole",
  "bit": "bit",
  "byte": "byte",
  "kB": "kilobyte",
  "KiB": "kibibyte",
  "MB": "megabyte",
  "MiB": "mebibyte",
  "GB": "gigabyte",
  "rad": "radian",
  "deg": "degree",
  "grad": "gradian"
};
export function unitLabel(unit) {
  const name = unitNames[unit];
  return name && name !== unit ? `${unit} (${name})` : unit;
}
