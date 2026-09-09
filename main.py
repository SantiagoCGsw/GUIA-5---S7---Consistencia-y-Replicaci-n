#!/usr/bin/env python3
"""
Punto de entrada de conveniencia, para ejecutar la simulación
directamente desde la raíz del repositorio sin necesidad de instalar
el paquete:

    python main.py fuerte
    python main.py sin_lock
"""

import sys
from pathlib import Path

# Permite importar el paquete desde src/ sin necesidad de `pip install -e .`
sys.path.insert(0, str(Path(__file__).parent / "src"))

from banco_distribuido.simulacion import main  # noqa: E402

if __name__ == "__main__":
    main()
