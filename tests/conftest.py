import sys
from pathlib import Path

# Agrega src/ al path para poder hacer `import banco_distribuido`
# sin necesidad de instalar el paquete (pip install -e .).
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
