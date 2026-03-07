import re


class GrblSim:
    """Simulateur GRBL minimal pour développement sans machine physique."""

    def __init__(self):
        self.pos = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.state = "Idle"
        self.settings = {
            "$0": "10", "$1": "25", "$2": "0", "$3": "0", "$4": "0",
            "$5": "0", "$6": "0", "$10": "1", "$11": "0.010", "$12": "0.002",
            "$13": "0", "$20": "0", "$21": "0", "$22": "0", "$23": "0",
            "$24": "25.000", "$25": "500.000", "$26": "250", "$27": "1.000",
            "$30": "1000", "$31": "0", "$32": "0",
            "$100": "250.000", "$101": "250.000", "$102": "250.000",
            "$110": "500.000", "$111": "500.000", "$112": "500.000",
            "$120": "10.000", "$121": "10.000", "$122": "10.000",
            "$130": "200.000", "$131": "200.000", "$132": "200.000",
        }

    def process(self, cmd: str) -> str:
        cmd = cmd.strip().upper()

        if cmd == "?":
            return f"<{self.state}|MPos:{self.pos['x']:.3f},{self.pos['y']:.3f},{self.pos['z']:.3f}|Bf:15,128|FS:0,0>"

        if cmd == "$$":
            return "\n".join([f"{k}={v}" for k, v in self.settings.items()]) + "\nok"

        if cmd == "\x18":  # soft reset
            self.state = "Idle"
            return "Grbl 1.1h ['$' for help]"

        if cmd in ("$I", ""):
            return "[VER:1.1h.20190825:] ok"

        # G-code basique
        if cmd.startswith("G"):
            match_x = re.search(r"X([-\d.]+)", cmd)
            match_y = re.search(r"Y([-\d.]+)", cmd)
            match_z = re.search(r"Z([-\d.]+)", cmd)
            if match_x:
                self.pos["x"] = float(match_x.group(1))
            if match_y:
                self.pos["y"] = float(match_y.group(1))
            if match_z:
                self.pos["z"] = float(match_z.group(1))
            return "ok"

        # Setting write
        match = re.match(r"\$(\d+)=([\d.]+)", cmd)
        if match:
            key = f"${match.group(1)}"
            self.settings[key] = match.group(2)
            return "ok"

        return "ok"
