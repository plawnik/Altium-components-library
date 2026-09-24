# Altium Components Library

This repository contains ready-to-use integrated libraries for Altium Designer. Download the latest compiled package, open the **Components** panel in Altium Designer, select **File-based Libraries Preferences**, click **Install**, and select the required `*.IntLib` files. Installed libraries are available to all projects and their components can be placed directly from the Components panel.

> **Quick download:** The ZIP package containing all compiled libraries is available in the **Releases** section on the right side of the repository page. Open the latest release and download `Altium-components-library.zip`.

## Using the Library

1. [Download the latest compiled library package](https://github.com/plawnik/Altium-components-library/releases/latest/download/Altium-components-library.zip).
2. Extract the ZIP archive. Alternatively, clone the repository and use the `compiled/` directory.
3. In Altium Designer, open the **Components** panel.
4. Open the panel menu and select **File-based Libraries Preferences**.
5. Click **Install** and select one or more extracted `*.IntLib` files.
6. Select the installed library in the Components panel, search for the required component, and place it on the schematic.

A new numbered GitHub Release is created automatically after every push to `main`. It contains `Altium-components-library.zip` with all current compiled `IntLib` files. Older automatically generated releases are removed, so only the latest package remains available.

After pulling a newer repository revision, reopen or refresh the library in Altium Designer if the updated components are not immediately visible.

## Library Layer Convention <-- NOT VALID;TODO

The table below is an example structure only. Replace the layer numbers, names, colors, and descriptions with the actual library convention used in this repository.

| Color | Layer number | Layer name | Description |
|---|---:|---|---|
| ![Red](https://placehold.co/48x18/E53935/E53935.png) | 1 | Top Copper | Copper objects placed on the top side of the PCB. |
| ![Blue](https://placehold.co/48x18/1E88E5/1E88E5.png) | 2 | Bottom Copper | Copper objects placed on the bottom side of the PCB. |
| ![Yellow](https://placehold.co/48x18/FDD835/FDD835.png) | 21 | Top Silkscreen | Top-side component outlines, reference designators, and assembly markings. |
| ![Cyan](https://placehold.co/48x18/00ACC1/00ACC1.png) | 22 | Bottom Silkscreen | Bottom-side component outlines, reference designators, and assembly markings. |
| ![Magenta](https://placehold.co/48x18/D81B60/D81B60.png) | 101 | Board Outline | PCB outline and routed-board geometry. |
| ![Green](https://placehold.co/48x18/43A047/43A047.png) | 102 | Courtyard | Recommended component placement and assembly clearance. |

## Adding a New Component

1. Select the appropriate category under `source/`. Create a new category only when none of the existing categories is suitable.
2. Add or edit the required `LibPkg`, `SchLib`, and `PcbLib` files in that category directory.
3. Use the exact parameter names defined in the tables below. Check the symbol pins, PCB pads, footprint dimensions, polarity, pin-1 marking, and 3D model against the manufacturer documentation.
4. Use `Manufacturer 1` and `Part Number 1` for the primary approved component. Use `Manufacturer 2` and `Part Number 2` only for an approved alternative with the same electrical and mechanical requirements.
5. Compile the `LibPkg` in Altium Designer and leave the generated `IntLib` in the default `Project Outputs for ...` directory.
6. Commit and push the source files together with the generated output directory. The repository workflow will move the compiled library to `compiled/`, remove the generated output directory, and update the component list at the end of this README.
7. Pull the workflow commit before making the next library change.

## Component Categories

| Category | Contents |
|---|---|
| `CAPACITORS` | Ceramic, electrolytic, polymer, tantalum, film, and other capacitors. |
| `RESISTORS` | Fixed resistors, current-sense resistors, resistor arrays, and networks. |
| `INDUCTORS` | Power inductors, RF inductors, chokes, and coupled inductors. |
| `FERRITES` | Ferrite beads, ferrite filters, and related EMI suppression components. |
| `DIODES` | Rectifier, switching, Schottky, Zener, TVS, and other semiconductor diodes. |
| `TRANSISTORS` | MOSFETs, BJTs, IGBTs, JFETs, and transistor arrays. |
| `IC` | Integrated circuits, including controllers, converters, processors, interfaces, and sensors implemented as ICs. |
| `CONNECTORS` | Board, cable, panel, card-edge, FFC/FPC, RF, and other connectors. |
| `CRYSTALS_OSCILLATORS` | Crystals, resonators, oscillators, and clock modules. |
| `PROTECTION` | Fuses, PTC resettable fuses, TVS/ESD protectors, MOVs, and gas-discharge tubes. |
| `OPTOELECTRONICS` | LEDs, photodiodes, phototransistors, optocouplers, and other optical components. |
| `TRANSFORMERS` | Power, pulse, isolation, current, and Ethernet transformers or magnetics. |
| `ELECTROMECHANICAL` | Relays, switches, encoders, buzzers, motors, fans, and similar components. |
| `MODULES` | Radio modules, system-on-modules, converter modules, displays, and other functional assemblies. |
| `MISC` | Test points, fiducials, mounting holes, solder jumpers, logos, and special-purpose items. |

## Category Parameter Definitions

Parameter names are case-sensitive library conventions. Use the spelling shown below. Use `N/A` only when a required parameter genuinely does not apply or the value is not available. Optional alternative-manufacturer fields may be left empty.

Use only `SMT`, `THT`, or `Other` in every `Mounting Type` field. Use `Other` for panel-mounted, chassis-mounted, cable-mounted, socketed, press-fit, M.2, mechanical, and other parts that are neither conventional SMT nor through-hole components.

Write rectangular body dimensions as `W5.1xL10.2xH8.0mm` (width × length × height), cylindrical or radial body dimensions as `D5.0xH7.0mm` (diameter × height), and axial body dimensions as `D2.5xL6.5mm` (diameter × body length). Use a decimal point, omit spaces, and write `mm` once at the end. Standard package names such as `0603`, `SOT-23`, and `QFN-32` may be used without dimensions.

### CAPACITORS

| Parameter | Requirement | Format and examples |
|---|---|---|
| `Value` | Required | Use compact engineering notation without a decimal separator: `1m` = 1 mF, `470u` = 470 µF, `10u` = 10 µF, `100n` = 100 nF, `1n` = 1 nF, `5p6` = 5.6 pF. |
| `Voltage Rating` | Required | Rated working voltage, for example `6V3`, `10V`, `16V`, `25V`, `50V`, `450V`. |
| `Dielectric` | Required | Examples: `C0G/NP0`, `X5R`, `X7R`, `Y5V`, `Electrolytic`, `Polymer`, `Tantalum`, `Film`. Use `N/A` when the dielectric is unknown or not applicable. |
| `Package` | Required | SMT examples: `0201`, `0402`, `0603`, `0805`, `1206`. Round THT example: `D5.0xH7.0mm`. Rectangular THT example: `W5.1xL10.2xH8.0mm`. |
| `Mounting Type` | Required | Allowed values: `SMT`, `THT`, or `Other`. |
| `Manufacturer 1` | Required | Use `Generic` for a generic capacitor definition. |
| `Part Number 1` | Required | Use `Generic` for a generic capacitor definition. |
| `Manufacturer 2` | Optional | Approved alternative manufacturer, for example `Murata`, `TDK`, `KEMET`; otherwise leave empty. |
| `Part Number 2` | Optional | Exact ordering code matching `Manufacturer 2`; otherwise leave empty. |

### RESISTORS

| Parameter | Requirement | Format and examples |
|---|---|---|
| `Value` | Required | Examples: `0R`, `10mR`, `4R7`, `10R`, `1k`, `4k7`, `100k`, `1M`. Use `R`, `k`, or `M` as the decimal marker where appropriate. |
| `Tolerance` | Required | Examples: `0.05%`, `0.1%`, `1%`, `2%`, `5%`, `10%`. |
| `Package` | Required | SMT examples: `0201`, `0402`, `0603`, `0805`, `1206`, `2512`. THT examples: axial `D2.5xL6.5mm`, rectangular `W5.1xL10.2xH8.0mm`. |
| `Mounting Type` | Required | Allowed values: `SMT`, `THT`, or `Other`. |
| `Manufacturer 1` | Required | Use `Generic` for a generic resistor definition. |
| `Part Number 1` | Required | Use `Generic` for a generic resistor definition. |
| `Manufacturer 2` | Optional | Approved alternative manufacturer, for example `Yageo`, `Vishay`, `Panasonic`; otherwise leave empty. |
| `Part Number 2` | Optional | Exact ordering code matching `Manufacturer 2`; otherwise leave empty. |

### INDUCTORS

| Parameter | Requirement | Format and examples |
|---|---|---|
| `Value` | Required | Examples: `2n2`, `100n`, `4u7`, `10u`, `100u`, `1m`. |
| `Tolerance` | Required | Examples: `5%`, `10%`, `20%`, `±0.3nH`. |
| `Current Rating` | Required | Continuous/RMS current, for example `250mA`, `1A`, `2A`, `8A`. |
| `Saturation Current` | Required | Saturation current, for example `700mA`, `2A5`, `12A`; use `N/A` only when the manufacturer does not specify it. |
| `DCR` | Required | DC resistance, for example `8mR`, `35mR`, `0R12`, `1R5`. |
| `Package` | Required | Use labelled dimensions, for example `W3.0xL3.0xH1.5mm`, `W6.0xL6.0xH3.0mm`, or `W10.0xL10.0xH4.0mm`. For round parts use, for example, `D8.0xH10.0mm`. |
| `Mounting Type` | Required | Allowed values: `SMT`, `THT`, or `Other`. |
| `Manufacturer 1` | Required | Actual manufacturer; `Generic` is not allowed. Examples: `Coilcraft`, `Würth Elektronik`, `Bourns`. |
| `Part Number 1` | Required | Exact manufacturer ordering code; `Generic` is not allowed. Example: `XAL5030-103ME`. |
| `Manufacturer 2` | Optional | Approved equivalent manufacturer; otherwise leave empty. |
| `Part Number 2` | Optional | Exact ordering code matching `Manufacturer 2`; otherwise leave empty. |

### FERRITES

| Parameter | Requirement | Format and examples |
|---|---|---|
| `Value` | Required | Short schematic value containing impedance and test frequency only, for example `100R@100MHz`, `220R@100MHz`, or `600R@100MHz`. Do not add the current rating here. |
| `Impedance` | Required | Use impedance and test frequency, for example `100Z@100MHz`, `600Z@100MHz`, `1kZ@100MHz`. |
| `Current Rating` | Required | Examples: `200mA`, `500mA`, `1A`, `2A`, `6A`. Store the rated current only in this field. |
| `Package` | Required | Examples: `0402`, `0603`, `0805`, `1206`, or `W2.0xL1.2xH0.9mm`. |
| `Mounting Type` | Required | Allowed values: `SMT`, `THT`, or `Other`. |
| `Manufacturer 1` | Required | Actual manufacturer; `Generic` is not allowed. Examples: `Murata`, `TDK`, `Würth Elektronik`. |
| `Part Number 1` | Required | Exact manufacturer ordering code; `Generic` is not allowed. Example: `BLM18PG121SN1D`. |
| `Manufacturer 2` | Optional | Approved equivalent manufacturer; otherwise leave empty. |
| `Part Number 2` | Optional | Exact ordering code matching `Manufacturer 2`; otherwise leave empty. |

### DIODES

| Parameter | Requirement | Format and examples |
|---|---|---|
| `Type` | Required | Examples: `Rectifier`, `Schottky`, `Switching`, `Zener`, `TVS`, `ESD Array`, `Avalanche`. |
| `Forward Voltage` | Required | Include the test current when useful, for example `0V35@1A`, `0V7@10mA`, `1V1@3A`. Use `N/A` if the value is not applicable. |
| `Forward Current` | Required | Continuous forward current, for example `100mA`, `500mA`, `1A`, `3A`, `10A`. |
| `Package` | Required | Examples: `SOD-323`, `SOD-123`, `SMA`, `SMB`, `DO-35`, `DO-41`, `TO-220-2`. |
| `Mounting Type` | Required | Allowed values: `SMT`, `THT`, or `Other`. |
| `Manufacturer 1` | Required | Actual manufacturer; `Generic` is not allowed. Examples: `Nexperia`, `Vishay`, `onsemi`, `Semtech`. |
| `Part Number 1` | Required | Exact manufacturer ordering code; `Generic` is not allowed. Example: `PMEG2010ER`. |
| `Manufacturer 2` | Optional | Approved equivalent manufacturer; otherwise leave empty. |
| `Part Number 2` | Optional | Exact ordering code matching `Manufacturer 2`; otherwise leave empty. |

### TRANSISTORS

| Parameter | Requirement | Format and examples |
|---|---|---|
| `Type` | Required | Examples: `MOSFET`, `BJT`, `IGBT`, `JFET`, `Darlington`, `Transistor Array`. |
| `Polarity` | Required | Examples: `N-Channel`, `P-Channel`, `NPN`, `PNP`. Use `N/A` when not applicable. |
| `Voltage Rating` | Required | Main blocking voltage, for example `20V`, `60V`, `650V`, `1200V`. |
| `Current Rating` | Required | Main continuous-current rating, for example `200mA`, `5A`, `30A`, `100A`. |
| `RDS(on) / Gain` | Required | MOSFET examples: `8mR@10V`, `25mR@4V5`. BJT examples: `hFE 100-300`. Use the value appropriate for the device type. |
| `Package` | Required | Examples: `SOT-23`, `SOT-223`, `SO-8`, `TO-92`, `TO-220`, or `DFN-8 W3.0xL3.0xH0.9mm`. |
| `Mounting Type` | Required | Allowed values: `SMT`, `THT`, or `Other`. |
| `Manufacturer 1` | Required | Actual manufacturer; `Generic` is not allowed. Examples: `Infineon`, `Nexperia`, `onsemi`, `STMicroelectronics`. |
| `Part Number 1` | Required | Exact manufacturer ordering code; `Generic` is not allowed. |
| `Manufacturer 2` | Optional | Approved equivalent manufacturer; otherwise leave empty. |
| `Part Number 2` | Optional | Exact ordering code matching `Manufacturer 2`; otherwise leave empty. |

### IC

| Parameter | Requirement | Format and examples |
|---|---|---|
| `Function` | Required | Short functional description, for example `Buck Converter`, `MCU`, `USB-C PD Controller`, `Op-Amp`, `ADC`, `Temperature Sensor`, `CAN Transceiver`. |
| `Package` | Required | Examples: `SOIC-8`, `DIP-8`, `QFN-32 W5.0xL5.0xH0.9mm`, `TQFP-64 W10.0xL10.0xH1.0mm`, `BGA-196 W15.0xL15.0xH1.2mm`. |
| `Mounting Type` | Required | Allowed values: `SMT`, `THT`, or `Other`. |
| `Manufacturer 1` | Required | Actual manufacturer; `Generic` is not allowed. Examples: `Texas Instruments`, `STMicroelectronics`, `NXP`, `Microchip`. |
| `Part Number 1` | Required | Exact manufacturer ordering code; `Generic` is not allowed. Example: `STM32H5F4IJT7Q`. |
| `Manufacturer 2` | Optional | Approved equivalent manufacturer; otherwise leave empty. |
| `Part Number 2` | Optional | Exact ordering code matching `Manufacturer 2`; otherwise leave empty. |

### CONNECTORS

| Parameter | Requirement | Format and examples |
|---|---|---|
| `Pitch` | Required | Contact pitch, for example `0.4mm`, `0.5mm`, `1.27mm`, `2.00mm`, `2.54mm`. Use `N/A` for connectors without a useful regular pitch. |
| `Positions` | Required | Total number of electrical positions, for example `2`, `6`, `10`, `19`, `40`, `80`. |
| `Rows` | Required | Examples: `1`, `2`, `3`, `4`; use `N/A` when rows do not describe the connector correctly. |
| `Orientation` | Required | Use `Straight` or `Right Angle`. If necessary, add a mechanical qualifier, for example `Straight Vertical` or `Right Angle Horizontal`. |
| `Mounting Type` | Required | Allowed values: `SMT`, `THT`, or `Other`. Use `Other` for cable, panel, card-edge, or similar connectors. |
| `Manufacturer 1` | Required | Actual manufacturer; `Generic` is not allowed. Examples: `TE Connectivity`, `Molex`, `Hirose`, `JST`. |
| `Part Number 1` | Required | Exact manufacturer ordering code; `Generic` is not allowed. Example: `1827059-3`. |
| `Manufacturer 2` | Optional | Approved equivalent manufacturer; otherwise leave empty. |
| `Part Number 2` | Optional | Exact ordering code matching `Manufacturer 2`; otherwise leave empty. |

### CRYSTALS_OSCILLATORS

| Parameter | Requirement | Format and examples |
|---|---|---|
| `Frequency` | Required | Examples: `32.768kHz`, `8MHz`, `16MHz`, `25MHz`, `100MHz`. |
| `Frequency Tolerance` | Required | Initial frequency tolerance, for example `±10ppm`, `±20ppm`, `±30ppm`, `±50ppm`. |
| `Load Capacitance` | Required | Examples: `6pF`, `8pF`, `12pF`, `18pF`. Use `N/A` for active oscillators when not applicable. |
| `Mounting Type` | Required | Allowed values: `SMT`, `THT`, or `Other`. |
| `Manufacturer 1` | Required | Actual manufacturer; `Generic` is not allowed. Examples: `Abracon`, `Epson`, `NDK`, `TXC`. |
| `Part Number 1` | Required | Exact manufacturer ordering code; `Generic` is not allowed. |
| `Manufacturer 2` | Optional | Approved equivalent manufacturer; otherwise leave empty. |
| `Part Number 2` | Optional | Exact ordering code matching `Manufacturer 2`; otherwise leave empty. |

### PROTECTION

| Parameter | Requirement | Format and examples |
|---|---|---|
| `Type` | Required | Examples: `Fuse`, `Resettable Fuse`, `TVS`, `ESD Array`, `MOV`, `GDT`, `Surge Arrestor`. |
| `Working Voltage` | Required | Examples: `3V3`, `5V`, `24V`, `48V`, `230VAC`, `275VAC`. Use `N/A` where not applicable. |
| `Breakdown Voltage` | Required | Examples: `6V`, `33V`, `470V`; use `N/A` for ordinary fuses and devices without this rating. |
| `Clamping Voltage` | Required | Examples: `9V2@1A`, `53V@10A`; use `N/A` when not applicable. |
| `Current Rating` | Required | Examples: `100mA`, `500mA`, `2A`, `10A`; use the nominal fuse rating or continuous current as appropriate. |
| `Hold Current` | Required when applicable | Resettable-fuse examples: `200mA`, `1A1`, `3A`; otherwise use `N/A`. |
| `Trip Current` | Required when applicable | Resettable-fuse examples: `400mA`, `2A2`, `6A`; otherwise use `N/A`. |
| `Peak Pulse / Surge Rating` | Required when applicable | Examples: `30A@8/20us`, `600W@10/1000us`, `6kA`; otherwise use `N/A`. |
| `Package` | Required | Examples: `0402`, `0603`, `SOD-323`, `SMA`, `SMB`, cartridge fuse `D5.0xL20.0mm`, or radial MOV `D10.0xH5.0mm`. |
| `Mounting Type` | Required | Allowed values: `SMT`, `THT`, or `Other`. |
| `Manufacturer 1` | Required | Actual manufacturer; `Generic` is not allowed. Examples: `Littelfuse`, `Bourns`, `Semtech`, `TDK`. |
| `Part Number 1` | Required | Exact manufacturer ordering code; `Generic` is not allowed. |
| `Manufacturer 2` | Optional | Approved equivalent manufacturer; otherwise leave empty. |
| `Part Number 2` | Optional | Exact ordering code matching `Manufacturer 2`; otherwise leave empty. |

### OPTOELECTRONICS

| Parameter | Requirement | Format and examples |
|---|---|---|
| `Type` | Required | Examples: `LED`, `RGB LED`, `IR LED`, `Photodiode`, `Phototransistor`, `Optocoupler`, `Laser Diode`. |
| `Color` | Required | Examples: `Red 625nm`, `Green 525nm`, `Blue 470nm`, `White 4000K`, `IR 940nm`. Use `N/A` when color does not apply. |
| `Forward Voltage` | Required | Examples: `1V8@20mA`, `2V1@20mA`, `3V2@20mA`; use `N/A` for receiving devices when not applicable. |
| `Forward Current` | Required | Examples: `5mA`, `20mA`, `350mA`, `1A`; use `N/A` when not applicable. |
| `Mounting Type` | Required | Allowed values: `SMT`, `THT`, or `Other`. |
| `Manufacturer 1` | Required | Actual manufacturer; `Generic` is not allowed. Examples: `ams OSRAM`, `Vishay`, `Broadcom`, `Luminus`. |
| `Part Number 1` | Required | Exact manufacturer ordering code; `Generic` is not allowed. |
| `Manufacturer 2` | Optional | Approved equivalent manufacturer; otherwise leave empty. |
| `Part Number 2` | Optional | Exact ordering code matching `Manufacturer 2`; otherwise leave empty. |

### TRANSFORMERS

| Parameter | Requirement | Format and examples |
|---|---|---|
| `Type` | Required | Examples: `Flyback Transformer`, `Pulse Transformer`, `AC-AC Power Transformer`, `Isolation Transformer`, `Current Transformer`, `Ethernet Magnetics`. |
| `Ratio` | Required | Examples: `1:1`, `1:2`, `1CT:1CT`, `230V:12V`, `1000:1`. Use the winding or voltage ratio stated by the manufacturer. |
| `Mounting Type` | Required | Allowed values: `SMT`, `THT`, or `Other`. |
| `Manufacturer 1` | Required | Actual manufacturer; `Generic` is not allowed. Examples: `Würth Elektronik`, `Pulse Electronics`, `Bourns`, `Hammond`. |
| `Part Number 1` | Required | Exact manufacturer ordering code; `Generic` is not allowed. |
| `Manufacturer 2` | Optional | Approved equivalent manufacturer; otherwise leave empty. |
| `Part Number 2` | Optional | Exact ordering code matching `Manufacturer 2`; otherwise leave empty. |

### ELECTROMECHANICAL

| Parameter | Requirement | Format and examples |
|---|---|---|
| `Type` | Required | Examples: `Relay`, `Switch`, `Rotary Encoder`, `Buzzer`, `Fan`, `Motor`, `Solenoid`. |
| `Coil Voltage` | Required | Relay/solenoid examples: `5VDC`, `12VDC`, `24VDC`, `230VAC`. Use `N/A` when the component has no coil. |
| `Contact Rating` | Required | Examples: `2A@30VDC`, `5A@250VAC`, `10A@250VAC`. Use `N/A` for devices without electrical contacts. |
| `Mounting Type` | Required | Allowed values: `SMT`, `THT`, or `Other`. |
| `Manufacturer 1` | Required | Actual manufacturer; `Generic` is not allowed. Examples: `Omron`, `Panasonic`, `C&K`, `Sunon`. |
| `Part Number 1` | Required | Exact manufacturer ordering code; `Generic` is not allowed. |
| `Manufacturer 2` | Optional | Approved equivalent manufacturer; otherwise leave empty. |
| `Part Number 2` | Optional | Exact ordering code matching `Manufacturer 2`; otherwise leave empty. |

### MODULES

| Parameter | Requirement | Format and examples |
|---|---|---|
| `Function` | Required | Examples: `Wi-Fi/Bluetooth Module`, `System-on-Module`, `GNSS Receiver`, `DC/DC Converter`, `Cellular Modem`, `Display Module`. |
| `Mounting Type` | Required | Allowed values: `SMT`, `THT`, or `Other`. Use `Other` for M.2, cable-mounted, panel-mounted, or board-to-board modules that are not conventional SMT parts. |
| `Manufacturer 1` | Required | Actual manufacturer; `Generic` is not allowed. Examples: `u-blox`, `Espressif`, `Murata`, `Quectel`. |
| `Part Number 1` | Required | Exact manufacturer ordering code; `Generic` is not allowed. |
| `Manufacturer 2` | Optional | Approved equivalent manufacturer; otherwise leave empty. |
| `Part Number 2` | Optional | Exact ordering code matching `Manufacturer 2`; otherwise leave empty. |

### MISC

| Parameter | Requirement | Format and examples |
|---|---|---|
| `Type` | Required | Examples: `Test Point`, `Mounting Hole`, `Fiducial`, `Solder Jumper`, `Logo`, `Mechanical Marker`. |
| `Value` | Required | Examples: `TP`, `M3`, `FID`, `JUMPER`, `LOGO`, `N/A`. |
| `Package` | Required | Examples: `Test Point D1.0mm`, `Mounting Hole D3.2mm`, `Fiducial D1.0mm`, `N/A`. |
| `Mounting Type` | Required | Allowed values: `SMT`, `THT`, or `Other`. Use `Other` for PCB features and purely mechanical items. |
| `Notes` | Optional | Short clarification, for example `Do not populate`, `Bare copper`, `No solder mask`, `Assembly aid only`. |
| `Manufacturer 1` | Required | Use `N/A` or `Generic` for non-purchased PCB features. Use the actual manufacturer for purchased hardware. |
| `Part Number 1` | Required | Use `N/A` or `Generic` for non-purchased PCB features. Otherwise enter the exact ordering code. |
| `Manufacturer 2` | Optional | Approved alternative manufacturer; otherwise leave empty. |
| `Part Number 2` | Optional | Exact ordering code matching `Manufacturer 2`; otherwise leave empty. |

<!-- ALTIUM-CATALOG:START -->

## Compiled Library Contents

> This section is generated by `scripts/update_repository.py`. Do not edit it manually.
> Data is read exclusively from the compiled libraries in `compiled/*.IntLib`.

Total: **4 components** in **15 categories**.

### Category Summary

| Category | Components | IntLib files |
|---|---:|---:|
| CAPACITORS | 0 | 0 |
| CONNECTORS | 0 | 0 |
| CRYSTALS_OSCILLATORS | 0 | 0 |
| DIODES | 0 | 0 |
| ELECTROMECHANICAL | 0 | 0 |
| FERRITES | 0 | 0 |
| IC | 4 | 1 |
| INDUCTORS | 0 | 0 |
| MISC | 0 | 0 |
| MODULES | 0 | 0 |
| OPTOELECTRONICS | 0 | 0 |
| PROTECTION | 0 | 0 |
| RESISTORS | 0 | 0 |
| TRANSFORMERS | 0 | 0 |
| TRANSISTORS | 0 | 0 |

### IC

| Manufacturer part number | Manufacturer | Package |
|---|---|---|
| * | * | * |
| ESP32-C3FH4 | Espressif | QFN32 (5x5mm) |
| LT8619C | Lontium | QFN76 (9x9mm) |
| RP2354B | Raspberry Pi | QFN80 (10x10mm) |

<!-- ALTIUM-CATALOG:END -->
